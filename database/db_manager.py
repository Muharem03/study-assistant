import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from cryptography.fernet import Fernet
import os
import json


class DatabaseManager:
    """Manages all database operations for the AI Study Assistant"""
    
    def __init__(self, db_path: str = "study_assistant.db"):
        self.db_path = db_path
        # Get encryption key from environment variable
        encryption_key = os.getenv('ENCRYPTION_KEY')
        if not encryption_key:
            # Try to load from .encryption_key file
            key_file = '.encryption_key'
            if os.path.exists(key_file):
                with open(key_file, 'r') as f:
                    encryption_key = f.read().strip()
            else:
                # Generate a new key if none exists (for first run)
                encryption_key = Fernet.generate_key().decode()
                # Save it to file
                with open(key_file, 'w') as f:
                    f.write(encryption_key)
                print(f"⚠️ WARNING: Generated new encryption key and saved to {key_file}")
                print(f"Add this to your .env file: ENCRYPTION_KEY={encryption_key}")
        
        self.cipher = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
        self.initialize_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def initialize_database(self):
        """Create all tables if they don't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            ''')
            
            # User settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    azure_api_key TEXT,
                    azure_endpoint TEXT,
                    azure_deployment_name TEXT,
                    azure_api_version TEXT DEFAULT '2024-02-15-preview',
                    embedding_model TEXT DEFAULT 'text-embedding-ada-002',
                    chat_model TEXT DEFAULT 'gpt-4',
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # Subjects table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subjects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    color TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # Documents table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    file_path TEXT,
                    file_type TEXT,
                    file_size INTEGER,
                    faiss_index_path TEXT,
                    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processing_status TEXT DEFAULT 'pending',
                    chunk_count INTEGER,
                    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # Chat history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    tokens_used INTEGER,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # Quizzes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS quizzes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    title TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # Quiz questions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS quiz_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    quiz_id INTEGER NOT NULL,
                    question TEXT NOT NULL,
                    correct_answer TEXT NOT NULL,
                    option_a TEXT,
                    option_b TEXT,
                    option_c TEXT,
                    option_d TEXT,
                    explanation TEXT,
                    FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
                )
            ''')
            
            # Quiz attempts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS quiz_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    quiz_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    attempt_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    score REAL,
                    time_taken INTEGER,
                    FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # Quiz answers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS quiz_answers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    attempt_id INTEGER NOT NULL,
                    question_id INTEGER NOT NULL,
                    user_answer TEXT NOT NULL,
                    is_correct BOOLEAN,
                    FOREIGN KEY (attempt_id) REFERENCES quiz_attempts(id) ON DELETE CASCADE,
                    FOREIGN KEY (question_id) REFERENCES quiz_questions(id) ON DELETE CASCADE
                )
            ''')
            
            # Flashcard sets table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS flashcard_sets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # Flashcard items table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS flashcard_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    flashcard_set_id INTEGER NOT NULL,
                    front TEXT NOT NULL,
                    back TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (flashcard_set_id) REFERENCES flashcard_sets(id) ON DELETE CASCADE
                )
            ''')
            
            # Flashcard reviews table (for spaced repetition)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS flashcard_reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    flashcard_item_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    difficulty INTEGER,
                    review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    next_review_date TIMESTAMP,
                    FOREIGN KEY (flashcard_item_id) REFERENCES flashcard_items(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # Tasks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    subject_id INTEGER,
                    title TEXT NOT NULL,
                    description TEXT,
                    due_date DATE,
                    priority TEXT DEFAULT 'medium',
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE SET NULL
                )
            ''')
            
            # Processing logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS processing_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_subjects_user ON subjects(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_documents_subject ON documents(subject_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_documents_user ON documents(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_history_document ON chat_history(document_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_history_user ON chat_history(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_user ON tasks(user_id)')
    
    # ==================== ENCRYPTION METHODS ====================
    
    def encrypt_api_key(self, api_key: str) -> str:
        """Encrypt API key before storing"""
        return self.cipher.encrypt(api_key.encode()).decode()
    
    def decrypt_api_key(self, encrypted_key: str) -> str:
        """Decrypt API key when retrieving"""
        return self.cipher.decrypt(encrypted_key.encode()).decode()
    
    # ==================== USER METHODS ====================
    
    def create_user(self, email: str, username: str, password_hash: str) -> Optional[int]:
        """Create a new user"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (email, username, password_hash)
                    VALUES (?, ?, ?)
                ''', (email, username, password_hash))
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_last_login(self, user_id: int):
        """Update user's last login timestamp"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET last_login = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (user_id,))
    
    def update_user_password(self, user_id: int, password_hash: str):
        """
        Update user's password hash"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET password_hash = ?
                WHERE id = ?
            ''', (password_hash, user_id))

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    # ==================== USER SETTINGS METHODS ====================
    
    def save_user_settings(self, user_id: int, azure_api_key: str, azure_endpoint: str, 
                          azure_deployment_name: str, azure_api_version: str = '2024-02-15-preview',
                          embedding_model: str = 'text-embedding-ada-002',
                          chat_model: str = 'gpt-4') -> bool:
        """Save or update user's Azure OpenAI settings"""
        encrypted_key = self.encrypt_api_key(azure_api_key)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user_settings (user_id, azure_api_key, azure_endpoint, 
                                         azure_deployment_name, azure_api_version,
                                         embedding_model, chat_model)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    azure_api_key = excluded.azure_api_key,
                    azure_endpoint = excluded.azure_endpoint,
                    azure_deployment_name = excluded.azure_deployment_name,
                    azure_api_version = excluded.azure_api_version,
                    embedding_model = excluded.embedding_model,
                    chat_model = excluded.chat_model
            ''', (user_id, encrypted_key, azure_endpoint, azure_deployment_name, 
                  azure_api_version, embedding_model, chat_model))
            return True
    
    def get_user_settings(self, user_id: int) -> Optional[Dict]:
        """Get user's settings with decrypted API key"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM user_settings WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if row:
                settings = dict(row)
                if settings.get('azure_api_key'):
                    settings['azure_api_key'] = self.decrypt_api_key(settings['azure_api_key'])
                return settings
            return None
    
    # ==================== SUBJECT METHODS ====================
    
    def create_subject(self, user_id: int, name: str, description: str = None, 
                       color: str = None) -> int:
        """Create a new subject"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO subjects (user_id, name, description, color)
                VALUES (?, ?, ?, ?)
            ''', (user_id, name, description, color))
            return cursor.lastrowid
    
    def get_user_subjects(self, user_id: int) -> List[Dict]:
        """Get all subjects for a user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM subjects WHERE user_id = ?
                ORDER BY created_at DESC
            ''', (user_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_subject(self, subject_id: int) -> Optional[Dict]:
        """Get a specific subject"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM subjects WHERE id = ?', (subject_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_subject(self, subject_id: int, name: str = None, 
                       description: str = None, color: str = None):
        """Update subject details"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            updates = []
            params = []
            if name:
                updates.append("name = ?")
                params.append(name)
            if description is not None:
                updates.append("description = ?")
                params.append(description)
            if color:
                updates.append("color = ?")
                params.append(color)
            
            if updates:
                params.append(subject_id)
                cursor.execute(f'''
                    UPDATE subjects SET {', '.join(updates)}
                    WHERE id = ?
                ''', params)
    
    def delete_subject(self, subject_id: int):
        """Delete a subject (cascades to documents)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM subjects WHERE id = ?', (subject_id,))
    
    # ==================== DOCUMENT METHODS ====================
    
    def create_document(self, subject_id: int, user_id: int, title: str, 
                       file_path: str, file_type: str, file_size: int) -> int:
        """Create a new document"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO documents (subject_id, user_id, title, file_path, 
                                     file_type, file_size, processing_status)
                VALUES (?, ?, ?, ?, ?, ?, 'pending')
            ''', (subject_id, user_id, title, file_path, file_type, file_size))
            return cursor.lastrowid
    
    def get_subject_documents(self, subject_id: int) -> List[Dict]:
        """Get all documents for a subject"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM documents WHERE subject_id = ?
                ORDER BY upload_date DESC
            ''', (subject_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_document(self, document_id: int) -> Optional[Dict]:
        """Get a specific document"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM documents WHERE id = ?', (document_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_document_processing(self, document_id: int, status: str, 
                                   faiss_index_path: str = None, 
                                   chunk_count: int = None):
        """Update document processing status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if faiss_index_path and chunk_count:
                cursor.execute('''
                    UPDATE documents 
                    SET processing_status = ?, faiss_index_path = ?, chunk_count = ?
                    WHERE id = ?
                ''', (status, faiss_index_path, chunk_count, document_id))
            else:
                cursor.execute('''
                    UPDATE documents SET processing_status = ?
                    WHERE id = ?
                ''', (status, document_id))
    
    def delete_document(self, document_id: int):
        """Delete a document"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM documents WHERE id = ?', (document_id,))
    
    # ==================== CHAT HISTORY METHODS ====================
    
    def add_chat_message(self, document_id: int, user_id: int, role: str, 
                        message: str, tokens_used: int = None) -> int:
        """Add a chat message"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO chat_history (document_id, user_id, role, message, tokens_used)
                VALUES (?, ?, ?, ?, ?)
            ''', (document_id, user_id, role, message, tokens_used))
            return cursor.lastrowid
    
    def get_chat_history(self, document_id: int, limit: int = 50) -> List[Dict]:
        """Get chat history for a document"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM chat_history 
                WHERE document_id = ?
                ORDER BY timestamp ASC
                LIMIT ?
            ''', (document_id, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def clear_chat_history(self, document_id: int):
        """Clear chat history for a document"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM chat_history WHERE document_id = ?', (document_id,))
    
    # ==================== QUIZ METHODS ====================
    
    def create_quiz(self, document_id: int, user_id: int, title: str) -> int:
        """Create a new quiz"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO quizzes (document_id, user_id, title)
                VALUES (?, ?, ?)
            ''', (document_id, user_id, title))
            return cursor.lastrowid
    
    def add_quiz_question(self, quiz_id: int, question: str, correct_answer: str,
                         option_a: str = None, option_b: str = None,
                         option_c: str = None, option_d: str = None,
                         explanation: str = None) -> int:
        """Add a question to a quiz"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO quiz_questions 
                (quiz_id, question, correct_answer, option_a, option_b, option_c, option_d, explanation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (quiz_id, question, correct_answer, option_a, option_b, option_c, option_d, explanation))
            return cursor.lastrowid
    
    def get_document_quizzes(self, document_id: int) -> List[Dict]:
        """Get all quizzes for a document"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM quizzes WHERE document_id = ?
                ORDER BY created_at DESC
            ''', (document_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_quiz_questions(self, quiz_id: int) -> List[Dict]:
        """Get all questions for a quiz"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM quiz_questions WHERE quiz_id = ?
            ''', (quiz_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def create_quiz_attempt(self, quiz_id: int, user_id: int) -> int:
        """Create a new quiz attempt"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO quiz_attempts (quiz_id, user_id)
                VALUES (?, ?)
            ''', (quiz_id, user_id))
            return cursor.lastrowid
    
    def add_quiz_answer(self, attempt_id: int, question_id: int, 
                       user_answer: str, is_correct: bool):
        """Record an answer for a quiz attempt"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO quiz_answers (attempt_id, question_id, user_answer, is_correct)
                VALUES (?, ?, ?, ?)
            ''', (attempt_id, question_id, user_answer, is_correct))
    
    def complete_quiz_attempt(self, attempt_id: int, score: float, time_taken: int):
        """Update quiz attempt with final score"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE quiz_attempts 
                SET score = ?, time_taken = ?
                WHERE id = ?
            ''', (score, time_taken, attempt_id))
    
    def get_quiz_attempts(self, quiz_id: int) -> List[Dict]:
        """Get all attempts for a quiz"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM quiz_attempts WHERE quiz_id = ?
                ORDER BY attempt_date DESC
            ''', (quiz_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_quiz(self, quiz_id: int):
        """Delete a quiz (cascades to questions, attempts, and answers)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM quizzes WHERE id = ?', (quiz_id,))
    
    # ==================== FLASHCARD METHODS ====================
    
    def create_flashcard_set(self, document_id: int, user_id: int, title: str) -> int:
        """Create a new flashcard set"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO flashcard_sets (document_id, user_id, title)
                VALUES (?, ?, ?)
            ''', (document_id, user_id, title))
            return cursor.lastrowid
    
    def add_flashcard(self, flashcard_set_id: int, front: str, back: str) -> int:
        """Add a flashcard to a set"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO flashcard_items (flashcard_set_id, front, back)
                VALUES (?, ?, ?)
            ''', (flashcard_set_id, front, back))
            return cursor.lastrowid
    
    def delete_flashcard_set(self, flashcard_set_id: int):
        """Delete a flashcard set (cascades to flashcard items and reviews)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM flashcard_sets WHERE id = ?', (flashcard_set_id,))
    
    def get_flashcard_set(self, flashcard_set_id: int) -> Optional[Dict]:
        """ Get a specific flashcard set"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM flashcard_sets WHERE id = ?', (flashcard_set_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_document_flashcard_sets(self, document_id: int) -> List[Dict]:
        """Get all flashcard sets for a document"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM flashcard_sets WHERE document_id = ?
                ORDER BY created_at DESC
            ''', (document_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_flashcards(self, flashcard_set_id: int) -> List[Dict]:
        """Get all flashcards in a set"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM flashcard_items WHERE flashcard_set_id = ?
            ''', (flashcard_set_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def add_flashcard_review(self, flashcard_item_id: int, user_id: int, 
                            difficulty: int, next_review_date: str = None):
        """Record a flashcard review (for spaced repetition)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO flashcard_reviews 
                (flashcard_item_id, user_id, difficulty, next_review_date)
                VALUES (?, ?, ?, ?)
            ''', (flashcard_item_id, user_id, difficulty, next_review_date))
    
    # ==================== TASK/PLANNER METHODS ====================
    
    def create_task(self, user_id: int, title: str, description: str = None,
                   due_date: str = None, priority: str = 'medium', 
                   subject_id: int = None) -> int:
        """Create a new task"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO tasks (user_id, subject_id, title, description, due_date, priority)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, subject_id, title, description, due_date, priority))
            return cursor.lastrowid
    
    def get_user_tasks(self, user_id: int, status: str = None) -> List[Dict]:
        """Get tasks for a user, optionally filtered by status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute('''
                    SELECT * FROM tasks WHERE user_id = ? AND status = ?
                    ORDER BY due_date ASC, priority DESC
                ''', (user_id, status))
            else:
                cursor.execute('''
                    SELECT * FROM tasks WHERE user_id = ?
                    ORDER BY due_date ASC, priority DESC
                ''', (user_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def update_task_status(self, task_id: int, status: str):
        """Update task status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            completed_at = datetime.now().isoformat() if status == 'completed' else None
            cursor.execute('''
                UPDATE tasks SET status = ?, completed_at = ?
                WHERE id = ?
            ''', (status, completed_at, task_id))
    
    def update_task(self, task_id: int, title: str = None, description: str = None,
                    due_date: str = None, priority: str = None, status: str = None,
                    subject_id: int = None):
        """Update task details"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            updates = []
            params = []
            
            if title is not None:
                updates.append("title = ?")
                params.append(title)
            
            if description is not None:
                updates.append("description = ?")
                params.append(description)
            
            if due_date is not None:
                updates.append("due_date = ?")
                params.append(due_date)
            
            if priority is not None:
                updates.append("priority = ?")
                params.append(priority)
            
            if status is not None:
                updates.append("status = ?")
                params.append(status)
                # Update completed_at timestamp if status is completed
                if status == 'completed':
                    updates.append("completed_at = CURRENT_TIMESTAMP")
                elif status in ['pending', 'in_progress']:
                    updates.append("completed_at = NULL")
            
            if subject_id is not None:
                updates.append("subject_id = ?")
                params.append(subject_id)
            
            if updates:
                params.append(task_id)
                query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
                cursor.execute(query, params)

    def get_task(self, task_id: int) -> Optional[Dict]:
        """ Get a specific task"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def delete_task(self, task_id: int):
        """Delete a task"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    
    # ==================== PROCESSING LOG METHODS ====================
    
    def add_processing_log(self, document_id: int, status: str, message: str = None):
        """Add a processing log entry"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO processing_logs (document_id, status, message)
                VALUES (?, ?, ?)
            ''', (document_id, status, message))
    
    def get_processing_logs(self, document_id: int) -> List[Dict]:
        """Get processing logs for a document"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM processing_logs WHERE document_id = ?
                ORDER BY timestamp DESC
            ''', (document_id,))
            return [dict(row) for row in cursor.fetchall()]