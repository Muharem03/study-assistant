    # CSS global

import streamlit as st
import base64

def load_image_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()
 # Custom CSS for modern styling
# config/ui_styles.py

"""
UI Styling Configuration
Contains all CSS styles for the application
"""

# Hero Section Styles
HERO_STYLES = """
    .hero-section {
        
        padding: 4rem 2rem;
        border-radius: 20px;
        text-align: center;
        color: white;
        margin-bottom: 3rem;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
    }
    
    .hero-title {
        font-size: 3.5rem;
        font-weight: 800;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        animation: fadeInDown 0.8s ease-out;
    }
    
    .hero-subtitle {
        font-size: 1.5rem;
        margin: 1rem 0 2rem 0;
        opacity: 0.95;
        animation: fadeInUp 0.8s ease-out;
    }
    
    .hero-emoji {
        font-size: 5rem;
        animation: bounce 2s infinite;
    }
"""

# Feature Card Styles
FEATURE_CARD_STYLES = """
    .feature-card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
        height: 100%;
        border-left: 4px solid #667eea;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.2);
    }
    
    .feature-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        display: block;
    }
    
    .feature-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: #333;
        margin-bottom: 0.5rem;
    }
    
    .feature-text {
        color: #666;
        line-height: 1.6;
    }
"""

# Stats Section Styles
STATS_STYLES = """
    .stats-container {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        text-align: center;
        color: white;
        margin: 3rem 0;
    }
    
    .stat-box {
        padding: 1.5rem;
    }
    
    .stat-number {
        font-size: 3rem;
        font-weight: 800;
        margin: 0;
    }
    
    .stat-label {
        font-size: 1.1rem;
        opacity: 0.9;
        margin-top: 0.5rem;
    }
"""

# Step/How It Works Styles
STEP_STYLES = """
    .step-container {
        text-align: center;
        padding: 2rem 1rem;
    }
    
    .step-number {
        width: 80px;
        height: 80px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 1rem auto;
        font-size: 2rem;
        font-weight: 800;
        color: white;
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
    }
    
    .step-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #333;
        margin-bottom: 0.5rem;
    }
    
    .step-text {
        color: #666;
        line-height: 1.6;
    }
"""

# CTA Section Styles
CTA_STYLES = """
    .cta-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        text-align: center;
        color: white;
        margin: 3rem 0;
    }
    
    .cta-title {
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 1rem;
    }
    
    .cta-text {
        font-size: 1.2rem;
        margin-bottom: 2rem;
        opacity: 0.95;
    }
"""

# Tech Badge Styles
TECH_STYLES = """
    .tech-badge {
        display: inline-block;
        background: white;
        padding: 0.8rem 1.5rem;
        border-radius: 25px;
        margin: 0.5rem;
        font-weight: 600;
        color: #667eea;
        box-shadow: 0 3px 10px rgba(0,0,0,0.1);
    }
"""

# Testimonial Styles
TESTIMONIAL_STYLES = """
    .testimonial-box {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 15px;
        border-left: 4px solid #667eea;
        margin: 2rem 0;
    }
    
    .testimonial-text {
        font-style: italic;
        color: #555;
        font-size: 1.1rem;
        line-height: 1.8;
    }
    
    .testimonial-author {
        font-weight: 700;
        color: #667eea;
        margin-top: 1rem;
    }
"""

# Animation Styles
ANIMATION_STYLES = """
    @keyframes fadeInDown {
        from {
            opacity: 0;
            transform: translateY(-20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes bounce {
        0%, 100% {
            transform: translateY(0);
        }
        50% {
            transform: translateY(-10px);
        }
    }
    
    @keyframes pulse {
        0%, 100% {
            transform: scale(1);
        }
        50% {
            transform: scale(1.05);
        }
    }
"""

# Button Styles
BUTTON_STYLES = """
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.8rem 2rem;
        font-size: 1.1rem;
        font-weight: 600;
        border-radius: 10px;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
    }
"""

# Combine all styles for home page
HOME_PAGE_STYLES = f"""
    <style>
    {HERO_STYLES}
    {FEATURE_CARD_STYLES}
    {STATS_STYLES}
    {STEP_STYLES}
    {CTA_STYLES}
    {TECH_STYLES}
    {TESTIMONIAL_STYLES}
    {ANIMATION_STYLES}
    {BUTTON_STYLES}
    </style>
"""

# Common styles for all pages
COMMON_STYLES = f"""
    <style>
    {ANIMATION_STYLES}
    {BUTTON_STYLES}
    
    /* Global Styles */
    .main-header {{
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }}
    
    .page-subtitle {{
        color: #666;
        font-size: 1.1rem;
        text-align: center;
        margin-bottom: 2rem;
    }}
    
    /* Card Styles */
    .card {{
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }}
    
    .card:hover {{
        box-shadow: 0 4px 16px rgba(0,0,0,0.15);
    }}
    </style>
"""

# Dashboard specific styles
DASHBOARD_STYLES = """
    <style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
    }
    
    .metric-number {
        font-size: 2.5rem;
        font-weight: 800;
        margin: 0;
    }
    
    .metric-label {
        font-size: 1rem;
        opacity: 0.9;
        margin-top: 0.5rem;
    }
    </style>
"""

# Chat page styles
CHAT_STYLES = """
    <style>
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    
    .chat-message.user {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .chat-message.assistant {
        background: #f8f9fa;
        color: #333;
        border-left: 4px solid #667eea;
    }
    </style>
"""


def apply_page_styles(page_type: str = "common"):
    """
    Apply styles based on page type
    
    Args:
        page_type: Type of page ('home', 'dashboard', 'chat', 'common')
    
    Returns:
        Streamlit markdown object with injected styles
    """
    import streamlit as st
    
    styles = {
        'home': HOME_PAGE_STYLES,
        'dashboard': COMMON_STYLES + DASHBOARD_STYLES,
        'chat': COMMON_STYLES + CHAT_STYLES,
        'common': COMMON_STYLES
    }
    
    return st.markdown(styles.get(page_type, COMMON_STYLES), unsafe_allow_html=True)