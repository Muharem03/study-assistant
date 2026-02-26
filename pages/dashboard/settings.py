import streamlit as st
from utils.auth import AuthManager
from database.db_manager import DatabaseManager


def show_settings_page(db: DatabaseManager, auth: AuthManager, navigate_to):
    """
    Display the settings page for Azure OpenAI configuration
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
        with st.expander("📝 How to set up Azure Student Account and OpenAI Resource?"):
            st.markdown("""
            <div style='background-color:#e8f4fd; padding:15px; border-radius:10px;'>
                        
            1. **Create Azure Student Account**
            - Go to [Azure for Students](https://azure.microsoft.com/free/students/)
            - Sign up with your university email address
            - Verify your student status (usually via email or academic portal)
            - You’ll get free credits to use Azure services

            2. **Access Azure Portal**
            - Navigate to [Azure Portal](https://portal.azure.com)
            - Sign in with your student account

            3. **Create Azure OpenAI Resource**
            - In the portal, click **Create a resource**
            - Search for **Azure OpenAI**
            - Select your subscription (student credits)
            - Choose a resource group (or create a new one)
            - Pick a region where Azure OpenAI is available
            - Click **Review + Create**
                        
            4. **Deploy a Model**
            - Once the resource is created, go to it
            - Open the **Deployments** tab
            - Click **+ Create Deployment**
            - Choose a model (e.g., `gpt-4`, `text-embedding-ada-002`)
            - Give it a deployment name (you’ll need this later)

            5. **Get Keys and Endpoint**
            - In your Azure OpenAI resource, go to **Keys and Endpoint**
            - Copy your **API Key** and **Endpoint URL**
            - Note down your **Deployment Name** from the Deployments tab

            6. **Use in Your Project**
            - Paste the API Key, Endpoint, and Deployment Name into your app settings
            - Now your project can connect to Azure OpenAI using student credits
            </div>
            """,unsafe_allow_html=True)

        
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
                # Model selection with recommendations
                embedding_options = {
                    "text-embedding-3-small (Recommended)": "text-embedding-3-small",
                    "text-embedding-3-large (Highest Quality)": "text-embedding-3-large",
                    "text-embedding-ada-002 (Legacy)": "text-embedding-ada-002"
                }

                current_model = settings['embedding_model'] if settings and settings.get('embedding_model') else "text-embedding-3-small"

                # Find display name for current model
                current_display = next(
                    (k for k, v in embedding_options.items() if v == current_model),
                    list(embedding_options.keys())[0]
                )

                selected_display = st.selectbox(
                    "Embedding Model",
                    options=list(embedding_options.keys()),
                    index=list(embedding_options.keys()).index(current_display),
                    help="text-embedding-3-small recommended for best cost/performance"
                )

                embedding_model = embedding_options[selected_display]

                # Show model info
                model_info = {
                    "text-embedding-3-small": {
                        "dims": "1536",
                        "cost": "$0.00002/1K tokens (95% cheaper!)",
                        "perf": "Excellent"
                    },
                    "text-embedding-3-large": {
                        "dims": "3072",
                        "cost": "$0.00013/1K tokens",
                        "perf": "Best"
                    },
                    "text-embedding-ada-002": {
                        "dims": "1536",
                        "cost": "$0.0001/1K tokens",
                        "perf": "Good (outdated)"
                    }
                }

                if embedding_model in model_info:
                    info = model_info[embedding_model]
                    st.caption(f"📊 {info['dims']} dims | 💰 {info['cost']} | ⭐ {info['perf']}")
                            
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
        
    # Back to dashboard button
    st.markdown("---")
    if st.button("← Back to Dashboard", use_container_width=True):
        navigate_to('dashboard')