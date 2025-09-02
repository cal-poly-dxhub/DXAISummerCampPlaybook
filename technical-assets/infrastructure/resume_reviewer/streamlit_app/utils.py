from typing import Dict, List, Tuple
import re

def is_technical_major(major: str) -> bool:
    """Determine if a major is technical based on keywords."""
    technical_keywords = [
        'computer', 'software', 'engineering', 'science', 'mathematics', 'physics',
        'chemistry', 'biology', 'data', 'information', 'technology', 'cyber',
        'electrical', 'mechanical', 'civil', 'industrial', 'systems', 'robotics',
        'artificial intelligence', 'machine learning', 'statistics', 'analytics'
    ]
    
    major_lower = major.lower()
    return any(keyword in major_lower for keyword in technical_keywords)

def format_score(score: float) -> str:
    """Format score to 2 decimal places."""
    return f"{score:.2f}"

def format_timestamp(timestamp: str) -> str:
    """Format timestamp to readable date."""
    try:
        # Assuming timestamp is in ISO format
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return timestamp

def get_score_color(score: float) -> str:
    """Get color for score based on value."""
    if score >= 4.5:
        return "green"
    elif score >= 3.5:
        return "blue"
    elif score >= 2.5:
        return "orange"
    else:
        return "red"

def calculate_university_stats(candidates: List[Dict]) -> Dict:
    """Calculate statistics about university distribution."""
    stats = {
        'total': len(candidates),
        'universities': {},
        'technical': 0,
        'non_technical': 0
    }
    
    for candidate in candidates:
        # Count by university
        university = candidate['university']
        stats['universities'][university] = stats['universities'].get(university, 0) + 1
        
        # Count technical vs non-technical
        if is_technical_major(candidate['major']):
            stats['technical'] += 1
        else:
            stats['non_technical'] += 1
    
    return stats

def get_selection_progress(selected_candidates: List[Dict], waitlist_candidates: List[Dict]) -> Dict:
    """Calculate progress towards selection goals."""
    total_selected = len(selected_candidates)
    total_waitlist = len(waitlist_candidates)
    
    # Count universities in selected candidates
    university_counts = {}
    for candidate in selected_candidates:
        university = candidate['university']
        university_counts[university] = university_counts.get(university, 0) + 1
    
    # Count technical vs non-technical in selected candidates
    technical_count = sum(1 for c in selected_candidates if is_technical_major(c['major']))
    non_technical_count = total_selected - technical_count
    
    return {
        'total_selected': total_selected,
        'total_waitlist': total_waitlist,
        'universities': university_counts,
        'technical_ratio': technical_count / total_selected if total_selected > 0 else 0,
        'non_technical_ratio': non_technical_count / total_selected if total_selected > 0 else 0
    } 