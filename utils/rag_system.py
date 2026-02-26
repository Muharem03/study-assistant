import os
from typing import List, Dict, Optional, Tuple
import numpy as np
import faiss
from openai import AzureOpenAI
import pickle


class RAGSystem:
    """
   RAG System with Cosine Similarity
    """
    
    def __init__(self, azure_api_key: str, azure_endpoint: str, 
                 azure_deployment_name: str, azure_api_version: str = "2024-02-15-preview",
                 embedding_model: str = "text-embedding-ada-002"):
        """
        Initialize RAG system with Azure OpenAI credentials
        """
        self.client = AzureOpenAI(
            api_key=azure_api_key,
            api_version=azure_api_version,
            azure_endpoint=azure_endpoint
        )
        self.deployment_name = azure_deployment_name
        self.embedding_model = embedding_model
        self.index = None
        self.chunks = []
        self.metadata = []
        
        # Model configurations
        self.model_configs = {
            "text-embedding-ada-002": {"dimension": 1536, "max_tokens": 8191},
            "text-embedding-3-small": {"dimension": 1536, "max_tokens": 8191},
            "text-embedding-3-large": {"dimension": 3072, "max_tokens": 8191}
        }
        
        # Get dimension for selected model
        self.dimension = self.model_configs.get(embedding_model, {}).get("dimension", 1536)
    
    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Create embeddings for a list of texts using Azure OpenAI
        """
        embeddings = []
        
        # Process in batches to avoid rate limits
        batch_size = 100
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            response = self.client.embeddings.create(
                input=batch,
                model=self.embedding_model
            )
            
            batch_embeddings = [item.embedding for item in response.data]
            embeddings.extend(batch_embeddings)
        
        # Convert to numpy array
        embeddings_array = np.array(embeddings, dtype='float32')
        
        # CRITICAL: Normalize vectors for cosine similarity
        norms = np.linalg.norm(embeddings_array, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)  # Avoid division by zero
        normalized_embeddings = embeddings_array / norms
        
        return normalized_embeddings
    
    def create_index(self, chunks: List[str], metadata: Optional[List[Dict]] = None) -> faiss.Index:
        """
        Create FAISS index with COSINE SIMILARITY
        """
        self.chunks = chunks
        self.metadata = metadata if metadata else [{"index": i} for i in range(len(chunks))]
        
        # Create normalized embeddings
        embeddings = self.create_embeddings(chunks)
        
        # Use IndexFlatIP (Inner Product) for cosine similarity
        self.index = faiss.IndexFlatIP(self.dimension)
        self.index.add(embeddings)
        
        return self.index
    
    def save_index(self, index_path: str):
        """
        Save FAISS index and associated data to disk
        """
        if self.index is None:
            raise ValueError("No index to save. Create an index first.")
        
        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, f"{index_path}.faiss")
        
        # Save chunks, metadata, and model info
        with open(f"{index_path}.pkl", 'wb') as f:
            pickle.dump({
                'chunks': self.chunks,
                'metadata': self.metadata,
                'embedding_model': self.embedding_model,
                'dimension': self.dimension
            }, f)
    
    def load_index(self, index_path: str):
        """
        Load FAISS index and associated data from disk
        """
        # Load FAISS index
        self.index = faiss.read_index(f"{index_path}.faiss")
        
        # Load chunks and metadata
        with open(f"{index_path}.pkl", 'rb') as f:
            data = pickle.load(f)
            self.chunks = data['chunks']
            self.metadata = data['metadata']
            # Load model info if available
            if 'embedding_model' in data:
                self.embedding_model = data['embedding_model']
                self.dimension = data['dimension']
    
    def search(self, query: str, k: int = 5) -> List[Tuple[str, Dict, float]]:
        """
        Search for relevant chunks using COSINE SIMILARITY
        """
        if self.index is None:
            raise ValueError("No index loaded. Create or load an index first.")
        
        # Create normalized query embedding
        query_embedding = self.create_embeddings([query])
        
        # Search using inner product (cosine similarity)
        similarities, indices = self.index.search(query_embedding, k)
        
        # Return results
        results = []
        for idx, similarity in zip(indices[0], similarities[0]):
            if idx < len(self.chunks):
                results.append((
                    self.chunks[idx],
                    self.metadata[idx],
                    float(similarity)  #  0-1 range!
                ))
        
        return results
    
    def generate_response(self, query: str, context_chunks: List[str], 
                         chat_history: Optional[List[Dict]] = None,
                         system_prompt: Optional[str] = None,
                         temperature: float = 0.7,
                         max_tokens: int = 1000) -> str:
        """
        Generate a response using Azure OpenAI with RAG context
        
        Args:
            query: User's question
            context_chunks: Retrieved relevant chunks
            chat_history: Previous chat messages
            system_prompt: Custom system prompt
            temperature: Response randomness (0-1)
            max_tokens: Maximum tokens in response
            
        Returns:
            Generated response
        """
        # Build context from chunks
        context = "\n\n".join([f"[Context {i+1}]\n{chunk}" 
                               for i, chunk in enumerate(context_chunks)])
        
        # Default system prompt
        if system_prompt is None:
            system_prompt = """You are a helpful AI study assistant. Answer questions based on the provided context from the user's documents. 
If the context doesn't contain enough information to answer the question, say so clearly. 
Be concise, accurate, and educational in your responses.Give answers in the language they are asked"""
        
        # Build messages
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add chat history if provided
        if chat_history:
            messages.extend(chat_history)
        
        # Add current query with context
        user_message = f"""Context from your documents:
{context}

Question: {query}

Please answer based on the context above."""
        
        messages.append({"role": "user", "content": user_message})
        
        # Generate response
        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
    
    def chat(self, query: str, k: int = 5, max_tokens: int = 1000, 
             chat_history: Optional[List[Dict]] = None,
             temperature: float = 0.7) -> Tuple[str, List[Tuple]]:
        """
        Complete RAG chat flow: retrieve relevant chunks and generate response
        
        Args:
            query: User's question
            k: Number of chunks to retrieve
            chat_history: Previous chat messages
            temperature: Response randomness
            
        Returns:
            Tuple of (response, sources_used)
        """
        # Search for relevant chunks
        search_results = self.search(query, k=k)
        
        # Extract chunks and prepare sources
        context_chunks = [result[0] for result in search_results]
        sources = [(result[0], result[1], result[2]) for result in search_results]
        
        # Generate response
        response = self.generate_response(
            query=query,
            context_chunks=context_chunks,
            chat_history=chat_history,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response, sources
    
    def generate_quiz_questions(self, num_questions: int = 5, 
                               difficulty: str = "medium",
                               topic: Optional[str] = None) -> str:
        """
        Generate quiz questions from the document content
        
        Args:
            num_questions: Number of questions to generate
            difficulty: Difficulty level (easy, medium, hard)
            topic: Optional specific topic to focus on
            
        Returns:
            JSON string with quiz questions
        """
        # Sample chunks for quiz generation
        num_chunks = min(max(5, num_questions // 2), len(self.chunks))
        sample_indices = np.random.choice(len(self.chunks), num_chunks, replace=False)
        sample_chunks = [self.chunks[i] for i in sample_indices]
        
        context = "\n\n".join(sample_chunks)
        
        topic_text = f" focusing on {topic}" if topic else ""
        
        prompt = f"""Based on the following content, generate {num_questions} multiple-choice questions at a {difficulty} difficulty level{topic_text}.
                Always provide the questions and answers in the same language as the content below.

Content:
{context}

For each question, provide:
1. The question text
2. Four answer options (A, B, C, D)
3. The correct answer (letter)
4. A brief explanation of why it's correct

Format your response as a JSON array of objects with keys: question, option_a, option_b, option_c, option_d, correct_answer, explanation"""
        
        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=[
                {"role": "system", "content": "You are an educational quiz generator. Create clear, accurate questions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=2000
        )
        
        return response.choices[0].message.content
    
    def generate_flashcards(self, num_cards: int = 10,
                           topic: Optional[str] = None) -> str:
        """
        Generate flashcards from the document content
        
        Args:
            num_cards: Number of flashcards to generate
            topic: Optional specific topic to focus on
            
        Returns:
            JSON string with flashcards
        """
        # Sample chunks for flashcard generation
        num_chunks = min(max(10, num_cards // 2), len(self.chunks))
        sample_indices = np.random.choice(len(self.chunks), num_chunks, replace=False)
        sample_chunks = [self.chunks[i] for i in sample_indices]
        
        context = "\n\n".join(sample_chunks)
        
        topic_text = f" focusing on {topic}" if topic else ""
        
        prompt = f"""Based on the following content, generate {num_cards} flashcards{topic_text}.
        Always provide the questions and answers in the same language as the content below.


Content:
{context}

For each flashcard, provide:
- Front: A question, term, or concept
- Back: The answer, definition, or explanation

Format your response as a JSON array of objects with keys: front, back"""
        
        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=[
                {"role": "system", "content": "You are an educational flashcard generator. Create clear, concise cards."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        return response.choices[0].message.content