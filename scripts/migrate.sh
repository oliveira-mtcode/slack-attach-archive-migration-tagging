#!/bin/bash

# Migration Runner Script

set -e

# Default values
MODE="migrate"
BATCH_SIZE=""
MAX_CONCURRENT=""
CONFIG_FILE="config.yaml"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --mode)
            MODE="$2"
            shift 2
            ;;
        --batch-size)
            BATCH_SIZE="$2"
            shift 2
            ;;
        --max-concurrent)
            MAX_CONCURRENT="$2"
            shift 2
            ;;
        --config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --mode MODE              Migration mode (migrate|webhook|both)"
            echo "  --batch-size SIZE        Override batch size"
            echo "  --max-concurrent NUM     Override max concurrent downloads"
            echo "  --config FILE            Configuration file path"
            echo "  --help                   Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run setup.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Run setup.sh first."
    exit 1
fi

# Check if Google credentials exist
if [ ! -f "credentials/google-service-account.json" ]; then
    echo "❌ Google service account credentials not found."
    echo "Please place your google-service-account.json file in the credentials/ directory."
    exit 1
fi

# Build command
CMD="python main.py --mode $MODE --config $CONFIG_FILE"

if [ -n "$BATCH_SIZE" ]; then
    CMD="$CMD --batch-size $BATCH_SIZE"
fi

if [ -n "$MAX_CONCURRENT" ]; then
    CMD="$CMD --max-concurrent $MAX_CONCURRENT"
fi

echo "🚀 Starting migration with mode: $MODE"
echo "Command: $CMD"
echo ""

# Run the migration
exec $CMD

# tweak 13 at 2025-09-26 19:30:06
