import shutil
import os
from datetime import datetime
import time
from pathlib import Path
from config.config import CONFIG
from utils.logger import LoggerManager

class BackupManager:
    @staticmethod
    def create_backup():
        """Create timestamped backup of all data"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path(CONFIG['BACKUPS_DIR']) / timestamp
        
        try:
            # Create backup directory
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup reviews
            shutil.copytree(
                CONFIG['REVIEWS_DIR'],
                backup_dir / 'reviews',
                dirs_exist_ok=True
            )
            
            # Backup form data
            form_backups = Path(CONFIG['FORM_BACKUPS_DIR'])
            if form_backups.exists():
                shutil.copytree(
                    form_backups,
                    backup_dir / 'form_backups',
                    dirs_exist_ok=True
                )
            
            LoggerManager.log_backup_creation(str(backup_dir))
            return True
            
        except Exception as e:
            LoggerManager.log_error(f"Backup failed: {str(e)}")
            return False

    @staticmethod
    def run_backup_service():
        """Run continuous backup service"""
        while True:
            BackupManager.create_backup()
            time.sleep(CONFIG['BACKUP_INTERVAL'])

    @staticmethod
    def restore_from_backup(backup_timestamp=None):
        """Restore data from backup"""
        try:
            backup_dirs = sorted(os.listdir(CONFIG['BACKUPS_DIR']), reverse=True)
            
            if not backup_dirs:
                raise ValueError("No backups found")
            
            # Use latest backup if timestamp not specified
            restore_dir = backup_timestamp or backup_dirs[0]
            backup_path = Path(CONFIG['BACKUPS_DIR']) / restore_dir
            
            # Restore reviews
            if (backup_path / 'reviews').exists():
                shutil.rmtree(CONFIG['REVIEWS_DIR'], ignore_errors=True)
                shutil.copytree(backup_path / 'reviews', CONFIG['REVIEWS_DIR'])
            
            # Restore form backups
            if (backup_path / 'form_backups').exists():
                shutil.rmtree(CONFIG['FORM_BACKUPS_DIR'], ignore_errors=True)
                shutil.copytree(backup_path / 'form_backups', CONFIG['FORM_BACKUPS_DIR'])
            
            LoggerManager.log_backup_creation(f"Restored from backup: {restore_dir}")
            return True
            
        except Exception as e:
            LoggerManager.log_error(f"Restore failed: {str(e)}")
            return False