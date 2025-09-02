import json
from pathlib import Path
from datetime import datetime
from config.config import CONFIG
from utils.logger import LoggerManager

class DataConsistencyChecker:
    @staticmethod
    def verify_review_file(filepath):
        """Verify a single review file"""
        try:
            with open(filepath) as f:
                data = json.load(f)
                
                # Check required fields
                required_fields = [
                    'review_id', 'username', 'resume_id', 
                    'scores', 'notes', 'timestamp'
                ]
                if not all(field in data for field in required_fields):
                    return False
                
                # Verify scores
                if not all(category in data['scores'] 
                          for category in CONFIG['SCORING_CATEGORIES']):
                    return False
                
                # Verify score ranges
                if not all(0 <= score <= 100 
                          for score in data['scores'].values()):
                    return False
                
                # Verify timestamp format
                datetime.fromisoformat(data['timestamp'])
                
                return True
                
        except Exception:
            return False

    @staticmethod
    def check_all_reviews():
        """Check all review files for consistency"""
        issues = []
        review_path = Path(CONFIG['REVIEWS_DIR'])
        
        for filepath in review_path.glob('*.json'):
            if not DataConsistencyChecker.verify_review_file(filepath):
                issues.append(str(filepath))
        
        if issues:
            LoggerManager.log_error(
                "Consistency check found issues", 
                {'files': issues}
            )
        
        return issues

    @staticmethod
    def verify_review_counts():
        """Verify review counts per resume"""
        review_counts = {}
        review_path = Path(CONFIG['REVIEWS_DIR'])
        
        for filepath in review_path.glob('*.json'):
            try:
                with open(filepath) as f:
                    data = json.load(f)
                    resume_id = data['resume_id']
                    review_counts[resume_id] = review_counts.get(resume_id, 0) + 1
            except Exception as e:
                LoggerManager.log_error(f"Error checking review count: {str(e)}")
        
        issues = {
            resume_id: count 
            for resume_id, count in review_counts.items() 
            if count > CONFIG['REQUIRED_REVIEWS']
        }
        
        if issues:
            LoggerManager.log_error(
                "Found resumes with too many reviews", 
                {'issues': issues}
            )
        
        return issues

    @staticmethod
    def check_duplicate_reviews():
        """Check for duplicate reviews from same user"""
        reviews_by_user = {}
        review_path = Path(CONFIG['REVIEWS_DIR'])
        
        for filepath in review_path.glob('*.json'):
            try:
                with open(filepath) as f:
                    data = json.load(f)
                    key = (data['username'], data['resume_id'])
                    if key in reviews_by_user:
                        LoggerManager.log_error(
                            "Found duplicate review", 
                            {'user': data['username'], 'resume': data['resume_id']}
                        )
                        return True
                    reviews_by_user[key] = filepath
            except Exception as e:
                LoggerManager.log_error(f"Error checking duplicates: {str(e)}")
        
        return False