"""
Run script for the AI Council research system using Hypercorn.
"""
import asyncio
import logging
from hypercorn.config import Config
from hypercorn.asyncio import serve
from src.app import create_app

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def main():
    """Run the application with Hypercorn"""
    app = create_app()
    
    # Configure Hypercorn
    config = Config()
    config.bind = ["0.0.0.0:5000"]  # Listen on all interfaces, port 5000
    config.use_reloader = True  # Enable auto-reload on code changes
    config.worker_class = "asyncio"  # Use asyncio worker
    
    logger.info("Starting Hypercorn server...")
    await serve(app, config)

if __name__ == "__main__":
    asyncio.run(main()) 