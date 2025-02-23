# Slack Archive Migration Tool

A comprehensive Python-based solution that automates the migration of large archives of images and videos from Slack's file storage to Google Drive, with intelligent AI-powered tagging and real-time processing capabilities.

## 🚀 Features

- **Complete Slack Integration**: Fetches all images and videos from Slack with pagination support
- **Google Drive Migration**: Preserves original channel-based folder hierarchy and permissions
- **AI-Powered Analysis**: Uses Google Cloud Vision API and Video Intelligence for automatic tagging
- **Real-time Processing**: Webhook-based processing of new Slack attachments
- **Metadata Preservation**: Maintains uploader, timestamp, channel, and other metadata
- **Robust Error Handling**: Comprehensive logging and retry mechanisms
- **Docker Support**: Easy deployment with Docker and Docker Compose
- **Google Apps Script Integration**: Additional Drive functionality and automation

## 📋 Prerequisites

### Slack Setup
1. Create a Slack App at [api.slack.com](https://api.slack.com/apps)
2. Enable the following OAuth scopes:
   - `files:read`
   - `channels:read`
   - `groups:read`
   - `users:read`
3. Enable Event Subscriptions for real-time processing
4. Note your Bot Token and App Token

### Google Cloud Setup
1. Create a Google Cloud Project
2. Enable the following APIs:
   - Google Drive API
   - Google Cloud Vision API
   - Video Intelligence API
   - Google Cloud Storage API
3. Create a Service Account and download the JSON credentials
4. Create a Google Drive folder for the migration

### System Requirements
- Python 3.11+
- Docker (optional)
- 4GB+ RAM recommended
- 10GB+ free disk space

## 🛠️ Installation

### Option 1: Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd slack-attach-archive-migration-tagging
   ```

2. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your credentials
   ```

3. **Place Google credentials**
   ```bash
   mkdir -p credentials
   # Place your google-service-account.json in the credentials folder
   ```

4. **Run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

### Option 2: Local Installation

1. **Clone and setup**
   ```bash
   git clone <repository-url>
   cd slack-attach-archive-migration-tagging
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure the application**
   ```bash
   cp env.example .env
   # Edit .env and config.yaml with your settings
   ```

3. **Run the migration**
   ```bash
   python main.py --mode migrate
   ```

## ⚙️ Configuration

### Environment Variables (.env)
```bash
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_APP_TOKEN=xapp-your-app-token-here

# Google Cloud Configuration
GOOGLE_CREDENTIALS_PATH=./credentials/google-service-account.json
GOOGLE_PROJECT_ID=your-project-id
GOOGLE_DRIVE_FOLDER_ID=your-root-folder-id
GOOGLE_SHARED_DRIVE_ID=your-shared-drive-id

# Webhook Configuration
WEBHOOK_SECRET=your-webhook-secret-here
```

### Configuration File (config.yaml)
The `config.yaml` file contains detailed settings for:
- File types to migrate
- AI analysis features
- Migration batch sizes
- Retry policies
- Logging configuration

## 🔄 Workflow

### Migration Process

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Start Migration│───▶│Authenticate with │───▶│  Fetch All Files│
└─────────────────┘    │     Slack        │    └─────────────────┘
                       └──────────────────┘             │
                                                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│Migration Complete│◀───│Cleanup Local Files│◀───│  Update Database│
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                ▲                        │
                                │                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Upload to Drive│───▶│Preserve Metadata │───▶│AI Analysis & Tag│
└─────────────────┘    └──────────────────┘    └─────────────────┘
         ▲                        ▲                        ▲
         │                        │                        │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│Create Drive Fold│◀───│Download from Slack│◀───│Create Drive Struct│
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Real-time Processing

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  New Slack File │───▶│ Webhook Received │───▶│Validate File Type│
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Process Complete │◀───│   Update Tags    │◀───│  Upload to Drive│
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                ▲                        ▲
                                │                        │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   AI Analysis   │───▶│  Download File   │◀───│ Check File Size │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🎯 Usage

### One-time Migration
```bash
python main.py --mode migrate --batch-size 20 --max-concurrent 10
```

### Real-time Webhook Server
```bash
python main.py --mode webhook
```

### Both Migration and Webhook
```bash
python main.py --mode both
```

### Docker Commands
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up --build -d
```

## 🤖 AI Analysis Features

### Image Analysis (Google Vision API)
- **Label Detection**: Identifies objects, concepts, and activities
- **Text Detection**: Extracts text from images
- **Face Detection**: Detects faces and emotions
- **Landmark Detection**: Recognizes famous landmarks
- **Logo Detection**: Identifies brand logos
- **Web Detection**: Finds similar images on the web
- **Safe Search**: Detects inappropriate content

### Video Analysis (Video Intelligence API)
- **Label Detection**: Identifies objects and activities in videos
- **Shot Change Detection**: Detects scene changes
- **Explicit Content Detection**: Identifies inappropriate content
- **Speech Transcription**: Converts speech to text
- **Text Detection**: Extracts text from video frames
- **Object Tracking**: Tracks objects across frames
- **Person Detection**: Identifies people in videos

## 📁 Project Structure

```
slack-attach-archive-migration-tagging/
├── src/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── logger.py              # Logging setup
│   ├── database.py            # Database operations
│   ├── slack_client.py        # Slack API client
│   ├── google_drive_client.py # Google Drive client
│   ├── ai_analyzer.py         # AI analysis module
│   ├── migration_orchestrator.py # Main migration logic
│   └── webhook_handler.py     # Webhook processing
├── google_apps_script/
│   └── Code.gs               # Google Apps Script
├── main.py                   # Application entry point
├── config.yaml              # Configuration file
├── requirements.txt         # Python dependencies
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose setup
├── nginx.conf              # Nginx configuration
└── README.md               # This file
```

## 🔧 Google Apps Script Setup

1. Go to [script.google.com](https://script.google.com)
2. Create a new project
3. Copy the code from `google_apps_script/Code.gs`
4. Update the configuration variables
5. Deploy as a web app
6. Set up triggers for automated processing

## 📊 Monitoring and Logging

### Log Files
- `logs/migration.log`: Main application logs
- Structured JSON logging for easy parsing
- Log rotation with configurable size limits

### Database
- SQLite database for tracking migration progress
- File metadata and status tracking
- Migration statistics and reporting

### Health Checks
- HTTP endpoint: `http://localhost:8080/health`
- Docker health checks configured
- Comprehensive error reporting

## 🚨 Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify Slack tokens are correct
   - Check Google Cloud credentials path
   - Ensure APIs are enabled in Google Cloud

2. **File Download Failures**
   - Check file permissions in Slack
   - Verify file size limits
   - Check network connectivity

3. **Google Drive Upload Issues**
   - Verify folder permissions
   - Check Google Drive API quotas
   - Ensure sufficient storage space

4. **AI Analysis Failures**
   - Check Google Cloud billing
   - Verify API quotas
   - Check file format support

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python main.py --mode migrate
```

## 🔒 Security Considerations

- Store credentials securely (use environment variables)
- Enable HTTPS for webhook endpoints
- Regularly rotate API keys
- Monitor API usage and costs
- Implement proper access controls

## 📈 Performance Optimization

- Adjust batch sizes based on your system
- Use concurrent processing for large migrations
- Monitor memory usage during processing
- Consider using Google Cloud Storage for temporary files

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the logs for error details

## 🔄 Version History

- **v1.0.0**: Initial release with full migration and AI analysis capabilities

---

**Note**: This tool is designed for enterprise use and requires proper Slack and Google Cloud setup. Always test with a small subset of files before running a full migration.

# tweak 9 at 2025-09-26 19:30:05
