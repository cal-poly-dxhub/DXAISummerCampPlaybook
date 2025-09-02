import streamlit as st
import pandas as pd
from typing import Dict, List
from datetime import datetime
import base64
import os
import sys
import io
import json

# Add the root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))



from data_cache import get_candidate_data
from utils import (
    is_technical_major,
    format_score,
    format_timestamp,
    get_score_color,
    calculate_university_stats,
    get_selection_progress
)

class PDFViewer:
    @staticmethod
    def display_pdf_native(pdf_file):
        """Display PDF in its native format"""
        base64_pdf = base64.b64encode(pdf_file.read()).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)

def get_resume_pdf(candidate_id: str) -> tuple[bytes, str]:
    """Get the resume PDF from the rows folder."""
    # Get the absolute path to the rows directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rows_dir = os.path.join(base_dir, 'rows')
    
    # Construct the path to the PDF
    pdf_path = os.path.join(rows_dir, str(candidate_id), 'file_0.pdf')
    
    if not os.path.exists(pdf_path):
        return None, None
    
    try:
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()
            base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
            return pdf_bytes, base64_pdf
    except Exception as e:
        st.error(f"Error reading PDF file: {str(e)}")
        return None, None

def shorten_university_name(university: str) -> str:
    """Shorten university name to just the location."""
    if not university:
        return ''
    
    # Extract location from common patterns
    if 'California State University' in university:
        # Extract location after the comma
        parts = university.split(',')
        if len(parts) > 1:
            return parts[1].strip()
        # If no comma, try to extract after "University"
        parts = university.split('University')
        if len(parts) > 1:
            return parts[1].strip()
    
    # Handle special cases
    special_cases = {
        'San Diego State University': 'San Diego',
        'San Francisco State University': 'San Francisco',
        'San José State University': 'San José',
        'California Polytechnic State University, San Luis Obispo': 'SLO',
        'California State Polytechnic University, Pomona': 'Pomona',
        'California State University Maritime Academy': 'Maritime',
        'California State Polytechnic University, Humboldt': 'Humboldt',
        'California State University Channel Islands': 'Channel Islands',
        'California State University, Dominguez Hills': 'Dominguez Hills',
        'California State University, East Bay': 'East Bay',
        'California State University San Marcos': 'San Marcos',
        'California State University, Bakersfield': 'Bakersfield',
        'California State University, Chico': 'Chico',
        'California State University, Fullerton': 'Fullerton',
        'California State University, Long Beach': 'Long Beach',
        'California State University, Los Angeles': 'Los Angeles',
        'California State University, Monterey Bay': 'Monterey Bay',
        'California State University, Northridge': 'Northridge',
        'California State University, Sacramento': 'Sacramento',
        'California State University, San Bernardino': 'San Bernardino',
        'California State University, Stanislaus': 'Stanislaus',
        'Sonoma State University': 'Sonoma'
    }
    
    return special_cases.get(university, university)

# Set page config - must be the first Streamlit command
st.set_page_config(
    page_title="CSU AI Summer Camp - Candidate Selection",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    /* Main container */
    .main {
        padding: 2rem;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #1E88E5;
        margin-bottom: 1rem;
    }
    
    /* Cards */
    .stButton>button {
        width: 100%;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        background-color: #f0f2f6;
        border: 1px solid #e0e0e0;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #e0e0e0;
        border-color: #1E88E5;
    }
    
    /* Metrics */
    .stMetric {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
    }
    
    /* Sidebar */
    .css-1d391kg {
        padding: 2rem 1rem;
    }
    
    /* Filters */
    .stSelectbox, .stMultiselect, .stSlider {
        margin-bottom: 1rem;
    }
    
    /* Candidate cards */
    .candidate-card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* PDF viewer */
    iframe {
        border: none;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Progress bars */
    .stProgress > div > div {
        background-color: #1E88E5;
    }
    
    /* Charts */
    .stChart {
        border-radius: 0.5rem;
        padding: 1rem;
        background-color: #ffffff;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    /* Dataframe styling */
    .stDataFrame {
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    /* Dataframe header */
    .stDataFrame th {
        background-color: #f8f9fa !important;
        color: #1E88E5 !important;
        font-weight: bold !important;
    }

    /* Dataframe rows */
    .stDataFrame td {
        padding: 0.5rem !important;
    }

    /* Dataframe hover */
    .stDataFrame tr:hover {
        background-color: #f0f2f6 !important;
    }

    /* Dataframe selected row */
    .stDataFrame tr.selected {
        background-color: #e3f2fd !important;
    }
    </style>
""", unsafe_allow_html=True)

def save_selection_data():
    """Save selected and waitlisted candidates to a JSON file."""
    data = {
        'selected': [c['id'] for c in st.session_state.selected_candidates],
        'waitlist': [c['id'] for c in st.session_state.waitlist_candidates],
        'timestamp': datetime.now().isoformat()
    }
    
    # Create data directory if it doesn't exist
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # Save to JSON file
    with open(os.path.join(data_dir, 'selection_data.json'), 'w') as f:
        json.dump(data, f)

def load_selection_data(candidates):
    """Load selected and waitlisted candidates from JSON file."""
    data_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'selection_data.json')
    
    if not os.path.exists(data_file):
        return [], []
    
    try:
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        # Convert IDs back to candidate objects
        selected = [c for c in candidates if c['id'] in data['selected']]
        waitlist = [c for c in candidates if c['id'] in data['waitlist']]
        
        return selected, waitlist
    except Exception as e:
        st.error(f"Error loading selection data: {str(e)}")
        return [], []

# Initialize session state
if 'selected_candidates' not in st.session_state:
    st.session_state.selected_candidates = []
if 'waitlist_candidates' not in st.session_state:
    st.session_state.waitlist_candidates = []
if 'expanded_candidate' not in st.session_state:
    st.session_state.expanded_candidate = None
if 'show_reviewer_names' not in st.session_state:
    st.session_state.show_reviewer_names = False

# Load data
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_data():
    candidates = get_candidate_data()
    
    # Load AI scores
    ai_scores_df = pd.read_csv('/home/ec2-user/resume_reviewer/resume_scores_final.csv')
    ai_scores_dict = {}
    for _, row in ai_scores_df.iterrows():
        record_id = str(row['Record ID'])
        ai_scores_dict[record_id] = {
            'collaboration': row['Collab_avg'],
            'initiative': row['Init_avg'],
            'creativity': row['Creat_avg'],
            'communication': row['Comm_avg'],
            'problem_decomposition': row['Decomp_avg'],
            'growth_mindset': row['Growth_avg'],
            'technical_experience': row['Tech_avg'],
            'final_score': row['FinalScore']
        }
    
    # Add AI scores to candidates
    for candidate in candidates:
        candidate_id = str(candidate['id'])
        if candidate_id in ai_scores_dict:
            candidate['ai_scores'] = ai_scores_dict[candidate_id]
        else:
            candidate['ai_scores'] = None
    
    return candidates

# Load candidates and selection data
candidates = load_data()
if not st.session_state.selected_candidates and not st.session_state.waitlist_candidates:
    st.session_state.selected_candidates, st.session_state.waitlist_candidates = load_selection_data(candidates)

# Main content
st.title("🎓 CSU AI Summer Camp - Candidate Selection")

# Add refresh button with icon
col1, col2 = st.columns([6, 1])
with col2:
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.experimental_rerun()

# Convert to DataFrame for easier filtering and sorting
df = pd.DataFrame([{
    'id': c['id'],
    'name': c['name'],
    'email': c['email'],
    'university': shorten_university_name(c['university']),
    'major': c['major'],
    'year': c['year'],
    'overall_score': c['avg_scores']['overall'],
    'technical_score': c['avg_scores']['technical_skills'],
    'is_technical': is_technical_major(c['major']),
    'raw_data': c  # Keep the full data for details view
} for c in candidates])

# Display progress with improved styling
progress = get_selection_progress(st.session_state.selected_candidates, 
                                st.session_state.waitlist_candidates)

st.markdown("### 📊 Selection Progress")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(
        "Selected Candidates",
        progress['total_selected'],
        "100",
        delta_color="normal"
    )
with col2:
    st.metric(
        "Waitlist",
        progress['total_waitlist'],
        "50",
        delta_color="normal"
    )
with col3:
    st.metric(
        "Technical Ratio",
        f"{progress['technical_ratio']:.1%}",
        "70%",
        delta_color="normal"
    )
with col4:
    st.metric(
        "Non-Technical Ratio",
        f"{progress['non_technical_ratio']:.1%}",
        "30%",
        delta_color="normal"
    )

# University distribution with improved styling
st.markdown("### 🏫 University Distribution")
university_counts = progress['universities']
university_df = pd.DataFrame({
    'University': [shorten_university_name(uni) for uni in university_counts.keys()],
    'Count': list(university_counts.values())
})
st.bar_chart(university_df.set_index('University'))

# Interactive table with filtering
st.markdown("### 👥 Candidates")
st.markdown("""
    <div style='margin-bottom: 1rem;'>
        Use the interactive table below to filter and sort candidates. You can:
        <ul>
            <li>Click column headers to sort</li>
            <li>Use the search box to filter by any field</li>
            <li>Click on a row to view candidate details</li>
        </ul>
    </div>
""", unsafe_allow_html=True)

# Prepare the display dataframe (without raw_data)
display_df = df.drop('raw_data', axis=1).copy()
display_df['overall_score'] = display_df['overall_score'].apply(format_score)
display_df['technical_score'] = display_df['technical_score'].apply(format_score)

# Add action buttons to the dataframe
def get_action_buttons(row):
    candidate = df[df['id'] == row['id']]['raw_data'].iloc[0]
    if candidate in st.session_state.selected_candidates:
        return "✅ Selected"
    elif candidate in st.session_state.waitlist_candidates:
        return "⏳ Waitlisted"
    return "👀 View"

display_df['status'] = display_df.apply(get_action_buttons, axis=1)

# Display the interactive table
edited_df = st.data_editor(
    display_df,
    column_config={
        "id": st.column_config.NumberColumn("ID", width=50),
        "name": st.column_config.TextColumn("Name", width=200),
        "overall_score": st.column_config.TextColumn("Overall Score", width=100),
        "technical_score": st.column_config.TextColumn("Technical Score", width=100),
        "university": st.column_config.TextColumn("University", width=100),
        "major": st.column_config.TextColumn("Major", width=200),
        "year": st.column_config.NumberColumn("Year", width=80),
        "is_technical": st.column_config.CheckboxColumn("Technical Major", width=100),
        "status": st.column_config.TextColumn("Status", width=100),
    },
    hide_index=True,
    use_container_width=True,
    height=400,
    num_rows="fixed",
    disabled=True,
    key="candidate_table"
)

# Add a selectbox for candidate selection
selected_candidate_id = st.selectbox(
    "Select a candidate to view details:",
    options=display_df['id'].tolist(),
    format_func=lambda x: f"{x} - {display_df[display_df['id'] == x]['name'].iloc[0]} - {display_df[display_df['id'] == x]['university'].iloc[0]}",
    key="candidate_selector"
)

if selected_candidate_id:
    selected_row = display_df[display_df['id'] == selected_candidate_id].iloc[0]
    candidate = df[df['id'] == selected_row['id']]['raw_data'].iloc[0]
    
    # Display candidate details
    st.markdown("### 📋 Candidate Details")
    with st.container():
        st.markdown(f"""
            <div class='candidate-card'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <h3 style='margin: 0;'>{selected_row['name']}</h3>
                    <span style='color: {get_score_color(float(selected_row['overall_score']))}; font-weight: bold;'>
                        Score: {selected_row['overall_score']}
                    </span>
                </div>
                <p style='margin: 0.5rem 0;'>{selected_row['university']} • {selected_row['major']} • Year {selected_row['year']}</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Basic info
        st.markdown("#### 📝 Basic Information")
        st.markdown(f"**📧 Email:** {selected_row['email']}")
        st.markdown(f"**🎓 Major:** {selected_row['major']}")
        st.markdown(f"**📅 Year:** {selected_row['year']}")
        
        # Scores
        st.markdown("#### 📊 Scores")
        scores_col1, scores_col2 = st.columns(2)
        
        with scores_col1:
            st.markdown("##### 👥 Human Review")
            for category, score in candidate['avg_scores'].items():
                if category != 'overall':
                    st.markdown(f"- **{category.replace('_', ' ').title()}:** {format_score(score)}")
        
        with scores_col2:
            if candidate.get('ai_scores'):
                st.markdown("##### 🤖 AI Scores")
                for key, value in candidate['ai_scores'].items():
                    if key not in ['record_id', 'id', 'candidate_id', 'resume_id'] and isinstance(value, (int, float)):
                        st.markdown(f"- **{key.replace('_', ' ').title()}:** {format_score(value)}")
        
        # Reviews
        if candidate.get('reviews'):
            st.markdown("#### 📝 Reviews")
            
            cols = st.columns(len(candidate['reviews']))
            for i, review in enumerate(candidate['reviews']):
                # Create a unique key for this review's show name button
                show_name_key = f"show_name_{candidate['id']}_{i}"
                
                # Initialize the show name state if not exists
                if show_name_key not in st.session_state:
                    st.session_state[show_name_key] = False
                
                
                with cols[i]:
                    if st.button("👁️ Show Name", key=f"btn_{show_name_key}"):
                        st.session_state[show_name_key] = not st.session_state[show_name_key]
                
                    reviewer_name = review['username'] if st.session_state[show_name_key] else f"Reviewer {i+1}"
                    
                    st.markdown(f"""
                    <div>
                        <h4>Review by {reviewer_name}</h4>
                        <p>{review['timestamp']}</p>
                        <div>
                            <strong>Scores:</strong><br>
                            {"<br>".join([f"- {category.replace('_', ' ').title()}: {format_score(score)}" for category, score in review['scores'].items() if category != 'overall'])}
                        </div>
                        {f"<div style='margin-top: 0.5rem;'><strong>Notes:</strong><br>{review['notes']}</div>" if review.get('notes') else ""}
                    </div>

                    <style>
                    .review-box {{
                        background-color: #f8f9fa;
                        color: #000;
                        padding: 1rem;
                        border-radius: 0.5rem;
                        margin-bottom: 1rem;
                        border: 1px solid #ddd;
                    }}
                    .review-box h4 {{
                        margin: 0 0 0.5rem 0;
                        font-size: 1.2rem;
                    }}
                    .review-box p {{
                        margin: 0 0 0.5rem 0;
                        color: #666;
                        font-size: 0.9rem;
                    }}
                    /* Dark mode overrides */
                    [data-theme="dark"] .review-box {{
                        background-color: #222 !important;
                        color: #eee !important;
                        border-color: #444 !important;
                    }}
                    [data-theme="dark"] .review-box p {{
                        color: #aaa !important;
                    }}
                    </style>
                """, unsafe_allow_html=True)


        
        # Resume section at the bottom
        st.markdown("#### 📄 Resume")
        pdf_bytes, base64_pdf = get_resume_pdf(str(selected_row['id']))
        if pdf_bytes:
            # Create a BytesIO object for the PDFViewer
            pdf_file = io.BytesIO(pdf_bytes)
            PDFViewer.display_pdf_native(pdf_file)
        else:
            st.warning("No resume available for this candidate.")
        
        # Action buttons at the bottom
        st.markdown("### 🎯 Actions")
        col1, col2 = st.columns(2)
        with col1:
            if candidate not in st.session_state.selected_candidates:
                if st.button("✅ Approve", key=f"approve_{candidate['id']}", use_container_width=True):
                    st.session_state.selected_candidates.append(candidate)
                    save_selection_data()
                    st.experimental_rerun()

            elif candidate in st.session_state.selected_candidates:
                if st.button("❌ Remove from Selected", key=f"remove_selected_{candidate['id']}", use_container_width=True):
                    st.session_state.selected_candidates.remove(candidate)
                    save_selection_data()
                    st.experimental_rerun()
        with col2:
            if candidate not in st.session_state.waitlist_candidates:
                if st.button("⏳ Waitlist", key=f"waitlist_{candidate['id']}", use_container_width=True):
                    st.session_state.waitlist_candidates.append(candidate)
                    save_selection_data()
                    st.experimental_rerun()
            
            elif candidate in st.session_state.waitlist_candidates:
                if st.button("❌ Remove from Waitlist", key=f"remove_waitlist_{candidate['id']}", use_container_width=True):
                    st.session_state.waitlist_candidates.remove(candidate)
                    save_selection_data()
                    st.experimental_rerun()

# Selected candidates with improved styling
if st.session_state.selected_candidates:
    st.markdown("### ✅ Selected Candidates")
    
    # Create a DataFrame for selected candidates
    selected_df = pd.DataFrame([{
        'id': c['id'],
        'name': c['name'],
        'university': c['university'],
        'major': c['major'],
        'year': c['year'],
        'overall_score': format_score(c['avg_scores']['overall']),
        'technical_score': format_score(c['avg_scores']['technical_skills']),
        'is_technical': is_technical_major(c['major']),
        'ai_score': format_score(c['ai_scores']['final_score']) if c['ai_scores'] else 'N/A',
        'ai_technical': format_score(c['ai_scores']['technical_experience']) if c['ai_scores'] else 'N/A'
    } for c in st.session_state.selected_candidates])
    
    # Display the table with a remove button for each row
    for _, row in selected_df.iterrows():
        col1, col2 = st.columns([0.9, 0.1])
        with col1:
            st.markdown(f"""
                <div style='padding: 0.5rem; border-radius: 0.5rem; background-color: #f8f9fa; margin-bottom: 0.5rem;'>
                    <strong>ID: {row['id']} - {row['name']}</strong> • {row['university']} • {row['major']} • Year {row['year']}<br>
                    Human: {row['overall_score']} • Technical: {row['technical_score']}<br>
                    AI: {row['ai_score']} • AI Technical: {row['ai_technical']}
                </div>
            """, unsafe_allow_html=True)
        with col2:
            if st.button("❌", key=f"remove_selected_list_{row['id']}", use_container_width=True):
                st.session_state.selected_candidates = [c for c in st.session_state.selected_candidates if c['id'] != row['id']]
                save_selection_data()
                st.experimental_rerun()

# Waitlist with improved styling
if st.session_state.waitlist_candidates:
    st.markdown("### ⏳ Waitlist")
    
    # Create a DataFrame for waitlisted candidates
    waitlist_df = pd.DataFrame([{
        'id': c['id'],
        'name': c['name'],
        'university': c['university'],
        'major': c['major'],
        'year': c['year'],
        'overall_score': format_score(c['avg_scores']['overall']),
        'technical_score': format_score(c['avg_scores']['technical_skills']),
        'is_technical': is_technical_major(c['major']),
        'ai_score': format_score(c['ai_scores']['final_score']) if c['ai_scores'] else 'N/A',
        'ai_technical': format_score(c['ai_scores']['technical_experience']) if c['ai_scores'] else 'N/A'
    } for c in st.session_state.waitlist_candidates])
    
    # Display the table with a remove button for each row
    for _, row in waitlist_df.iterrows():
        col1, col2 = st.columns([0.9, 0.1])
        with col1:
            st.markdown(f"""
                <div style='padding: 0.5rem; border-radius: 0.5rem; background-color: #f8f9fa; margin-bottom: 0.5rem;'>
                    <strong>ID: {row['id']} - {row['name']}</strong> • {row['university']} • {row['major']} • Year {row['year']}<br>
                    Human: {row['overall_score']} • Technical: {row['technical_score']}<br>
                    AI: {row['ai_score']} • AI Technical: {row['ai_technical']}
                </div>
            """, unsafe_allow_html=True)
        with col2:
            if st.button("❌", key=f"remove_waitlist_list_{row['id']}", use_container_width=True):
                st.session_state.waitlist_candidates = [c for c in st.session_state.waitlist_candidates if c['id'] != row['id']]
                save_selection_data()
                st.experimental_rerun() 