"""
Global pytest fixtures for AI Council Guide Creation Website tests
"""
import pytest
import os
import sys
from dotenv import load_dotenv
from pymongo import MongoClient

# Add the src directory to path so imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables from .env file
load_dotenv()

@pytest.fixture(scope="session", autouse=True)
def load_env():
    """Load environment variables before tests run"""
    # Import config variables
    try:
        import config
        if not os.environ.get('MONGO_URI') and hasattr(config, 'MONGO_URI'):
            os.environ['MONGO_URI'] = config.MONGO_URI
    except ImportError:
        pass
    
    # Provide default if not set
    if not os.environ.get('MONGO_URI'):
        os.environ['MONGO_URI'] = 'mongodb://localhost:27017/ai_council'

@pytest.fixture(scope="session")
def app():
    """Create the Flask application for testing"""
    from app import create_app
    app = create_app()
    app.config.update({
        "TESTING": True,
    })
    
    # Create app context
    with app.app_context():
        yield app

@pytest.fixture(scope="module")
def test_db():
    """
    Create a test database connection.
    Uses the same host as production but with a test database name.
    """
    mongo_uri = os.environ.get('MONGO_URI')
    
    # Add _test suffix to database name to avoid affecting production
    if '/' in mongo_uri:
        base_uri = mongo_uri.rsplit('/', 1)[0]
        db_name = mongo_uri.rsplit('/', 1)[1].split('?')[0] + '_test'
        auth_params = '?' + mongo_uri.split('?', 1)[1] if '?' in mongo_uri else ''
        test_uri = f"{base_uri}/{db_name}{auth_params}"
    else:
        test_uri = mongo_uri + '_test'
    
    # Create client
    client = MongoClient(test_uri)
    db = client.get_database()
    
    # Clear database before tests
    client.drop_database(db.name)
    
    yield db
    
    # Clean up after tests
    client.drop_database(db.name)
    client.close() 