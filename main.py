#!/usr/bin/env python3
"""Main entry point for the Slack Archive Migration tool."""

import asyncio
import argparse
import sys
from src.config import Config
from src.logger import setup_logging, MigrationLogger
from src.migration_orchestrator import MigrationOrchestrator
from src.webhook_handler import WebhookHandler

def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(description="Slack Archive Migration Tool")
    parser.add_argument(
        "--mode",
        choices=["migrate", "webhook", "both"],
        default="migrate",
        help="Operation mode: migrate (one-time), webhook (real-time), or both"
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        help="Override batch size for migration"
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        help="Override max concurrent downloads"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = Config(args.config)
    
    # Override config with command line arguments
    if args.batch_size:
        config.config['migration']['batch_size'] = args.batch_size
    if args.max_concurrent:
        config.config['migration']['max_concurrent_downloads'] = args.max_concurrent
    
    # Setup logging
    setup_logging(config)
    logger = MigrationLogger("main")
    
    logger.info("Starting Slack Archive Migration Tool", mode=args.mode)
    
    try:
        if args.mode in ["migrate", "both"]:
            # Run migration
            asyncio.run(run_migration(config))
        
        if args.mode in ["webhook", "both"]:
            # Run webhook server
            run_webhook_server(config)
            
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.log_error_with_context(e, {"operation": "main"})
        sys.exit(1)

async def run_migration(config: Config):
    """Run the migration process."""
    logger = MigrationLogger("migration")
    logger.info("Starting migration process")
    
    try:
        orchestrator = MigrationOrchestrator(config)
        results = await orchestrator.run_full_migration()
        
        if results["status"] == "completed":
            logger.info("Migration completed successfully", **results["stats"])
        else:
            logger.error("Migration failed", error=results.get("error"))
            sys.exit(1)
            
    except Exception as e:
        logger.log_error_with_context(e, {"operation": "run_migration"})
        sys.exit(1)

def run_webhook_server(config: Config):
    """Run the webhook server."""
    logger = MigrationLogger("webhook_server")
    logger.info("Starting webhook server")
    
    try:
        webhook_handler = WebhookHandler(config)
        webhook_handler.run()
    except Exception as e:
        logger.log_error_with_context(e, {"operation": "run_webhook_server"})
        sys.exit(1)

if __name__ == "__main__":
    main()
