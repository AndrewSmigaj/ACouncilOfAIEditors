"""
ASGI entry point for the AI Council research system.
"""
import logging
import sys
import os
from logging.handlers import RotatingFileHandler

# Configure debug mode based on environment variable
DEBUG_MODE = os.environ.get('AI_COUNCIL_DEBUG', 'true').lower() == 'true'

# Configure logging before importing any application modules
log_level = logging.DEBUG if DEBUG_MODE else logging.INFO
logging.basicConfig(
    level=log_level,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        # Console handler - shows all configured level messages and higher
        logging.StreamHandler(sys.stdout),
        # File handler - rotating log files, 5MB each, keep 5 backups
        RotatingFileHandler(
            'debug.log', 
            maxBytes=5*1024*1024,  # 5MB
            backupCount=5,
            encoding='utf-8'
        )
    ]
)

# Set specific loggers to DEBUG level if in debug mode
if DEBUG_MODE:
    for logger_name in [
        'quart.app', 
        'quart.serving',
        'src.app',
        'src.langchain.chains.ai_council',
        'src.langchain.chains.research_services',
        'src.backend.blueprints.research',
        'src.database.mongodb'
    ]:
        logging.getLogger(logger_name).setLevel(logging.DEBUG)

# Announce startup
logger = logging.getLogger('wsgi')
logger.info("========== STARTING APPLICATION ==========")
logger.info(f"Python version: {sys.version}")
logger.info(f"Working directory: {os.getcwd()}")
logger.info(f"Debug mode: {DEBUG_MODE}")

# Import application after logging is configured
from src.app import create_app

# Create the application
logger.info("Creating application...")
app = create_app()
logger.info("Application created successfully")

# Log application configuration details
logger.info(f"Application name: {app.name}")
logger.info(f"Blueprints registered: {', '.join(app.blueprints.keys()) if app.blueprints else 'None'}")
logger.info(f"URL Map: {app.url_map}")
logger.info("========== APPLICATION READY ==========")

if __name__ == "__main__":
    logger.info("Running application in debug mode...")
    app.run(debug=True) 