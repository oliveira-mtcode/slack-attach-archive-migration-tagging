#!/bin/bash

# Slack Archive Migration Tool Setup Script

set -e

echo "🚀 Setting up Slack Archive Migration Tool..."

# Check if Python 3.11+ is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3.11+ is required but not installed."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python 3.11+ is required. Current version: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python version check passed: $PYTHON_VERSION"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs data downloads credentials ssl

# Copy configuration files
echo "⚙️ Setting up configuration..."
if [ ! -f .env ]; then
    cp env.example .env
    echo "📝 Created .env file. Please update it with your credentials."
fi

if [ ! -f config.yaml ]; then
    echo "📝 Configuration file already exists."
fi

# Set up Google Apps Script
echo "🔧 Setting up Google Apps Script..."
if [ ! -d "google_apps_script" ]; then
    mkdir -p google_apps_script
fi

# Make scripts executable
chmod +x scripts/*.sh

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env with your Slack and Google Cloud credentials"
echo "2. Place your Google service account JSON file in credentials/"
echo "3. Update config.yaml with your preferences"
echo "4. Run: python main.py --mode migrate"
echo ""
echo "For Docker setup, run: docker-compose up -d"

# tweak 15 at 2025-09-26 19:30:07
