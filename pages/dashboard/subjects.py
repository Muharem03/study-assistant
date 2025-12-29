import streamlit as st
from utils.auth import AuthManager
from database.db_manager import DatabaseManager


def show_subjects_page(db: DatabaseManager, auth: AuthManager, navigate_to):
    """
    Display the subjects management page
    
    Args:
        db: DatabaseManager instance
        auth: AuthManager instance
        navigate_to: Navigation function
    """
    
    # Page header
    st.markdown("""
        <div style='padding: 1rem 0;'>
            <h1 style='color: #667eea;'> Subjects</h1>
            <p style='color: #764ba2; font-size: 1.1rem;'>Organize your study materials by subject</p>
        </div>
    """, unsafe_allow_html=True)
    
    user_id = auth.get_current_user_id()
    
    # Get all subjects
    subjects = db.get_user_subjects(user_id)
    
    # Action buttons
    col1, col2, col3 = st.columns([2, 2, 6])
    
    with col1:
        if st.button("➕ Create Subject", type="primary", use_container_width=True):
            st.session_state.show_create_form = True
            st.session_state.show_edit_form = False
    
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    st.markdown("---")
    
    # Create subject form
    if st.session_state.get('show_create_form', False):
        st.markdown("### ➕ Create New Subject")
        
        with st.form("create_subject_form", clear_on_submit=True):
            subject_name = st.text_input(
                "Subject Name *",
                placeholder="e.g., Computer Science, Mathematics, History",
                max_chars=100
            )
            
            subject_description = st.text_area(
                "Description",
                placeholder="Brief description of this subject (optional)",
                max_chars=500,
                height=100
            )
            
            # Color picker for subject
            colors = {
                "Blue": "#1f77b4",
                "Green": "#2ca02c",
                "Red": "#d62728",
                "Purple": "#9467bd",
                "Orange": "#ff7f0e",
                "Pink": "#e377c2",
                "Brown": "#8c564b",
                "Gray": "#7f7f7f"
            }
            
            col_a, col_b = st.columns([3, 1])
            with col_a:
                selected_color_name = st.selectbox(
                    "Color (for organization)",
                    options=list(colors.keys()),
                    help="Choose a color to help identify this subject"
                )
            with col_b:
                st.markdown(f"""
                    <div style='width: 100%; height: 50px; background-color: {colors[selected_color_name]}; 
                                border-radius: 5px; margin-top: 1.8rem;'></div>
                """, unsafe_allow_html=True)
            
            subject_color = colors[selected_color_name]
            
            col_submit, col_cancel = st.columns(2)
            
            with col_submit:
                submit = st.form_submit_button("Create Subject", type="primary", use_container_width=True)
            
            with col_cancel:
                cancel = st.form_submit_button("Cancel", use_container_width=True)
            
            if submit:
                if not subject_name:
                    st.error("⚠️ Please enter a subject name")
                else:
                    try:
                        subject_id = db.create_subject(
                            user_id=user_id,
                            name=subject_name,
                            description=subject_description,
                            color=subject_color
                        )
                        
                        if subject_id:
                            st.success(f"✅ Subject '{subject_name}' created successfully!")
                            st.session_state.show_create_form = False
                            import time
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Failed to create subject")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
            
            if cancel:
                st.session_state.show_create_form = False
                st.rerun()
        
        st.markdown("---")
    
    # Display subjects
    if subjects:
        st.markdown(f"### 📚 Your Subjects ({len(subjects)})")
        
        # Search/filter
        search_term = st.text_input("🔍 Search subjects", placeholder="Type to search...")
        
        # Filter subjects by search term
        if search_term:
            filtered_subjects = [s for s in subjects if search_term.lower() in s['name'].lower() 
                               or (s['description'] and search_term.lower() in s['description'].lower())]
        else:
            filtered_subjects = subjects
        
        if not filtered_subjects:
            st.info("No subjects found matching your search.")
        else:
            # Display subjects in a grid
            cols_per_row = 2
            for i in range(0, len(filtered_subjects), cols_per_row):
                cols = st.columns(cols_per_row)
                
                for j, col in enumerate(cols):
                    idx = i + j
                    if idx < len(filtered_subjects):
                        subject = filtered_subjects[idx]
                        
                        with col:
                            # Get document count
                            docs = db.get_subject_documents(subject['id'])
                            doc_count = len(docs)
                            
                            # Subject card
                            card_color = subject['color'] if subject.get('color') else '#1f77b4'
                            
                            st.markdown(f"""
                                <div style='background-color: #f8f9fa; padding: 1.5rem; border-radius: 10px; 
                                            border-left: 5px solid {card_color}; margin-bottom: 1rem; min-height: 200px;'>
                                    <h3 style='margin: 0 0 0.5rem 0; color: {card_color};'>
                                        📖 {subject['name']}
                                    </h3>
                                    <p style='color: #666; font-size: 0.9rem; margin: 0.5rem 0;'>
                                        {subject['description'] if subject['description'] else '<em>No description</em>'}
                                    </p>
                                    <p style='color: #999; font-size: 0.85rem; margin-top: 1rem;'>
                                        📄 {doc_count} document{'s' if doc_count != 1 else ''}
                                    </p>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            # Action buttons
                            col_1, col_2, col_3, col_4 = st.columns(4)
                            
                            with col_1:
                                if st.button("📄", key=f"docs_{subject['id']}", 
                                           help="View documents", use_container_width=True):
                                    st.session_state.selected_subject_id = subject['id']
                                    navigate_to('documents')
                            
                            with col_2:
                                if st.button("💬", key=f"chat_{subject['id']}", 
                                           help="Chat", use_container_width=True):
                                    st.session_state.selected_subject_id = subject['id']
                                    navigate_to('chat')
                            
                            with col_3:
                                if st.button("✏️", key=f"edit_{subject['id']}", 
                                           help="Edit subject", use_container_width=True):
                                    st.session_state.editing_subject_id = subject['id']
                                    st.session_state.show_edit_form = True
                                    st.session_state.show_create_form = False
                                    st.rerun()
                            
                            with col_4:
                                if st.button("🗑️", key=f"delete_{subject['id']}", 
                                           help="Delete subject", use_container_width=True):
                                    st.session_state.deleting_subject_id = subject['id']
                                    st.rerun()
            
            # Edit subject form
            if st.session_state.get('show_edit_form', False):
                st.markdown("---")
                editing_id = st.session_state.get('editing_subject_id')
                subject_to_edit = db.get_subject(editing_id)
                
                if subject_to_edit:
                    st.markdown(f"### ✏️ Edit Subject: {subject_to_edit['name']}")
                    
                    with st.form("edit_subject_form"):
                        edit_name = st.text_input(
                            "Subject Name *",
                            value=subject_to_edit['name'],
                            max_chars=100
                        )
                        
                        edit_description = st.text_area(
                            "Description",
                            value=subject_to_edit['description'] if subject_to_edit['description'] else "",
                            max_chars=500,
                            height=100
                        )
                        
                        # Color picker
                        colors = {
                            "Blue": "#1f77b4",
                            "Green": "#2ca02c",
                            "Red": "#d62728",
                            "Purple": "#9467bd",
                            "Orange": "#ff7f0e",
                            "Pink": "#e377c2",
                            "Brown": "#8c564b",
                            "Gray": "#7f7f7f"
                        }
                        
                        # Find current color
                        current_color = subject_to_edit.get('color', '#1f77b4')
                        current_color_name = next((name for name, hex_val in colors.items() 
                                                  if hex_val == current_color), "Blue")
                        
                        col_a, col_b = st.columns([3, 1])
                        with col_a:
                            selected_color_name = st.selectbox(
                                "Color",
                                options=list(colors.keys()),
                                index=list(colors.keys()).index(current_color_name)
                            )
                        with col_b:
                            st.markdown(f"""
                                <div style='width: 100%; height: 50px; background-color: {colors[selected_color_name]}; 
                                            border-radius: 5px; margin-top: 1.8rem;'></div>
                            """, unsafe_allow_html=True)
                        
                        edit_color = colors[selected_color_name]
                        
                        col_save, col_cancel = st.columns(2)
                        
                        with col_save:
                            save = st.form_submit_button("Save Changes", type="primary", use_container_width=True)
                        
                        with col_cancel:
                            cancel = st.form_submit_button("Cancel", use_container_width=True)
                        
                        if save:
                            if not edit_name:
                                st.error("⚠️ Please enter a subject name")
                            else:
                                try:
                                    db.update_subject(
                                        subject_id=editing_id,
                                        name=edit_name,
                                        description=edit_description,
                                        color=edit_color
                                    )
                                    st.success(f"✅ Subject '{edit_name}' updated successfully!")
                                    st.session_state.show_edit_form = False
                                    st.session_state.editing_subject_id = None
                                    import time
                                    time.sleep(1)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error: {str(e)}")
                        
                        if cancel:
                            st.session_state.show_edit_form = False
                            st.session_state.editing_subject_id = None
                            st.rerun()
            
            # Delete confirmation dialog
            if st.session_state.get('deleting_subject_id'):
                st.markdown("---")
                deleting_id = st.session_state.deleting_subject_id
                subject_to_delete = db.get_subject(deleting_id)
                
                if subject_to_delete:
                    st.error(f"### ⚠️ Delete Subject: {subject_to_delete['name']}?")
                    
                    docs = db.get_subject_documents(deleting_id)
                    doc_count = len(docs)
                    
                    st.warning(f"""
                    **Warning:** This will permanently delete:
                    - The subject "{subject_to_delete['name']}"
                    - All {doc_count} document(s) in this subject
                    - All associated chat history, quizzes, and flashcards
                    
                    This action cannot be undone!
                    """)
                    
                    col_confirm, col_cancel = st.columns(2)
                    
                    with col_confirm:
                        if st.button("🗑️ Yes, Delete", type="primary", use_container_width=True):
                            try:
                                db.delete_subject(deleting_id)
                                st.success(f"✅ Subject '{subject_to_delete['name']}' deleted successfully!")
                                st.session_state.deleting_subject_id = None
                                import time
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
                    
                    with col_cancel:
                        if st.button("Cancel", use_container_width=True):
                            st.session_state.deleting_subject_id = None
                            st.rerun()
    else:
        # Empty state
        st.info("📚 **No subjects yet**")
        st.markdown("""
        Get started by creating your first subject! Subjects help you organize your study materials by course or topic.
        
        **Examples:**
        - Computer Science
        - Mathematics
        - History
        - Biology
        - Literature
        """)
        
        if st.button("➕ Create Your First Subject", type="primary"):
            st.session_state.show_create_form = True
            st.rerun()
    
    # Back to dashboard
    st.markdown("---")
    if st.button("← Back to Dashboard", use_container_width=True):
        navigate_to('dashboard')