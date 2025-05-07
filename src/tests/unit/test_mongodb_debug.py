"""
Debug script for MongoDB indexes
"""
import os
import sys
import json
from pymongo import MongoClient
from dotenv import load_dotenv

# Add the src directory to path so imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Load environment variables
load_dotenv()

# Try to import from config.py
try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
    import config
    MONGODB_URI = getattr(config, 'MONGO_URI', None)
except (ImportError, AttributeError):
    MONGODB_URI = None

# Fall back to environment variables if not found in config
if not MONGODB_URI:
    MONGODB_URI = os.environ.get('MONGO_URI') or os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/ai_council')

print(f"Using MongoDB URI: {MONGODB_URI}")

# Add _test suffix to database name to avoid affecting production
if '/' in MONGODB_URI:
    base_uri = MONGODB_URI.rsplit('/', 1)[0]
    db_name = MONGODB_URI.rsplit('/', 1)[1].split('?')[0] + '_test'
    auth_params = '?' + MONGODB_URI.split('?', 1)[1] if '?' in MONGODB_URI else ''
    test_uri = f"{base_uri}/{db_name}{auth_params}"
else:
    test_uri = MONGODB_URI + '_test'

print(f"Using test URI: {test_uri}")

# Connect to MongoDB
client = MongoClient(test_uri)
db = client.get_database()

# Clear database
client.drop_database(db.name)

# Initialize collections
from database.mongodb import initialize_collections
db = initialize_collections()

# Print all collections
print("\nCollections:")
for collection in db.list_collection_names():
    print(f"- {collection}")

# Print indexes for each collection
print("\nIndexes for guides collection:")
for idx in db.guides.list_indexes():
    print(json.dumps(idx, default=str, indent=2))

print("\nIndexes for users collection:")
for idx in db.users.list_indexes():
    print(json.dumps(idx, default=str, indent=2))

print("\nIndexes for word_lists collection:")
for idx in db.word_lists.list_indexes():
    print(json.dumps(idx, default=str, indent=2))

# Clean up
client.drop_database(db.name)
client.close()

print("\nDebug complete") 