import os
import shutil
from datetime import datetime
from config import Config
from utils.logger import log_event

class BackupService:
    @staticmethod
    def get_backup_directory():
        """Ensures backup folder exists and returns the path."""
        os.makedirs(Config.BACKUP_FOLDER, exist_ok=True)
        return Config.BACKUP_FOLDER

    @classmethod
    def backup_database(cls):
        """
        Creates a time-stamped duplicate copy of the SQLite database.
        Returns (success, filename_or_error_msg).
        """
        try:
            backup_dir = cls.get_backup_directory()
            db_path = Config.DATABASE_PATH
            
            if not os.path.exists(db_path):
                return False, "Active database file not found."
                
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"database_backup_{timestamp}.db"
            dest_path = os.path.join(backup_dir, backup_filename)
            
            # Copy file
            shutil.copy2(db_path, dest_path)
            log_event("INFO", "DatabaseBackup", f"Created database backup: {backup_filename}")
            return True, backup_filename
        except Exception as e:
            log_event("ERROR", "DatabaseBackup", f"Backup failed: {str(e)}")
            return False, str(e)

    @classmethod
    def restore_database(cls, backup_filename):
        """
        Restores a database state by copying a backup file over the active DB.
        Returns (success, msg).
        """
        try:
            backup_dir = cls.get_backup_directory()
            backup_path = os.path.join(backup_dir, backup_filename)
            db_path = Config.DATABASE_PATH
            
            # Verify file exists
            if not os.path.exists(backup_path):
                return False, f"Backup file '{backup_filename}' not found."
                
            # Perform overwrite (restore)
            shutil.copy2(backup_path, db_path)
            log_event("WARNING", "DatabaseBackup", f"Restored database checkpoint from: {backup_filename}")
            return True, "Database restored successfully."
        except Exception as e:
            log_event("ERROR", "DatabaseBackup", f"Restore failed for '{backup_filename}': {str(e)}")
            return False, str(e)

    @classmethod
    def list_backups(cls):
        """
        Lists all available database backup files.
        Returns a sorted list of dictionaries with details.
        """
        backup_dir = cls.get_backup_directory()
        backups = []
        
        try:
            for file in os.listdir(backup_dir):
                if file.startswith("database_backup_") and file.endswith(".db"):
                    file_path = os.path.join(backup_dir, file)
                    stats = os.stat(file_path)
                    
                    # Parse timestamp from filename
                    parts = file.replace("database_backup_", "").replace(".db", "").split("_")
                    formatted_time = "Unknown Date"
                    if len(parts) == 2:
                        try:
                            dt = datetime.strptime(f"{parts[0]}{parts[1]}", "%Y%m%d%H%M%S")
                            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                        except Exception:
                            pass
                            
                    backups.append({
                        'filename': file,
                        'size_kb': round(stats.st_size / 1024, 1),
                        'created_at': formatted_time,
                        'timestamp': stats.st_mtime
                    })
                    
            # Sort newest first
            backups.sort(key=lambda x: x['timestamp'], reverse=True)
        except Exception as e:
            log_event("ERROR", "DatabaseBackup", f"Failed to list backups: {str(e)}")
            
        return backups
