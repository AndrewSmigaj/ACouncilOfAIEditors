"""
Tests for research validation logic in the AI Council Guide Creation Website
Task 1.2: Test enhanced input validation logic
"""
import pytest
import json
from src.backend.blueprints.research import validate_topic

class TestTopicValidation:
    """Test cases for topic validation"""
    
    def test_empty_topic(self):
        """Should reject empty topics"""
        assert validate_topic('') is not None
        assert validate_topic(None) is not None
        assert validate_topic('   ') is not None
    
    def test_short_topic(self):
        """Should reject topics with fewer than 3 words"""
        assert validate_topic('Web development') is not None
    
    def test_too_short_chars(self):
        """Should reject topics with fewer than 10 characters"""
        assert validate_topic('A B C') is not None
    
    def test_too_long_topic(self):
        """Should reject topics longer than 100 characters"""
        long_topic = 'This is an extremely long topic that exceeds the maximum limit of one hundred characters and should be rejected by the validation function'
        assert validate_topic(long_topic) is not None
    
    def test_invalid_characters(self):
        """Should reject topics with invalid characters"""
        assert validate_topic('How to use <script> tags in HTML') is not None
        assert validate_topic('Python & JavaScript programming') is not None
    
    def test_long_words(self):
        """Should reject topics with excessively long words"""
        assert validate_topic('How to use supercalifragilisticexpialidocious in conversation') is not None
    
    def test_valid_topics(self):
        """Should accept valid topics"""
        valid_topics = [
            'How to start a podcast',
            'Building a sustainable garden',
            'Advanced techniques for digital photography',
            'Creating a personal financial plan'
        ]
        
        for topic in valid_topics:
            assert validate_topic(topic) is None, f"Topic should be valid: {topic}"

def test_api_validation(client):
    """
    Tests the API endpoint validation
    Note: This test requires a Flask test client fixture
    """
    # Test invalid topic (too short)
    response = client.post(
        '/api/research/', 
        data=json.dumps({'topic': 'Too short'}),
        content_type='application/json'
    )
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    
    # Test valid topic
    response = client.post(
        '/api/research/', 
        data=json.dumps({'topic': 'How to start a podcast'}),
        content_type='application/json'
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'guide_id' in data
    assert data['status'] == 'paused_research' 