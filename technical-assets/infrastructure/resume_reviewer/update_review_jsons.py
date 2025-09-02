import json
import shutil
from pathlib import Path
from datetime import datetime

def backup_reviews_folder():
    """Create a backup of the test_reviews folder"""
    reviews_dir = Path("test_reviews")
    if not reviews_dir.exists():
        print("Error: test_reviews directory not found")
        return False
        
    # Create backup directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path(f"test_reviews_backup_{timestamp}")
    
    try:
        # Copy entire directory
        shutil.copytree(reviews_dir, backup_dir)
        print(f"Successfully created backup at: {backup_dir}")
        return True
    except Exception as e:
        print(f"Error creating backup: {e}")
        return False

def update_json_files():
    """Update JSON files with candidate IDs from filenames"""
    reviews_dir = Path("test_reviews")
    if not reviews_dir.exists():
        print("Error: test_reviews directory not found")
        return
        
    updated_count = 0
    error_count = 0
    
    for file in reviews_dir.glob('*.json'):
        try:
            # Extract candidate_id from filename
            filename = file.stem  # Get filename without extension
            parts = filename.split('_')
            if len(parts) >= 2:
                candidate_id = parts[1]  # Get candidate_id from filename
                
                # Read existing JSON
                with open(file, 'r') as f:
                    review = json.load(f)
                
                # Check if candidate_id is missing or different
                if 'candidate_id' not in review or review['candidate_id'] != candidate_id:
                    review['candidate_id'] = candidate_id
                    
                    # Write updated JSON
                    with open(file, 'w') as f:
                        json.dump(review, f, indent=2)
                    updated_count += 1
                    print(f"Updated {file.name}")
                    
        except Exception as e:
            print(f"Error processing {file}: {e}")
            error_count += 1
    
    print(f"\nUpdate Summary:")
    print(f"Files updated: {updated_count}")
    print(f"Errors encountered: {error_count}")

def main():
    print("Starting review files update process...")
    
    # First create backup
    if backup_reviews_folder():
        print("\nBackup created successfully. Proceeding with updates...")
        update_json_files()
    else:
        print("\nBackup failed. Aborting updates to prevent data loss.")

if __name__ == "__main__":
    main() 