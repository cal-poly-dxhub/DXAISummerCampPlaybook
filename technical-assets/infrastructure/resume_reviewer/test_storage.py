import json
import os
from pathlib import Path
from datetime import datetime, timedelta
import io
import random
from config.config import CONFIG
from collections import defaultdict

class TestStorageManager:
    def __init__(self):
        self.base_dir = "test_data/rows"
        self.reviews_dir = "test_reviews"
        self.locks_dir = "review_locks"
        os.makedirs(self.reviews_dir, exist_ok=True)
        os.makedirs(self.locks_dir, exist_ok=True)
        self._review_cache = None
        self._load_review_cache()

    def _load_review_cache(self):
        """Load all reviews into memory for quick lookups"""
        self._review_cache = {
            'by_user_candidate': set(),  # Set of (username, candidate_id) tuples
            'by_candidate': {}  # Dict of candidate_id -> count
        }
        
        for file in Path(self.reviews_dir).glob('*.json'):
            try:
                with open(file, 'r') as f:
                    review = json.load(f)
                    username = review.get('username')
                    candidate_id = str(review.get('candidate_id', ''))
                    if username and candidate_id:
                        self._review_cache['by_user_candidate'].add((username, candidate_id))
                        self._review_cache['by_candidate'][candidate_id] = self._review_cache['by_candidate'].get(candidate_id, 0) + 1
            except Exception as e:
                print(f"Error loading review into cache: {e}")

    def get_resume_content(self, candidate_id):
        """Get resume content from local test directory"""
        try:
            candidate_dir = Path(self.base_dir) / str(candidate_id)
            content_package = {}

            # Get main resume (file_0.pdf)
            main_resume_path = candidate_dir / "file_0.pdf"
            if main_resume_path.exists():
                with open(main_resume_path, 'rb') as f:
                    content_package['resume'] = io.BytesIO(f.read())

            # Get supplemental PDFs
            i = 0
            while True:
                supp_path = candidate_dir / f"supplemental_file_{i}.pdf"
                if not supp_path.exists():
                    break
                with open(supp_path, 'rb') as f:
                    content_package[f'supplemental_file_{i}'] = io.BytesIO(f.read())
                i += 1

            # Get supplemental.json if it exists
            json_path = candidate_dir / "supplemental.json"
            if json_path.exists():
                with open(json_path, 'r') as f:
                    content_package['supplemental_json'] = f.read()

            return content_package

        except Exception as e:
            print(f"Error loading resume: {e}")
            return None

    def _get_lock_file(self, candidate_id):
        """Get path to lock file for a candidate"""
        return Path(self.locks_dir) / f"{candidate_id}.lock"

    def _cleanup_user_locks(self, username):
        """Clean up any locks belonging to the user"""
        try:
            for lock_file in Path(self.locks_dir).glob('*.lock'):
                try:
                    with open(lock_file, 'r') as f:
                        lock_data = json.load(f)
                        if lock_data.get('username') == username:
                            lock_file.unlink()
                except (json.JSONDecodeError, FileNotFoundError):
                    # If lock file is corrupted, remove it
                    lock_file.unlink()
        except Exception as e:
            print(f"Error cleaning up user locks: {e}")

    def _acquire_lock(self, candidate_id, username):
        """Try to acquire a lock for reviewing a candidate"""
        # First clean up any existing locks for this user
        self._cleanup_user_locks(username)
        
        lock_file = self._get_lock_file(candidate_id)
        try:
            # Check if already locked
            if lock_file.exists():
                try:
                    with open(lock_file, 'r') as f:
                        lock_data = json.load(f)
                        if lock_data.get('username') != username:
                            # If locked by different user, check if lock is stale
                            lock_time = datetime.fromisoformat(lock_data.get('timestamp', ''))
                            if datetime.now() - lock_time > timedelta(minutes=1):
                                lock_file.unlink()  # Remove stale lock
                            else:
                                return False
                except (json.JSONDecodeError, FileNotFoundError):
                    # If lock file is corrupted or missing, remove it
                    lock_file.unlink()

            # Create new lock
            lock_data = {
                'username': username,
                'timestamp': datetime.now().isoformat()
            }
            with open(lock_file, 'w') as f:
                json.dump(lock_data, f)
            return True
        except Exception as e:
            print(f"Error acquiring lock for candidate {candidate_id}: {e}")
            # If there's any error, try to clean up the lock file
            try:
                if lock_file.exists():
                    lock_file.unlink()
            except:
                pass
            return False

    def _release_lock(self, candidate_id):
        """Release the lock for a candidate"""
        try:
            lock_file = self._get_lock_file(candidate_id)
            if lock_file.exists():
                lock_file.unlink()
        except Exception as e:
            # Ignore errors for non-existent files
            if not isinstance(e, FileNotFoundError):
                print(f"Error releasing lock: {e}")

    def get_available_candidates(self, reviewer_username):
        """Get list of candidates needing review"""
        try:
            # Clean up any existing locks for this user first
            self._cleanup_user_locks(reviewer_username)
            
            # Get all candidate directories
            candidates = [
                d.name for d in Path(self.base_dir).iterdir() 
                if d.is_dir() and d.name.isdigit()
            ]
            print(f"Total candidates found: {len(candidates)}")
            
            # Filter based on review count only
            available = []
            for candidate in candidates:
                review_count = self._get_review_count(candidate)
                has_reviewed = self._has_user_reviewed(reviewer_username, candidate)
                print(f"Candidate {candidate}: reviews={review_count}, has_reviewed={has_reviewed}")
                
                if (review_count < CONFIG['REQUIRED_REVIEWS'] and 
                    not has_reviewed):
                    available.append(candidate)
            
            print(f"Final available candidates: {len(available)}")
            return available

        except Exception as e:
            print(f"Error getting candidates: {e}")
            return []

    def reserve_candidate(self, reviewer_username, candidate_id):
        """Try to reserve a candidate for review"""
        try:
            # First check if we can review this candidate
            review_count = self._get_review_count(candidate_id)
            has_reviewed = self._has_user_reviewed(reviewer_username, candidate_id)
            
            if review_count >= CONFIG['REQUIRED_REVIEWS'] or has_reviewed:
                return False
                
            # Try to acquire lock
            if self._acquire_lock(candidate_id, reviewer_username):
                return True
            return False
        except Exception as e:
            print(f"Error reserving candidate {candidate_id}: {e}")
            return False

    def save_review(self, username, candidate_id, review_data):
        """Save review to local file"""
        try:
            # Reload cache to ensure we have latest data
            self._load_review_cache()
            
            # Final safety check for duplicates
            if self._has_user_reviewed(username, candidate_id):
                error_msg = f"You have already reviewed this resume. Please reload the page to get a new resume."
                print(f"Duplicate review prevented: {username} has already reviewed candidate {candidate_id}")
                return False, error_msg

            # Verify lock is still held
            if not self._acquire_lock(candidate_id, username):
                return False, "This resume is currently being reviewed by another user. Please reload the page to get a new resume."

            # Calculate average score
            scores = review_data['scores']
            total_score = sum(scores.values()) / len(scores)
            
            # Add total score, username, and candidate_id to review data
            review_data['total_score'] = round(total_score, 2)
            review_data['username'] = username
            review_data['candidate_id'] = str(candidate_id)
            
            review_id = f"{username}_{candidate_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            filepath = Path(self.reviews_dir) / f"{review_id}.json"
            
            with open(filepath, 'w') as f:
                json.dump(review_data, f, indent=2)
            
            # Update the review cache
            self._review_cache['by_user_candidate'].add((username, str(candidate_id)))
            self._review_cache['by_candidate'][str(candidate_id)] = self._review_cache['by_candidate'].get(str(candidate_id), 0) + 1
            
            # Release lock after successful save
            self._release_lock(candidate_id)
            return True, None

        except Exception as e:
            error_msg = "An error occurred while saving your review. Please try again."
            print(f"Error saving review: {e}")
            self._release_lock(candidate_id)  # Release lock on error
            return False, error_msg

    def _get_review_count(self, candidate_id):
        """Count existing reviews for a candidate using cache"""
        return self._review_cache['by_candidate'].get(str(candidate_id), 0)

    def _has_user_reviewed(self, username, candidate_id):
        """Check if user has already reviewed this candidate using cache"""
        return (username, str(candidate_id)) in self._review_cache['by_user_candidate']

    def get_reviewer_stats(self):
        """Get statistics for all reviewers"""
        reviewer_stats = {}
        for file in Path(self.reviews_dir).glob('*.json'):
            try:
                with open(file, 'r') as f:
                    review = json.load(f)
                    username = review.get('username', 'Unknown')
                    if username not in reviewer_stats:
                        reviewer_stats[username] = {
                            'total_reviews': 0,
                            'avg_score': 0,
                            'total_score': 0
                        }
                    reviewer_stats[username]['total_reviews'] += 1
                    reviewer_stats[username]['total_score'] += review.get('total_score', 0)
                    reviewer_stats[username]['avg_score'] = (
                        reviewer_stats[username]['total_score'] / 
                        reviewer_stats[username]['total_reviews']
                    )
            except Exception as e:
                print(f"Error processing review file {file}: {e}")
                continue
        return reviewer_stats

    def backup_form_data(self, username, candidate_id, form_data):
        """Backup form data in case of submission failure"""
        try:
            backup_dir = Path("form_backups")
            backup_dir.mkdir(exist_ok=True)
            
            filename = f"{username}_{candidate_id}_backup.json"
            filepath = backup_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(form_data, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error backing up form data: {e}")
            return False

    def get_review_progress(self):
        """Calculate accurate progress and reviews needed"""
        try:
            # Get all candidate directories
            all_candidates = [
                d.name for d in Path(self.base_dir).iterdir() 
                if d.is_dir() and d.name.isdigit()
            ]
            total_candidates = len(all_candidates)
            
            # Count reviews per candidate
            candidate_reviews = defaultdict(int)
            for file in Path(self.reviews_dir).glob('*.json'):
                try:
                    # Extract candidate_id from filename (more reliable than JSON content)
                    candidate_id = file.stem.split('_')[1]
                    candidate_reviews[candidate_id] += 1
                except:
                    continue
            
            # Calculate metrics
            resumes_with_2_reviews = sum(1 for count in candidate_reviews.values() if count >= 2)
            resumes_with_1_review = sum(1 for count in candidate_reviews.values() if count == 1)
            
            # Calculate progress percentage
            progress = (resumes_with_2_reviews + (resumes_with_1_review / 2)) / total_candidates
            
            # Calculate reviews still needed
            reviews_needed = (total_candidates * 2) - (resumes_with_2_reviews * 2 + resumes_with_1_review)
            
            return {
                'progress_percentage': progress * 100,
                'reviews_needed': reviews_needed,
                'total_candidates': total_candidates,
                'resumes_with_2_reviews': resumes_with_2_reviews,
                'resumes_with_1_review': resumes_with_1_review
            }
            
        except Exception as e:
            print(f"Error calculating review progress: {e}")
            return {
                'progress_percentage': 0,
                'reviews_needed': 0,
                'total_candidates': 0,
                'resumes_with_2_reviews': 0,
                'resumes_with_1_review': 0
            }