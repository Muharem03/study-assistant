import streamlit as st
from config.ui_styles import load_image_base64,apply_page_styles
from utils.auth import AuthManager


def show_home_page(auth: AuthManager, navigate_to):
    """
     home page 
    """
    
    # Custom CSS 
    apply_page_styles('home')
    
    # Hero Section
    if auth.is_authenticated():
        st.markdown(f"""
            <div class="hero-section">
                <h1 class="hero-title">Welcome Back, {auth.get_current_username()}!</h1>
                <p class="hero-subtitle">Ready to continue your learning journey?</p>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(" Go to Dashboard", type="primary", use_container_width=True):
                navigate_to('dashboard')
        
        st.markdown("---")
    else:
        img_base64 = load_image_base64("images/logo4.png")

        st.markdown(
           f"""
            <style>
            .hero-seection {{
                background-image: linear-gradient(rgba(0, 0, 0, 0.45), rgba(0, 0, 0, 0.45)), url("data:image/png;base64,{img_base64}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                padding: 4rem 2rem;
                border-radius: 20px;
                text-align: center;
                color: white;
                margin-bottom: 3rem;
                box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
                min-height: 470px;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            </style>

            <div class="hero-seection">
                <h1 class="hero-title">AI Study Assistant</h1>
                <p class="hero-subtitle">
                Transform your study materials into interactive learning experiences. 
                Chat with your documents, generate instant quizzes, and master your subjects with AI-powered Flashcards.
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Features Section
    st.markdown("## Powerful Features")
    st.markdown("")
    
    col1, col2, col3 = st.columns(3)
    
    features = [
        {
            "icon": "📖",
            "title": "Smart Organization",
            "text": "Organize your materials by subjects. Upload unlimited documents. Automatic text extraction and intelligent processing."
        },
        {
            "icon": "💬",
            "title": "AI Chat Assistant",
            "text": "Ask questions and get instant answers from your documents. Context-aware responses with source citations."
        },
        {
            "icon": "❓",
            "title": "Quiz Generator",
            "text": "Auto-generate practice quizzes from your content. With multiple difficulty levels. Track your progress and scores over time."
        },
        {
            "icon": "🎴",
            "title": "Smart Flashcards",
            "text": "AI-created flashcards from your materials. Spaced repetition algorithm. Perfect for memorization and quick review."
        },
        {
            "icon": "📅",
            "title": "Study Planner",
            "text": "Create and manage study tasks. Set deadlines and priorities. Never miss an important assignment again."
        },
        {
            "icon": "🔒",
            "title": "Privacy First",
            "text": "Your data stays yours. Encrypted credential storage. Use your own Azure OpenAI API. Complete data control."
        }
    ]
    
    for i, feature in enumerate(features):
        col = [col1, col2, col3][i % 3]
        with col:
            st.markdown(f"""
                <div class="feature-card">
                    <span class="feature-icon">{feature['icon']}</span>
                    <div class="feature-title">{feature['title']}</div>
                    <div class="feature-text">{feature['text']}</div>
                </div>
            """, unsafe_allow_html=True)
            st.markdown("")
    
    # How it Works
    st.markdown("---")
    st.markdown("## How It Works")
    st.markdown("")
    
    col1, col2, col3, col4 = st.columns(4)
    
    steps = [
        {"num": "1", "title": "Sign Up", "text": "Create your free account in seconds"},
        {"num": "2", "title": "Configure", "text": "Add your Azure OpenAI credentials"},
        {"num": "3", "title": "Upload", "text": "Add your study materials"},
        {"num": "4", "title": "Learn", "text": "Chat, quiz, and study smarter"}
    ]
    
    for col, step in zip([col1, col2, col3, col4], steps):
        with col:
            st.markdown(f"""
                <div class="step-container">
                    <div class="step-number">{step['num']}</div>
                    <div class="step-title">{step['title']}</div>
                    <div class="step-text">{step['text']}</div>
                </div>
            """, unsafe_allow_html=True)
    
    # Technology Stack
    st.markdown("---")
    st.markdown("## Powered By Advanced Technology")
    st.markdown("")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            <div style="text-align: center; padding: 2rem;">
                <h3 style="color: #667eea; margin-bottom: 1.5rem;">AI & Search</h3>
                <span class="tech-badge">🤖 Azure OpenAI</span>
                <span class="tech-badge">🧠 GPT-4</span>
                <span class="tech-badge">🔍 FAISS Vector Search</span>
                <span class="tech-badge">📊 RAG Architecture</span>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div style="text-align: center; padding: 2rem;">
                <h3 style="color: #667eea; margin-bottom: 1.5rem;">Development</h3>
                <span class="tech-badge">🐍 Python</span>
                <span class="tech-badge">🎈 Streamlit</span>
                <span class="tech-badge">🗄️ SQLite</span>
                <span class="tech-badge">🔐 Encryption</span>
            </div>
        """, unsafe_allow_html=True)
    
    # What is RAG?
    st.markdown("---")
    st.markdown("## What Makes This Special?")
    st.markdown("")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("""
            <div style="background: linear-gradient(180deg, #0f1c3f 0%, #3b82f6 100%);; 
                        padding: 2rem; border-radius: 15px; color: white; height: 100%;">
                <h3 style="margin-top: 0;">🧠 RAG Technology</h3>
                <p style="font-size: 1.05rem; line-height: 1.8;">
                    <strong>Retrieval-Augmented Generation</strong> combines the power of search with AI intelligence:
                </p>
                <ul style="font-size: 1.05rem; line-height: 1.8;">
                    <li>Finds relevant content from YOUR documents</li>
                    <li>Provides context to the AI</li>
                    <li>Generates accurate, source-based answers</li>
                    <li>Reduces AI "hallucinations"</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div style="background: linear-gradient(180deg, #0b102a 0%, #4facfe 100%); 
                        padding: 2rem; border-radius: 15px; color: white; height: 100%;">
                <h3 style="margin-top: 0;">🔒 Your Privacy Matters</h3>
                <p style="font-size: 1.05rem; line-height: 1.8;">
                    We take security seriously:
                </p>
                <ul style="font-size: 1.05rem; line-height: 1.8;">
                    <li>Encrypted API key storage</li>
                    <li>Bcrypt password hashing</li>
                    <li>Local document storage</li>
                    <li>Your own Azure OpenAI instance</li>
                </ul>
                <p style="font-size: 1.05rem; margin-bottom: 0;">
                    <strong>Your data never leaves your control!</strong>
                </p>
            </div>
        """, unsafe_allow_html=True)
    
    # CTA Section
    if not auth.is_authenticated():
        st.markdown("---")
        st.markdown("""
            <div class="cta-section">
                <h2 class="cta-title">Ready to Study Smarter? 🎓</h2>
                <p class="cta-text">Join students who are transforming their learning with AI</p>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            col_a, col_b = st.columns(2)
            
            with col_a:
                if st.button(" Sign Up Now", type="primary", use_container_width=True):
                    navigate_to('signup')
            
            with col_b:
                if st.button(" Login", use_container_width=True):
                    navigate_to('login')
    
    # Why Choose Us
    st.markdown("---")
    st.markdown("## Why Choose AI Study Assistant?")
    st.markdown("")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            <div style="text-align: center; padding: 1.5rem;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">⚡</div>
                <h4 style="color: #667eea;">Lightning Fast</h4>
                <p style="color: #666;">Get answers in seconds, not hours. FAISS-powered search finds relevant content instantly.</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div style="text-align: center; padding: 1.5rem;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🎯</div>
                <h4 style="color: #667eea;">Accurate Results</h4>
                <p style="color: #666;">RAG technology ensures answers come from your actual documents, not generic knowledge.</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div style="text-align: center; padding: 1.5rem;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🔧</div>
                <h4 style="color: #667eea;">Easy to Use</h4>
                <p style="color: #666;">Intuitive interface designed for students. No technical knowledge required.</p>
            </div>
        """, unsafe_allow_html=True)
    
    # Getting Started Guide
    st.markdown("---")
    st.markdown("## Getting Started Guide")
    st.markdown("")
    
    with st.expander("📝 Step-by-Step Setup", expanded=False):
        st.markdown("""
            ### 1️⃣ Create Azure OpenAI Account
            - Visit [Azure Portal](https://portal.azure.com)
            - Create an Azure OpenAI resource
            - Deploy a GPT model
            - Note your API key, endpoint, and deployment name
            
            ### 2️⃣ Sign Up for AI Study Assistant
            - Click "Sign Up" above
            - Create your account with email and password
            - Verify your account
            
            ### 3️⃣ Configure Settings
            - Go to Settings after login
            - Enter your Azure OpenAI credentials
            - Test the connection
            
            ### 4️⃣ Start Learning
            - Create subjects for your courses
            - Upload your study materials
            - Start chatting, creating quizzes, and studying!
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; padding: 2rem 0;'>
            <div style="margin-top: 1rem;">
                <span class="tech-badge" style="font-size: 0.9rem;">🚀 Powered by AI</span>
                <span class="tech-badge" style="font-size: 0.9rem;">🔒 Secure</span>
                <span class="tech-badge" style="font-size: 0.9rem;">📚 Student-Focused</span>
            </div>
        </div>
    """, unsafe_allow_html=True)