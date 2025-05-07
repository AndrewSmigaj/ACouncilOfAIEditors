"""
Tests for MongoDB connectivity and schema validation
"""
import pytest
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from database.mongodb import get_database, initialize_collections

class TestMongoDBConnection:
    """Tests for MongoDB connectivity and schema"""
    
    def test_database_connection(self, test_db):
        """Test that we can connect to the MongoDB server"""
        # The test_db fixture has already connected, so if it exists, the connection worked
        assert test_db is not None
        
        # Verify we can execute a command on the server
        server_info = test_db.command('serverStatus')
        assert server_info is not None
    
    def test_initialize_collections(self, test_db, monkeypatch):
        """Test that collections are properly initialized with indexes"""
        # Monkeypatch get_database to return our test database
        def mock_get_database():
            return test_db
        
        monkeypatch.setattr('database.mongodb.get_database', mock_get_database)
        
        # Initialize collections
        db = initialize_collections()
        
        # Check that collections were created
        collection_names = db.list_collection_names()
        assert 'guides' in collection_names
        assert 'users' in collection_names
        assert 'word_lists' in collection_names
        
        # Check indexes on guides collection
        guide_indexes = list(db.guides.list_indexes())
        # Convert indexes to a more easily searchable format
        guide_index_names = [idx.get('name') for idx in guide_indexes]
        assert 'topic_1' in guide_index_names, "Topic index doesn't exist"
        assert 'status_1' in guide_index_names, "Status index doesn't exist"
        
        # Check indexes on users collection
        user_indexes = list(db.users.list_indexes())
        email_index = next((idx for idx in user_indexes if idx.get('name') == 'email_1'), None)
        assert email_index is not None, "Email index doesn't exist"
        assert email_index.get('unique', False) is True, "Email index is not unique"
        
        # Check indexes on word_lists collection
        word_list_indexes = list(db.word_lists.list_indexes())
        word_list_index_names = [idx.get('name') for idx in word_list_indexes]
        assert 'user_id_1' in word_list_index_names, "User ID index doesn't exist"

class TestMongoDBCRUD:
    """Tests for CRUD operations on MongoDB collections"""
    
    def test_guide_crud_operations(self, test_db):
        """Test CRUD operations on the guides collection"""
        # Test CREATE
        guide_data = {
            'topic': 'Python Testing',
            'status': 'research',
            'outline': [],
            'content': '',
            'created_at': '2023-06-01T12:00:00',
            'updated_at': '2023-06-01T12:00:00'
        }
        result = test_db.guides.insert_one(guide_data)
        assert result.inserted_id is not None
        
        # Test READ
        found_guide = test_db.guides.find_one({'topic': 'Python Testing'})
        assert found_guide is not None
        assert found_guide['status'] == 'research'
        
        # Test UPDATE
        result = test_db.guides.update_one(
            {'topic': 'Python Testing'},
            {'$set': {'status': 'outline'}}
        )
        assert result.modified_count == 1
        
        # Check that update was successful
        updated_guide = test_db.guides.find_one({'topic': 'Python Testing'})
        assert updated_guide['status'] == 'outline'
        
        # Test DELETE
        result = test_db.guides.delete_one({'topic': 'Python Testing'})
        assert result.deleted_count == 1
        
        # Verify guide was deleted
        deleted_guide = test_db.guides.find_one({'topic': 'Python Testing'})
        assert deleted_guide is None
    
    def test_user_crud_operations(self, test_db):
        """Test CRUD operations on the users collection"""
        # Test CREATE
        user_data = {
            'email': 'test@example.com',
            'password_hash': 'hashed_password',
            'name': 'Test User',
            'created_at': '2023-06-01T12:00:00',
        }
        result = test_db.users.insert_one(user_data)
        assert result.inserted_id is not None
        
        # Test READ
        found_user = test_db.users.find_one({'email': 'test@example.com'})
        assert found_user is not None
        assert found_user['name'] == 'Test User'
        
        # Test UPDATE
        result = test_db.users.update_one(
            {'email': 'test@example.com'},
            {'$set': {'name': 'Updated Name'}}
        )
        assert result.modified_count == 1
        
        # Check that update was successful
        updated_user = test_db.users.find_one({'email': 'test@example.com'})
        assert updated_user['name'] == 'Updated Name'
        
        # Test DELETE
        result = test_db.users.delete_one({'email': 'test@example.com'})
        assert result.deleted_count == 1
        
        # Verify user was deleted
        deleted_user = test_db.users.find_one({'email': 'test@example.com'})
        assert deleted_user is None
    
    def test_word_lists_crud_operations(self, test_db):
        """Test CRUD operations on the word_lists collection"""
        # Test CREATE
        word_list_data = {
            'user_id': '123456789',
            'name': 'Technical Terms',
            'words': ['Python', 'MongoDB', 'Flask'],
            'created_at': '2023-06-01T12:00:00',
        }
        result = test_db.word_lists.insert_one(word_list_data)
        assert result.inserted_id is not None
        
        # Test READ
        found_list = test_db.word_lists.find_one({'user_id': '123456789'})
        assert found_list is not None
        assert found_list['name'] == 'Technical Terms'
        assert 'MongoDB' in found_list['words']
        
        # Test UPDATE
        result = test_db.word_lists.update_one(
            {'user_id': '123456789'},
            {'$push': {'words': 'pytest'}}
        )
        assert result.modified_count == 1
        
        # Check that update was successful
        updated_list = test_db.word_lists.find_one({'user_id': '123456789'})
        assert 'pytest' in updated_list['words']
        
        # Test DELETE
        result = test_db.word_lists.delete_one({'user_id': '123456789'})
        assert result.deleted_count == 1
        
        # Verify word list was deleted
        deleted_list = test_db.word_lists.find_one({'user_id': '123456789'})
        assert deleted_list is None

class TestMongoDBErrorHandling:
    """Tests for MongoDB error handling and constraints"""
    
    def test_unique_constraint(self, test_db):
        """Test that unique constraint on email works"""
        # Insert first user
        user_data = {
            'email': 'duplicate@example.com',
            'password_hash': 'hashed_password',
            'name': 'Test User',
            'created_at': '2023-06-01T12:00:00',
        }
        test_db.users.insert_one(user_data)
        
        # Attempt to insert duplicate email (should fail because of unique index)
        duplicate_user = {
            'email': 'duplicate@example.com',
            'password_hash': 'different_hash',
            'name': 'Duplicate User',
            'created_at': '2023-06-01T13:00:00',
        }
        
        with pytest.raises(OperationFailure):
            test_db.users.insert_one(duplicate_user)
            
        # Clean up
        test_db.users.delete_one({'email': 'duplicate@example.com'}) 