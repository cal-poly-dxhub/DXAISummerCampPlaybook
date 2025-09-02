import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

def analyze_reviews():
    reviews_dir = Path("test_reviews")
    if not reviews_dir.exists():
        print("Error: test_reviews directory not found")
        return

    # Initialize counters
    candidate_reviews = defaultdict(int)
    reviewer_reviews = defaultdict(int)
    total_reviews = 0

    # Process each review file
    for file in reviews_dir.glob('*.json'):
        try:
            with open(file, 'r') as f:
                review = json.load(f)
                candidate_id = review.get('candidate_id')
                reviewer = review.get('username')
                
                if candidate_id and reviewer:
                    candidate_reviews[candidate_id] += 1
                    reviewer_reviews[reviewer] += 1
                    total_reviews += 1
        except Exception as e:
            print(f"Error processing {file}: {e}")

    # Print summary
    print("\n=== Review Analysis Summary ===")
    print(f"Total number of reviews: {total_reviews}")
    print(f"Number of unique candidates: {len(candidate_reviews)}")
    print(f"Number of unique reviewers: {len(reviewer_reviews)}")

    print("\n=== Reviews per Candidate ===")
    # Sort candidates by ID number
    for candidate_id in sorted(candidate_reviews.keys(), key=lambda x: int(x)):
        print(f"Candidate {candidate_id}: {candidate_reviews[candidate_id]} reviews")

    print("\n=== Reviews per Reviewer ===")
    for reviewer, count in sorted(reviewer_reviews.items(), key=lambda x: x[1], reverse=True):
        print(f"{reviewer}: {count} reviews")

if __name__ == "__main__":
    analyze_reviews() 