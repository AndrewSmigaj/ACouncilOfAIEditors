"""
Test script for the Research Orchestrator
"""
import asyncio
import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.langchain.chains.research_chain import ResearchOrchestrator, research_topic

class TestResearchOrchestrator(unittest.TestCase):
    """Test cases for the Research Orchestrator"""
    
    def setUp(self):
        """Set up test environment"""
        # Mock the MongoDB database
        self.db_patcher = patch('src.langchain.chains.research_chain.get_database')
        self.mock_db = self.db_patcher.start()
        
        # Create a mock database with guides collection
        self.mock_collection = MagicMock()
        self.mock_db.return_value = MagicMock()
        self.mock_db.return_value.guides = self.mock_collection
        
        # Mock the insert_one and update_one methods
        self.mock_collection.insert_one.return_value = MagicMock()
        self.mock_collection.insert_one.return_value.inserted_id = "mock_guide_id"
        self.mock_collection.update_one.return_value = MagicMock()
        self.mock_collection.find_one.return_value = None
        
    def tearDown(self):
        """Clean up after tests"""
        self.db_patcher.stop()
        
    @patch('src.langchain.chains.research_chain.ResearchOrchestrator._run_google_search')
    @patch('src.langchain.chains.research_chain.ResearchOrchestrator._run_grok_deepsearch')
    async def test_run_research(self, mock_grok, mock_google):
        """Test the run_research method"""
        # Configure mocks to complete successfully
        mock_google.return_value = None
        mock_grok.return_value = None
        
        # Create an instance of the orchestrator
        orchestrator = ResearchOrchestrator("Test topic for AI guide creation")
        
        # Mock the _combine_research_results method
        orchestrator._combine_research_results = MagicMock()
        orchestrator._update_guide_with_research = MagicMock()
        
        # Mock results
        orchestrator.results["combined_research"] = {
            "summary": "This is a test summary",
            "sources": []
        }
        
        # Run the research
        result = await orchestrator.run_research()
        
        # Verify results
        self.assertEqual(result["status"], "paused_research")
        self.assertEqual(result["guide_id"], "mock_guide_id")
        self.assertIn("research_summary", result)
        
        # Verify the correct methods were called
        mock_google.assert_called_once()
        mock_grok.assert_called_once()
        orchestrator._combine_research_results.assert_called_once()
        orchestrator._update_guide_with_research.assert_called_once()
        
    @patch('aiohttp.ClientSession.get')
    async def test_google_search(self, mock_get):
        """Test the Google Search method"""
        # Configure mock response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = MagicMock()
        mock_response.json.return_value = {
            "items": [
                {
                    "title": "Test Result 1",
                    "link": "https://example.com/1",
                    "snippet": "This is a test snippet 1"
                },
                {
                    "title": "Test Result 2",
                    "link": "https://example.com/2",
                    "snippet": "This is a test snippet 2"
                }
            ]
        }
        mock_get.return_value.__aenter__.return_value = mock_response
        
        # Create an instance of the orchestrator
        orchestrator = ResearchOrchestrator("Test topic")
        orchestrator._log_interaction = MagicMock()
        
        # Run the Google Search
        await orchestrator._run_google_search()
        
        # Verify results
        self.assertIsNotNone(orchestrator.results["google_search"])
        self.assertEqual(len(orchestrator.results["google_search"]["processed_results"]), 2)
        orchestrator._log_interaction.assert_called_once()
        
    @patch('aiohttp.ClientSession.post')
    async def test_grok_deepsearch(self, mock_post):
        """Test the Grok DeepSearch method"""
        # Configure mock response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "This is a test deep search result"
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 50,
                "completion_tokens": 100
            }
        }
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # Create an instance of the orchestrator
        orchestrator = ResearchOrchestrator("Test topic")
        orchestrator._log_interaction = MagicMock()
        
        # Run the Grok DeepSearch
        await orchestrator._run_grok_deepsearch()
        
        # Verify results
        self.assertIsNotNone(orchestrator.results["grok_deepsearch"])
        self.assertEqual(orchestrator.results["grok_deepsearch"]["content"], "This is a test deep search result")
        orchestrator._log_interaction.assert_called_once()
        
    def test_combine_research_results(self):
        """Test the combine_research_results method"""
        # Create an instance of the orchestrator
        orchestrator = ResearchOrchestrator("Test topic")
        
        # Set up test results
        orchestrator.results["google_search"] = {
            "processed_results": [
                {
                    "title": "Test Result 1",
                    "link": "https://example.com/1",
                    "snippet": "This is a test snippet 1",
                    "source": "Google Search"
                },
                {
                    "title": "Test Result 2",
                    "link": "https://example.com/2",
                    "snippet": "This is a test snippet 2",
                    "source": "Google Search"
                }
            ]
        }
        
        orchestrator.results["grok_deepsearch"] = {
            "content": "This is a test deep search result"
        }
        
        # Combine the results
        orchestrator._combine_research_results()
        
        # Verify results
        self.assertIsNotNone(orchestrator.results["combined_research"])
        self.assertIn("summary", orchestrator.results["combined_research"])
        self.assertIn("sources", orchestrator.results["combined_research"])
        self.assertEqual(len(orchestrator.results["combined_research"]["sources"]), 3)  # 2 Google + 1 Grok


# Run the tests if executed directly
if __name__ == '__main__':
    # Set up asyncio event loop for the tests
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(unittest.main(exit=False))
    loop.close() 