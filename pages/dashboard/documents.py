import streamlit as st
from utils.auth import AuthManager
from database.db_manager import DatabaseManager
from utils.document_processor import DocumentProcessor, process_uploaded_file, cleanup_file
from utils.rag_system import RAGSystem
import os
from pathlib import Path


def show_documents_page(db: DatabaseManager, auth: AuthManager, navigate_to):
    """
    Display the documents management page
    
    Args:
        db: DatabaseManager instance
        auth: AuthManager instance
        navigate_to: Navigation function
    """
    
    # Page header
    st.markdown("""
        <div style='padding: 1rem 0;'>
            <h1 style='color: #667eea'> Documents</h1>
            <p style='color: #764ba2; font-size: 1.1rem;'>Upload and manage your study materials</p>
        </div>
    """, unsafe_allow_html=True)
    
    user_id = auth.get_current_user_id()
    
    # Check Azure settings
    if not auth.has_azure_settings():
        st.warning("⚠️ **Azure OpenAI settings not configured**")
        st.info("You need to configure your Azure OpenAI credentials to process documents and use AI features.")
        if st.button("⚙️ Go to Settings", type="primary"):
            navigate_to('settings')
        return
    
    # Get user subjects
    subjects = db.get_user_subjects(user_id)
    
    if not subjects:
        st.warning("📚 **No subjects found**")
        st.info("You need to create at least one subject before uploading documents.")
        if st.button("➕ Create Subject", type="primary"):
            navigate_to('subjects')
        return
    
    # Subject selector
    st.markdown("### 📚 Select Subject")
    
    # Check if a subject is pre-selected (from navigation)
    selected_subject_id = st.session_state.get('selected_subject_id')
    
    # Create subject options
    subject_options = {f"{s['name']}": s['id'] for s in subjects}
    
    # Find index of pre-selected subject
    if selected_subject_id:
        selected_subject = db.get_subject(selected_subject_id)
        if selected_subject:
            default_index = list(subject_options.keys()).index(selected_subject['name'])
        else:
            default_index = 0
    else:
        default_index = 0
    
    selected_subject_name = st.selectbox(
        "Choose a subject to view or add documents",
        options=list(subject_options.keys()),
        index=default_index,
        key="subject_selector"
    )
    
    current_subject_id = subject_options[selected_subject_name]
    current_subject = db.get_subject(current_subject_id)
    
    # Update session state
    st.session_state.selected_subject_id = current_subject_id
    
    st.markdown("---")
    
    # Action buttons
    col1, col2, col3 = st.columns([2, 2, 6])
    
    with col1:
        if st.button("📤 Upload Document", type="primary", use_container_width=True):
            st.session_state.show_upload_form = True
    
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    st.markdown("---")
    
    # Upload document form
    if st.session_state.get('show_upload_form', False):
        st.markdown("### 📤 Upload New Document")
        
        st.info(f"📚 Uploading to: **{current_subject['name']}**")
        
        with st.form("upload_document_form", clear_on_submit=True):
            uploaded_file = st.file_uploader(
                "Choose a file",
                type=['pdf', 'docx', 'txt', 'md'],
                help="Supported formats: PDF, DOCX, TXT, MD"
            )
            
            document_title = st.text_input(
                "Document Title (optional)",
                placeholder="Leave blank to use filename",
                help="Custom title for this document"
            )
            
            col_upload, col_cancel = st.columns(2)
            
            with col_upload:
                upload = st.form_submit_button("Upload & Process", type="primary", use_container_width=True)
            
            with col_cancel:
                cancel = st.form_submit_button("Cancel", use_container_width=True)
            
            if cancel:
                st.session_state.show_upload_form = False
                st.rerun()
            
            if upload:
                if not uploaded_file:
                    st.error("⚠️ Please select a file to upload")
                else:
                    # Use filename as title if not provided
                    title = document_title if document_title else uploaded_file.name
                    
                    try:
                        with st.spinner("Uploading file..."):
                            # Save uploaded file
                            file_path, file_type = process_uploaded_file(uploaded_file, "uploads")
                            file_size = os.path.getsize(file_path)
                        
                        # Create document record
                        document_id = db.create_document(
                            subject_id=current_subject_id,
                            user_id=user_id,
                            title=title,
                            file_path=file_path,
                            file_type=file_type,
                            file_size=file_size
                        )
                        
                        if document_id:
                            st.success(f"✅ File uploaded: {title}")
                            
                            # Add processing log
                            db.add_processing_log(document_id, "uploaded", "File uploaded successfully")
                            
                            # Process document
                            with st.spinner("Processing document... This may take a moment."):
                                try:
                                    # Update status
                                    db.update_document_processing(document_id, "processing")
                                    db.add_processing_log(document_id, "processing", "Starting document processing")
                                    
                                    # Initialize processor
                                    processor = DocumentProcessor(chunk_size=1000, chunk_overlap=200)
                                    
                                    # Process document
                                    chunk_texts, chunk_metadata, stats = processor.process_document(file_path)
                                    
                                    st.info(f"📊 Extracted {stats['total_chunks']} chunks from document")
                                    
                                    # Get user settings for RAG
                                    settings = db.get_user_settings(user_id)
                                    
                                    # Initialize RAG system
                                    rag = RAGSystem(
                                        azure_api_key=settings['azure_api_key'],
                                        azure_endpoint=settings['azure_endpoint'],
                                        azure_deployment_name=settings['azure_deployment_name'],
                                        azure_api_version=settings['azure_api_version'],
                                        embedding_model=settings['embedding_model']
                                    )
                                    
                                    # Create FAISS index
                                    rag.create_index(chunk_texts, chunk_metadata)
                                    
                                    # Save index
                                    index_dir = f"data/faiss_indices/user_{user_id}"
                                    os.makedirs(index_dir, exist_ok=True)
                                    index_path = f"{index_dir}/doc_{document_id}"
                                    rag.save_index(index_path)
                                    
                                    # Update document with processing results
                                    db.update_document_processing(
                                        document_id=document_id,
                                        status="completed",
                                        faiss_index_path=index_path,
                                        chunk_count=stats['total_chunks']
                                    )
                                    
                                    db.add_processing_log(
                                        document_id,
                                        "completed",
                                        f"Successfully processed {stats['total_chunks']} chunks"
                                    )
                                    
                                    st.success("✅ Document processed successfully!")
                                    st.balloons()
                                    
                                except Exception as e:
                                    st.error(f"❌ Error processing document: {str(e)}")
                                    db.update_document_processing(document_id, "failed")
                                    db.add_processing_log(document_id, "failed", str(e))
                            
                            st.session_state.show_upload_form = False
                            import time
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error("❌ Failed to create document record")
                            cleanup_file(file_path)
                            
                    except Exception as e:
                        st.error(f"❌ Error uploading file: {str(e)}")
        
        st.markdown("---")
    
    # Display documents for selected subject
    documents = db.get_subject_documents(current_subject_id)
    
    if documents:
        st.markdown(f"### 📚 Documents in {current_subject['name']} ({len(documents)})")
        
        # Search documents
        search_term = st.text_input("🔍 Search documents", placeholder="Type to search...")
        
        # Filter documents
        if search_term:
            filtered_docs = [d for d in documents if search_term.lower() in d['title'].lower()]
        else:
            filtered_docs = documents
        
        if not filtered_docs:
            st.info("No documents found matching your search.")
        else:
            # Display documents as cards
            for doc in filtered_docs:
                # Status badge
                status = doc['processing_status']
                if status == 'completed':
                    status_badge = "✅ Ready"
                    status_color = "#4caf50"
                elif status == 'processing':
                    status_badge = "⏳ Processing"
                    status_color = "#ff9800"
                elif status == 'failed':
                    status_badge = "❌ Failed"
                    status_color = "#f44336"
                else:
                    status_badge = "⏸️ Pending"
                    status_color = "#9e9e9e"
                
                # Document card
                with st.container():
                    st.markdown(f"""
                        <div style='background-color: #f8f9fa; padding: 1.5rem; border-radius: 10px; 
                                    border-left: 5px solid {current_subject['color'] if current_subject.get('color') else '#1f77b4'}; 
                                    margin-bottom: 1rem;'>
                            <div style='display: flex; justify-content: space-between; align-items: start;'>
                                <div>
                                    <h3 style='margin: 0 0 0.5rem 0; color: #333;'>📄 {doc['title']}</h3>
                                    <p style='color: #666; font-size: 0.9rem; margin: 0.3rem 0;'>
                                        <strong>Type:</strong> {doc['file_type'].upper()} | 
                                        <strong>Size:</strong> {doc['file_size'] / 1024:.1f} KB | 
                                        <strong>Chunks:</strong> {doc['chunk_count'] if doc['chunk_count'] else 'N/A'}
                                    </p>
                                    <p style='color: #999; font-size: 0.85rem; margin: 0.3rem 0;'>
                                        Uploaded: {doc['upload_date'][:10]}
                                    </p>
                                </div>
                                <div style='background-color: {status_color}; color: white; padding: 0.5rem 1rem; 
                                            border-radius: 5px; font-size: 0.85rem; font-weight: bold;'>
                                    {status_badge}
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Action buttons
                    col_1, col_2, col_3, col_4, col_5, col_6 = st.columns(6)
                    
                    with col_1:
                        if st.button("💬 Chat", key=f"chat_{doc['id']}", 
                                   use_container_width=True, 
                                   disabled=(status != 'completed')):
                            st.session_state.selected_document_id = doc['id']
                            navigate_to('chat')
                    
                    with col_2:
                        if st.button("❓ Quiz", key=f"quiz_{doc['id']}", 
                                   use_container_width=True,
                                   disabled=(status != 'completed')):
                            st.session_state.selected_document_id = doc['id']
                            navigate_to('quiz')
                    
                    with col_3:
                        if st.button("🎴 Cards", key=f"flash_{doc['id']}", 
                                   use_container_width=True,
                                   disabled=(status != 'completed')):
                            st.session_state.selected_document_id = doc['id']
                            navigate_to('flashcard')
                    
                    with col_4:
                        if st.button("📊 Info", key=f"info_{doc['id']}", 
                                   use_container_width=True):
                            st.session_state.viewing_document_id = doc['id']
                            st.rerun()
                    
                    with col_5:
                        if st.button("🔄 Reprocess", key=f"reprocess_{doc['id']}", 
                                   use_container_width=True,
                                   disabled=(status == 'processing')):
                            st.session_state.reprocessing_document_id = doc['id']
                            st.rerun()
                    
                    with col_6:
                        if st.button("🗑️ Delete", key=f"delete_{doc['id']}", 
                                   use_container_width=True):
                            st.session_state.deleting_document_id = doc['id']
                            st.rerun()
                    
                    st.markdown("---")
            
            # Document info dialog
            if st.session_state.get('viewing_document_id'):
                viewing_id = st.session_state.viewing_document_id
                doc_info = db.get_document(viewing_id)
                
                if doc_info:
                    st.markdown("---")
                    st.markdown(f"### 📊 Document Information: {doc_info['title']}")
                    
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        st.write(f"**Title:** {doc_info['title']}")
                        st.write(f"**File Type:** {doc_info['file_type'].upper()}")
                        st.write(f"**File Size:** {doc_info['file_size'] / 1024:.2f} KB")
                        st.write(f"**Upload Date:** {doc_info['upload_date']}")
                    
                    with col_b:
                        st.write(f"**Status:** {doc_info['processing_status']}")
                        st.write(f"**Chunks:** {doc_info['chunk_count'] if doc_info['chunk_count'] else 'N/A'}")
                        st.write(f"**Index Path:** {doc_info['faiss_index_path'] if doc_info['faiss_index_path'] else 'N/A'}")
                    
                    # Processing logs
                    st.markdown("#### 📝 Processing Logs")
                    logs = db.get_processing_logs(viewing_id)
                    
                    if logs:
                        for log in logs:
                            st.text(f"[{log['timestamp'][:19]}] {log['status']}: {log['message']}")
                    else:
                        st.info("No processing logs available")
                    
                    if st.button("Close", use_container_width=True):
                        st.session_state.viewing_document_id = None
                        st.rerun()
            
            # Reprocess confirmation
            if st.session_state.get('reprocessing_document_id'):
                st.markdown("---")
                reprocess_id = st.session_state.reprocessing_document_id
                doc_reprocess = db.get_document(reprocess_id)
                
                if doc_reprocess:
                    st.warning(f"### 🔄 Reprocess Document: {doc_reprocess['title']}?")
                    st.info("This will re-extract text and recreate the FAISS index. Existing chat history will be preserved.")
                    
                    col_yes, col_no = st.columns(2)
                    
                    with col_yes:
                        if st.button("Yes, Reprocess", type="primary", use_container_width=True):
                            # Implement reprocessing logic (similar to upload)
                            st.info("Reprocessing... (implement full reprocessing logic)")
                            st.session_state.reprocessing_document_id = None
                            # TODO: Add full reprocessing implementation
                    
                    with col_no:
                        if st.button("Cancel", use_container_width=True):
                            st.session_state.reprocessing_document_id = None
                            st.rerun()
            
            # Delete confirmation
            if st.session_state.get('deleting_document_id'):
                st.markdown("---")
                deleting_id = st.session_state.deleting_document_id
                doc_delete = db.get_document(deleting_id)
                
                if doc_delete:
                    st.error(f"### ⚠️ Delete Document: {doc_delete['title']}?")
                    st.warning("""
                    **Warning:** This will permanently delete:
                    - The document and its file
                    - All associated chat history
                    - All quizzes and flashcards
                    - The FAISS index
                    
                    This action cannot be undone!
                    """)
                    
                    col_yes, col_no = st.columns(2)
                    
                    with col_yes:
                        if st.button("🗑️ Yes, Delete", type="primary", use_container_width=True):
                            try:
                                # Delete FAISS index files
                                if doc_delete['faiss_index_path']:
                                    cleanup_file(f"{doc_delete['faiss_index_path']}.faiss")
                                    cleanup_file(f"{doc_delete['faiss_index_path']}.pkl")
                                
                                # Delete uploaded file
                                cleanup_file(doc_delete['file_path'])
                                
                                # Delete from database (cascades to related data)
                                db.delete_document(deleting_id)
                                
                                st.success(f"✅ Document '{doc_delete['title']}' deleted successfully!")
                                st.session_state.deleting_document_id = None
                                import time
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error deleting document: {str(e)}")
                    
                    with col_no:
                        if st.button("Cancel", use_container_width=True):
                            st.session_state.deleting_document_id = None
                            st.rerun()
    else:
        # Empty state
        st.info(f"📄 **No documents in {current_subject['name']} yet**")
        st.markdown("""
        Upload your first document to get started! Supported formats:
        - **PDF** (.pdf) - Textbooks, papers, lecture notes
        - **Word** (.docx) - Essays, study guides
        - **Text** (.txt, .md) - Notes, summaries
        """)
        
        if st.button("📤 Upload First Document", type="primary"):
            st.session_state.show_upload_form = True
            st.rerun()
    
    # Back to dashboard
    st.markdown("---")
    if st.button("← Back to Dashboard", use_container_width=True):
        navigate_to('dashboard')