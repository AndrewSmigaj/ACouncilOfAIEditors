"""
MongoDB connection module for AI Council Guide Creation Website
"""
import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv

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

def get_database():
    """
    Create a MongoDB connection and return the database object
    Returns:
        pymongo.database.Database: MongoDB database object
    """
    # Create a MongoDB client
    client = MongoClient(MONGODB_URI)
    
    # Extract database name from URI
    db_name = MONGODB_URI.split('/')[-1]
    if '?' in db_name:
        db_name = db_name.split('?')[0]
    
    # Return the database
    return client[db_name]

def initialize_collections():
    """
    Initialize MongoDB collections with indexes and schema validation if needed
    """
    db = get_database()
    
    # Create indexes for better performance
    # Guides collection
    if 'guides' not in db.list_collection_names():
        db.create_collection('guides')
    db.guides.create_index([('topic', 1)])
    db.guides.create_index([('status', 1)])
    
    # Users collection
    if 'users' not in db.list_collection_names():
        db.create_collection('users')
    db.users.create_index([('email', 1)], unique=True)
    
    # Word lists collection
    if 'word_lists' not in db.list_collection_names():
        db.create_collection('word_lists')
    db.word_lists.create_index([('user_id', 1)])
    
    # Research collection for shared research data
    if 'research' not in db.list_collection_names():
        db.create_collection('research')
    db.research.create_index([('topic', 1)])
    db.research.create_index([('timestamp', -1)])
    db.research.create_index([('recursive_research_completed', 1)])
    
    print(f"MongoDB collections initialized: {', '.join(db.list_collection_names())}")
    
    return db 