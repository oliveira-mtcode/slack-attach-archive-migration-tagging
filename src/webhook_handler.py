"""Webhook handler for real-time Slack file processing."""

import json
import hmac
import hashlib
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify
from src.config import Config
from src.logger import MigrationLogger
from src.migration_orchestrator import MigrationOrchestrator

class WebhookHandler:
    """Handles real-time webhooks from Slack for new file uploads."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = MigrationLogger("webhook_handler")
        self.app = Flask(__name__)
        self.orchestrator = MigrationOrchestrator(config)
        self._setup_routes()
    
    def _setup_routes(self):
        """Set up Flask routes."""
        
        @self.app.route(self.config.webhook_endpoint, methods=['POST'])
        def handle_slack_webhook():
            return self._handle_slack_webhook()
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            return jsonify({"status": "healthy"})
    
    def _handle_slack_webhook(self) -> Dict[str, Any]:
        """Handle incoming Slack webhook."""
        try:
            # Verify webhook signature
            if not self._verify_webhook_signature():
                self.logger.warning("Invalid webhook signature")
                return jsonify({"error": "Invalid signature"}), 403
            
            # Parse webhook payload
            payload = request.get_json()
            if not payload:
                return jsonify({"error": "No payload"}), 400
            
            # Handle different event types
            event_type = payload.get('type')
            
            if event_type == 'url_verification':
                return self._handle_url_verification(payload)
            elif event_type == 'event_callback':
                return self._handle_event_callback(payload)
            else:
                self.logger.warning(f"Unknown event type: {event_type}")
                return jsonify({"error": "Unknown event type"}), 400
                
        except Exception as e:
            self.logger.log_error_with_context(e, {
                "operation": "handle_slack_webhook"
            })
            return jsonify({"error": "Internal server error"}), 500
    
    def _verify_webhook_signature(self) -> bool:
        """Verify Slack webhook signature."""
        try:
            signature = request.headers.get('X-Slack-Signature')
            timestamp = request.headers.get('X-Slack-Request-Timestamp')
            
            if not signature or not timestamp:
                return False
            
            # Create signature base string
            body = request.get_data()
            sig_basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
            
            # Create expected signature
            expected_signature = 'v0=' + hmac.new(
                self.config.webhook_secret.encode(),
                sig_basestring.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            self.logger.log_error_with_context(e, {
                "operation": "verify_webhook_signature"
            })
            return False
    
    def _handle_url_verification(self, payload: Dict[str, Any]) -> Dict[str, str]:
        """Handle Slack URL verification challenge."""
        challenge = payload.get('challenge')
        if challenge:
            self.logger.info("URL verification successful")
            return jsonify({"challenge": challenge})
        else:
            return jsonify({"error": "No challenge provided"}), 400
    
    def _handle_event_callback(self, payload: Dict[str, Any]) -> Dict[str, str]:
        """Handle Slack event callback."""
        try:
            event = payload.get('event', {})
            event_type = event.get('type')
            
            if event_type == 'file_shared':
                # Process new file upload
                file_info = event.get('file', {})
                self._process_new_file(file_info)
            
            return jsonify({"status": "ok"})
            
        except Exception as e:
            self.logger.log_error_with_context(e, {
                "operation": "handle_event_callback",
                "event_type": event.get('type', 'unknown')
            })
            return jsonify({"error": "Failed to process event"}), 500
    
    def _process_new_file(self, file_info: Dict[str, Any]):
        """Process a newly uploaded file."""
        try:
            # Check if file type is supported
            file_type = file_info.get('filetype', '').lower()
            if file_type not in self.config.file_types:
                self.logger.info(f"Skipping unsupported file type: {file_type}")
                return
            
            # Check file size
            file_size = file_info.get('size', 0)
            max_size_bytes = self.config.max_file_size_mb * 1024 * 1024
            if file_size > max_size_bytes:
                self.logger.info(f"File too large: {file_size} bytes")
                return
            
            # Create file record
            from src.database import FileRecord
            from datetime import datetime
            
            file_record = FileRecord(
                id=file_info['id'],
                slack_file_id=file_info['id'],
                slack_channel_id=file_info.get('channels', [''])[0],
                slack_user_id=file_info['user'],
                file_name=file_info['name'],
                file_type=file_type,
                file_size=file_size,
                upload_timestamp=datetime.fromtimestamp(file_info['timestamp'])
            )
            
            # Save to database
            self.db.add_file_record(file_record)
            
            # Process file immediately
            self._process_file_immediately(file_record)
            
        except Exception as e:
            self.logger.log_error_with_context(e, {
                "operation": "process_new_file",
                "file_id": file_info.get('id', 'unknown')
            })
    
    def _process_file_immediately(self, file_record):
        """Process a file immediately after upload."""
        try:
            # This would implement immediate processing
            # For now, just log the file
            self.logger.info(f"New file uploaded: {file_record.file_name}")
            
        except Exception as e:
            self.logger.log_error_with_context(e, {
                "operation": "process_file_immediately",
                "file_id": file_record.id
            })
    
    def run(self):
        """Run the webhook server."""
        self.logger.info(f"Starting webhook server on {self.config.webhook_host}:{self.config.webhook_port}")
        self.app.run(
            host=self.config.webhook_host,
            port=self.config.webhook_port,
            debug=False
        )
