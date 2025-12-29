import streamlit as st
import bcrypt
from typing import Optional, Dict
from database.db_manager import DatabaseManager
import re


class AuthManager:
    """Handles user authentication and session management"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize session state variables if they don't exist"""
        if 'user' not in st.session_state:
            st.session_state.user = None
        if 'user_id' not in st.session_state:
            st.session_state.user_id = None
        if 'username' not in st.session_state:
            st.session_state.username = None
        if 'email' not in st.session_state:
            st.session_state.email = None
    
    @staticmethod
    
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_password(password: str) -> tuple[bool, str]:
        """
        Validate password strength
        Returns: (is_valid, error_message)
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        if not re.search(r'\d', password):
            return False, "Password must contain at least one digit"
        return True, ""
    
    @staticmethod
    def validate_username(username: str) -> tuple[bool, str]:
        """
        Validate username
        Returns: (is_valid, error_message)
        """
        if len(username) < 3:
            return False, "Username must be at least 3 characters long"
        if len(username) > 20:
            return False, "Username must be no more than 20 characters"
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "Username can only contain letters, numbers, and underscores"
        return True, ""
    
    def signup(self, email: str, username: str, password: str, confirm_password: str) -> tuple[bool, str]:
        """
        Register a new user
        Returns: (success, message)
        """
        # Validate email
        if not self.validate_email(email):
            return False, "Invalid email format"
        
        # Validate username
        is_valid, message = self.validate_username(username)
        if not is_valid:
            return False, message
        
        # Validate password
        is_valid, message = self.validate_password(password)
        if not is_valid:
            return False, message
        
        # Check if passwords match
        if password != confirm_password:
            return False, "Passwords do not match"
        
        # Check if email already exists
        if self.db.get_user_by_email(email):
            return False, "Email already registered"
        
        # Check if username already exists
        if self.db.get_user_by_username(username):
            return False, "Username already taken"
        
        # Hash password and create user
        password_hash = self.hash_password(password)
        user_id = self.db.create_user(email, username, password_hash)
        
        if user_id:
            return True, "Account created successfully! Please login."
        else:
            return False, "An error occurred during registration"
    
    def login(self, email_or_username: str, password: str) -> tuple[bool, str]:
        """
        Authenticate user and create session
        Returns: (success, message)
        """
        # Try to find user by email or username
        user = None
        if self.validate_email(email_or_username):
            user = self.db.get_user_by_email(email_or_username)
        else:
            user = self.db.get_user_by_username(email_or_username)
        
        if not user:
            return False, "Invalid credentials"
        
        # Verify password
        if not self.verify_password(password, user['password_hash']):
            return False, "Invalid credentials"
        
        # Update last login
        self.db.update_last_login(user['id'])
        
        # Set session state
        st.session_state.user = user
        st.session_state.user_id = user['id']
        st.session_state.username = user['username']
        st.session_state.email = user['email']
        
        return True, f"Welcome back, {user['username']}!"
    
    def logout(self):
        """Clear session and log out user"""
        st.session_state.user = None
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.email = None
        
        # Clear any other session state variables
        for key in list(st.session_state.keys()):
            if key not in ['user', 'user_id', 'username', 'email']:
                del st.session_state[key]
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return st.session_state.user is not None and st.session_state.user_id is not None
    
    def require_authentication(self):
        """Decorator/function to require authentication for a page"""
        if not self.is_authenticated():
            st.warning("Please login to access this page")
            st.stop()
    
    def get_current_user(self) -> Optional[Dict]:
        """Get currently logged in user"""
        return st.session_state.user
    
    def get_current_user_id(self) -> Optional[int]:
        """Get current user ID"""
        return st.session_state.user_id
    
    def get_current_username(self) -> Optional[str]:
        """Get current username"""
        return st.session_state.username
    
    def change_password(self, current_password: str, new_password: str, 
                   confirm_new_password: str) -> tuple[bool, str]:
        """
        Change user's password"""
        if not self.is_authenticated():
            return False, "User not authenticated"
        
        user = self.get_current_user()
        
        # Verify current password
        if not self.verify_password(current_password, user['password_hash']):
            return False, "Current password is incorrect"
        
        # Validate new password
        is_valid, message = self.validate_password(new_password)
        if not is_valid:
            return False, message
        
        # Check if passwords match
        if new_password != confirm_new_password:
            return False, "New passwords do not match"
        
        # Check if new password is different from current
        if self.verify_password(new_password, user['password_hash']):
            return False, "New password must be different from current password"
        
        try:
            # Hash and update password
            new_password_hash = self.hash_password(new_password)
            
            # Update in database
            self.db.update_user_password(user['id'], new_password_hash)
            
            # Update session state with new password hash
            user['password_hash'] = new_password_hash
            st.session_state.user = user
            
            return True, "Password changed successfully"
            
        except Exception as e:
            return False, f"Error changing password: {str(e)}"
    
    def get_user_settings(self) -> Optional[Dict]:
        """Get settings for current user"""
        if not self.is_authenticated():
            return None
        return self.db.get_user_settings(st.session_state.user_id)
    
    def has_azure_settings(self) -> bool:
        """Check if user has configured Azure OpenAI settings"""
        settings = self.get_user_settings()
        if not settings:
            return False
        return all([
            settings.get('azure_api_key'),
            settings.get('azure_endpoint'),
            settings.get('azure_deployment_name')
        ])


# Utility function for quick authentication check
def require_auth(db_manager: DatabaseManager):
    """Quick function to require authentication on a page"""
    auth = AuthManager(db_manager)
    auth.require_authentication()
    return auth