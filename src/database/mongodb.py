"""
MongoDB connection module for AI Council Guide Creation Website
"""
import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Try to import from config.py
try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    import config
    MONGODB_URI = getattr(config, 'MONGO_URI', None)
except (ImportError, AttributeError):
    MONGODB_URI = None

# Fall back to environment variables if not found in config
if not MONGODB_URI:
    MONGODB_URI = os.environ.get('MONGO_URI') or os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/ai_council')

logger = logging.getLogger(__name__)

def get_database():
    """
    Create a MongoDB connection and return the database object
    Returns:
        pymongo.database.Database: MongoDB database object
    """
    logger.debug(f"Connecting to MongoDB at: {MONGODB_URI}")
    logger.debug(f"Connection source: {'config.py' if MONGODB_URI == getattr(config, 'MONGO_URI', None) else 'environment variables'}")
    
    # Create a MongoDB client
    client = MongoClient(MONGODB_URI)
    logger.debug(f"MongoDB client created with address: {client.address}")
    
    # Extract database name from URI
    db_name = MONGODB_URI.split('/')[-1]
    if '?' in db_name:
        db_name = db_name.split('?')[0]
    
    logger.debug(f"Using database: {db_name}")
    db = client[db_name]
    
    # Verify connection
    try:
        # The ismaster command is cheap and does not require auth
        client.admin.command('ismaster')
        logger.debug("Successfully connected to MongoDB")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}", exc_info=True)
        raise
        
    return db

def initialize_collections():
    """
    Initialize MongoDB collections with indexes and schema validation if needed
    """
    logger.debug("Initializing MongoDB collections")
    db = get_database()
    
    # Create indexes for better performance
    # Guides collection
    if 'guides' not in db.list_collection_names():
        logger.debug("Creating guides collection")
        db.create_collection('guides')
    logger.debug("Creating indexes for guides collection")
    db.guides.create_index([('topic', 1)])
    db.guides.create_index([('status', 1)])
    
    # Users collection
    if 'users' not in db.list_collection_names():
        logger.debug("Creating users collection")
        db.create_collection('users')
    logger.debug("Creating indexes for users collection")
    db.users.create_index([('email', 1)], unique=True)
    
    # Word lists collection
    if 'word_lists' not in db.list_collection_names():
        logger.debug("Creating word_lists collection")
        db.create_collection('word_lists')
    logger.debug("Creating indexes for word_lists collection")
    db.word_lists.create_index([('user_id', 1)])
    
    # Research collection for shared research data
    if 'research' not in db.list_collection_names():
        logger.debug("Creating research collection")
        db.create_collection('research')
    logger.debug("Creating indexes for research collection")
    db.research.create_index([('topic', 1)])
    db.research.create_index([('timestamp', -1)])
    db.research.create_index([('recursive_research_completed', 1)])
    
    collections = db.list_collection_names()
    logger.debug(f"MongoDB collections initialized: {', '.join(collections)}")
    
    return db 