import os
from typing import List, Dict, Optional, Tuple
import numpy as np
import faiss
from openai import AzureOpenAI
import pickle


class RAGSystem:
    """Retrieval-Augmented Generation system using FAISS and Azure OpenAI"""
    
    def __init__(self, azure_api_key: str, azure_endpoint: str, 
                 azure_deployment_name: str, azure_api_version: str = "2024-02-15-preview",
                 embedding_model: str = "text-embedding-ada-002"):
        """
        Initialize RAG system with Azure OpenAI credentials
        
        Args:
            azure_api_key: Azure OpenAI API key
            azure_endpoint: Azure OpenAI endpoint URL
            azure_deployment_name: Deployment name for the chat model
            azure_api_version: API version
            embedding_model: Model name for embeddings
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
    
    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Create embeddings for a list of texts using Azure OpenAI
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            numpy array of embeddings
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
        
        return np.array(embeddings, dtype='float32')
    
    def create_index(self, chunks: List[str], metadata: Optional[List[Dict]] = None) -> faiss.Index:
        """
        Create FAISS index from text chunks
        
        Args:
            chunks: List of text chunks
            metadata: Optional metadata for each chunk (page number, section, etc.)
            
        Returns:
            FAISS index
        """
        self.chunks = chunks
        self.metadata = metadata if metadata else [{"index": i} for i in range(len(chunks))]
        
        # Create embeddings
        embeddings = self.create_embeddings(chunks)
        
        # Create FAISS index
        dimension = embeddings.shape[1]  # Should be 1536 for text-embedding-ada-002
        self.index = faiss.IndexFlatL2(dimension)  # L2 distance
        self.index.add(embeddings)
        
        return self.index
    
    def save_index(self, index_path: str):
        """
        Save FAISS index and associated data to disk
        
        Args:
            index_path: Path to save the index (without extension)
        """
        if self.index is None:
            raise ValueError("No index to save. Create an index first.")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, f"{index_path}.faiss")
        
        # Save chunks and metadata
        with open(f"{index_path}.pkl", 'wb') as f:
            pickle.dump({
                'chunks': self.chunks,
                'metadata': self.metadata
            }, f)
    
    def load_index(self, index_path: str):
        """
        Load FAISS index and associated data from disk
        
        Args:
            index_path: Path to the index (without extension)
        """
        # Load FAISS index
        self.index = faiss.read_index(f"{index_path}.faiss")
        
        # Load chunks and metadata
        with open(f"{index_path}.pkl", 'rb') as f:
            data = pickle.load(f)
            self.chunks = data['chunks']
            self.metadata = data['metadata']
    
    def search(self, query: str, k: int = 5) -> List[Tuple[str, Dict, float]]:
        """
        Search for relevant chunks using the query
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of tuples (chunk_text, metadata, distance)
        """
        if self.index is None:
            raise ValueError("No index loaded. Create or load an index first.")
        
        # Create query embedding
        query_embedding = self.create_embeddings([query])
        
        # Search
        distances, indices = self.index.search(query_embedding, k)
        
        # Return results
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.chunks):  # Valid index
                results.append((
                    self.chunks[idx],
                    self.metadata[idx],
                    float(distance)
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
Be concise, accurate, and educational in your responses."""
        
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
    
    def chat(self, query: str, k: int = 5, 
             chat_history: Optional[List[Dict]] = None,
             temperature: float = 0.7) -> Tuple[str, List[Dict]]:
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
        
        # Extract chunks and metadata
        context_chunks = [result[0] for result in search_results]
        sources = []
        for chunk_text, metadata, distance in search_results:
            sources.append({
                "text": chunk_text,
                "metadata": metadata,
                "distance": distance
            })

        # Generate response
        response = self.generate_response(
            query=query,
            context_chunks=context_chunks,
            chat_history=chat_history,
            temperature=temperature
        )
        
        return response, sources
    
    def generate_quiz_questions(self, num_questions: int = 5, 
                               difficulty: str = "medium",
                               topic: Optional[str] = None) -> List[Dict]:
        """
        Generate quiz questions from the document content
        
        Args:
            num_questions: Number of questions to generate
            difficulty: Difficulty level (easy, medium, hard)
            topic: Optional specific topic to focus on
            
        Returns:
            List of quiz questions with answers
        """
        # Sample chunks for quiz generation (more chunks = better coverage)
        num_chunks = min(10, len(self.chunks))
        sample_indices = np.random.choice(len(self.chunks), num_chunks, replace=False)
        sample_chunks = [self.chunks[i] for i in sample_indices]
        
        context = "\n\n".join(sample_chunks)
        
        topic_text = f" focusing on {topic}" if topic else ""
        
        prompt = f"""Based on the following content, generate {num_questions} multiple-choice questions at a {difficulty} difficulty level{topic_text}.

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
        
        # Parse response ()
        return response.choices[0].message.content
    
    def generate_flashcards(self, num_cards: int = 10,
                           topic: Optional[str] = None) -> List[Dict]:
        """
        Generate flashcards from the document content
        
        Args:
            num_cards: Number of flashcards to generate
            topic: Optional specific topic to focus on
            
        Returns:
            List of flashcards with front/back
        """
        # Sample chunks for flashcard generation
        num_chunks = min(10, len(self.chunks))
        sample_indices = np.random.choice(len(self.chunks), num_chunks, replace=False)
        sample_chunks = [self.chunks[i] for i in sample_indices]
        
        context = "\n\n".join(sample_chunks)
        
        topic_text = f" focusing on {topic}" if topic else ""
        
        prompt = f"""Based on the following content, generate {num_cards} flashcards{topic_text}.

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
    
    def summarize_document(self, max_length: int = 500) -> str:
        """
        Generate a summary of the entire document
        
        Args:
            max_length: Maximum length of summary in words
            
        Returns:
            Document summary
        """
        # Sample chunks across the document
        num_chunks = min(20, len(self.chunks))
        step = len(self.chunks) // num_chunks if num_chunks > 0 else 1
        sample_chunks = [self.chunks[i] for i in range(0, len(self.chunks), step)]
        
        context = "\n\n".join(sample_chunks)
        
        prompt = f"""Please provide a comprehensive summary of the following document in approximately {max_length} words. 
Cover the main topics, key concepts, and important points.

Document content:
{context}"""
        
        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=[
                {"role": "system", "content": "You are a document summarization expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=max_length * 2  # Rough token estimation
        )
        
        return response.choices[0].message.content