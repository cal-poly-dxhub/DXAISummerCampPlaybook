import os
import json
from utils.university_mapping import verify_university_mappings, print_verification_stats

def collect_emails_from_rows():
    """Collect all email addresses from the rows directory."""
    emails = []
    rows_dir = 'rows'
    
    for dir_name in os.listdir(rows_dir):
        dir_path = os.path.join(rows_dir, dir_name)
        if os.path.isdir(dir_path):
            general_json_path = os.path.join(dir_path, 'general.json')
            if os.path.exists(general_json_path):
                try:
                    with open(general_json_path, 'r') as f:
                        data = json.load(f)
                        email = data.get('YourUniversityEmailAddressedu', '')
                        if email:
                            emails.append(email)
                except Exception as e:
                    print(f"Error reading {general_json_path}: {e}")
    
    return emails

def main():
    # Collect all email addresses
    print("Collecting email addresses from rows directory...")
    emails = collect_emails_from_rows()
    total_emails = len(emails)
    print(f"Found {total_emails} email addresses")
    
    # Verify mappings
    university_counts, unrecognized_emails = verify_university_mappings(emails)
    
    # Print statistics
    print_verification_stats(university_counts, unrecognized_emails, total_emails)

if __name__ == "__main__":
    main() 