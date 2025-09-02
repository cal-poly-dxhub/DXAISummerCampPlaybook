import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data'
REVIEWS_DIR = DATA_DIR / 'reviews'
BACKUPS_DIR = DATA_DIR / 'backups'
FORM_BACKUPS_DIR = DATA_DIR / 'form_backups'

# Create directories if they don't exist
for directory in [DATA_DIR, REVIEWS_DIR, BACKUPS_DIR, FORM_BACKUPS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

CONFIG = {
    # AWS Configuration
    'AWS_ACCESS_KEY': os.getenv('AWS_ACCESS_KEY', ''),
    'AWS_SECRET_KEY': os.getenv('AWS_SECRET_KEY', ''),
    'AWS_REGION': os.getenv('AWS_REGION', 'us-east-1'),
    'BUCKET_NAME': os.getenv('BUCKET_NAME', 'your-resume-bucket'),
    
    # Application Directories
    'DATA_DIR': str(DATA_DIR),
    'REVIEWS_DIR': str(REVIEWS_DIR),
    'BACKUPS_DIR': str(BACKUPS_DIR),
    'FORM_BACKUPS_DIR': str(FORM_BACKUPS_DIR),
    
    # Logging Configuration
    'LOG_FILE': str(BASE_DIR / 'resume_scorer.log'),
    'LOG_LEVEL': 'INFO',
    
    # Application Settings
    'REQUIRED_REVIEWS': 2,
    'MAX_RETRY_ATTEMPTS': 3,
    'BACKUP_INTERVAL': 3600,  # 1 hour in seconds
    
    # Scoring Categories
    'SCORING_CATEGORIES': [
        'Collaboration',
        'Initiative',
        'Creativity',
        'Communication',
        'Problem Decomposition',
        'Growth Mindset',
        'Technical Experience'
    ]
}

# Major Classifications
MAJOR_CATEGORIES = {
    'technical': [
        'Computer Science',
        'Data Science',
        'Computer Engineering',
        'Software Engineering'
    ],
    'semi_technical': [
        'Mechanical Engineering',
        'Civil Engineering',
        'Electrical Engineering',
        'Chemical Engineering',
        'Industrial Engineering'
    ],
    'non_technical': [
        'Business',
        'Psychology',
        'English',
        'Political Science',
        'Economics',
        'Communications',
        'Marketing'
    ]
}