import streamlit as st
import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from collections import defaultdict

def format_min_sec(value):
    if pd.isna(value) or value == 0:
        return "0m 0s"
    minutes = int(value)
    seconds = int(round((value - minutes) * 60))
    return f"{minutes}m {seconds}s"

class ReviewerAnalytics:
    def __init__(self):
        self.reviews_dir = "test_reviews"
        self.reviews_data = self._load_reviews()

    def _load_reviews(self):
        reviews = []
        review_counts = defaultdict(int)
        review_durations = defaultdict(list)
        
        # Process all review files
        for file in Path(self.reviews_dir).glob('*.json'):
            try:
                username = file.stem.split('_')[0]
                review_counts[username] += 1
                
                with open(file, 'r') as f:
                    review = json.load(f)
                    # Calculate review duration in minutes
                    start_time = datetime.fromisoformat(review.get('review_start_time', ''))
                    end_time = datetime.fromisoformat(review.get('review_end_time', ''))
                    duration = (end_time - start_time).total_seconds() / 60
                    review_durations[username].append(duration)
                    
                    # Add duration to review data
                    review['duration'] = duration
                    reviews.append(review)
            except Exception as e:
                print(f"Error loading review {file}: {e}")
        
        # Store the actual review counts and durations
        self.review_counts = dict(review_counts)
        self.review_durations = dict(review_durations)
        return reviews

    def _remove_outliers(self, durations, threshold=1.5):
        """Remove outliers using IQR method"""
        if len(durations) < 4:  # Need at least 4 points for meaningful IQR
            return durations
            
        q1 = np.percentile(durations, 25)
        q3 = np.percentile(durations, 75)
        iqr = q3 - q1
        lower_bound = q1 - threshold * iqr
        upper_bound = q3 + threshold * iqr
        
        return [d for d in durations if lower_bound <= d <= upper_bound]

    def get_reviewer_stats(self):
        df = pd.DataFrame(self.reviews_data)
        if df.empty:
            return pd.DataFrame()

        # Create stats DataFrame with actual file counts
        reviewer_stats = pd.DataFrame({
            'total_reviews': pd.Series(self.review_counts),
            'avg_score': df.groupby('username')['total_score'].mean().round(2)
        })
        
        # Calculate time statistics with outlier removal
        for username in reviewer_stats.index:
            durations = self.review_durations[username]
            clean_durations = self._remove_outliers(durations)
            
            if clean_durations:
                reviewer_stats.loc[username, 'avg_time'] = np.mean(clean_durations).round(2)
                reviewer_stats.loc[username, 'median_time'] = np.median(clean_durations).round(2)
                reviewer_stats.loc[username, 'min_time'] = np.min(clean_durations).round(2)
                reviewer_stats.loc[username, 'max_time'] = np.max(clean_durations).round(2)
                reviewer_stats.loc[username, 'outliers_removed'] = len(durations) - len(clean_durations)
            else:
                reviewer_stats.loc[username, 'avg_time'] = 0
                reviewer_stats.loc[username, 'median_time'] = 0
                reviewer_stats.loc[username, 'min_time'] = 0
                reviewer_stats.loc[username, 'max_time'] = 0
                reviewer_stats.loc[username, 'outliers_removed'] = 0
        
        return reviewer_stats

    def get_category_distribution(self, username):
        df = pd.DataFrame(self.reviews_data)
        if df.empty:
            return pd.DataFrame()
        
        # Filter for specific reviewer
        reviewer_df = df[df['username'] == username]
        
        # Get category scores
        category_scores = []
        for _, row in reviewer_df.iterrows():
            scores = row['scores']
            for category, score in scores.items():
                category_scores.append({
                    'category': category,
                    'score': score
                })
        
        return pd.DataFrame(category_scores)

def main():
    st.set_page_config(page_title="Reviewer Analytics Dashboard", layout="wide")
    st.title("Reviewer Analytics Dashboard")

    analytics = ReviewerAnalytics()
    reviewer_stats = analytics.get_reviewer_stats()

    if reviewer_stats.empty:
        st.warning("No review data available.")
        return

    # Overall Statistics
    st.header("Overall Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Reviewers", len(reviewer_stats))
    with col2:
        total_reviews = reviewer_stats['total_reviews'].sum()
        st.metric("Total Reviews", total_reviews)
    with col3:
        st.metric("Average Score", f"{reviewer_stats['avg_score'].mean():.2f}")
    with col4:
        st.metric("Average Time per Review", format_min_sec(reviewer_stats['avg_time'].mean()))

    # Reviewer Selection
    st.header("Reviewer Details")
    selected_reviewer = st.selectbox(
        "Select Reviewer",
        options=reviewer_stats.index.tolist()
    )

    # Selected Reviewer Statistics
    reviewer_data = reviewer_stats.loc[selected_reviewer]
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Reviews", reviewer_data['total_reviews'])
    with col2:
        st.metric("Average Score", f"{reviewer_data['avg_score']:.2f}")
    with col3:
        st.metric("Average Time", format_min_sec(reviewer_data['avg_time']))
    with col4:
        st.metric("Median Time", format_min_sec(reviewer_data['median_time']))

    # Time Distribution
    st.subheader("Time Distribution")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Minimum Time", format_min_sec(reviewer_data['min_time']))
    with col2:
        st.metric("Maximum Time", format_min_sec(reviewer_data['max_time']))
    with col3:
        st.metric("Outliers Removed", reviewer_data['outliers_removed'])

    # Category Distribution
    st.subheader("Category Score Distribution")
    category_df = analytics.get_category_distribution(selected_reviewer)
    
    if not category_df.empty:
        fig = px.box(category_df, x='category', y='score',
                    title=f"Score Distribution by Category for {selected_reviewer}")
        st.plotly_chart(fig, use_container_width=True)

    # All Reviewers Table
    st.header("All Reviewers")
    st.dataframe(reviewer_stats.style.format({
        'avg_score': '{:.2f}',
        'avg_time': format_min_sec,
        'median_time': format_min_sec,
        'min_time': format_min_sec,
        'max_time': format_min_sec
    }))

if __name__ == "__main__":
    main() 