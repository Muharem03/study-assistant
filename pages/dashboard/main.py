import streamlit as st
from utils.auth import AuthManager
from database.db_manager import DatabaseManager
from datetime import datetime, timedelta


def show_dashboard_page(db: DatabaseManager, auth: AuthManager, navigate_to):
    """
    Display the main dashboard/overview page
    
    Args:
        db: DatabaseManager instance
        auth: AuthManager instance
        navigate_to: Navigation function
    """
    
    # Page header
    st.markdown(f"""
        <div style='padding: 1rem 0;'>
            <h1 style='color: #667eea ;'> Dashboard</h1>
            <p style='color: #764ba2; font-size: 1.1rem;'>Welcome back, <strong>{auth.get_current_username()}</strong>!</p>
        </div>
    """, unsafe_allow_html=True)
    
    user_id = auth.get_current_user_id()
    
    # Check if user has configured Azure settings
    settings = auth.get_user_settings()
    
    if not auth.has_azure_settings():
        st.warning("⚠️ **Action Required: Configure Azure OpenAI Settings**")
        st.info("""
        To start using the AI features, you need to add your Azure OpenAI credentials.
        
        **You'll need:**
        - Azure OpenAI API Key
        - Azure OpenAI Endpoint URL
        - Deployment Name
        - API Version
        """)
        
        if st.button("⚙️ Go to Settings", type="primary"):
            navigate_to('settings')
        
        st.markdown("---")
    
    # Statistics cards
    st.markdown("### 📈 Your Study Statistics")
    
    # Get statistics
    subjects = db.get_user_subjects(user_id)
    total_subjects = len(subjects)
    
    # Count total documents
    total_documents = 0
    for subject in subjects:
        documents = db.get_subject_documents(subject['id'])
        total_documents += len(documents)
    
    # Count total tasks
    all_tasks = db.get_user_tasks(user_id)
    pending_tasks = len([t for t in all_tasks if t['status'] == 'pending'])
    completed_tasks = len([t for t in all_tasks if t['status'] == 'completed'])
    
    # Display stats in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
            <div style='background-color: #e3f2fd; padding: 1.5rem; border-radius: 10px; text-align: center;'>
                <h2 style='color: #1976d2; margin: 0; font-size: 2.5rem;'>{total_subjects}</h2>
                <p style='color: #666; margin: 0.5rem 0 0 0;'>Subjects</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div style='background-color: #f3e5f5; padding: 1.5rem; border-radius: 10px; text-align: center;'>
                <h2 style='color: #7b1fa2; margin: 0; font-size: 2.5rem;'>{total_documents}</h2>
                <p style='color: #666; margin: 0.5rem 0 0 0;'>Documents</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div style='background-color: #fff3e0; padding: 1.5rem; border-radius: 10px; text-align: center;'>
                <h2 style='color: #f57c00; margin: 0; font-size: 2.5rem;'>{pending_tasks}</h2>
                <p style='color: #666; margin: 0.5rem 0 0 0;'>Pending Tasks</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
            <div style='background-color: #e8f5e9; padding: 1.5rem; border-radius: 10px; text-align: center;'>
                <h2 style='color: #388e3c; margin: 0; font-size: 2.5rem;'>{completed_tasks}</h2>
                <p style='color: #666; margin: 0.5rem 0 0 0;'>Completed Tasks</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quick actions
    st.markdown("### ⚡ Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("➕ Add Subject", use_container_width=True, type="primary"):
            navigate_to('subjects')
    
    with col2:
        if st.button("📄 Upload Document", use_container_width=True, type="primary"):
            navigate_to('documents')
    
    with col3:
        if st.button("💬 Start Chatting", use_container_width=True, type="primary"):
            navigate_to('chat')
    
    with col4:
        if st.button("📅 Add Task", use_container_width=True, type="primary"):
            navigate_to('planner')
    
    st.markdown("---")
    
    # Two column layout for subjects and tasks
    col_left, col_right = st.columns([3, 2])
    
    with col_left:
        # Recent subjects
        st.markdown("### 📚 Your Subjects")
        
        if subjects:
            for subject in subjects[:5]:  # Show up to 5 subjects
                with st.expander(f"📖 {subject['name']}", expanded=False):
                    if subject['description']:
                        st.write(subject['description'])
                    else:
                        st.write("*No description*")
                    
                    # Get document count for this subject
                    docs = db.get_subject_documents(subject['id'])
                    st.write(f"**Documents:** {len(docs)}")
                    
                    # Action buttons
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        if st.button("View", key=f"view_subject_{subject['id']}", use_container_width=True):
                            st.session_state.selected_subject_id = subject['id']
                            navigate_to('documents')
                    with col_b:
                        if st.button("Chat", key=f"chat_subject_{subject['id']}", use_container_width=True):
                            st.session_state.selected_subject_id = subject['id']
                            navigate_to('chat')
                    with col_c:
                        if st.button("Quiz", key=f"quiz_subject_{subject['id']}", use_container_width=True):
                            st.session_state.selected_subject_id = subject['id']
                            navigate_to('quiz')
            
            if len(subjects) > 5:
                st.info(f"Showing 5 of {len(subjects)} subjects. View all in the Subjects page.")
                if st.button("View All Subjects"):
                    navigate_to('subjects')
        else:
            st.info("No subjects yet. Create your first subject to get started!")
            if st.button("Create First Subject", type="primary"):
                navigate_to('subjects')
    
    with col_right:
        # Upcoming tasks
        st.markdown("### 📅 Upcoming Tasks")
        
        # Get tasks due in the next 7 days
        today = datetime.now().date()
        upcoming_tasks = []
        
        for task in all_tasks:
            if task['status'] != 'completed' and task['due_date']:
                try:
                    due_date = datetime.strptime(task['due_date'], '%Y-%m-%d').date()
                    if due_date >= today and due_date <= today + timedelta(days=7):
                        upcoming_tasks.append(task)
                except:
                    pass
        
        # Sort by due date
        upcoming_tasks.sort(key=lambda x: x['due_date'])
        
        if upcoming_tasks:
            for task in upcoming_tasks[:5]:  # Show up to 5 tasks
                due_date = datetime.strptime(task['due_date'], '%Y-%m-%d').date()
                days_until = (due_date - today).days
                
                # Color code by urgency
                if days_until == 0:
                    urgency_color = "#f44336"
                    urgency_text = "📌 Due Today!"
                elif days_until == 1:
                    urgency_color = "#ff9800"
                    urgency_text = "⚠️ Due Tomorrow"
                else:
                    urgency_color = "#4caf50"
                    urgency_text = f"📆 Due in {days_until} days"
                
                st.markdown(f"""
                    <div style='background-color: #f5f5f5; padding: 1rem; border-radius: 8px; 
                                margin-bottom: 0.5rem; border-left: 4px solid {urgency_color};'>
                        <p style='margin: 0; font-weight: bold;'>{task['title']}</p>
                        <p style='margin: 0.5rem 0 0 0; font-size: 0.9rem; color: {urgency_color};'>
                            {urgency_text}
                        </p>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown("")
            if st.button("View All Tasks", use_container_width=True):
                navigate_to('planner')
        else:
            st.info("No upcoming tasks in the next 7 days.")
            if st.button("Create a Task", type="primary", use_container_width=True):
                navigate_to('planner')
        
        # Pending tasks summary
        if pending_tasks > 0:
            st.markdown("---")
            st.warning(f"⏳ You have **{pending_tasks}** pending task(s)")
    
    st.markdown("---")
    
    # Activity tips
    st.markdown("### 💡 Study Tips")
    
    tips = [
        "📚 Review your flashcards regularly to improve retention",
        "❓ Take quizzes to test your understanding",
        "💬 Ask questions about concepts you find difficult",
        "📅 Set realistic deadlines for your study tasks",
        "🎯 Focus on one subject at a time for better concentration",
        "🔄 Use spaced repetition for long-term memory",
        "✍️ Take breaks every 25-30 minutes (Pomodoro technique)",
        "🎨 Use the AI to generate different types of study materials"
    ]
    
    import random
    daily_tip = random.choice(tips)
    
    st.info(f"**Tip of the day:** {daily_tip}")
    
    # Footer stats
    st.markdown("---")
    st.markdown(f"""
        <div style='text-align: center; color: #666; padding: 1rem 0;'>
            <p style='margin: 0;'>
                Account created: {auth.get_current_user()['created_at'][:10]} | 
                Last login: {auth.get_current_user()['last_login'][:10] if auth.get_current_user()['last_login'] else 'First time'}
            </p>
        </div>
    """, unsafe_allow_html=True)