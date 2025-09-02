import os
import json
import pandas as pd
from typing import Dict, List, Tuple
from datetime import datetime
from university_mapping import get_university_name

def load_candidate_data(rows_dir: str = '../rows') -> List[Dict]:
    """Load candidate data from rows directory."""
    candidates = []
    print(f"\n=== Loading candidate data from {rows_dir} ===")
    
    if not os.path.exists(rows_dir):
        print(f"ERROR: Directory {rows_dir} does not exist!")
        return candidates
    
    dir_contents = os.listdir(rows_dir)
    print(f"Found {len(dir_contents)} items in directory")
    
    for dir_name in dir_contents:
        dir_path = os.path.join(rows_dir, dir_name)
        if os.path.isdir(dir_path):
            print(f"\nProcessing directory: {dir_name}")
            # Load general.json
            general_path = os.path.join(dir_path, 'general.json')
            metadata_path = os.path.join(dir_path, 'metadata.json')
            resume_path = os.path.join(dir_path, 'file_0.pdf')
            
            if os.path.exists(general_path) and os.path.exists(metadata_path):
                try:
                    with open(general_path, 'r') as f:
                        general_data = json.load(f)
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    
                    # Extract email and get university
                    email = general_data.get('YourUniversityEmailAddressedu', '')
                    university = get_university_name(email)
                    
                    # Get resume path if it exists
                    resume_link = resume_path if os.path.exists(resume_path) else ''
                    
                    candidate = {
                        'id': metadata.get('id'),
                        'name': f"{metadata.get('first', '')} {metadata.get('last', '')}",
                        'email': email,
                        'university': university,
                        'major': general_data.get('WhatAcademicMajorAreYouStudyingincludingAdditionalAcademicProgramsAsApplicable', ''),
                        'year': general_data.get('HowManyYearsOfInstructionHaveYouCompletedmayIncludeTransferCredit', ''),
                        'resume_link': resume_link,
                        'resume_id': metadata.get('resume_id', ''),
                        'resume_name': metadata.get('resume_name', '')
                    }
                    print(f"Loaded candidate: {candidate['name']} (ID: {candidate['id']})")
                    print(f"Resume path: {resume_link}")
                    candidates.append(candidate)
                except Exception as e:
                    print(f"Error loading data for directory {dir_name}: {e}")
            else:
                print(f"Missing required files in {dir_name}")
    
    print(f"\nTotal candidates loaded: {len(candidates)}")
    return candidates

def load_review_data(reviews_dir: str = '../test_reviews') -> Dict[str, List[Dict]]:
    """Load review data from test_reviews directory."""
    reviews_by_candidate = {}
    print(f"\n=== Loading review data from {reviews_dir} ===")
    
    if not os.path.exists(reviews_dir):
        print(f"ERROR: Directory {reviews_dir} does not exist!")
        return reviews_by_candidate
    
    review_files = [f for f in os.listdir(reviews_dir) if f.endswith('.json')]
    print(f"Found {len(review_files)} review files")
    
    for filename in review_files:
        try:
            with open(os.path.join(reviews_dir, filename), 'r') as f:
                review_data = json.load(f)
                
            candidate_id = review_data.get('candidate_id')
            if candidate_id:
                if candidate_id not in reviews_by_candidate:
                    reviews_by_candidate[candidate_id] = []
                
                # Handle both score formats
                scores = review_data.get('scores', {})
                if isinstance(scores, dict):
                    # Convert score keys to lowercase and map to our format
                    score_mapping = {
                        'collaboration': ['collaboration', 'Collaboration'],
                        'initiative': ['initiative', 'Initiative'],
                        'creativity': ['creativity', 'Creativity'],
                        'communication': ['communication', 'Communication'],
                        'critical_thinking': ['critical_thinking', 'Problem Decomposition'],
                        'technical_skills': ['technical_skills', 'Technical Experience'],
                        'growth_mindset': ['growth_mindset', 'Growth Mindset']
                    }
                    
                    mapped_scores = {}
                    for our_key, possible_keys in score_mapping.items():
                        for key in possible_keys:
                            if key in scores:
                                mapped_scores[our_key] = scores[key]
                                break
                        if our_key not in mapped_scores:
                            mapped_scores[our_key] = 0
                    
                    # Calculate overall score as average of all scores
                    valid_scores = [s for s in mapped_scores.values() if isinstance(s, (int, float))]
                    overall_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0
                    mapped_scores['overall'] = overall_score
                else:
                    mapped_scores = {
                        'collaboration': 0,
                        'initiative': 0,
                        'creativity': 0,
                        'communication': 0,
                        'critical_thinking': 0,
                        'technical_skills': 0,
                        'growth_mindset': 0,
                        'overall': 0
                    }
                
                review = {
                    'username': review_data.get('username', ''),
                    'timestamp': review_data.get('review_start_time', ''),
                    'scores': mapped_scores,
                    'notes': review_data.get('notes', ''),
                    'total_score': review_data.get('total_score', 0)
                }
                print(f"Loaded review for candidate {candidate_id} from {filename}")
                print(f"Review scores: {review['scores']}")
                reviews_by_candidate[candidate_id].append(review)
            else:
                print(f"Warning: No candidate_id found in {filename}")
        except Exception as e:
            print(f"Error loading review {filename}: {e}")
    
    print(f"\nTotal candidates with reviews: {len(reviews_by_candidate)}")
    return reviews_by_candidate

def load_ai_scores(csv_path: str = '../resume_scores_final.csv') -> pd.DataFrame:
    """Load AI scores from CSV file."""
    print(f"\n=== Loading AI scores from {csv_path} ===")
    try:
        if not os.path.exists(csv_path):
            print(f"ERROR: AI scores file {csv_path} does not exist!")
            return pd.DataFrame()
            
        df = pd.read_csv(csv_path)
        print(f"Loaded AI scores with {len(df)} rows and columns: {df.columns.tolist()}")
        return df
    except Exception as e:
        print(f"Error loading AI scores: {e}")
        return pd.DataFrame()

def combine_candidate_data(candidates: List[Dict], 
                         reviews: Dict[str, List[Dict]], 
                         ai_scores: pd.DataFrame) -> List[Dict]:
    """Combine all candidate data into a unified structure."""
    print("\n=== Combining candidate data ===")
    combined_data = []
    
    print(f"Processing {len(candidates)} candidates")
    print(f"Found reviews for {len(reviews)} candidates")
    print(f"AI scores shape: {ai_scores.shape if not ai_scores.empty else 'Empty'}")
    
    for candidate in candidates:
        candidate_id = candidate['id']
        print(f"\nProcessing candidate: {candidate['name']} (ID: {candidate_id})")
        
        # Get reviews for this candidate
        candidate_reviews = reviews.get(candidate_id, [])
        print(f"Found {len(candidate_reviews)} reviews for this candidate")
        
        # Calculate average scores from human reviews
        if candidate_reviews:
            print("Calculating average scores from reviews:")
            avg_scores = {
                'collaboration': sum(r['scores']['collaboration'] for r in candidate_reviews) / len(candidate_reviews),
                'initiative': sum(r['scores']['initiative'] for r in candidate_reviews) / len(candidate_reviews),
                'creativity': sum(r['scores']['creativity'] for r in candidate_reviews) / len(candidate_reviews),
                'communication': sum(r['scores']['communication'] for r in candidate_reviews) / len(candidate_reviews),
                'critical_thinking': sum(r['scores']['critical_thinking'] for r in candidate_reviews) / len(candidate_reviews),
                'technical_skills': sum(r['scores']['technical_skills'] for r in candidate_reviews) / len(candidate_reviews),
                'overall': sum(r['scores']['overall'] for r in candidate_reviews) / len(candidate_reviews)
            }
            print(f"Average scores: {avg_scores}")
        else:
            print("No reviews found, using default scores of 0")
            avg_scores = {k: 0 for k in ['collaboration', 'initiative', 'creativity', 
                                       'communication', 'critical_thinking', 
                                       'technical_skills', 'overall']}
        
        # Get AI scores if available
        ai_score_row = pd.DataFrame()
        if not ai_scores.empty:
            print("Looking for AI scores...")
            # Try different possible column names for record ID
            id_columns = ['record_id', 'id', 'candidate_id', 'resume_id']
            for col in id_columns:
                if col in ai_scores.columns:
                    print(f"Trying to match on column: {col}")
                    ai_score_row = ai_scores[ai_scores[col] == candidate_id]
                    if not ai_score_row.empty:
                        print(f"Found AI scores using column {col}")
                        break
            if ai_score_row.empty:
                print("No matching AI scores found")
        
        combined_candidate = {
            **candidate,
            'reviews': candidate_reviews,
            'avg_scores': avg_scores,
            'ai_scores': ai_score_row.to_dict('records')[0] if not ai_score_row.empty else {}
        }
        
        combined_data.append(combined_candidate)
    
    print(f"\nTotal combined candidates: {len(combined_data)}")
    return combined_data

def load_all_data() -> List[Dict]:
    """Load and combine all data sources."""
    print("\n=== Starting data loading process ===")
    candidates = load_candidate_data()
    reviews = load_review_data()
    ai_scores = load_ai_scores()
    
    return combine_candidate_data(candidates, reviews, ai_scores) 