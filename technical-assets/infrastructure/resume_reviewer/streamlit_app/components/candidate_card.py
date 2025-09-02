import streamlit as st
from typing import Dict
from utils import format_score, get_score_color, is_technical_major

def display_candidate_card(candidate: Dict, show_details: bool = False):
    """Display a candidate card with their information and scores."""
    with st.container():
        # Basic info in columns
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            st.markdown(f"### {candidate['name']}")
            st.markdown(f"**ID:** {candidate['id']}")
            st.markdown(f"**Email:** {candidate['email']}")
            st.markdown(f"**University:** {candidate['university']}")
        
        with col2:
            st.markdown(f"**Major:** {candidate['major']}")
            st.markdown(f"**Year:** {candidate['year']}")
            if candidate.get('avg_scores'):
                st.markdown(f"**Avg Score:** {format_score(candidate['avg_scores']['overall'])}")
        
        with col3:
            if candidate.get('resume_link'):
                st.markdown(f"[View Resume]({candidate['resume_link']})")
        
        # Show details if requested
        if show_details:
            with st.expander("Review Details", expanded=True):
                # Human reviews
                if candidate.get('reviews'):
                    st.markdown("### Human Reviews")
                    for review in candidate['reviews']:
                        st.markdown(f"**Reviewer:** {review['username']}")
                        st.markdown(f"**Date:** {review['timestamp']}")
                        st.markdown("**Scores:**")
                        for category, score in review['scores'].items():
                            st.markdown(f"- {category.replace('_', ' ').title()}: {format_score(score)}")
                        if review.get('notes'):
                            st.markdown(f"**Notes:** {review['notes']}")
                        st.markdown("---")
                
                # AI scores
                if candidate.get('ai_scores'):
                    st.markdown("### AI Scores")
                    ai_scores = candidate['ai_scores']
                    for key, value in ai_scores.items():
                        if key != 'record_id' and isinstance(value, (int, float)):
                            st.markdown(f"**{key.replace('_', ' ').title()}:** {format_score(value)}")
        
        # Action buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("Approve", key=f"approve_{candidate['id']}"):
                st.session_state.selected_candidates.append(candidate)
                st.experimental_rerun()
        with col2:
            if st.button("Waitlist", key=f"waitlist_{candidate['id']}"):
                st.session_state.waitlist_candidates.append(candidate)
                st.experimental_rerun()
        with col3:
            if st.button("View Resume", key=f"resume_{candidate['id']}"):
                if candidate.get('resume_link'):
                    st.markdown(f"[Open Resume]({candidate['resume_link']})") 