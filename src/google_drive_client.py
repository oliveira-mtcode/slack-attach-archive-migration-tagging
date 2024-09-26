"""Google Drive API client for file operations and folder management."""

import os
from typing import List, Dict, Any, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from src.logger import MigrationLogger
from src.config import Config

class GoogleDriveClient:
    """Client for interacting with Google Drive API."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = MigrationLogger("google_drive_client")
        self.service = self._build_service()
    
    def _build_service(self):
        """Build Google Drive service with authentication."""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.config.google_credentials_path,
                scopes=['https://www.googleapis.com/auth/drive']
            )
            return build('drive', 'v3', credentials=credentials)
        except Exception as e:
            self.logger.log_error_with_context(e, {
                "operation": "build_service",
                "credentials_path": self.config.google_credentials_path
            })
            raise
    
    def create_folder(self, name: str, parent_id: str = None) -> Optional[str]:
        """Create a folder in Google Drive."""
        try:
            if not parent_id:
                parent_id = self.config.google_drive_folder_id
            
            folder_metadata = {
                'name': name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id]
            }
            
            folder = self.service.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()
            
            folder_id = folder.get('id')
            self.logger.info(f"Created folder: {name}", folder_id=folder_id)
            return folder_id
            
        except HttpError as e:
            self.logger.log_error_with_context(e, {
                "operation": "create_folder",
                "name": name,
                "parent_id": parent_id,
                "error_code": e.resp.status
            })
            return None
    
    def get_or_create_folder(self, name: str, parent_id: str = None) -> Optional[str]:
        """Get existing folder or create new one."""
        try:
            if not parent_id:
                parent_id = self.config.google_drive_folder_id
            
            # Search for existing folder
            query = f"name='{name}' and parents in '{parent_id}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(
                q=query,
                fields="files(id, name)"
            ).execute()
            
            files = results.get('files', [])
            if files:
                return files[0]['id']
            else:
                return self.create_folder(name, parent_id)
                
        except Exception as e:
            self.logger.log_error_with_context(e, {
                "operation": "get_or_create_folder",
                "name": name,
                "parent_id": parent_id
            })
            return None
    
    def upload_file(self, file_path: str, file_name: str, 
                   parent_id: str, metadata: Dict[str, Any] = None) -> Optional[str]:
        """Upload a file to Google Drive."""
        try:
            file_metadata = {
                'name': file_name,
                'parents': [parent_id]
            }
            
            # Add custom metadata if provided
            if metadata:
                file_metadata.update(metadata)
            
            media = MediaFileUpload(file_path, resumable=True)
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            file_id = file.get('id')
            self.logger.log_file_operation(
                "upload", file_id, file_name, 
                status="completed"
            )
            return file_id
            
        except HttpError as e:
            self.logger.log_error_with_context(e, {
                "operation": "upload_file",
                "file_path": file_path,
                "file_name": file_name,
                "parent_id": parent_id,
                "error_code": e.resp.status
            })
            return None
    
    def set_file_permissions(self, file_id: str, permissions: List[Dict[str, str]]) -> bool:
        """Set permissions for a file."""
        try:
            for permission in permissions:
                self.service.permissions().create(
                    fileId=file_id,
                    body=permission
                ).execute()
            return True
        except HttpError as e:
            self.logger.log_error_with_context(e, {
                "operation": "set_file_permissions",
                "file_id": file_id,
                "error_code": e.resp.status
            })
            return False
    
    def add_file_description(self, file_id: str, description: str) -> bool:
        """Add description to a file."""
        try:
            self.service.files().update(
                fileId=file_id,
                body={'description': description}
            ).execute()
            return True
        except HttpError as e:
            self.logger.log_error_with_context(e, {
                "operation": "add_file_description",
                "file_id": file_id,
                "error_code": e.resp.status
            })
            return False
    
    def create_channel_folder_structure(self, channel_name: str, 
                                      user_folders: List[str] = None) -> Optional[str]:
        """Create folder structure for a Slack channel."""
        try:
            # Create main channel folder
            channel_folder_id = self.get_or_create_folder(
                f"Slack - {channel_name}",
                self.config.google_drive_folder_id
            )
            
            if not channel_folder_id:
                return None
            
            # Create user subfolders if provided
            if user_folders:
                for user_name in user_folders:
                    self.get_or_create_folder(
                        user_name,
                        channel_folder_id
                    )
            
            return channel_folder_id
            
        except Exception as e:
            self.logger.log_error_with_context(e, {
                "operation": "create_channel_folder_structure",
                "channel_name": channel_name
            })
            return None
