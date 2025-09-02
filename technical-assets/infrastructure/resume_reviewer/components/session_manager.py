import streamlit as st
from datetime import datetime
from utils.storage import StorageManager
from utils.logger import LoggerManager

class SessionManager:
    @staticmethod
    def init_session():
        """Initialize session state variables"""
        if 'username' not in st.session_state:
            st.session_state.username = None
        if 'current_resume' not in st.session_state:
            st.session_state.current_resume = None
        if 'form_data' not in st.session_state:
            st.session_state.form_data = None
        if 'session_start' not in st.session_state:
            st.session_state.session_start = datetime.now()
        if 'reviews_completed' not in st.session_state:
            st.session_state.reviews_completed = 0

    @staticmethod
    def login(username, password):
        """Handle user login"""
        # In a real application, implement proper authentication
        # This is a simplified version
        if username and password:  # Add proper validation
            st.session_state.username = username
            LoggerManager.log_user_action(username, "login")
            return True
        return False

    @staticmethod
    def logout():
        """Handle user logout"""
        if st.session_state.username:
            LoggerManager.log_user_action(st.session_state.username, "logout")
        for key in ['username', 'current_resume', 'form_data']:
            if key in st.session_state:
                del st.session_state[key]

    @staticmethod
    def save_form_state(resume_id, scores, notes):
        """Save current form state"""
        st.session_state.form_data = {
            'resume_id': resume_id,
            'scores': scores,
            'notes': notes,
            'timestamp': datetime.now().isoformat()
        }
        StorageManager().backup_form_data(
            st.session_state.username,
            resume_id,
            scores,
            notes
        )

    @staticmethod
    def get_session_stats():
        """Get current session statistics"""
        if not st.session_state.session_start:
            return None
        
        return {
            'session_duration': datetime.now() - st.session_state.session_start,
            'reviews_completed': st.session_state.reviews_completed,
            'username': st.session_state.username
        }

    @staticmethod
    def increment_review_count():
        """Increment the number of completed reviews"""
        st.session_state.reviews_completed += 1