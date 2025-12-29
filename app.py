# app.py

import streamlit as st
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from database.db_manager import DatabaseManager
from utils.auth import AuthManager
from utils.sidebar import render_sidebar  # Import the new sidebar

# Page configuration
st.set_page_config(
    page_title="AI Study Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)
# Initialize session state keys only if missing
st.session_state.setdefault("user", None)
st.session_state.setdefault("user_id", None)
st.session_state.setdefault("current_page", "home")
# Initialize database and auth
@st.cache_resource
def get_database():
    """Initialize and return database manager"""
    return DatabaseManager("study_assistant.db")

@st.cache_resource
def get_auth_manager(_db):
    """Initialize and return auth manager"""
    return AuthManager(_db)

# Get instances
db = get_database()
auth = get_auth_manager(db)

# Initialize session state for navigation
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'home'

if 'selected_subject_id' not in st.session_state:
    st.session_state.selected_subject_id = None

if 'selected_document_id' not in st.session_state:
    st.session_state.selected_document_id = None

# Navigation functions
def navigate_to(page: str):
    """Navigate to a specific page"""
    st.session_state.current_page = page
    st.rerun()

# Page routing
def route_page():
    """Route to the appropriate page based on current_page state"""
    page = st.session_state.current_page
    
    # Import pages dynamically to avoid circular imports
    if page == 'home':
        from pages.home import show_home_page
        show_home_page(auth, navigate_to)
    
    elif page == 'login':
        from pages.login import show_login_page
        show_login_page(auth, navigate_to)
    
    elif page == 'signup':
        from pages.signup import show_signup_page
        show_signup_page(auth, navigate_to)
    
    elif page == 'dashboard':
        auth.require_authentication()
        from pages.dashboard.main import show_dashboard_page
        show_dashboard_page(db, auth, navigate_to)
    
    elif page == 'subjects':
        auth.require_authentication()
        from pages.dashboard.subjects import show_subjects_page
        show_subjects_page(db, auth, navigate_to)
    
    elif page == 'documents':
        auth.require_authentication()
        from pages.dashboard.documents import show_documents_page
        show_documents_page(db, auth, navigate_to)
    
    elif page == 'chat':
        auth.require_authentication()
        from pages.dashboard.chat import show_chat_page
        show_chat_page(db, auth, navigate_to)
    
    elif page == 'quiz':
        auth.require_authentication()
        from pages.dashboard.quiz import show_quiz_page
        show_quiz_page(db, auth, navigate_to)
    
    elif page == 'flashcard':
        auth.require_authentication()
        from pages.dashboard.flashcard import show_flashcard_page
        show_flashcard_page(db, auth, navigate_to)
    
    elif page == 'planner':
        auth.require_authentication()
        from pages.dashboard.planner import show_planner_page
        show_planner_page(db, auth, navigate_to)
    
    elif page == 'settings':
        auth.require_authentication()
        from pages.dashboard.settings import show_settings_page
        show_settings_page(db, auth, navigate_to)
    
    else:
        st.error(f"Page '{page}' not found")
        if st.button("Go to Home"):
            navigate_to('home')

# Main app
def main():
    """Main application entry point"""
    
    # Show unified sidebar
    render_sidebar(auth, navigate_to, st.session_state.current_page)
    
    # Route to appropriate page
    route_page()

if __name__ == "__main__":
    main()