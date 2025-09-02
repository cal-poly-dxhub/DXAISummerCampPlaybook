import streamlit as st
from datetime import datetime
from components.pdf_viewer import PDFViewer
from test_storage import TestStorageManager as StorageManager
import random
from pathlib import Path
from config.config import CONFIG

def local_css():
    st.markdown("""
        <style>
        .main {
            padding: 0rem 1rem;
        }
        .stButton>button {
            width: 100%;
        }
        .stTextInput>div>div>input {
            padding: 0.5rem;
        }
        .review-header {
            background-color: #262730;
            color: white;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
        .review-header h2 {
            color: white;
            margin: 0;
        }
        .score-input {
            background-color: #262730;
            color: white;
            padding: 1.5rem;
            border-radius: 0.5rem;
            margin-bottom: 0.5rem;
        }
        .score-input label {
            color: white !important;
        }
        iframe {
            border: none;
            border-radius: 0.5rem;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 2rem;
        }
        .stTabs [data-baseweb="tab"] {
            height: 3rem;
        }
        /* Make number inputs stand out against dark background */
        .score-input input[type="number"] {
            background-color: #ffffff;
            color: #262730;
            border: 1px solid #cccccc;
            border-radius: 0.3rem;
            padding: 0.3rem;
        }
        /* Remove empty space above score inputs */
        .score-input > div > div > div:first-child {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        /* Style the notes text area */
        .stTextArea textarea {
            background-color: #262730;
            color: white;
            border: 1px solid #4a4a4a;
            border-radius: 0.3rem;
        }
        /* Style the form container */
        .stForm {
            background-color: transparent;
            padding: 0 !important;
            margin-top: 0 !important;
        }
        /* Style the submit button */
        .stForm [data-baseweb="button"] {
            background-color: #262730;
            color: white;
            border-radius: 0.3rem;
            padding: 0.5rem 1rem;
            margin-top: 1rem;
        }
        /* Additional styling for form elements */
        div[data-baseweb="base-input"] {
            margin-top: 0 !important;
        }
        /* Remove extra spacing from form elements */
        .stForm > div {
            padding-top: 0 !important;
            margin-top: 0 !important;
        }
        /* Remove spacing from number input containers */
        .score-input > div {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        /* Remove spacing from form field containers */
        .stForm > div > div {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        /* Remove spacing from specific score input fields */
        .stForm div[data-baseweb="input"] {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        .stForm div[data-baseweb="input"] > div {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        /* Remove spacing from number input labels */
        .stForm div[data-baseweb="input"] label {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        /* Remove spacing from number input containers */
        .stForm div[data-baseweb="input"] > div > div {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        /* Remove spacing from number input elements */
        .stForm div[data-baseweb="input"] > div > div > div {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        </style>
    """, unsafe_allow_html=True)

# Scoring guide text
SCORING_GUIDE = """
### SCORING RULES:
1. **Use the full scoring range (0–100)**. Scoring must be **linear**:
   - A 90 should indicate significantly stronger evidence than a 70, not just slightly better.
   - Do **not** cluster scores in the 80s unless truly warranted.
   - Be willing to give low or high scores if evidence supports it.
2. **Focus only on what is documented**. Do not infer based on school name, GPA, formatting aesthetics, or class year.
3. Take the candidate's major into account **only** for technical categories:
   - For **Technical Experience** and **Problem Decomposition**:
   - A **CS / Data Science / Computer Engineering** major is expected to show depth, specificity, and well-documented application.
   - A **non-technical major** should be rewarded for effort, learning, or creative tech use, even if depth is lower.
   - Engineering majors are considered **semi-technical** — evaluate fairly, but don't expect the same level of coding/project rigor as CS.
   For all **non-technical categories**, major should have **zero impact** on score.
"""

CATEGORY_DESCRIPTIONS = {
    'Collaboration': """
    Look for: Team projects, clubs, working with others
    - 90-100: Strong team roles, clear collaboration impact
    - 70-89: Some good group involvement
    - 40-69: Limited or vague teamwork
    - 0-39: No collaboration shown
    """,
    'Initiative': """
    Look for: Independent work, self-started efforts, extra contributions
    - 90-100: Strong independent or proactive effort
    - 70-89: Some self-started activities
    - 40-69: Participated but didn't lead or initiate
    - 0-39: No signs of initiative
    """,
    'Creativity': """
    Look for: Unique solutions, interdisciplinary projects, original work
    - 90-100: Highly original or innovative work
    - 70-89: Some creative approaches
    - 40-69: Basic ideas with minor creativity
    - 0-39: No evidence of creativity
    """,
    'Communication': """
    Look for: Resume clarity, writing tone, organization
    - 90-100: Highly clear, polished, professional
    - 70-89: Generally readable and organized
    - 40-69: Some confusion or vagueness
    - 0-39: Poorly presented or unprofessional
    """,
    'Problem Decomposition': """
    Look for: Logical structure, technical breakdown, analysis
    - 90-100: Clear breakdown of complex problems
    - 70-89: Some systematic thinking
    - 40-69: Weak explanation or structure
    - 0-39: No decomposition shown
    """,
    'Growth Mindset': """
    Look for: Courses, self-learning, upskilling, adaptability
    - 90-100: Persistent learning and challenge-seeking
    - 70-89: Took some initiative to grow
    - 40-69: Minimal learning beyond school
    - 0-39: No signs of learning effort
    """,
    'Technical Experience': """
    Look for: Project work, applied skills, technical depth
    - Consider major:
      - CS majors should show concrete project work and depth
      - Non-technical majors should be scored generously if trying to bridge into tech
    - 90-100: Strong project work and applied skills
    - 70-89: Some good experience or tools used
    - 40-69: Basic buzzwords or vague claims
    - 0-39: No technical experience shown
    """
}

def login_page():
    """Enhanced login page"""
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("""
            <div style='text-align: center; padding: 2rem;'>
                <h1>Resume Review System</h1>
                <p>Please login to continue</p>
            </div>
        """, unsafe_allow_html=True)
        
        username = st.text_input("Username", key="login_username")
        if st.button("Login", key="login_button"):
            if username:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Please enter a username")

def main():
    st.set_page_config(
        page_title="Resume Scoring System",
        page_icon="📝",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    local_css()
    
    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'current_candidate' not in st.session_state:
        st.session_state.current_candidate = None
    if 'review_start_time' not in st.session_state:
        st.session_state.review_start_time = None

    # Handle login
    if not st.session_state.logged_in:
        login_page()
        return

    # Initialize storage manager
    storage = StorageManager()

    # If we have a current candidate but no start time, we probably reloaded
    if st.session_state.current_candidate and not st.session_state.review_start_time:
        # Release the lock and clear the candidate
        storage._release_lock(st.session_state.current_candidate)
        st.session_state.current_candidate = None
        st.rerun()
        return

    # Sidebar
    with st.sidebar:
        st.markdown(f"""
            <div style='text-align: center; padding: 1rem;'>
                <h3>Welcome, {st.session_state.username}!</h3>
            </div>
        """, unsafe_allow_html=True)
        
        with st.expander("Scoring Guide", expanded=False):
            st.markdown(SCORING_GUIDE)
        
        # Add Progress Bar
        st.markdown("""
            <div style='text-align: center; padding: 1rem; background-color: #262730; border-radius: 0.5rem; margin: 1rem 0;'>
                <h3>📊 Review Progress 📊</h3>
            </div>
        """, unsafe_allow_html=True)
        
        # Calculate progress
        progress_data = storage.get_review_progress()
        
        # Display progress
        st.progress(progress_data['progress_percentage'] / 100)
        st.write(f"Progress: {progress_data['progress_percentage']:.1f}%")
        st.write(f"Reviews still needed: {progress_data['reviews_needed']}")
        st.write(f"Resumes with 2 reviews: {progress_data['resumes_with_2_reviews']}")
        st.write(f"Resumes with 1 review: {progress_data['resumes_with_1_review']}")
        st.write(f"Total resumes: {progress_data['total_candidates']}")
        
        # Add Leaderboard
        st.markdown("""
            <div style='text-align: center; padding: 1rem; background-color: #262730; border-radius: 0.5rem; margin: 1rem 0;'>
                <h3>🏆 Review Leaderboard 🏆</h3>
            </div>
        """, unsafe_allow_html=True)
        
        # Get reviewer stats
        reviewer_stats = storage.get_reviewer_stats()
        
        # Sort reviewers by total reviews
        sorted_reviewers = sorted(
            reviewer_stats.items(),
            key=lambda x: x[1]['total_reviews'],
            reverse=True
        )
        
        # Display leaderboard
        for i, (username, stats) in enumerate(sorted_reviewers, 1):
            # Choose emoji based on rank
            rank_emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            
            # Calculate average score with 2 decimal places
            avg_score = round(stats['avg_score'], 2)
            
            # Create a colored background for the current user
            is_current_user = username == st.session_state.username
            bg_color = "#4a4a4a" if is_current_user else "#262730"
            
            st.markdown(f"""
                <div style='background-color: {bg_color}; padding: 0.5rem; border-radius: 0.3rem; margin: 0.2rem 0;'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <span style='font-size: 1.2rem;'>{rank_emoji} {username}</span>
                        <span style='font-size: 1.2rem;'>{stats['total_reviews']} reviews</span>
                    </div>
                    <div style='text-align: right; font-size: 0.9rem; color: #888;'>
                        Avg Score: {avg_score}
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        if st.button("Logout", key="logout_button"):
            st.session_state.clear()
            st.rerun()

    # Main content
    if not st.session_state.current_candidate:
        available_candidates = storage.get_available_candidates(st.session_state.username)
        if not available_candidates:
            st.info("No more resumes available for review!")
            return
            
        # Try to reserve a random candidate
        random.shuffle(available_candidates)  # Shuffle to distribute load
        for candidate in available_candidates:
            if storage.reserve_candidate(st.session_state.username, candidate):
                st.session_state.current_candidate = candidate
                st.session_state.review_start_time = datetime.now()
                break
        else:
            st.info("No resumes available at the moment. Please try again in a few seconds.")
            return

    # Safety check before showing the candidate
    if storage._has_user_reviewed(st.session_state.username, st.session_state.current_candidate):
        storage._release_lock(st.session_state.current_candidate)
        st.session_state.current_candidate = None
        st.rerun()
        return

    content_package = storage.get_resume_content(st.session_state.current_candidate)
    if content_package:
        # Review header
        st.markdown(f"""
            <div class='review-header'>
                <h2>Reviewing Candidate {st.session_state.current_candidate}</h2>
            </div>
        """, unsafe_allow_html=True)

        # Display resume(s)
        PDFViewer.display_resume_package(content_package)

        # Scoring form
        with st.form("scoring_form", clear_on_submit=True):
            scores = {}
            col1, col2 = st.columns(2)
            
            categories = list(CATEGORY_DESCRIPTIONS.keys())
            # Calculate how many categories should go in each column
            # For odd number of categories, first column gets the extra one
            first_col_count = (len(categories) + 1) // 2
            
            for i, column in enumerate([col1, col2]):
                with column:
                    st.markdown("<div class='score-input'>", unsafe_allow_html=True)
                    if i == 0:
                        category_slice = categories[:first_col_count]
                    else:
                        category_slice = categories[first_col_count:]
                    for category in category_slice:
                        scores[category] = st.slider(
                            f"Score for {category}",
                            min_value=0,
                            max_value=100,
                            value=50,
                            step=1,
                            help=CATEGORY_DESCRIPTIONS[category]
                        )
                    st.markdown("</div>", unsafe_allow_html=True)

            notes = st.text_area("Additional Notes", height=100)
            submitted = st.form_submit_button("Submit Review")

            if submitted:
                review_data = {
                    'scores': scores,
                    'notes': notes,
                    'review_start_time': st.session_state.review_start_time.isoformat(),
                    'review_end_time': datetime.now().isoformat(),
                    'total_score': sum(scores.values()) / len(scores)
                }

                success, error_msg = storage.save_review(
                    st.session_state.username,
                    st.session_state.current_candidate,
                    review_data
                )

                if success:
                    st.success("Review submitted successfully!")
                    st.session_state.current_candidate = None
                    st.session_state.review_start_time = None
                    st.rerun()
                else:
                    st.error(error_msg)
                    st.session_state.current_candidate = None
                    st.session_state.review_start_time = None
                    st.rerun()

    else:
        st.error("Failed to load resume")
        st.session_state.current_candidate = None
        st.rerun()

if __name__ == "__main__":
    main()