import json
import os
from datetime import datetime
import uuid
from pathlib import Path
import boto3
import io
from config.config import CONFIG
from utils.logger import LoggerManager

class StorageManager:
    def __init__(self):
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=CONFIG['AWS_ACCESS_KEY'],
            aws_secret_access_key=CONFIG['AWS_SECRET_KEY'],
            region_name=CONFIG['AWS_REGION']
        )

    def get_resume_content(self, user_id):
        """Retrieve resume and supplemental content from S3"""
        try:
            # List all objects in user's folder
            response = self.s3.list_objects_v2(
                Bucket=CONFIG['BUCKET_NAME'],
                Prefix=f"{user_id}/"
            )

            content_package = {}
            
            # Process each file in the folder
            for obj in response.get('Contents', []):
                key = obj['Key']
                if key.endswith('.pdf'):
                    if key.endswith('file_0.pdf'):
                        main_resume = self.s3.get_object(Bucket=CONFIG['BUCKET_NAME'], Key=key)
                        content_package['resume'] = io.BytesIO(main_resume['Body'].read())
                    else:
                        # Any other PDF is supplemental
                        supplemental = self.s3.get_object(Bucket=CONFIG['BUCKET_NAME'], Key=key)
                        content_package['supplemental'] = io.BytesIO(supplemental['Body'].read())
                elif key.endswith('metadata.json'):
                    metadata = self.s3.get_object(Bucket=CONFIG['BUCKET_NAME'], Key=key)
                    content_package['metadata'] = json.loads(metadata['Body'].read())
                elif key.endswith('general.json'):
                    general = self.s3.get_object(Bucket=CONFIG['BUCKET_NAME'], Key=key)
                    content_package['general'] = json.loads(general['Body'].read())

            if 'resume' not in content_package:
                raise ValueError(f"No file_0.pdf found for user {user_id}")

            return content_package

        except Exception as e:
            LoggerManager.log_error(f"Error retrieving content for user {user_id}: {str(e)}")
            return None

    def get_available_candidates(self, reviewer_username):
        """Get list of user IDs needing review"""
        try:
            # List all folders (user IDs) in the bucket
            response = self.s3.list_objects_v2(
                Bucket=CONFIG['BUCKET_NAME'],
                Delimiter='/'
            )
            
            # Extract user IDs from prefixes
            all_users = [
                prefix.strip('/') 
                for prefix in [p.get('Prefix') for p in response.get('CommonPrefixes', [])]
            ]
            
            # Filter users based on review count and reviewer history
            available_users = []
            for user_id in all_users:
                review_count = self._get_review_count(user_id)
                if (review_count < CONFIG['REQUIRED_REVIEWS'] and 
                    not self._has_user_reviewed(reviewer_username, user_id)):
                    available_users.append(user_id)
            
            return available_users
            
        except Exception as e:
            LoggerManager.log_error(f"Error getting available users: {str(e)}")
            return []

    def save_review(self, username, user_id, scores, notes):
        """Save a review with backup and verification"""
        try:
            review_data = {
                'review_id': str(uuid.uuid4()),
                'username': username,
                'user_id': user_id,
                'scores': scores,
                'notes': notes,
                'timestamp': datetime.utcnow().isoformat(),
                'version': '1.0'
            }
            
            # Create paths
            filename = f"{review_data['review_id']}.json"
            filepath = Path(CONFIG['REVIEWS_DIR']) / filename
            temp_filepath = filepath.with_suffix('.tmp')
            
            # Write to temporary file
            with open(temp_filepath, 'w') as f:
                json.dump(review_data, f, indent=2)
            
            # Verify temporary file
            with open(temp_filepath, 'r') as f:
                verification_data = json.load(f)
                if verification_data != review_data:
                    raise ValueError("Data verification failed")
            
            # Rename to final file
            temp_filepath.rename(filepath)
            
            LoggerManager.log_review_submission(username, user_id)
            return True
            
        except Exception as e:
            LoggerManager.log_error(f"Error saving review: {str(e)}", 
                                  {'username': username, 'user_id': user_id})
            if temp_filepath.exists():
                temp_filepath.unlink()
            return False

    def _get_review_count(self, user_id):
        """Get number of reviews for a user"""
        review_files = Path(CONFIG['REVIEWS_DIR']).glob('*.json')
        count = 0
        for review_file in review_files:
            with open(review_file) as f:
                review = json.load(f)
                if review['user_id'] == user_id:
                    count += 1
        return count

    def _has_user_reviewed(self, username, user_id):
        """Check if user has already reviewed this candidate"""
        review_files = Path(CONFIG['REVIEWS_DIR']).glob('*.json')
        for review_file in review_files:
            with open(review_file) as f:
                review = json.load(f)
                if (review['user_id'] == user_id and 
                    review['username'] == username):
                    return True
        return False

    def backup_form_data(self, username, user_id, scores, notes):
        """Backup form data in case of submission failure"""
        try:
            backup_data = {
                'username': username,
                'user_id': user_id,
                'scores': scores,
                'notes': notes,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            filename = f"{username}_{user_id}.json"
            filepath = Path(CONFIG['FORM_BACKUPS_DIR']) / filename
            
            with open(filepath, 'w') as f:
                json.dump(backup_data, f, indent=2)
                
            return True
            
        except Exception as e:
            LoggerManager.log_error(f"Error backing up form data: {str(e)}")
            return False

    def get_form_backup(self, username, user_id):
        """Retrieve backed up form data"""
        try:
            filename = f"{username}_{user_id}.json"
            filepath = Path(CONFIG['FORM_BACKUPS_DIR']) / filename
            
            if filepath.exists():
                with open(filepath) as f:
                    return json.load(f)
            return None
            
        except Exception as e:
            LoggerManager.log_error(f"Error retrieving form backup: {str(e)}")
            return None

    def clear_form_backup(self, username, user_id):
        """Clear backup after successful submission"""
        try:
            filename = f"{username}_{user_id}.json"
            filepath = Path(CONFIG['FORM_BACKUPS_DIR']) / filename
            
            if filepath.exists():
                filepath.unlink()
                
        except Exception as e:
            LoggerManager.log_error(f"Error clearing form backup: {str(e)}")