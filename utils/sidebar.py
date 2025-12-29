# utils/sidebar.py - Updated with active page highlighting

import streamlit as st
from utils.auth import AuthManager
from config.ui_styles import load_image_base64

def apply_sidebar_styles():
    """Apply consistent sidebar styling"""
    st.markdown("""
        <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
        }
        
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
            color: white;
        }
        
        /* Sidebar Headers */
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            color: white !important;
        }
        
        /* Sidebar Buttons - Default State */
        [data-testid="stSidebar"] .stButton > button {
            background: rgba(255, 255, 255, 0.15);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 10px;
            font-weight: 600;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        }
        
        [data-testid="stSidebar"] .stButton > button:hover {
            background: rgba(255, 255, 255, 0.25);
            border-color: rgba(255, 255, 255, 0.5);
            transform: translateX(5px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }
        
        /* Active Page Button Styling */
        [data-testid="stSidebar"] .stButton > button[kind="primary"] {
            background: #764ba2 !important;
            color: #667eea !important;
            border: 2px solid white !important;
            font-weight: 700 !important;
            box-shadow: 0 5px 20px rgba(255, 255, 255, 0.3) !important;
        }
        
        [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
            background: rgba(255, 255, 255, 0.95) !important;
            transform: translateX(5px);
        }
        
        [data-testid="stSidebar"] .stButton > button:active {
            background: rgba(255, 255, 255, 0.3);
        }
        
        /* Logo Container */
        .sidebar-logo {
            text-align: center;
            padding: 1rem 0 0.5rem 0;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            margin-bottom: 1rem;
            backdrop-filter: blur(10px);
        }
        
        .sidebar-logo img {
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }
        
        /* User Info Card */
        .user-info-card {
            background: rgba(255, 255, 255, 0.15);
            padding: 1rem;
            border-radius: 15px;
            color: white;
            margin-bottom: 1rem;
            border: 1px solid rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(10px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }
        
        .user-info-card strong {
            font-size: 1.1rem;
            display: block;
            margin-bottom: 0.3rem;
        }
        
        .user-info-card small {
            opacity: 0.9;
            font-size: 0.85rem;
        }
        
        /* Section Headers */
        .sidebar-section-header {
            color: white;
            font-size: 0.9rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin: 1.5rem 0 0.8rem 0;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid rgba(255, 255, 255, 0.3);
        }
        
        /* Info Box */
        .sidebar-info-box {
            background: rgba(255, 255, 255, 0.1);
            padding: 1rem;
            border-radius: 10px;
            border-left: 3px solid rgba(255, 255, 255, 0.5);
            margin: 1rem 0;
            backdrop-filter: blur(10px);
        }
        
        .sidebar-info-box ul {
            margin: 0.5rem 0 0 0;
            padding-left: 1.2rem;
        }
        
        .sidebar-info-box li {
            margin: 0.3rem 0;
            line-height: 1.4;
        }
        
        /* Divider */
        [data-testid="stSidebar"] hr {
            border-color: rgba(255, 255, 255, 0.3);
            margin: 1.5rem 0;
        }
        
        /* Navigation Icon Spacing */
        .nav-icon {
            margin-right: 0.5rem;
        }
        </style>
    """, unsafe_allow_html=True)


def show_logo():
    """Display app logo in sidebar"""
    img_base64 = load_image_base64("images/logo2.png")
    st.markdown(
        f"""
        <div class="sidebar-logo">
            <img src="data:image/png;base64,{img_base64}" alt="AI Study Assistant" 
                 style="width:80%; border-radius:10px;">
        </div>
        """,
        unsafe_allow_html=True
    )


def show_user_info(auth: AuthManager):
    """Display user info card"""
    user = auth.get_current_user()
    st.markdown(
        f"""
        <div class="user-info-card">
            <strong> Welcome back!</strong>
            <div style="font-size: 1.05rem; margin-top: 0.5rem;">
                {auth.get_current_username()}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def show_authenticated_sidebar(auth: AuthManager, navigate_to, current_page: str = None):
    """Show sidebar for authenticated users"""
    
    # Logo
    show_logo()
    
    # User info
    show_user_info(auth)
    
    st.markdown('<div class="sidebar-section-header"> Dashboard</div>', unsafe_allow_html=True)
    
    # Navigation items with active state
    nav_items = [
        ("🏠", "Overview", "dashboard"),
        ("📖", "Subjects", "subjects"),
        ("📄", "Documents", "documents"),
        ("💬", "Chat", "chat"),
        ("❓", "Quizzes", "quiz"),
        ("🎴", "Flashcards", "flashcard"),
        ("📅", "Study Planner", "planner"),
    ]
    
    for icon, label, page in nav_items:
        # Set button type based on current page
        is_active = current_page == page
        button_type = "primary" if is_active else "secondary"
        
        if st.button(
            f"{icon} {label}", 
            use_container_width=True, 
            key=f"nav_{page}", 
            type=button_type
        ):
            navigate_to(page)
    
    st.markdown("---")
    
    # Settings and logout section
    st.markdown('<div class="sidebar-section-header"> Account</div>', unsafe_allow_html=True)
    
    # Settings button with active state
    is_settings_active = current_page == "settings"
    if st.button(
        "⚙️ Settings", 
        use_container_width=True, 
        key="nav_settings",
        type="primary" if is_settings_active else "secondary"
    ):
        navigate_to("settings")
    
    if st.button("🚪 Logout", use_container_width=True, key="nav_logout"):
        auth.logout()
        navigate_to("home")
    
    st.markdown("---")

def show_guest_sidebar(navigate_to, current_page: str = None):
    """Show sidebar for non-authenticated users"""
    
    # Logo
    show_logo()
    
    # Welcome message
    st.markdown(
        """
        <div class="user-info-card">
            <strong> Welcome to</strong>
            <div style="font-size: 1.2rem; margin-top: 0.5rem; font-weight: 700;">
                AI Study Assistant
            </div>
            <small style="display: block; margin-top: 0.5rem;">
                Your AI-powered learning companion
            </small>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown('<div class="sidebar-section-header"> Get Started</div>', unsafe_allow_html=True)
    
    # Navigation for guests
    guest_nav = [
        ("🏠", "Home", "home"),
        ("🔐", "Login", "login"),
        ("📝", "Sign Up", "signup"),
    ]
    
    for icon, label, page in guest_nav:
        # Set button type based on current page
        is_active = current_page == page
        button_type = "primary" if is_active else "secondary"
        
        if st.button(
            f"{icon} {label}", 
            use_container_width=True, 
            key=f"guest_{page}", 
            type=button_type
        ):
            navigate_to(page)
    
    st.markdown("---")
    
    # Features preview
    st.markdown('<div class="sidebar-section-header"> Features</div>', unsafe_allow_html=True)
    
    st.markdown(
        """
        <div class="sidebar-info-box">
            <ul style="list-style: none; padding-left: 0;">
                <li>📚 Organize study materials</li>
                <li>💬 Chat with documents</li>
                <li>❓ Generate quizzes</li>
                <li>🎴 Create flashcards</li>
                <li>📅 Plan your studies</li>
                <li>🔒 Secure & private</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("---")

def render_sidebar(auth: AuthManager, navigate_to, current_page: str = None):
    """ Main function to render the sidebar"""
    apply_sidebar_styles()
    
    with st.sidebar:
        if auth.is_authenticated():
            show_authenticated_sidebar(auth, navigate_to, current_page)
        else:
            show_guest_sidebar(navigate_to, current_page)
        