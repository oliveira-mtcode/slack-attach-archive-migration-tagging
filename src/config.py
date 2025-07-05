"""Configuration management for the Slack Archive Migration tool."""

import os
import yaml
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

class Config:
    """Centralized configuration management."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize configuration from YAML file and environment variables."""
        load_dotenv()
        
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
        
        # Override with environment variables
        self._load_env_overrides()
    
    def _load_env_overrides(self):
        """Load configuration overrides from environment variables."""
        env_mappings = {
            'SLACK_BOT_TOKEN': 'slack.token',
            'SLACK_APP_TOKEN': 'slack.app_token',
            'GOOGLE_CREDENTIALS_PATH': 'google.credentials_path',
            'GOOGLE_PROJECT_ID': 'google.project_id',
            'GOOGLE_DRIVE_FOLDER_ID': 'google.drive_folder_id',
            'GOOGLE_SHARED_DRIVE_ID': 'google.shared_drive_id',
            'WEBHOOK_SECRET': 'webhook.secret',
            'MIGRATION_BATCH_SIZE': 'migration.batch_size',
            'MAX_CONCURRENT_DOWNLOADS': 'migration.max_concurrent_downloads'
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                self._set_nested_value(config_path, value)
    
    def _set_nested_value(self, path: str, value: Any):
        """Set a nested configuration value using dot notation."""
        keys = path.split('.')
        current = self.config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Convert numeric strings to appropriate types
        if value.isdigit():
            value = int(value)
        elif value.replace('.', '').isdigit():
            value = float(value)
        elif value.lower() in ('true', 'false'):
            value = value.lower() == 'true'
        
        current[keys[-1]] = value
    
    def get(self, path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        keys = path.split('.')
        current = self.config
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    @property
    def slack_token(self) -> str:
        """Get Slack bot token."""
        return self.get('slack.token')
    
    @property
    def slack_app_token(self) -> str:
        """Get Slack app token."""
        return self.get('slack.app_token')
    
    @property
    def google_credentials_path(self) -> str:
        """Get Google credentials file path."""
        return self.get('google.credentials_path')
    
    @property
    def google_project_id(self) -> str:
        """Get Google Cloud project ID."""
        return self.get('google.project_id')
    
    @property
    def google_drive_folder_id(self) -> str:
        """Get Google Drive root folder ID."""
        return self.get('google.drive_folder_id')
    
    @property
    def google_shared_drive_id(self) -> Optional[str]:
        """Get Google Drive shared drive ID."""
        return self.get('google.shared_drive_id')
    
    @property
    def file_types(self) -> List[str]:
        """Get list of file types to migrate."""
        return self.get('slack.file_types', [])
    
    @property
    def max_file_size_mb(self) -> int:
        """Get maximum file size in MB."""
        return self.get('slack.max_file_size_mb', 100)
    
    @property
    def batch_size(self) -> int:
        """Get migration batch size."""
        return self.get('migration.batch_size', 10)
    
    @property
    def max_concurrent_downloads(self) -> int:
        """Get maximum concurrent downloads."""
        return self.get('migration.max_concurrent_downloads', 5)
    
    @property
    def retry_attempts(self) -> int:
        """Get number of retry attempts."""
        return self.get('migration.retry_attempts', 3)
    
    @property
    def webhook_secret(self) -> str:
        """Get webhook secret."""
        return self.get('webhook.secret')
    
    @property
    def webhook_port(self) -> int:
        """Get webhook port."""
        return self.get('webhook.port', 8080)
    
    @property
    def webhook_host(self) -> str:
        """Get webhook host."""
        return self.get('webhook.host', '0.0.0.0')
    
    @property
    def webhook_endpoint(self) -> str:
        """Get webhook endpoint."""
        return self.get('webhook.endpoint', '/slack/webhook')
    
    @property
    def vision_features(self) -> List[str]:
        """Get Google Vision API features."""
        return self.get('google.vision.features', [])
    
    @property
    def video_intelligence_features(self) -> List[str]:
        """Get Google Video Intelligence API features."""
        return self.get('google.video_intelligence.features', [])
    
    @property
    def preserve_metadata(self) -> List[str]:
        """Get list of metadata fields to preserve."""
        return self.get('migration.preserve_metadata', [])
    
    @property
    def database_path(self) -> str:
        """Get database file path."""
        return self.get('database.path', 'data/migration.db')
    
    @property
    def log_level(self) -> str:
        """Get logging level."""
        return self.get('logging.level', 'INFO')
    
    @property
    def log_file(self) -> str:
        """Get log file path."""
        return self.get('logging.file', 'logs/migration.log')

# tweak 17 at 2025-09-26 19:30:07
