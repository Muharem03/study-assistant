import streamlit as st
from utils.auth import AuthManager
from database.db_manager import DatabaseManager
from utils.rag_system import RAGSystem
import json
import re
from datetime import datetime


def show_quiz_page(db: DatabaseManager, auth: AuthManager, navigate_to):
    """
    Display the quiz page for generating and taking quizzes
    
    Args:
        db: DatabaseManager instance
        auth: AuthManager instance
        navigate_to: Navigation function
    """
    
    user_id = auth.get_current_user_id()
    
    # ==================== FULL-SCREEN QUIZ MODE ====================
    if st.session_state.get('taking_quiz', False) or st.session_state.get('show_results', False):
        # Hide sidebar during quiz
        st.markdown("""
            <style>
            [data-testid="stSidebar"] {display: none;}
            </style>
        """, unsafe_allow_html=True)
        
        # Get quiz info
        quiz_id = st.session_state.get('current_quiz_id')
        settings = db.get_user_settings(user_id)
        current_document_id = st.session_state.get('selected_document_id')
        current_document = db.get_document(current_document_id)
        
        if st.session_state.get('taking_quiz', False):
            # TAKING QUIZ MODE
            quiz_questions = db.get_quiz_questions(quiz_id)
            
            if quiz_questions:
                # Quiz header
                st.markdown(f"""
                    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                padding: 2rem; border-radius: 15px; text-align: center; margin-bottom: 2rem;
                                box-shadow: 0 4px 15px rgba(0,0,0,0.2);'>
                        <h1 style='color: white; margin: 0;'>📝 Quiz Mode</h1>
                        <p style='color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0; font-size: 1.2rem;'>
                            {len(quiz_questions)} Questions
                        </p>
                    </div>
                """, unsafe_allow_html=True)
                
                # Initialize quiz state
                if 'quiz_answers' not in st.session_state:
                    st.session_state.quiz_answers = {}
                if 'quiz_start_time' not in st.session_state:
                    st.session_state.quiz_start_time = datetime.now()
                
                # Progress bar
                answered = len(st.session_state.quiz_answers)
                progress = answered / len(quiz_questions)
                st.progress(progress)
                st.markdown(f"**Progress:** {answered} / {len(quiz_questions)} questions answered")
                st.markdown("---")
                
                # Display questions
                for i, question in enumerate(quiz_questions, 1):
                    st.markdown(f"""
                        <div style='background-color: white; padding: 1.5rem; border-radius: 10px; 
                                    margin-bottom: 1.5rem; box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                                    border-left: 5px solid {"#4caf50" if question["id"] in st.session_state.quiz_answers else "#ccc"};'>
                            <h3 style='color: #333; margin: 0 0 1rem 0;'>
                                Question {i} of {len(quiz_questions)}
                            </h3>
                            <p style='font-size: 1.1rem; color: #555; margin-bottom: 1rem; line-height: 1.6;'>
                                {question['question']}
                            </p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    options = {
                        'A': question['option_a'],
                        'B': question['option_b'],
                        'C': question['option_c'],
                        'D': question['option_d']
                    }
                    
                    # Filter out empty options
                    options = {k: v for k, v in options.items() if v}
                    
                    answer = st.radio(
                        f"Select your answer:",
                        options=list(options.keys()),
                        format_func=lambda x: f"{x}. {options[x]}",
                        key=f"q_{question['id']}",
                        index=None,
                        label_visibility="collapsed"
                    )
                    
                    if answer:
                        st.session_state.quiz_answers[question['id']] = answer
                
                st.markdown("---")
                
                # Submit buttons
                col1, col2, col3 = st.columns([1, 2, 1])
                
                with col1:
                    if st.button("❌ Cancel Quiz", use_container_width=True):
                        st.session_state.taking_quiz = False
                        st.session_state.quiz_answers = {}
                        st.session_state.quiz_start_time = None
                        st.session_state.current_quiz_id = None
                        st.rerun()
                
                with col2:
                    if st.button("✅ Submit Quiz", type="primary", use_container_width=True):
                        if len(st.session_state.quiz_answers) < len(quiz_questions):
                            st.error(f"⚠️ Please answer all {len(quiz_questions)} questions before submitting")
                        else:
                            # Calculate score
                            correct = 0
                            total = len(quiz_questions)
                            
                            # Create attempt
                            attempt_id = db.create_quiz_attempt(quiz_id, user_id)
                            
                            # Calculate time taken
                            time_taken = int((datetime.now() - st.session_state.quiz_start_time).total_seconds())
                            
                            # Store answers and calculate score
                            for question in quiz_questions:
                                user_answer = st.session_state.quiz_answers.get(question['id'])
                                is_correct = user_answer == question['correct_answer']
                                
                                if is_correct:
                                    correct += 1
                                
                                db.add_quiz_answer(
                                    attempt_id=attempt_id,
                                    question_id=question['id'],
                                    user_answer=user_answer,
                                    is_correct=is_correct
                                )
                            
                            score = (correct / total) * 100
                            
                            # Update attempt with score
                            db.complete_quiz_attempt(attempt_id, score, time_taken)
                            
                            # Store results for display
                            st.session_state.quiz_results = {
                                'score': score,
                                'correct': correct,
                                'total': total,
                                'time_taken': time_taken
                            }
                            st.session_state.show_results = True
                            st.session_state.taking_quiz = False
                            st.rerun()
        
        elif st.session_state.get('show_results', False):
            # RESULTS MODE
            results = st.session_state.quiz_results
            
            # Score display
            score = results['score']
            if score >= 90:
                emoji = "🏆"
                message = "Excellent!"
                color = "#4caf50"
            elif score >= 70:
                emoji = "🎉"
                message = "Great job!"
                color = "#8bc34a"
            elif score >= 50:
                emoji = "👍"
                message = "Good effort!"
                color = "#ff9800"
            else:
                emoji = "📚"
                message = "Keep studying!"
                color = "#f44336"
            
            st.markdown(f"""
                <div style='background: linear-gradient(135deg, {color} 0%, {color}dd 100%); 
                            color: white; padding: 3rem; border-radius: 20px; text-align: center; 
                            margin: 2rem 0; box-shadow: 0 10px 30px rgba(0,0,0,0.2);'>
                    <h1 style='margin: 0; font-size: 5rem;'>{emoji}</h1>
                    <h2 style='margin: 1rem 0; font-size: 2rem;'>{message}</h2>
                    <h1 style='margin: 0.5rem 0; font-size: 4rem; font-weight: bold;'>{score:.1f}%</h1>
                    <p style='margin: 0; font-size: 1.5rem; opacity: 0.9;'>
                        {results['correct']} out of {results['total']} correct
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("⏱️ Time Taken", f"{results['time_taken'] // 60}m {results['time_taken'] % 60}s")
            with col2:
                st.metric("⚡ Avg Time/Question", f"{results['time_taken'] / results['total']:.1f}s")
            with col3:
                accuracy_emoji = "🎯" if score >= 80 else "📊"
                st.metric(f"{accuracy_emoji} Accuracy", f"{score:.0f}%")
            
            st.markdown("---")
            
            # Action buttons
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("🔄 Take Another Quiz", type="primary", use_container_width=True):
                    st.session_state.show_results = False
                    st.session_state.quiz_results = None
                    st.rerun()
            with col_b:
                if st.button("📚 Back to Quizzes", use_container_width=True):
                    st.session_state.show_results = False
                    st.session_state.quiz_results = None
                    st.rerun()
        
        return  # Exit here to prevent showing normal page
    
    # ==================== NORMAL PAGE MODE ====================
    
    # Page header
    st.markdown("""
        <div style='padding: 1rem 0;'>
            <h1 style='color: #667eea;'> Quizzes</h1>
            <p style='color: #764ba2; font-size: 1.1rem;'>Test your knowledge with AI-generated quizzes</p>
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
        key="quiz_subject_selector"
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
        key="quiz_document_selector"
    )
    
    current_document_id = doc_options[selected_doc_name]
    current_document = db.get_document(current_document_id)
    st.session_state.selected_document_id = current_document_id
    
    st.markdown("---")
    
    # Initialize tab index
    if 'quiz_active_tab' not in st.session_state:
        st.session_state.quiz_active_tab = 0
    
    # Tabs for different sections
    tab1, tab2, tab3 = st.tabs(["📝 Generate Quiz", "📚 Quiz History", "📊 Statistics"])
    
    # Force switch to tab 1 if taking quiz
    with tab1:
        # This will be displayed in tab1
        pass 
        st.markdown("### 📝 Create New Quiz")
        
        with st.form("quiz_generation_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    num_questions = st.slider(
                        "Number of Questions",
                        min_value=3,
                        max_value=20,
                        value=5,
                        help="How many questions to generate"
                    )
                    
                    difficulty = st.select_slider(
                        "Difficulty Level",
                        options=["easy", "medium", "hard"],
                        value="medium"
                    )
                
                with col2:
                    quiz_title = st.text_input(
                        "Quiz Title (optional)",
                        placeholder="Leave blank for auto-generated title",
                        help="Custom name for this quiz"
                    )
                    
                    topic_focus = st.text_input(
                        "Topic Focus (optional)",
                        placeholder="e.g., Chapter 3, Linear Algebra",
                        help="Focus on a specific topic"
                    )
                
                generate = st.form_submit_button("🎲 Generate Quiz", type="primary", use_container_width=True)
                
                if generate:
                    with st.spinner(f"Generating {num_questions} questions... This may take a moment."):
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
                            
                            # Generate quiz
                            quiz_json = rag.generate_quiz_questions(
                                num_questions=num_questions,
                                difficulty=difficulty,
                                topic=topic_focus if topic_focus else None
                            )
                            
                            # Parse JSON response
                            try:
                                # Try to extract JSON from response
                                json_match = re.search(r'\[.*\]', quiz_json, re.DOTALL)
                                if json_match:
                                    questions_data = json.loads(json_match.group())
                                else:
                                    questions_data = json.loads(quiz_json)
                            except json.JSONDecodeError:
                                st.error("Failed to parse quiz questions. Please try again.")
                                questions_data = None
                            
                            if questions_data:
                                # Create quiz in database
                                title = quiz_title if quiz_title else f"Quiz - {current_document['title']} ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
                                quiz_id = db.create_quiz(current_document_id, user_id, title)
                                
                                # Add questions to database
                                for q in questions_data:
                                    db.add_quiz_question(
                                        quiz_id=quiz_id,
                                        question=q.get('question', ''),
                                        correct_answer=q.get('correct_answer', ''),
                                        option_a=q.get('option_a', ''),
                                        option_b=q.get('option_b', ''),
                                        option_c=q.get('option_c', ''),
                                        option_d=q.get('option_d', ''),
                                        explanation=q.get('explanation', '')
                                    )
                                
                                st.success(f"✅ Quiz '{title}' created with {len(questions_data)} questions!")
                                st.session_state.current_quiz_id = quiz_id
                                st.session_state.taking_quiz = True
                                st.rerun()
                                
                        except Exception as e:
                            st.error(f"❌ Error generating quiz: {str(e)}")
        
        # Take quiz section
        if  st.session_state.get('taking_quiz', False) and not st.session_state.get('show_results', False):
            st.markdown("---")
            quiz_id = st.session_state.get('current_quiz_id')
            
            if quiz_id:
                quiz_questions = db.get_quiz_questions(quiz_id)
                
                if quiz_questions:
                    # Get quiz info
                    quiz_info = db.get_quiz_questions(quiz_id)
                    quiz_data = next((q for q in db.get_document_quizzes(current_document_id) if q['id'] == quiz_id), None)
                    
                    if quiz_data:
                        st.markdown(f"""
                            <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                                        padding: 2rem; border-radius: 15px; text-align: center; margin-bottom: 2rem;
                                        box-shadow: 0 4px 15px rgba(0,0,0,0.2);'>
                                <h2 style='color: white; margin: 0;'>📝 {quiz_data['title']}</h2>
                                <p style='color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0;'>
                                    {len(quiz_questions)} Questions
                                </p>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    # Initialize quiz state
                    if 'quiz_answers' not in st.session_state:
                        st.session_state.quiz_answers = {}
                    if 'quiz_start_time' not in st.session_state:
                        st.session_state.quiz_start_time = datetime.now()
                    
                    # Display questions with better styling
                    for i, question in enumerate(quiz_questions, 1):
                        st.markdown(f"""
                            <div style='background-color: white; padding: 1.5rem; border-radius: 10px; 
                                        margin-bottom: 1.5rem; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
                                <h4 style='color: #333; margin: 0 0 1rem 0;'>
                                    Question {i} of {len(quiz_questions)}
                                </h4>
                                <p style='font-size: 1.1rem; color: #555; margin-bottom: 1rem;'>
                                    {question['question']}
                                </p>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        options = {
                            'A': question['option_a'],
                            'B': question['option_b'],
                            'C': question['option_c'],
                            'D': question['option_d']
                        }
                        
                        # Filter out empty options
                        options = {k: v for k, v in options.items() if v}
                        
                        answer = st.radio(
                            f"Select your answer for Question {i}:",
                            options=list(options.keys()),
                            format_func=lambda x: f"{x}. {options[x]}",
                            key=f"history_q_{question['id']}",  # Changed to make unique
                            index=None,
                            label_visibility="collapsed"
                        )
                        
                        if answer:
                            st.session_state.quiz_answers[question['id']] = answer
                    
                    # Submit quiz
                    col_submit, col_cancel = st.columns(2)
                    
                    with col_submit:
                        if st.button("✅ Submit Quiz", type="primary", use_container_width=True):
                            if len(st.session_state.quiz_answers) < len(quiz_questions):
                                st.warning(f"⚠️ Please answer all {len(quiz_questions)} questions before submitting")
                            else:
                                # Calculate score
                                correct = 0
                                total = len(quiz_questions)
                                
                                # Create attempt
                                attempt_id = db.create_quiz_attempt(quiz_id, user_id)
                                
                                # Calculate time taken
                                time_taken = int((datetime.now() - st.session_state.quiz_start_time).total_seconds())
                                
                                # Store answers and calculate score
                                for question in quiz_questions:
                                    user_answer = st.session_state.quiz_answers.get(question['id'])
                                    is_correct = user_answer == question['correct_answer']
                                    
                                    if is_correct:
                                        correct += 1
                                    
                                    db.add_quiz_answer(
                                        attempt_id=attempt_id,
                                        question_id=question['id'],
                                        user_answer=user_answer,
                                        is_correct=is_correct
                                    )
                                
                                score = (correct / total) * 100
                                
                                # Update attempt with score
                                db.complete_quiz_attempt(attempt_id, score, time_taken)
                                
                                # Store results for display
                                st.session_state.quiz_results = {
                                    'score': score,
                                    'correct': correct,
                                    'total': total,
                                    'time_taken': time_taken
                                }
                                st.session_state.show_results = True
                                st.session_state.taking_quiz = False
                                st.rerun()
                    
                    with col_cancel:
                        if st.button("Cancel Quiz", use_container_width=True):
                            st.session_state.taking_quiz = False
                            st.session_state.quiz_answers = {}
                            st.session_state.quiz_start_time = None
                            st.session_state.current_quiz_id = None
                            st.rerun()
        
        # Show results
        if st.session_state.get('show_results', False):
            st.markdown("---")
            results = st.session_state.quiz_results
            
            st.markdown("### 🎯 Quiz Results")
            
            # Score display
            score = results['score']
            if score >= 90:
                emoji = "🏆"
                message = "Excellent!"
                color = "#4caf50"
            elif score >= 70:
                emoji = "🎉"
                message = "Great job!"
                color = "#8bc34a"
            elif score >= 50:
                emoji = "👍"
                message = "Good effort!"
                color = "#ff9800"
            else:
                emoji = "📚"
                message = "Keep studying!"
                color = "#f44336"
            
            st.markdown(f"""
                <div style='background-color: {color}; color: white; padding: 2rem; 
                            border-radius: 10px; text-align: center; margin: 1rem 0;'>
                    <h1 style='margin: 0; font-size: 4rem;'>{emoji}</h1>
                    <h2 style='margin: 0.5rem 0;'>{message}</h2>
                    <h1 style='margin: 0.5rem 0; font-size: 3rem;'>{score:.1f}%</h1>
                    <p style='margin: 0; font-size: 1.2rem;'>
                        {results['correct']} out of {results['total']} correct
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Time Taken", f"{results['time_taken'] // 60}m {results['time_taken'] % 60}s")
            with col2:
                st.metric("Average Time per Question", f"{results['time_taken'] / results['total']:.1f}s")
            
            if st.button("🔄 Take Another Quiz", type="primary", use_container_width=True):
                st.session_state.show_results = False
                st.session_state.quiz_results = None
                st.rerun()
    
    # ==================== TAB 2: Quiz History ====================
    with tab2:
        # Check if taking a quiz
        if st.session_state.get('taking_quiz', False) and not st.session_state.get('show_results', False):
            # SHOW QUIZ IN THIS TAB
            quiz_id = st.session_state.get('current_quiz_id')
            
            if quiz_id:
                quiz_questions = db.get_quiz_questions(quiz_id)
                
                if quiz_questions:
                    # Get quiz info
                    quiz_data = next((q for q in db.get_document_quizzes(current_document_id) if q['id'] == quiz_id), None)
                    
                    if quiz_data:
                        st.markdown(f"""
                            <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                                        padding: 2rem; border-radius: 15px; text-align: center; margin-bottom: 2rem;
                                        box-shadow: 0 4px 15px rgba(0,0,0,0.2);'>
                                <h2 style='color: white; margin: 0;'>📝 {quiz_data['title']}</h2>
                                <p style='color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0;'>
                                    {len(quiz_questions)} Questions
                                </p>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    # Initialize quiz state
                    if 'quiz_answers' not in st.session_state:
                        st.session_state.quiz_answers = {}
                    if 'quiz_start_time' not in st.session_state:
                        st.session_state.quiz_start_time = datetime.now()
                    
                    # Display questions with better styling
                    for i, question in enumerate(quiz_questions, 1):
                        st.markdown(f"""
                            <div style='background-color: white; padding: 1.5rem; border-radius: 10px; 
                                        margin-bottom: 1.5rem; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
                                <h4 style='color: #333; margin: 0 0 1rem 0;'>
                                    Question {i} of {len(quiz_questions)}
                                </h4>
                                <p style='font-size: 1.1rem; color: #555; margin-bottom: 1rem;'>
                                    {question['question']}
                                </p>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        options = {
                            'A': question['option_a'],
                            'B': question['option_b'],
                            'C': question['option_c'],
                            'D': question['option_d']
                        }
                        
                        # Filter out empty options
                        options = {k: v for k, v in options.items() if v}
                        
                        answer = st.radio(
                            f"Select your answer for Question {i}:",
                            options=list(options.keys()),
                            format_func=lambda x: f"{x}. {options[x]}",
                            key=f"q_{question['id']}",
                            index=None,
                            label_visibility="collapsed"
                        )
                        
                        if answer:
                            st.session_state.quiz_answers[question['id']] = answer
                    
                    st.markdown("---")
                    
                    # Submit quiz
                    col_submit, col_cancel = st.columns(2)
                    
                    with col_submit:
                        if st.button("✅ Submit Quiz", type="primary", use_container_width=True):
                            if len(st.session_state.quiz_answers) < len(quiz_questions):
                                st.warning(f"⚠️ Please answer all {len(quiz_questions)} questions before submitting")
                            else:
                                # Calculate score
                                correct = 0
                                total = len(quiz_questions)
                                
                                # Create attempt
                                attempt_id = db.create_quiz_attempt(quiz_id, user_id)
                                
                                # Calculate time taken
                                time_taken = int((datetime.now() - st.session_state.quiz_start_time).total_seconds())
                                
                                # Store answers and calculate score
                                for question in quiz_questions:
                                    user_answer = st.session_state.quiz_answers.get(question['id'])
                                    is_correct = user_answer == question['correct_answer']
                                    
                                    if is_correct:
                                        correct += 1
                                    
                                    db.add_quiz_answer(
                                        attempt_id=attempt_id,
                                        question_id=question['id'],
                                        user_answer=user_answer,
                                        is_correct=is_correct
                                    )
                                
                                score = (correct / total) * 100
                                
                                # Update attempt with score
                                db.complete_quiz_attempt(attempt_id, score, time_taken)
                                
                                # Store results for display
                                st.session_state.quiz_results = {
                                    'score': score,
                                    'correct': correct,
                                    'total': total,
                                    'time_taken': time_taken
                                }
                                st.session_state.show_results = True
                                st.session_state.taking_quiz = False
                                st.rerun()
                    
                    with col_cancel:
                        if st.button("Cancel Quiz", use_container_width=True):
                            st.session_state.taking_quiz = False
                            st.session_state.quiz_answers = {}
                            st.session_state.quiz_start_time = None
                            st.session_state.current_quiz_id = None
                            st.rerun()
        
        # Show results if just completed
        elif st.session_state.get('show_results', False):
            results = st.session_state.quiz_results
            
            st.markdown("### 🎯 Quiz Results")
            
            # Score display
            score = results['score']
            if score >= 90:
                emoji = "🏆"
                message = "Excellent!"
                color = "#4caf50"
            elif score >= 70:
                emoji = "🎉"
                message = "Great job!"
                color = "#8bc34a"
            elif score >= 50:
                emoji = "👍"
                message = "Good effort!"
                color = "#ff9800"
            else:
                emoji = "📚"
                message = "Keep studying!"
                color = "#f44336"
            
            st.markdown(f"""
                <div style='background-color: {color}; color: white; padding: 2rem; 
                            border-radius: 10px; text-align: center; margin: 1rem 0;'>
                    <h1 style='margin: 0; font-size: 4rem;'>{emoji}</h1>
                    <h2 style='margin: 0.5rem 0;'>{message}</h2>
                    <h1 style='margin: 0.5rem 0; font-size: 3rem;'>{score:.1f}%</h1>
                    <p style='margin: 0; font-size: 1.2rem;'>
                        {results['correct']} out of {results['total']} correct
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Time Taken", f"{results['time_taken'] // 60}m {results['time_taken'] % 60}s")
            with col2:
                st.metric("Average Time per Question", f"{results['time_taken'] / results['total']:.1f}s")
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("🔄 Take Another Quiz", type="primary", use_container_width=True):
                    st.session_state.show_results = False
                    st.session_state.quiz_results = None
                    st.rerun()
            with col_b:
                if st.button("📚 Back to Quiz List", use_container_width=True):
                    st.session_state.show_results = False
                    st.session_state.quiz_results = None
                    st.rerun()
        
        # Show quiz list (default view)
        else:
            st.markdown("### 📚 Your Quizzes")
            
            quizzes = db.get_document_quizzes(current_document_id)
            
            if quizzes:
                for quiz in quizzes:
                    attempts = db.get_quiz_attempts(quiz['id'])
                    num_attempts = len(attempts)
                    
                    # Calculate average score
                    if attempts:
                        avg_score = sum(a['score'] for a in attempts) / len(attempts)
                        best_score = max(a['score'] for a in attempts)
                    else:
                        avg_score = 0
                        best_score = 0
                    
                    # Quiz card with better styling
                    st.markdown(f"""
                        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                    padding: 1.5rem; border-radius: 15px; margin-bottom: 1.5rem;
                                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);'>
                            <h3 style='color: white; margin: 0 0 1rem 0;'>📝 {quiz['title']}</h3>
                            <div style='background-color: rgba(255,255,255,0.2); padding: 1rem; 
                                        border-radius: 10px; margin-bottom: 1rem;'>
                                <div style='display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;'>
                                    <div>
                                        <p style='color: rgba(255,255,255,0.8); font-size: 0.85rem; margin: 0;'>Created</p>
                                        <p style='color: white; font-weight: bold; margin: 0.3rem 0 0 0;'>{quiz['created_at'][:10]}</p>
                                    </div>
                                    <div>
                                        <p style='color: rgba(255,255,255,0.8); font-size: 0.85rem; margin: 0;'>Attempts</p>
                                        <p style='color: white; font-weight: bold; margin: 0.3rem 0 0 0;'>{num_attempts}</p>
                                    </div>
                                    <div>
                                        <p style='color: rgba(255,255,255,0.8); font-size: 0.85rem; margin: 0;'>Best Score</p>
                                        <p style='color: white; font-weight: bold; margin: 0.3rem 0 0 0;'>{best_score:.1f}%</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Get questions for this quiz
                    questions = db.get_quiz_questions(quiz['id'])
                    
                    # Action buttons
                    col_a, col_b, col_c = st.columns(3)
                    
                    with col_a:
                        if st.button("▶️ Take Quiz", key=f"take_{quiz['id']}", use_container_width=True, type="primary"):
                            st.session_state.current_quiz_id = quiz['id']
                            st.session_state.taking_quiz = True
                            st.session_state.quiz_answers = {}
                            st.session_state.quiz_start_time = datetime.now()
                            st.session_state.show_results = False  # Reset results
                            st.rerun()
                    
                    with col_b:
                        with st.expander("📊 View Details"):
                            st.write(f"**Questions:** {len(questions)}")
                            st.write(f"**Average Score:** {avg_score:.1f}%")
                            
                            if attempts:
                                st.markdown("#### Recent Attempts")
                                for i, attempt in enumerate(attempts[-5:], 1):  # Last 5 attempts
                                    score_color = "#4caf50" if attempt['score'] >= 70 else "#ff9800" if attempt['score'] >= 50 else "#f44336"
                                    st.markdown(f"""
                                        <div style='background-color: rgba(255,255,255,0.2); padding: 0.5rem; border-radius: 5px; 
                                                    margin: 0.3rem 0; border-left: 3px solid {score_color};'>
                                            {attempt['attempt_date'][:10]} - Score: {attempt['score']:.1f}% - Time: {attempt['time_taken']}s
                                        </div>
                                    """, unsafe_allow_html=True)
                    
                    with col_c:
                        if st.button("🗑️ Delete Quiz", key=f"delete_quiz_{quiz['id']}", use_container_width=True):
                            st.session_state.deleting_quiz_id = quiz['id']
                            st.rerun()
            
           
                    # Delete confirmation
                    if st.session_state.get('deleting_quiz_id') == quiz['id']:
                        st.error("⚠️ **Delete this quiz?** All attempts and answers will also be deleted.")
                        col_yes, col_no = st.columns(2)

                        with col_yes:
                            if st.button(
                                "Yes, Delete",
                                key=f"confirm_delete_{quiz['id']}",   # unique key
                                type="primary",
                                use_container_width=True
                            ):
                                try:
                                    db.delete_quiz(quiz['id'])
                                    st.success("✅ Quiz deleted successfully!")
                                except Exception as e:
                                    st.error(f"❌ Error deleting quiz: {str(e)}")
                                finally:
                                    st.session_state.deleting_quiz_id = None
                                    st.rerun()

                        with col_no:
                            if st.button(
                                "Cancel",
                                key=f"cancel_delete_{quiz['id']}",   # unique key
                                use_container_width=True
                            ):
                                st.session_state.deleting_quiz_id = None
                                st.rerun()
            else:
                st.info("📝 No quizzes yet. Generate your first quiz in the 'Generate Quiz' tab!")
    
    # ==================== TAB 3: Statistics ====================
    with tab3:
        st.markdown("### 📊 Quiz Statistics")
        
        all_quizzes = db.get_document_quizzes(current_document_id)
        
        if all_quizzes:
            total_quizzes = len(all_quizzes)
            total_attempts = sum(len(db.get_quiz_attempts(q['id'])) for q in all_quizzes)
            
            all_attempts = []
            for quiz in all_quizzes:
                all_attempts.extend(db.get_quiz_attempts(quiz['id']))
            
            if all_attempts:
                avg_score = sum(a['score'] for a in all_attempts) / len(all_attempts)
                best_score = max(a['score'] for a in all_attempts)
                total_time = sum(a['time_taken'] for a in all_attempts)
            else:
                avg_score = 0
                best_score = 0
                total_time = 0
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Quizzes", total_quizzes)
            with col2:
                st.metric("Total Attempts", total_attempts)
            with col3:
                st.metric("Average Score", f"{avg_score:.1f}%")
            with col4:
                st.metric("Best Score", f"{best_score:.1f}%")
            
            st.markdown("---")
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.metric("Total Study Time", f"{total_time // 60}m {total_time % 60}s")
            
            with col_b:
                if total_attempts > 0:
                    st.metric("Avg Time per Attempt", f"{total_time / total_attempts:.0f}s")
        else:
            st.info("📊 No statistics yet. Take some quizzes to see your progress!")
    
    # Back to dashboard
    st.markdown("---")
    if st.button("← Back to Dashboard", use_container_width=True):
        navigate_to('dashboard')