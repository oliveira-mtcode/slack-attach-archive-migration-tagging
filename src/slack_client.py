"""Slack API client for fetching files and metadata."""

import asyncio
import aiohttp
from typing import List, Dict, Any, Optional, AsyncGenerator
from slack_sdk.web import WebClient
from slack_sdk.errors import SlackApiError
from src.logger import MigrationLogger
from src.config import Config

class SlackClient:
    """Client for interacting with Slack API."""
    
    def __init__(self, config: Config):
        self.config = config
        self.client = WebClient(token=config.slack_token)
        self.logger = MigrationLogger("slack_client")
    
    async def get_all_files(self, file_types: List[str] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Get all files from Slack with pagination."""
        if not file_types:
            file_types = self.config.file_types
        
        page = 1
        while True:
            try:
                response = await self._get_files_page(page, file_types)
                files = response.get('files', [])
                
                if not files:
                    break
                
                for file_info in files:
                    yield file_info
                
                page += 1
                
            except Exception as e:
                self.logger.log_error_with_context(e, {
                    "operation": "get_all_files",
                    "page": page
                })
                break
    
    async def _get_files_page(self, page: int, file_types: List[str]) -> Dict[str, Any]:
        """Get a page of files from Slack."""
        try:
            response = self.client.files_list(
                page=page,
                types=','.join(file_types),
                count=200  # Maximum per page
            )
            return response.data
        except SlackApiError as e:
            self.logger.log_error_with_context(e, {
                "operation": "_get_files_page",
                "page": page,
                "error_code": e.response["error"]
            })
            raise
    
    async def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific file."""
        try:
            response = self.client.files_info(file=file_id)
            return response.data['file']
        except SlackApiError as e:
            self.logger.log_error_with_context(e, {
                "operation": "get_file_info",
                "file_id": file_id,
                "error_code": e.response["error"]
            })
            return None
    
    async def download_file(self, file_url: str, file_path: str) -> bool:
        """Download a file from Slack."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(file_url) as response:
                    if response.status == 200:
                        with open(file_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                f.write(chunk)
                        return True
                    else:
                        self.logger.warning(f"Failed to download file: HTTP {response.status}")
                        return False
        except Exception as e:
            self.logger.log_error_with_context(e, {
                "operation": "download_file",
                "file_url": file_url,
                "file_path": file_path
            })
            return False
    
    async def get_channels(self) -> List[Dict[str, Any]]:
        """Get all channels from Slack."""
        try:
            response = self.client.conversations_list(
                types="public_channel,private_channel",
                limit=1000
            )
            return response.data['channels']
        except SlackApiError as e:
            self.logger.log_error_with_context(e, {
                "operation": "get_channels",
                "error_code": e.response["error"]
            })
            return []
    
    async def get_users(self) -> List[Dict[str, Any]]:
        """Get all users from Slack."""
        try:
            response = self.client.users_list(limit=1000)
            return response.data['members']
        except SlackApiError as e:
            self.logger.log_error_with_context(e, {
                "operation": "get_users",
                "error_code": e.response["error"]
            })
            return []
