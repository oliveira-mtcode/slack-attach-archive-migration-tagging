"""Main migration orchestrator that coordinates the entire migration process."""

import asyncio
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from src.config import Config
from src.logger import MigrationLogger
from src.database import DatabaseManager, FileRecord
from src.slack_client import SlackClient
from src.google_drive_client import GoogleDriveClient
from src.ai_analyzer import AIAnalyzer

class MigrationOrchestrator:
    """Orchestrates the complete migration process."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = MigrationLogger("migration_orchestrator")
        self.db = DatabaseManager(config.database_path)
        self.slack_client = SlackClient(config)
        self.drive_client = GoogleDriveClient(config)
        self.ai_analyzer = AIAnalyzer(config)
        
        # Create necessary directories
        os.makedirs("downloads", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        os.makedirs("data", exist_ok=True)
    
    async def run_full_migration(self) -> Dict[str, Any]:
        """Run the complete migration process."""
        self.logger.info("Starting full migration process")
        
        try:
            # Step 1: Fetch and catalog all files from Slack
            await self._catalog_slack_files()
            
            # Step 2: Create folder structure in Google Drive
            await self._create_drive_structure()
            
            # Step 3: Migrate files with AI analysis
            migration_results = await self._migrate_files()
            
            # Step 4: Generate final report
            final_stats = self.db.get_migration_stats()
            
            self.logger.info("Migration completed successfully", **final_stats)
            return {
                "status": "completed",
                "stats": final_stats,
                "migration_results": migration_results
            }
            
        except Exception as e:
            self.logger.log_error_with_context(e, {"operation": "run_full_migration"})
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _catalog_slack_files(self):
        """Catalog all files from Slack and store in database."""
        self.logger.info("Cataloging Slack files")
        
        file_count = 0
        async for file_info in self.slack_client.get_all_files():
            try:
                # Create file record
                file_record = FileRecord(
                    id=file_info['id'],
                    slack_file_id=file_info['id'],
                    slack_channel_id=file_info.get('channels', [''])[0],
                    slack_user_id=file_info['user'],
                    file_name=file_info['name'],
                    file_type=file_info['filetype'],
                    file_size=file_info['size'],
                    upload_timestamp=datetime.fromtimestamp(file_info['timestamp'])
                )
                
                # Save to database
                self.db.add_file_record(file_record)
                file_count += 1
                
                if file_count % 100 == 0:
                    self.logger.log_migration_progress(
                        total=file_count, 
                        processed=file_count,
                        current_file=file_info['name']
                    )
                    
            except Exception as e:
                self.logger.log_error_with_context(e, {
                    "operation": "catalog_slack_files",
                    "file_id": file_info.get('id', 'unknown')
                })
        
        self.logger.info(f"Cataloged {file_count} files from Slack")
    
    async def _create_drive_structure(self):
        """Create folder structure in Google Drive."""
        self.logger.info("Creating Google Drive folder structure")
        
        try:
            # Get channels and users from Slack
            channels = await self.slack_client.get_channels()
            users = await self.slack_client.get_users()
            
            # Create user lookup
            user_lookup = {user['id']: user['name'] for user in users}
            
            # Create folder structure for each channel
            for channel in channels:
                channel_name = channel['name']
                channel_folder_id = self.drive_client.create_channel_folder_structure(
                    channel_name
                )
                
                if channel_folder_id:
                    # Store channel folder mapping in database
                    # This would be implemented in the database module
                    pass
                    
        except Exception as e:
            self.logger.log_error_with_context(e, {"operation": "create_drive_structure"})
    
    async def _migrate_files(self) -> Dict[str, Any]:
        """Migrate files with AI analysis."""
        self.logger.info("Starting file migration with AI analysis")
        
        pending_files = self.db.get_pending_files(limit=self.config.batch_size)
        results = {
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        for file_record in pending_files:
            try:
                # Download file from Slack
                download_path = f"downloads/{file_record.id}_{file_record.file_name}"
                success = await self._download_and_analyze_file(file_record, download_path)
                
                if success:
                    results["successful"] += 1
                else:
                    results["failed"] += 1
                    
            except Exception as e:
                self.logger.log_error_with_context(e, {
                    "operation": "migrate_files",
                    "file_id": file_record.id
                })
                results["failed"] += 1
                results["errors"].append(str(e))
        
        return results
    
    async def _download_and_analyze_file(self, file_record: FileRecord, 
                                       download_path: str) -> bool:
        """Download file and perform AI analysis."""
        try:
            # Get file info from Slack
            file_info = await self.slack_client.get_file_info(file_record.slack_file_id)
            if not file_info:
                return False
            
            # Download file
            download_success = await self.slack_client.download_file(
                file_info['url_private_download'],
                download_path
            )
            
            if not download_success:
                return False
            
            # Perform AI analysis
            tags = []
            if file_record.file_type in ['jpg', 'jpeg', 'png', 'gif']:
                tags = self.ai_analyzer.analyze_image(download_path)
            elif file_record.file_type in ['mp4', 'mov', 'avi', 'webm']:
                tags = self.ai_analyzer.analyze_video(download_path)
            
            # Upload to Google Drive
            folder_id = self._get_target_folder_id(file_record)
            if not folder_id:
                return False
            
            # Create metadata for Google Drive
            metadata = {
                'description': self.ai_analyzer.generate_file_description(
                    tags, file_record.file_type
                ),
                'properties': {
                    'slack_channel': file_record.slack_channel_id,
                    'slack_user': file_record.slack_user_id,
                    'upload_timestamp': file_record.upload_timestamp.isoformat(),
                    'original_name': file_record.file_name
                }
            }
            
            # Upload file
            drive_file_id = self.drive_client.upload_file(
                download_path,
                file_record.file_name,
                folder_id,
                metadata
            )
            
            if drive_file_id:
                # Update database
                self.db.update_file_migration_status(
                    file_record.id, "completed", drive_file_id
                )
                self.db.update_file_tags(file_record.id, tags)
                
                # Clean up downloaded file
                os.remove(download_path)
                return True
            
            return False
            
        except Exception as e:
            self.logger.log_error_with_context(e, {
                "operation": "download_and_analyze_file",
                "file_id": file_record.id
            })
            return False
    
    def _get_target_folder_id(self, file_record: FileRecord) -> Optional[str]:
        """Get the target folder ID for a file."""
        # This would implement the folder mapping logic
        # For now, return the root folder ID
        return self.config.google_drive_folder_id

# tweak 21 at 2025-09-26 19:30:08
