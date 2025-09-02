# analyze_scores.py
import json
import os
from collections import defaultdict
from datetime import datetime

def format_time(seconds):
    """Convert seconds to HH:MM:SS format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def calculate_duration(start_time_str, end_time_str):
    """Calculate duration between two timestamp strings"""
    try:
        start_time = datetime.fromisoformat(start_time_str)
        end_time = datetime.fromisoformat(end_time_str)
        return (end_time - start_time).total_seconds()
    except Exception as e:
        print(f"Error calculating duration: {e}")
        return 0

def analyze_reviews(reviews_dir='test_reviews'):
    """Analyze all reviews and calculate candidate averages"""
    
    # Store data for each candidate
    candidate_data = defaultdict(list)
    
    # Process each review file
    for filename in os.listdir(reviews_dir):
        if filename.endswith('.json'):
            # Split filename and handle timestamp parts safely
            parts = filename.replace('.json', '').split('_')
            reviewer = parts[0]
            candidate_id = parts[1]
            
            with open(os.path.join(reviews_dir, filename), 'r') as f:
                review = json.load(f)
                
                # Calculate review duration
                duration = calculate_duration(
                    review['review_start_time'],
                    review['review_end_time']
                )
                
                # Store review data
                review_data = {
                    'reviewer': reviewer,
                    'total_score': review['total_score'],
                    'individual_scores': review['scores'],
                    'notes': review.get('notes', ''),
                    'start_time': review['review_start_time'],
                    'end_time': review['review_end_time'],
                    'duration': duration,
                    'duration_formatted': format_time(duration)
                }
                
                candidate_data[candidate_id].append(review_data)

    # Calculate final results
    results = {}
    for candidate_id, reviews in candidate_data.items():
        # Calculate average of total scores
        total_scores = [r['total_score'] for r in reviews]
        average_score = sum(total_scores) / len(total_scores)
        
        # Calculate average duration
        durations = [r['duration'] for r in reviews]
        average_duration = sum(durations) / len(durations)
        
        results[candidate_id] = {
            'average_total_score': round(average_score, 2),
            'number_of_reviews': len(reviews),
            'average_duration_seconds': round(average_duration, 2),
            'average_duration_formatted': format_time(average_duration),
            'reviews': reviews
        }

    return results

def print_results(results):
    """Print results in an organized format"""
    print("\nCANDIDATE SCORING SUMMARY")
    print("=" * 70)
    
    # Sort candidates by average total score
    sorted_candidates = sorted(
        results.items(), 
        key=lambda x: x[1]['average_total_score'], 
        reverse=True
    )
    
    for candidate_id, data in sorted_candidates:
        print(f"\nCandidate {candidate_id}")
        print(f"Average Total Score: {data['average_total_score']}")
        print(f"Number of Reviews: {data['number_of_reviews']}")
        print(f"Average Review Duration: {data['average_duration_formatted']}")
        print("\nIndividual Reviews:")
        
        for review in data['reviews']:
            print(f"\n  Reviewer: {review['reviewer']}")
            print(f"  Total Score: {review['total_score']}")
            print(f"  Review Timing:")
            print(f"    Start Time: {review['start_time']}")
            print(f"    End Time:   {review['end_time']}")
            print(f"    Duration:   {review['duration_formatted']}")
            print("  Category Scores:")
            for category, score in review['individual_scores'].items():
                print(f"    {category}: {score}")
            if review['notes']:
                print(f"  Notes: {review['notes']}")
        print("-" * 70)

def main():
    # Analyze reviews
    results = analyze_reviews()
    
    # Print results
    print_results(results)
    
    # Save results to file
    with open('analysis_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary of top candidates
    print("\nTOP CANDIDATES BY AVERAGE SCORE")
    print("=" * 70)
    sorted_candidates = sorted(
        [(cid, data['average_total_score'], data['average_duration_formatted']) 
         for cid, data in results.items()],
        key=lambda x: x[1],
        reverse=True
    )
    for candidate_id, score, duration in sorted_candidates:
        print(f"Candidate {candidate_id}: Score {score} (Avg. Time: {duration})")

if __name__ == "__main__":
    main()