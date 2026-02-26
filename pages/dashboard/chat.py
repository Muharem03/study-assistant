import streamlit as st
from utils.auth import AuthManager
from database.db_manager import DatabaseManager
from utils.rag_system import RAGSystem
from datetime import datetime


def show_chat_page(db: DatabaseManager, auth: AuthManager, navigate_to):
    """
     chat interface for documents
    """
    
    # Page header
    st.markdown("""
        <div style='padding: 1rem 0;'>
            <h1 style='color: #667eea;'> Chat with Documents</h1>
            <p style='color: #764ba2; font-size: 1.1rem;'>Ask questions and get answers from your study materials</p>
        </div>
    """, unsafe_allow_html=True)
    
    user_id = auth.get_current_user_id()
    
    # Check Azure settings
    if not auth.has_azure_settings():
        st.warning("⚠️ **Azure OpenAI settings not configured**")
        if st.button("⚙️ Go to Settings", type="primary"):
            navigate_to('settings')
        return
    
    # Get user settings
    settings = db.get_user_settings(user_id)
    
    # Get subjects
    subjects = db.get_user_subjects(user_id)
    
    if not subjects:
        st.warning("📚 **No subjects found**")
        st.info("Create a subject and upload documents first.")
        if st.button("➕ Create Subject", type="primary"):
            navigate_to('subjects')
        return
    
    # Subject selector
    st.markdown("### 📚 Select Subject")
    
    selected_subject_id = st.session_state.get('selected_subject_id')
    subject_options = {f"{s['name']}": s['id'] for s in subjects}
    
    if selected_subject_id:
        selected_subject = db.get_subject(selected_subject_id)
        if selected_subject:
            default_index = list(subject_options.keys()).index(selected_subject['name'])
        else:
            default_index = 0
    else:
        default_index = 0
    
    selected_subject_name = st.selectbox(
        "Choose a subject",
        options=list(subject_options.keys()),
        index=default_index,
        key="chat_subject_selector"
    )
    
    current_subject_id = subject_options[selected_subject_name]
    st.session_state.selected_subject_id = current_subject_id
    
    # Get documents for subject
    documents = db.get_subject_documents(current_subject_id)
    completed_docs = [d for d in documents if d['processing_status'] == 'completed']
    
    if not completed_docs:
        st.warning(f"📄 **No processed documents in this subject**")
        st.info("Upload and process documents first.")
        if st.button("📤 Upload Document", type="primary"):
            navigate_to('documents')
        return
    
    # Document selector
    st.markdown("### 📄 Select Document")
    
    selected_document_id = st.session_state.get('selected_document_id')
    doc_options = {f"{d['title']}": d['id'] for d in completed_docs}
    
    if selected_document_id and selected_document_id in doc_options.values():
        selected_doc = db.get_document(selected_document_id)
        if selected_doc:
            default_doc_index = list(doc_options.keys()).index(selected_doc['title'])
        else:
            default_doc_index = 0
    else:
        default_doc_index = 0
    
    selected_doc_name = st.selectbox(
        "Choose a document to chat with",
        options=list(doc_options.keys()),
        index=default_doc_index,
        key="chat_document_selector"
    )
    
    current_document_id = doc_options[selected_doc_name]
    current_document = db.get_document(current_document_id)
    st.session_state.selected_document_id = current_document_id
    
    # Tips
    st.markdown("---")
    st.markdown("### 💡 Tips for Better Answers")
    with st.expander("How to ask effective questions"):
        st.markdown("""
        **✅ Good Questions:**
        - "What is the definition of [term]?"
        - "Explain the relationship between [concept A] and [concept B]"
        - "What are the steps in [process]?"
        - "Compare and contrast [X] and [Y]"
        
        **❌ Avoid:**
        - Very vague questions without context
        - Questions about topics not in the document
        - Asking for opinions (AI provides factual information from documents)
        
        **💡 Pro Tips:**
        - Be specific about what you want to know
        - Reference specific sections or concepts
        - Ask follow-up questions to dive deeper
        - Adjust temperature for more creative or focused responses
        """)
    
    # Initialize chat session state
    chat_key = f"chat_messages_{current_document_id}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []
    
    st.markdown("---")
    
    # Chat settings in expander
    with st.expander("⚙️ Chat Settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.1,
                help="Higher = more creative, Lower = more focused"
            )
            
            num_chunks = st.slider(
                "Context Chunks",
                min_value=3,
                max_value=10,
                value=5,
                help="Number of relevant chunks to retrieve"
            )
        
        with col2:
            max_tokens = st.slider(
                "Max Response Length",
                min_value=100,
                max_value=2000,
                value=1000,
                step=100,
                help="Maximum tokens in response"
            )
            
            show_sources = st.checkbox(
                "Show Sources",
                value=True,
                help="Display source chunks used for response"
            )
    
    # Action buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔄 New Chat", use_container_width=True):
            st.session_state[chat_key] = []
            st.rerun()
    
    with col2:
        if st.button("💾 Save History", use_container_width=True):
            # Save current chat to database
            if st.session_state[chat_key]:
                for msg in st.session_state[chat_key]:
                    if not msg.get('saved', False):
                        db.add_chat_message(
                            document_id=current_document_id,
                            user_id=user_id,
                            role=msg['role'],
                            message=msg['content']
                        )
                        msg['saved'] = True
                st.success("✅ Chat history saved!")
            else:
                st.info("No messages to save")
    
    with col3:
        if st.button("📜 Load History", use_container_width=True):
            history = db.get_chat_history(current_document_id, limit=50)
            if history:
                st.session_state[chat_key] = [
                    {'role': h['role'], 'content': h['message'], 'saved': True}
                    for h in history
                ]
                st.success(f"✅ Loaded {len(history)} messages")
                st.rerun()
            else:
                st.info("No previous chat history")
    
    with col4:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            if st.session_state[chat_key]:
                st.session_state.confirm_clear_chat = True
                st.rerun()
            else:
                st.info("Chat is already empty")
    
    # Clear confirmation dialog
    if st.session_state.get('confirm_clear_chat', False):
        st.warning("⚠️ **Clear current chat?** This will only clear the current session, not saved history.")
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("Yes, Clear", type="primary", use_container_width=True):
                st.session_state[chat_key] = []
                st.session_state.confirm_clear_chat = False
                st.rerun()
        with col_no:
            if st.button("Cancel", use_container_width=True):
                st.session_state.confirm_clear_chat = False
                st.rerun()
    
    st.markdown("---")
    
    # Display document info
    st.info(f"💬 Chatting with: **{current_document['title']}** ({current_document['chunk_count']} chunks)")
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        # Display chat messages
        for message in st.session_state[chat_key]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # Show sources if available 
                if message["role"] == "assistant" and message.get("sources"):
                    if show_sources and message["sources"]:
                        with st.expander("📚 View Sources", expanded=False):
                            for i, source in enumerate(message["sources"], 1):
                                st.markdown(f"**Source {i}:**")
                                source_text = source.get('text', '')
                                source_metadata = source.get('metadata', {})
                                
                                # Show the text
                                if len(source_text) > 300:
                                    st.text(source_text[:300] + "...")
                                else:
                                    st.text(source_text)
                                
                                # Show metadata
                                if source_metadata:
                                    meta_str = ", ".join([f"{k}: {v}" for k, v in source_metadata.items()])
                                    st.caption(f"📍 {meta_str}")
                                
                                if i < len(message["sources"]):
                                    st.markdown("---")
    
    # Chat input
    if prompt := st.chat_input("Ask a question about the document..."):
        # Add user message to chat
        st.session_state[chat_key].append({"role": "user", "content": prompt, "saved": False})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Initialize RAG system
                    rag = RAGSystem(
                        azure_api_key=settings['azure_api_key'],
                        azure_endpoint=settings['azure_endpoint'],
                        azure_deployment_name=settings['azure_deployment_name'],
                        azure_api_version=settings['azure_api_version'],
                        embedding_model=settings['embedding_model']
                    )
                    
                    # Load FAISS index
                    rag.load_index(current_document['faiss_index_path'])
                    
                    # Prepare chat history for context (last 5 messages)
                    chat_history = []
                    for msg in st.session_state[chat_key][-6:-1]:  # Exclude the current message
                        chat_history.append({
                            "role": msg["role"],
                            "content": msg["content"]
                        })
                    
                    # Get response with RAG
                    response, sources = rag.chat(
                        query=prompt,
                        k=num_chunks,
                        max_tokens=max_tokens,
                        chat_history=chat_history if chat_history else None,
                        temperature=temperature
                    )
                    
                    # Display response
                    st.markdown(response)
                    
                    # Prepare sources for storage
                    sources_for_storage = []
                    if sources:
                        for source in sources:
                            if isinstance(source, dict):
                                sources_for_storage.append({
                                    "text": source.get("text", ""),
                                    "metadata": source.get("metadata", {}),
                                    "distance": source.get("distance", None)
                                })
                            # Fallback for tuple format 
                            elif isinstance(source, tuple) and len(source) >= 2:
                                sources_for_storage.append({
                                    "text": source[0],
                                    "metadata": source[1],
                                    "distance": source[2] if len(source) > 2 else None
                                })
                    
                    # Show sources if enabled
                    if show_sources and sources_for_storage:
                        with st.expander(f"📚 View Sources ({len(sources_for_storage)})"):
                            with st.container(height=280, border=True):
                                for i, source in enumerate(sources_for_storage, 1):
                                    st.markdown(f"**Source {i}:**")
                                    chunk_text = source.get("text", "")
                                    st.code(chunk_text[:600] + ("..." if len(chunk_text) > 600 else ""), language="text")

                                    if source.get("metadata"):
                                        st.caption(f"Metadata: {source['metadata']}")
                                    if source.get("distance") is not None:
                                        st.caption(f"Similarity score: {source['distance']:.4f}")

                                    st.divider()

                           
                    
                    # Add assistant response to chat
                    st.session_state[chat_key].append({
                        "role": "assistant",
                        "content": response,
                        "sources": sources_for_storage,
                        "saved": False
                    })
                    
                except Exception as e:
                    error_message = f"Error: {str(e)}"
                    st.error(f"❌ Error generating response: {error_message}")
                
                    st.session_state[chat_key].append({
                        "role": "assistant",
                        "content": f"I encountered an error: {error_message}",
                        "sources": None,
                        "saved": False
                    })
    
    # Welcome message when chat is empty
    if not st.session_state[chat_key]:
        st.markdown("---")
        st.info("""
        💡 **Ready to chat!** 
        
        Ask questions about the document like:
        - "What are the main topics covered?"
        - "Can you summarize the key points?"
        - "Explain [specific concept] in detail"
        - "What are the important takeaways?"
        """)
    
    
    