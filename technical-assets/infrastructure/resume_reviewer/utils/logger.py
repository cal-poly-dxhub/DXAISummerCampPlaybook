import logging
from datetime import datetime
from config.config import CONFIG

# Configure logging
logging.basicConfig(
    filename=CONFIG['LOG_FILE'],
    level=getattr(logging, CONFIG['LOG_LEVEL']),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('resume_scorer')

# Add console handler for development
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

class LoggerManager:
    @staticmethod
    def log_review_submission(username, resume_id, success=True):
        if success:
            logger.info(f"Review submitted - User: {username}, Resume: {resume_id}")
        else:
            logger.error(f"Review submission failed - User: {username}, Resume: {resume_id}")

    @staticmethod
    def log_backup_creation(backup_path, success=True):
        if success:
            logger.info(f"Backup created successfully at {backup_path}")
        else:
            logger.error(f"Backup creation failed for {backup_path}")

    @staticmethod
    def log_error(error_message, context=None):
        if context:
            logger.error(f"{error_message} - Context: {context}")
        else:
            logger.error(error_message)

    @staticmethod
    def log_user_action(username, action, details=None):
        message = f"User Action - {username}: {action}"
        if details:
            message += f" - Details: {details}"
        logger.info(message)