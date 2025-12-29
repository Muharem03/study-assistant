# pages/dashboard/flashcard.py - Complete Redesign

import streamlit as st
from utils.auth import AuthManager
from database.db_manager import DatabaseManager
from utils.rag_system import RAGSystem
import json
import re
from datetime import datetime, timedelta
import random


def show_flashcard_page(db: DatabaseManager, auth: AuthManager, navigate_to):
    """
    Display the flashcard page for creating and studying flashcards
    
    Args:
        db: DatabaseManager instance
        auth: AuthManager instance
        navigate_to: Navigation function
    """
    
    user_id = auth.get_current_user_id()
    
    # ==================== FULL-SCREEN STUDY MODE ====================
    if st.session_state.get('studying_flashcards', False):
        # Hide sidebar during study
        st.markdown("""
            <style>
            [data-testid="stSidebar"] {display: none;}
            
            /* Flashcard Container */
            .flashcard-container {
                perspective: 1000px;
                margin: 2rem auto;
                max-width: 800px;
            }
            
            .flashcard {
                position: relative;
                width: 100%;
                min-height: 400px;
                transition: transform 0.6s;
                transform-style: preserve-3d;
                cursor: pointer;
            }
            
            .flashcard.flipped {
                transform: rotateY(180deg);
            }
            
            .flashcard-face {
                position: absolute;
                width: 100%;
                min-height: 400px;
                backface-visibility: hidden;
                border-radius: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 3rem;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            }
            
            .flashcard-front {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            
            .flashcard-back {
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                color: white;
                transform: rotateY(180deg);
            }
            
            .flashcard-content {
                text-align: center;
                font-size: 1.8rem;
                line-height: 1.6;
                word-wrap: break-word;
            }
            
            .flashcard-label {
                position: absolute;
                top: 2rem;
                left: 2rem;
                font-size: 0.9rem;
                opacity: 0.8;
                text-transform: uppercase;
                letter-spacing: 2px;
            }
            
            /* Study Mode Header */
            .study-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 2rem;
                border-radius: 15px;
                text-align: center;
                color: white;
                margin-bottom: 2rem;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            }
            
            /* Difficulty Buttons */
            .difficulty-btn {
                flex: 1;
                padding: 1rem;
                border-radius: 10px;
                text-align: center;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                border: 2px solid transparent;
            }
            
            .difficulty-hard {
                background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
                color: white;
            }
            
            .difficulty-medium {
                background: linear-gradient(135deg, #ffd93d 0%, #f9ca24 100%);
                color: #333;
            }
            
            .difficulty-easy {
                background: linear-gradient(135deg, #6bcf7f 0%, #4cd964 100%);
                color: white;
            }
            </style>
        """, unsafe_allow_html=True)
        
        # Get study session data
        current_set_id = st.session_state.get('current_flashcard_set_id')
        flashcards = db.get_flashcards(current_set_id)
        flashcard_set = db.get_flashcard_set(current_set_id)
        
        if not flashcards:
            st.error("No flashcards found in this set.")
            st.session_state.studying_flashcards = False
            st.rerun()
            return
        
        # Initialize study state
        if 'flashcard_index' not in st.session_state:
            st.session_state.flashcard_index = 0
            st.session_state.show_back = False
            st.session_state.cards_reviewed = 0
            st.session_state.cards_mastered = 0
            st.session_state.cards_difficult = 0
            
            # Shuffle cards if random mode
            if st.session_state.get('study_mode') == "Random":
                st.session_state.card_order = random.sample(range(len(flashcards)), len(flashcards))
            else:
                st.session_state.card_order = list(range(len(flashcards)))
        
        card_order = st.session_state.card_order
        card_index = st.session_state.flashcard_index
        
        if card_index >= len(flashcards):
            # Study session complete
            st.markdown("""
                <div class="study-header">
                    <h1 style='font-size: 3rem; margin: 0;'>🎉</h1>
                    <h2 style='margin: 1rem 0;'>Study Session Complete!</h2>
                    <p style='font-size: 1.2rem; margin: 0;'>Great work on completing this set!</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Stats
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Cards Reviewed", st.session_state.cards_reviewed)
            with col2:
                st.metric("✅ Mastered", st.session_state.cards_mastered)
            with col3:
                st.metric("😰 Need Review", st.session_state.cards_difficult)
            
            st.markdown("---")
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("🔄 Study Again", type="primary", use_container_width=True):
                    st.session_state.flashcard_index = 0
                    st.session_state.show_back = False
                    st.session_state.cards_reviewed = 0
                    st.session_state.cards_mastered = 0
                    st.session_state.cards_difficult = 0
                    st.rerun()
            with col_b:
                if st.button("✔️ Finish", use_container_width=True):
                    st.session_state.studying_flashcards = False
                    # Clean up study state
                    for key in ['flashcard_index', 'show_back', 'cards_reviewed', 
                               'cards_mastered', 'cards_difficult', 'card_order']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()
            
            return
        
        current_card = flashcards[card_order[card_index]]
        
        # Study header with progress
        progress = (card_index + 1) / len(flashcards)
        st.markdown(f"""
            <div class="study-header">
                <h1 style='margin: 0; font-size: 2rem;'>🎴 Flashcard Study</h1>
                <p style='margin: 0.5rem 0 0 0; font-size: 1.1rem;'>{flashcard_set['title']}</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.progress(progress)
        st.markdown(f"**Card {card_index + 1} of {len(flashcards)}**")
        
        st.markdown("---")
        
        # Flashcard display
        if not st.session_state.get('show_back', False):
            # Show front
            st.markdown(f"""
                <div class="flashcard-container">
                    <div class="flashcard">
                        <div class="flashcard-face flashcard-front">
                            <div class="flashcard-label">Question</div>
                            <div class="flashcard-content">
                                {current_card['front']}
                            </div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("")
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🔄 Show Answer", use_container_width=True, type="primary", key="show_answer"):
                    st.session_state.show_back = True
                    st.rerun()
        else:
            # Show back
            st.markdown(f"""
                <div class="flashcard-container">
                    <div class="flashcard flipped">
                        <div class="flashcard-face flashcard-back">
                            <div class="flashcard-label">Answer</div>
                            <div class="flashcard-content">
                                {current_card['back']}
                            </div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("### How well did you know this?")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("😰 Hard", use_container_width=True, key="hard"):
                    db.add_flashcard_review(
                        flashcard_item_id=current_card['id'],
                        user_id=user_id,
                        difficulty=1,
                        next_review_date=(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
                    )
                    st.session_state.cards_difficult += 1
                    st.session_state.cards_reviewed += 1
                    st.session_state.flashcard_index += 1
                    st.session_state.show_back = False
                    st.rerun()
            
            with col2:
                if st.button("🤔 Medium", use_container_width=True, key="medium"):
                    db.add_flashcard_review(
                        flashcard_item_id=current_card['id'],
                        user_id=user_id,
                        difficulty=3,
                        next_review_date=(datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
                    )
                    st.session_state.cards_reviewed += 1
                    st.session_state.flashcard_index += 1
                    st.session_state.show_back = False
                    st.rerun()
            
            with col3:
                if st.button("✅ Easy", use_container_width=True, key="easy"):
                    db.add_flashcard_review(
                        flashcard_item_id=current_card['id'],
                        user_id=user_id,
                        difficulty=5,
                        next_review_date=(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
                    )
                    st.session_state.cards_mastered += 1
                    st.session_state.cards_reviewed += 1
                    st.session_state.flashcard_index += 1
                    st.session_state.show_back = False
                    st.rerun()
        
        # Navigation
        st.markdown("---")
        col_nav1, col_nav2, col_nav3 = st.columns([1, 1, 1])
        
        with col_nav1:
            if st.button("⏸️ Pause", use_container_width=True):
                st.session_state.studying_flashcards = False
                st.rerun()
        
        with col_nav2:
            if card_index > 0:
                if st.button("⬅️ Previous", use_container_width=True):
                    st.session_state.flashcard_index -= 1
                    st.session_state.show_back = False
                    if st.session_state.cards_reviewed > 0:
                        st.session_state.cards_reviewed -= 1
                    st.rerun()
        
        with col_nav3:
            if not st.session_state.get('show_back', False):
                if st.button("➡️ Skip", use_container_width=True):
                    st.session_state.flashcard_index += 1
                    st.session_state.show_back = False
                    st.rerun()
        
        return  # Exit to prevent showing normal page
    
    # ==================== NORMAL PAGE MODE ====================
    
    # Page header
    st.markdown("""
        <div style='padding: 1rem 0;'>
            <h1 style='color: #667eea;'> Flashcards</h1>
            <p style='color: #764ba2; font-size: 1.1rem;'>Create and study with AI-generated flashcards</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Check Azure settings
    if not auth.has_azure_settings():
        st.warning("⚠️ **Azure OpenAI settings not configured**")
        if st.button("⚙️ Go to Settings", type="primary"):
            navigate_to('settings')
        return
    
    # Get user settings
    settings = db.get_user_settings(user_id)
    
    # Get subjects
    subjects = db.get_user_subjects(user_id)
    
    if not subjects:
        st.warning("📚 **No subjects found**")
        if st.button("➕ Create Subject", type="primary"):
            navigate_to('subjects')
        return
    
    # Subject selector
    st.markdown("### 📚 Select Subject")
    
    selected_subject_id = st.session_state.get('selected_subject_id')
    subject_options = {f"{s['name']}": s['id'] for s in subjects}
    
    if selected_subject_id:
        selected_subject = db.get_subject(selected_subject_id)
        if selected_subject:
            default_index = list(subject_options.keys()).index(selected_subject['name'])
        else:
            default_index = 0
    else:
        default_index = 0
    
    selected_subject_name = st.selectbox(
        "Choose a subject",
        options=list(subject_options.keys()),
        index=default_index,
        key="flashcard_subject_selector"
    )
    
    current_subject_id = subject_options[selected_subject_name]
    st.session_state.selected_subject_id = current_subject_id
    
    # Get documents for subject
    documents = db.get_subject_documents(current_subject_id)
    completed_docs = [d for d in documents if d['processing_status'] == 'completed']
    
    if not completed_docs:
        st.warning(f"📄 **No processed documents in this subject**")
        if st.button("📤 Upload Document", type="primary"):
            navigate_to('documents')
        return
    
    # Document selector
    st.markdown("### 📄 Select Document")
    
    selected_document_id = st.session_state.get('selected_document_id')
    doc_options = {f"{d['title']}": d['id'] for d in completed_docs}
    
    if selected_document_id and selected_document_id in doc_options.values():
        selected_doc = db.get_document(selected_document_id)
        if selected_doc:
            default_doc_index = list(doc_options.keys()).index(selected_doc['title'])
        else:
            default_doc_index = 0
    else:
        default_doc_index = 0
    
    selected_doc_name = st.selectbox(
        "Choose a document",
        options=list(doc_options.keys()),
        index=default_doc_index,
        key="flashcard_document_selector"
    )
    
    current_document_id = doc_options[selected_doc_name]
    current_document = db.get_document(current_document_id)
    st.session_state.selected_document_id = current_document_id
    
    st.markdown("---")
    
    # Tabs for different sections
    tab1, tab2, tab3 = st.tabs(["🎴 Generate Flashcards", "📚 Study", "📊 Statistics"])
    
    # ==================== TAB 1: Generate Flashcards ====================
    with tab1:
        st.markdown("### 🎴 Create New Flashcard Set")
        
        with st.form("flashcard_generation_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                num_cards = st.slider(
                    "Number of Flashcards",
                    min_value=5,
                    max_value=50,
                    value=10,
                    help="How many flashcards to generate"
                )
            
            with col2:
                set_title = st.text_input(
                    "Set Title (optional)",
                    placeholder="Leave blank for auto-generated title",
                    help="Custom name for this flashcard set"
                )
            
            topic_focus = st.text_input(
                "Topic Focus (optional)",
                placeholder="e.g., Chapter 3, Key Terms, Important Concepts",
                help="Focus on a specific topic"
            )
            
            generate = st.form_submit_button("🎲 Generate Flashcards", type="primary", use_container_width=True)
            
            if generate:
                with st.spinner(f"Generating {num_cards} flashcards... This may take a moment."):
                    try:
                        # Initialize RAG system
                        rag = RAGSystem(
                            azure_api_key=settings['azure_api_key'],
                            azure_endpoint=settings['azure_endpoint'],
                            azure_deployment_name=settings['azure_deployment_name'],
                            azure_api_version=settings['azure_api_version']
                        )
                        
                        # Load FAISS index
                        rag.load_index(current_document['faiss_index_path'])
                        
                        # Generate flashcards
                        flashcards_json = rag.generate_flashcards(
                            num_cards=num_cards,
                            topic=topic_focus if topic_focus else None
                        )
                        
                        # Parse JSON response
                        try:
                            json_match = re.search(r'\[.*\]', flashcards_json, re.DOTALL)
                            if json_match:
                                cards_data = json.loads(json_match.group())
                            else:
                                cards_data = json.loads(flashcards_json)
                        except json.JSONDecodeError:
                            st.error("Failed to parse flashcards. Please try again.")
                            cards_data = None
                        
                        if cards_data:
                            # Create flashcard set in database
                            title = set_title if set_title else f"Flashcards - {current_document['title']} ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
                            set_id = db.create_flashcard_set(current_document_id, user_id, title)
                            
                            # Add flashcards to database
                            for card in cards_data:
                                db.add_flashcard(
                                    flashcard_set_id=set_id,
                                    front=card.get('front', ''),
                                    back=card.get('back', '')
                                )
                            
                            st.success(f"✅ Flashcard set '{title}' created with {len(cards_data)} cards!")
                            st.balloons()
                            
                            import time
                            time.sleep(1)
                            st.rerun()
                            
                    except Exception as e:
                        st.error(f"❌ Error generating flashcards: {str(e)}")
    
    # ==================== TAB 2: Study ====================
    with tab2:
        st.markdown("### 📚 Study Flashcards")
        
        # Get flashcard sets for this document
        flashcard_sets = db.get_document_flashcard_sets(current_document_id)
        
        if flashcard_sets:
            # Select flashcard set
            set_options = {f"{s['title']} ({s['created_at'][:10]})": s['id'] for s in flashcard_sets}
            
            selected_set_name = st.selectbox(
                "Choose a flashcard set",
                options=list(set_options.keys()),
                key="study_set_selector"
            )
            
            selected_set_id = set_options[selected_set_name]
            
            # Get flashcards in this set
            flashcards = db.get_flashcards(selected_set_id)
            
            if flashcards:
                st.info(f"📚 This set has **{len(flashcards)}** flashcards")
                
                # Study mode selector
                study_mode = st.radio(
                    "Study Mode",
                    options=["Sequential", "Random", "Review Difficult"],
                    horizontal=True,
                    help="Sequential: In order, Random: Shuffled, Review Difficult: Focus on cards marked as hard"
                )
                
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("▶️ Start Studying", type="primary", use_container_width=True):
                        # Initialize study session
                        st.session_state.studying_flashcards = True
                        st.session_state.current_flashcard_set_id = selected_set_id
                        st.session_state.study_mode = study_mode
                        st.rerun()
                
                # Preview cards
                st.markdown("---")
                st.markdown("#### 👀 Preview Cards")
                
                with st.expander("View all cards in this set", expanded=False):
                    for i, card in enumerate(flashcards, 1):
                        st.markdown(f"""
                            <div style='background: #f8f9fa; padding: 1rem; border-radius: 10px; 
                                        margin-bottom: 0.5rem; border-left: 4px solid #667eea;'>
                                <strong>Card {i}</strong><br>
                                <strong>Q:</strong> {card['front']}<br>
                                <strong>A:</strong> {card['back']}
                            </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("This set has no flashcards.")
        else:
            st.info("📝 No flashcard sets yet. Generate your first set!")
    
    # ==================== TAB 3: Statistics ====================
    with tab3:
        st.markdown("### 📊 Flashcard Statistics")
        
        all_sets = db.get_document_flashcard_sets(current_document_id)
        
        if all_sets:
            total_sets = len(all_sets)
            total_cards = sum(len(db.get_flashcards(s['id'])) for s in all_sets)
            
            # Display metrics
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Sets", total_sets)
            with col2:
                st.metric("Total Flashcards", total_cards)
            
            st.markdown("---")
            
            # List all sets with stats
            st.markdown("### 📚 Your Flashcard Sets")
            
            for fset in all_sets:
                cards = db.get_flashcards(fset['id'])
                
                # Card display similar to quiz
                st.markdown(f"""
                    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                padding: 1.5rem; border-radius: 15px; margin-bottom: 1.5rem;
                                box-shadow: 0 4px 15px rgba(0,0,0,0.1); color: white;'>
                        <h3 style='color: white; margin: 0 0 1rem 0;'>🎴 {fset['title']}</h3>
                        <div style='background-color: rgba(255,255,255,0.2); padding: 1rem; 
                                    border-radius: 10px; margin-bottom: 1rem;'>
                            <div style='display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem;'>
                                <div>
                                    <p style='color: rgba(255,255,255,0.8); font-size: 0.85rem; margin: 0;'>Created</p>
                                    <p style='color: white; font-weight: bold; margin: 0.3rem 0 0 0;'>{fset['created_at'][:10]}</p>
                                </div>
                                <div>
                                    <p style='color: rgba(255,255,255,0.8); font-size: 0.85rem; margin: 0;'>Cards</p>
                                    <p style='color: white; font-weight: bold; margin: 0.3rem 0 0 0;'>{len(cards)}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    if st.button("▶️ Study", key=f"study_{fset['id']}", use_container_width=True, type="primary"):
                        st.session_state.studying_flashcards = True
                        st.session_state.current_flashcard_set_id = fset['id']
                        st.session_state.study_mode = "Sequential"
                        st.rerun()
                
                with col_b:
                    with st.expander("📊 Details", expanded=False):
                        st.write(f"**Total Cards:** {len(cards)}")
                        st.write(f"**Created:** {fset['created_at'][:16]}")
                
                with col_c:
                    if st.button("🗑️ Delete", key=f"delete_set_{fset['id']}", use_container_width=True):
                        st.session_state.deleting_set_id = fset['id']
                        st.rerun()
                
                # Delete confirmation
                if st.session_state.get('deleting_set_id') == fset['id']:
                    st.error("⚠️ **Delete this flashcard set?** This action cannot be undone!")
                    col_yes, col_no = st.columns(2)
                    
                    with col_yes:
                        if st.button("Yes, Delete", type="primary", use_container_width=True, key=f"confirm_{fset['id']}"):
                            try:
                                db.delete_flashcard_set(fset['id'])
                                st.success("✅ Flashcard set deleted!")
                                st.session_state.deleting_set_id = None
                                import time
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                    
                    with col_no:
                        if st.button("Cancel", use_container_width=True, key=f"cancel_{fset['id']}"):
                            st.session_state.deleting_set_id = None
                            st.rerun()
                
                st.markdown("---")
        else:
            st.info("📊 No statistics yet. Create some flashcard sets to see your progress!")
    
    # Back to dashboard
    st.markdown("---")
    if st.button("← Back to Dashboard", use_container_width=True):
        navigate_to('dashboard')