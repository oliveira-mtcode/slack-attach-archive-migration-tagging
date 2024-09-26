"""Database management for tracking migration progress and metadata."""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from src.logger import MigrationLogger

@dataclass
class FileRecord:
    """Represents a file record in the database."""
    id: str
    slack_file_id: str
    slack_channel_id: str
    slack_user_id: str
    file_name: str
    file_type: str
    file_size: int
    upload_timestamp: datetime
    google_drive_file_id: Optional[str] = None
    google_drive_folder_id: Optional[str] = None
    migration_status: str = "pending"
    migration_timestamp: Optional[datetime] = None
    error_message: Optional[str] = None
    tags: Optional[str] = None  # JSON string of tags
    metadata: Optional[str] = None  # JSON string of additional metadata

class DatabaseManager:
    """Manages database operations for migration tracking."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.logger = MigrationLogger("database")
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Files table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id TEXT PRIMARY KEY,
                    slack_file_id TEXT UNIQUE NOT NULL,
                    slack_channel_id TEXT NOT NULL,
                    slack_user_id TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    upload_timestamp DATETIME NOT NULL,
                    google_drive_file_id TEXT,
                    google_drive_folder_id TEXT,
                    migration_status TEXT DEFAULT 'pending',
                    migration_timestamp DATETIME,
                    error_message TEXT,
                    tags TEXT,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Channels table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS channels (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    google_drive_folder_id TEXT,
                    migration_status TEXT DEFAULT 'pending',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT,
                    google_drive_folder_id TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Migration stats table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS migration_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    total_files INTEGER DEFAULT 0,
                    migrated_files INTEGER DEFAULT 0,
                    failed_files INTEGER DEFAULT 0,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            self.logger.info("Database initialized successfully")
    
    def add_file_record(self, file_record: FileRecord) -> bool:
        """Add a new file record to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO files (
                        id, slack_file_id, slack_channel_id, slack_user_id,
                        file_name, file_type, file_size, upload_timestamp,
                        google_drive_file_id, google_drive_folder_id,
                        migration_status, migration_timestamp, error_message,
                        tags, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    file_record.id,
                    file_record.slack_file_id,
                    file_record.slack_channel_id,
                    file_record.slack_user_id,
                    file_record.file_name,
                    file_record.file_type,
                    file_record.upload_timestamp,
                    file_record.google_drive_file_id,
                    file_record.google_drive_folder_id,
                    file_record.migration_status,
                    file_record.migration_timestamp,
                    file_record.error_message,
                    file_record.tags,
                    file_record.metadata
                ))
                conn.commit()
                return True
        except Exception as e:
            self.logger.log_error_with_context(e, {
                "operation": "add_file_record",
                "file_id": file_record.id
            })
            return False
    
    def update_file_migration_status(self, file_id: str, status: str, 
                                   google_drive_file_id: str = None,
                                   error_message: str = None) -> bool:
        """Update file migration status."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE files 
                    SET migration_status = ?, 
                        google_drive_file_id = ?,
                        migration_timestamp = CURRENT_TIMESTAMP,
                        error_message = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (status, google_drive_file_id, error_message, file_id))
                conn.commit()
                return True
        except Exception as e:
            self.logger.log_error_with_context(e, {
                "operation": "update_file_migration_status",
                "file_id": file_id,
                "status": status
            })
            return False
    
    def update_file_tags(self, file_id: str, tags: List[Dict[str, Any]]) -> bool:
        """Update file tags."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE files 
                    SET tags = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (json.dumps(tags), file_id))
                conn.commit()
                return True
        except Exception as e:
            self.logger.log_error_with_context(e, {
                "operation": "update_file_tags",
                "file_id": file_id
            })
            return False
    
    def get_pending_files(self, limit: int = None) -> List[FileRecord]:
        """Get files pending migration."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = "SELECT * FROM files WHERE migration_status = 'pending'"
                if limit:
                    query += f" LIMIT {limit}"
                
                cursor.execute(query)
                rows = cursor.fetchall()
                
                return [self._row_to_file_record(row) for row in rows]
        except Exception as e:
            self.logger.log_error_with_context(e, {"operation": "get_pending_files"})
            return []
    
    def get_migration_stats(self) -> Dict[str, int]:
        """Get migration statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_files,
                        SUM(CASE WHEN migration_status = 'completed' THEN 1 ELSE 0 END) as migrated_files,
                        SUM(CASE WHEN migration_status = 'failed' THEN 1 ELSE 0 END) as failed_files
                    FROM files
                """)
                row = cursor.fetchone()
                return {
                    "total_files": row[0] or 0,
                    "migrated_files": row[1] or 0,
                    "failed_files": row[2] or 0
                }
        except Exception as e:
            self.logger.log_error_with_context(e, {"operation": "get_migration_stats"})
            return {"total_files": 0, "migrated_files": 0, "failed_files": 0}
    
    def _row_to_file_record(self, row: sqlite3.Row) -> FileRecord:
        """Convert database row to FileRecord object."""
        return FileRecord(
            id=row['id'],
            slack_file_id=row['slack_file_id'],
            slack_channel_id=row['slack_channel_id'],
            slack_user_id=row['slack_user_id'],
            file_name=row['file_name'],
            file_type=row['file_type'],
            file_size=row['file_size'],
            upload_timestamp=datetime.fromisoformat(row['upload_timestamp']),
            google_drive_file_id=row['google_drive_file_id'],
            google_drive_folder_id=row['google_drive_folder_id'],
            migration_status=row['migration_status'],
            migration_timestamp=datetime.fromisoformat(row['migration_timestamp']) if row['migration_timestamp'] else None,
            error_message=row['error_message'],
            tags=row['tags'],
            metadata=row['metadata']
        )
