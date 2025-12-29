import streamlit as st
from utils.auth import AuthManager


def show_login_page(auth: AuthManager, navigate_to):
    """
    Display the login page
    
    Args:
        auth: AuthManager instance
        navigate_to: Navigation function
    """
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Header
        st.markdown("""
            <div style='text-align: center; padding: 2rem 0 1rem 0;'>
                <h1 style='color: #1f77b4;'> Login</h1>
                <p style='color: #666;'>Welcome back! Please login to your account</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Login form
        with st.form("login_form", clear_on_submit=False):
            email_or_username = st.text_input(
                "Email or Username",
                placeholder="Enter your email or username",
                help="You can login with either your email or username"
            )
            
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password"
            )
            # Submit button
            col_a, col_b = st.columns(2)
            with col_a:
                submit = st.form_submit_button("Login", type="primary", use_container_width=True)
            with col_b:
                if st.form_submit_button("Cancel", use_container_width=True):
                    navigate_to('home')
            
            if submit:
                if not email_or_username or not password:
                    st.error("⚠️ Please fill in all fields")
                else:
                    # Attempt login
                    with st.spinner("Logging in..."):
                        success, message = auth.login(email_or_username, password)
                    
                    if success:
                        st.success(f"✅ {message}")
                        st.balloons()
                        # Small delay to show success message
                        import time
                        time.sleep(1)
                        navigate_to('dashboard')
                    else:
                        st.error(f"❌ {message}")
        
        # Divider
        st.markdown("---")
        
        st.markdown("**Don't have an account?**")
        if st.button("Sign Up", use_container_width=True):
            navigate_to('signup')
        
        # Info box
        st.markdown("---")
        st.info("""
        **💡 First time here?**
        
        1. Create an account by clicking "Sign Up"
        2. Add your Azure OpenAI API credentials in Settings
        3. Start uploading your study materials
        4. Begin learning with AI assistance!
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