import streamlit as st
from utils.auth import AuthManager
from database.db_manager import DatabaseManager


def show_settings_page(db: DatabaseManager, auth: AuthManager, navigate_to):
    """
    Display the settings page for Azure OpenAI configuration
    
    Args:
        db: DatabaseManager instance
        auth: AuthManager instance
        navigate_to: Navigation function
    """
    
    # Page header
    st.markdown("""
        <div style='padding: 1rem 0;'>
            <h1 style='color: #667eea;'> Settings</h1>
            <p style='color: #764ba2;; font-size: 1.1rem;'>Configure your Azure OpenAI credentials and preferences</p>
        </div>
    """, unsafe_allow_html=True)
    
    user_id = auth.get_current_user_id()
    
    # Tabs for different settings sections
    tab1, tab2= st.tabs(["🔑 Azure OpenAI", "👤 Account"])
    
    # ==================== TAB 1: Azure OpenAI Settings ====================
    with tab1:
        st.markdown("### Azure OpenAI Configuration")
        
        # Get existing settings
        settings = db.get_user_settings(user_id)
        
        # Info box
        st.info("""
        **📝 Where to get these credentials:**
        
        1. Go to [Azure Portal](https://portal.azure.com)
        2. Navigate to your Azure OpenAI resource
        3. Go to "Keys and Endpoint" section
        4. Copy your API Key and Endpoint URL
        5. Note your deployment name from the "Deployments" section
        """)
        
        # Configuration form
        with st.form("azure_settings_form"):
            st.markdown("#### Required Configuration")
            
            azure_api_key = st.text_input(
                "Azure OpenAI API Key *",
                type="password",
                value=settings['azure_api_key'] if settings and settings.get('azure_api_key') else "",
                help="Your Azure OpenAI API key (will be encrypted)",
                placeholder="Enter your Azure OpenAI API key"
            )
            
            azure_endpoint = st.text_input(
                "Azure OpenAI Endpoint *",
                value=settings['azure_endpoint'] if settings and settings.get('azure_endpoint') else "",
                help="Your Azure OpenAI endpoint URL",
                placeholder="https://your-resource.openai.azure.com/"
            )
            
            azure_deployment_name = st.text_input(
                "Azure Deployment Name *",
                value=settings['azure_deployment_name'] if settings and settings.get('azure_deployment_name') else "",
                help="The name of your deployed model",
                placeholder="gpt-4"
            )
            
            azure_api_version = st.text_input(
                "Azure API Version *",
                value=settings['azure_api_version'] if settings and settings.get('azure_api_version') else "2024-02-15-preview",
                help="Azure OpenAI API version",
                placeholder="2024-02-15-preview"
            )
            
            st.markdown("#### Model Configuration")
            
            col1, col2 = st.columns(2)
            
            with col1:
                embedding_model = st.text_input(
                    "Embedding Model",
                    value=settings['embedding_model'] if settings and settings.get('embedding_model') else "text-embedding-ada-002",
                    help="Model used for creating embeddings"
                )
            
            with col2:
                chat_model = st.text_input(
                    "Chat Model",
                    value=settings['chat_model'] if settings and settings.get('chat_model') else "gpt-4",
                    help="Model used for chat completions"
                )
            
            st.markdown("---")
            
            # Submit buttons
            col_a, col_b = st.columns([3, 1])
            
            with col_a:
                submit = st.form_submit_button("💾 Save Configuration", type="primary", use_container_width=True)
            
            with col_b:
                test = st.form_submit_button("🧪 Test", use_container_width=True)
            
            if submit:
                if not all([azure_api_key, azure_endpoint, azure_deployment_name, azure_api_version]):
                    st.error("⚠️ Please fill in all required fields (marked with *)")
                else:
                    try:
                        # Save settings
                        success = db.save_user_settings(
                            user_id=user_id,
                            azure_api_key=azure_api_key,
                            azure_endpoint=azure_endpoint,
                            azure_deployment_name=azure_deployment_name,
                            azure_api_version=azure_api_version,
                            embedding_model=embedding_model,
                            chat_model=chat_model
                        )
                        
                        if success:
                            st.success("✅ Settings saved successfully!")
                            st.balloons()
                            
                            # Rerun to update the form with new values
                            import time
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Failed to save settings. Please try again.")
                    except Exception as e:
                        st.error(f"❌ Error saving settings: {str(e)}")
            
            if test:
                if not all([azure_api_key, azure_endpoint, azure_deployment_name, azure_api_version]):
                    st.error("⚠️ Please fill in all required fields before testing")
                else:
                    with st.spinner("Testing Azure OpenAI connection..."):
                        try:
                            from openai import AzureOpenAI
                            
                            # Test connection
                            client = AzureOpenAI(
                                api_key=azure_api_key,
                                api_version=azure_api_version,
                                azure_endpoint=azure_endpoint
                            )
                            
                            # Try a simple completion
                            response = client.chat.completions.create(
                                model=azure_deployment_name,
                                messages=[{"role": "user", "content": "Hello"}],
                                max_tokens=10
                            )
                            
                            st.success("✅ Connection successful! Your Azure OpenAI credentials are working.")
                            st.info(f"Response preview: {response.choices[0].message.content}")
                            
                        except Exception as e:
                            st.error(f"❌ Connection failed: {str(e)}")
                            st.warning("Please check your credentials and try again.")
        
        # Show current status
        st.markdown("---")
        st.markdown("### 📊 Configuration Status")
        
        if settings and settings.get('azure_api_key'):
            st.success("✅ Azure OpenAI credentials are configured")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Endpoint:** {settings['azure_endpoint'][:50]}..." if len(settings['azure_endpoint']) > 50 else f"**Endpoint:** {settings['azure_endpoint']}")
                st.write(f"**Deployment:** {settings['azure_deployment_name']}")
            with col2:
                st.write(f"**API Version:** {settings['azure_api_version']}")
                st.write(f"**Embedding Model:** {settings['embedding_model']}")
        else:
            st.warning("⚠️ Azure OpenAI credentials not configured yet")
    
    # ==================== TAB 2: Account Settings ====================
    with tab2:
        st.markdown("### Account Information")
        
        user = auth.get_current_user()
        
        # Display account info
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("Username", value=user['username'], disabled=True)
            st.text_input("Email", value=user['email'], disabled=True)
        
        with col2:
            st.text_input("Account Created", value=user['created_at'][:10], disabled=True)
            if user['last_login']:
                st.text_input("Last Login", value=user['last_login'][:10], disabled=True)
        
        st.markdown("---")
        
        # Change password section
        st.markdown("### 🔒 Change Password")
        
        with st.form("change_password_form"):
            current_password = st.text_input(
                "Current Password",
                type="password",
                placeholder="Enter your current password"
            )
            
            new_password = st.text_input(
                "New Password",
                type="password",
                placeholder="Enter your new password"
            )
            
            confirm_new_password = st.text_input(
                "Confirm New Password",
                type="password",
                placeholder="Re-enter your new password"
            )
            
            with st.expander("ℹ️ Password Requirements"):
                st.markdown("""
                Your password must contain:
                - At least **8 characters**
                - At least **one uppercase letter** (A-Z)
                - At least **one lowercase letter** (a-z)
                - At least **one digit** (0-9)
                """)
            
            if st.form_submit_button("Change Password", type="primary", use_container_width=True):
                if not all([current_password, new_password, confirm_new_password]):
                    st.error("⚠️ Please fill in all fields")
                else:
                    success, message = auth.change_password(
                        current_password, 
                        new_password, 
                        confirm_new_password
                    )
                    
                    if success:
                        st.success(f"✅ {message}")
                    else:
                        st.error(f"❌ {message}")
        
        st.markdown("---")
        
        # Danger zone
        st.markdown("### ⚠️ Danger Zone")
        
        with st.expander("Delete Account", expanded=False):
            st.warning("""
            **Warning:** This action cannot be undone. This will permanently delete:
            - Your account and profile
            - All subjects and documents
            - All chat history, quizzes, and flashcards
            - All tasks and study plans
            """)
            
            st.text_input(
                "Type 'DELETE' to confirm",
                key="delete_confirmation",
                placeholder="Type DELETE to confirm"
            )
            
            if st.button("🗑️ Delete My Account", type="secondary"):
                if st.session_state.get("delete_confirmation") == "DELETE":
                    st.error("Account deletion feature is disabled in this demo")
                    # In production, you would implement:
                    # db.delete_user_and_all_data(user_id)
                    # auth.logout()
                    # navigate_to('home')
                else:
                    st.error("Please type 'DELETE' to confirm")
    
    # ==================== TAB 3: Help ===================
    
    # Back to dashboard button
    st.markdown("---")
    if st.button("← Back to Dashboard", use_container_width=True):
        navigate_to('dashboard')