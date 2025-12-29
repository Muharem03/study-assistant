import streamlit as st
from utils.auth import AuthManager


def show_signup_page(auth: AuthManager, navigate_to):
    """
    Display the signup/registration page
    
    Args:
        auth: AuthManager instance
        navigate_to: Navigation function
    """
    
    # Center the signup form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Header
        st.markdown("""
            <div style='text-align: center; padding: 2rem 0 1rem 0;'>
                <h1 style='color: #1f77b4;'> Sign Up</h1>
                <p style='color: #666;'>Create your account and start studying smarter</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Signup form
        with st.form("signup_form", clear_on_submit=False):
            email = st.text_input(
                "Email *",
                placeholder="your.email@example.com",
                help="We'll never share your email with anyone"
            )
            
            username = st.text_input(
                "Username *",
                placeholder="Choose a unique username",
                help="3-20 characters, letters, numbers, and underscores only",
                max_chars=20
            )
            
            col_pass1, col_pass2 = st.columns(2)
            
            with col_pass1:
                password = st.text_input(
                    "Password *",
                    type="password",
                    placeholder="Create a strong password"
                )
            
            with col_pass2:
                confirm_password = st.text_input(
                    "Confirm Password *",
                    type="password",
                    placeholder="Re-enter your password"
                )
            
            # Password requirements info
            with st.expander("ℹ️ Password Requirements"):
                st.markdown("""
                Your password must contain:
                - At least **8 characters**
                - At least **one uppercase letter** (A-Z)
                - At least **one lowercase letter** (a-z)
                - At least **one digit** (0-9)
                """)
            
            # Submit buttons
            col_a, col_b = st.columns(2)
            with col_a:
                submit = st.form_submit_button("Create Account", type="primary", use_container_width=True)
            with col_b:
                if st.form_submit_button("Cancel", use_container_width=True):
                    navigate_to('home')
            
            if submit:
                # Validate inputs
                if not all([email, username, password, confirm_password]):
                    st.error("⚠️ Please fill in all required fields")
                else:
                    # Attempt signup
                    with st.spinner("Creating your account..."):
                        success, message = auth.signup(email, username, password, confirm_password)
                    
                    if success:
                        st.success(f"✅ {message}")
                        st.balloons()
                        st.info("👉 Please login with your new credentials")
                        
                        # Small delay then navigate to login
                        import time
                        time.sleep(2)
                        navigate_to('login')
                    else:
                        st.error(f"❌ {message}")
        
        # Divider
        st.markdown("---")
        
        # Link to login
        st.markdown("**Already have an account?**")
        if st.button("Login Here", use_container_width=True):
            navigate_to('login')
        
        # Info boxes
        st.markdown("---")
        
        # What you'll get
        st.success("""
        **✨ What you'll get with your account:**
        
        - 📚 Unlimited subjects and documents
        - 💬 AI-powered chat with your materials
        - ❓ Automatic quiz generation
        - 🎴 Smart flashcard creation
        - 📅 Integrated study planner
        - 🔐 Secure, encrypted data storage
        """)
        
        # Privacy notice
        st.info("""
        **🔒 Your Privacy Matters**
        
        We take your privacy seriously. Your documents and API keys are stored securely and encrypted. 
        We never share your data with third parties. You maintain full control over your information.
        """)
        
        # Back to home link
        st.markdown("""
            <div style='text-align: center; margin-top: 2rem;'>
                <p style='color: #666;'>
                    Want to learn more first?
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("← Back to Home", use_container_width=True):
            navigate_to('home')