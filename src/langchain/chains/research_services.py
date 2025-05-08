"""
Service implementations for the research system.
"""
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import aiohttp
from motor.motor_asyncio import AsyncIOMotorClient
from bson.objectid import ObjectId
from langchain.callbacks.base import AsyncCallbackHandler
from .research_base import (
    SearchService, DatabaseService, LoggingService,
    ResearchResult, ResearchConfig, SearchError, DatabaseError
)
from .ai_council import AICouncil
from src.database.mongodb import get_database

# Configure logging
logger = logging.getLogger(__name__)

class ResearchCallbackHandler(AsyncCallbackHandler):
    """Custom callback handler for research tasks"""
    def __init__(self, logging_service: LoggingService):
        self.logging_service = logging_service
        
    async def on_llm_start(self, *args, **kwargs):
        """Called when LLM starts"""
        await self.logging_service.log_interaction(
            'llm', 'start', kwargs.get('prompt', ''), 'LLM started', 0
        )
        
    async def on_llm_end(self, *args, **kwargs):
        """Called when LLM ends"""
        await self.logging_service.log_interaction(
            'llm', 'end', '', 'LLM completed', kwargs.get('token_usage', 0)
        )
        
    async def on_llm_error(self, error: Exception, *args, **kwargs):
        """Called when LLM errors"""
        await self.logging_service.log_interaction(
            'llm', 'error', '', str(error), 0
        )

class ResearchService:
    """Main research service coordinating AI Council and database operations"""
    def __init__(self, config: ResearchConfig):
        self.council = AICouncil(config)
        self.db_service = MongoDBService(config)
        self.logging_service = LoggingService()
        
    async def research_topic(self, topic: str, guide_id: Optional[str] = None) -> Dict[str, Any]:
        """Conduct research and store results"""
        try:
            # Run research using council
            logger.debug(f"Starting research for topic: {topic}")
            research_results = await self.council.conduct_research(topic)
            
            # Create guide document
            guide_doc = {
                "topic": topic,
                "status": "completed",
                "metadata": {
                    "created": datetime.utcnow(),
                    "updated": datetime.utcnow(),
                    "ais": [name for name, config in self.council.members.items() if config["enabled"]],
                    "depth": await self._get_topic_depth(guide_id)
                },
                "research": research_results,
                "children": []
            }
            
            # Store results
            if guide_id:
                await self.db_service.store_research(guide_doc, guide_id)
                
            # Log completion
            await self.logging_service.log_interaction(
                'research',
                'complete',
                topic,
                'Research completed successfully',
                0
            )
            
            return guide_doc
            
        except Exception as e:
            logger.error(f"Research failed: {str(e)}")
            await self.logging_service.log_interaction(
                'research',
                'error',
                topic,
                str(e),
                0
            )
            raise ResearchError(f"Research failed: {str(e)}")
            
    async def _get_topic_depth(self, guide_id: str) -> int:
        """Get the depth of a topic in the research tree"""
        if not guide_id:
            return 0
            
        depth = 0
        current_id = guide_id
        
        while current_id:
            guide = await self.db_service.guide_collection.find_one({"_id": current_id})
            if not guide or not guide.get("parent_id"):
                break
            current_id = guide["parent_id"]
            depth += 1
            
        return depth

class GoogleSearchService(SearchService):
    """Google Search API implementation"""
    def __init__(self, config: ResearchConfig):
        self.api_key = config.google_search_api_key
        self.engine_id = config.google_search_engine_id
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        
    async def search(self, query: str) -> Dict[str, Any]:
        """Execute Google search"""
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    'key': self.api_key,
                    'cx': self.engine_id,
                    'q': query
                }
                async with session.get(self.base_url, params=params) as response:
                    if response.status != 200:
                        raise SearchError(f"Google Search API error: {response.status}")
                    data = await response.json()
                    return self._process_results(data)
        except Exception as e:
            raise SearchError(f"Google search failed: {str(e)}")
            
    def _process_results(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and structure search results"""
        items = data.get('items', [])
        return {
            'web_results': [
                {
                    'title': item.get('title', ''),
                    'link': item.get('link', ''),
                    'snippet': item.get('snippet', '')
                }
                for item in items
            ]
        }

class MongoDBService(DatabaseService):
    """MongoDB implementation for research storage"""
    def __init__(self, config: ResearchConfig):
        # Create async MongoDB client
        self.client = None
        self.db = None
        self.research_collection = None
        self.guide_collection = None
        self.config = config
        logger.debug("MongoDBService initialized")
        
    async def initialize(self):
        """Initialize MongoDB connection"""
        if self.client is None:
            logger.debug("Initializing MongoDB connection")
            self.client = AsyncIOMotorClient(self.config.mongo_connection)
            # Get database name from connection string
            db_name = self.config.mongo_connection.split('/')[-1].split('?')[0]
            self.db = self.client[db_name]
            self.research_collection = self.db.research
            self.guide_collection = self.db.guides
            logger.debug("MongoDB connection initialized")
            
    async def get_guide(self, guide_id: str) -> Optional[Dict[str, Any]]:
        """Get a guide by ID"""
        try:
            await self.initialize()
            logger.debug(f"Looking up guide in database: {guide_id}")
            guide = await self.guide_collection.find_one({"_id": ObjectId(guide_id)})
            logger.debug(f"Guide lookup result: {guide}")
            return guide
        except Exception as e:
            logger.error(f"Failed to get guide: {str(e)}", exc_info=True)
            raise DatabaseError(f"Failed to get guide: {str(e)}")
            
    async def get_research_results(self, guide_id: str) -> Optional[Dict[str, Any]]:
        """Get research results for a guide"""
        try:
            await self.initialize()
            logger.debug(f"Getting research results for guide: {guide_id}")
            guide = await self.get_guide(guide_id)
            if not guide:
                logger.error(f"Guide not found: {guide_id}")
                return None
                
            logger.debug(f"Found guide with research results: {guide.get('research_results')}")
            return guide.get('research_results')
        except Exception as e:
            logger.error(f"Failed to get research results: {str(e)}", exc_info=True)
            raise DatabaseError(f"Failed to get research results: {str(e)}")
            
    async def store_research(self, research: Dict[str, Any], guide_id: Optional[str] = None) -> str:
        """Store research results"""
        try:
            await self.initialize()
            logger.debug(f"Storing research for guide_id: {guide_id}")
            logger.debug(f"Research data: {json.dumps(research, default=str)}")
            
            # Create guide document
            guide_doc = {
                "topic": research["topic"],
                "status": research.get("status", "completed"),  # Default to completed if not specified
                "metadata": research.get("metadata", {
                    "created": datetime.utcnow(),
                    "updated": datetime.utcnow()
                }),
                "research": research.get("research_results", {}),  # Use research_results if available
                "children": research.get("children", []),
                "updated_at": datetime.utcnow()
            }
            logger.debug(f"Created guide document: {json.dumps(guide_doc, default=str)}")
            
            # Use upsert for guide_id to ensure atomic updates
            if guide_id:
                logger.debug(f"Updating existing guide: {guide_id}")
                result = await self.guide_collection.update_one(
                    {'_id': ObjectId(guide_id)},
                    {'$set': guide_doc},
                    upsert=True
                )
                logger.debug(f"Guide update result: {result.modified_count} documents modified")
                logger.debug(f"Upserted ID: {result.upserted_id}")
                return guide_id
            else:
                logger.debug("Creating new guide document")
                guide_doc["created_at"] = datetime.utcnow()
                result = await self.guide_collection.insert_one(guide_doc)
                logger.debug(f"New guide created with ID: {result.inserted_id}")
                return str(result.inserted_id)
                
        except Exception as e:
            logger.error(f"Failed to store research: {str(e)}", exc_info=True)
            logger.error(f"Research data that failed: {json.dumps(research, default=str)}")
            raise DatabaseError(f"Failed to store research: {str(e)}")
            
    async def get_cached_research(self, topic: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached research results"""
        try:
            await self.initialize()
            logger.debug(f"Looking up cached research for topic: {topic}")
            doc = await self.guide_collection.find_one({
                'topic': {'$regex': topic, '$options': 'i'}
            })
            logger.debug(f"Cached research lookup result: {doc}")
            return doc
        except Exception as e:
            logger.error(f"Failed to retrieve cached research: {str(e)}", exc_info=True)
            raise DatabaseError(f"Failed to retrieve cached research: {str(e)}")
            
    async def update_guide_status(self, guide_id: str, status: str, message: Optional[str] = None):
        """Update guide document status"""
        try:
            await self.initialize()
            update = {
                'status': status,
                'updated_at': datetime.utcnow()
            }
            if message:
                update['status_message'] = message
                
            await self.guide_collection.update_one(
                {'_id': ObjectId(guide_id)},
                {'$set': update}
            )
        except Exception as e:
            raise DatabaseError(f"Failed to update guide status: {str(e)}")
            
    async def close(self):
        """Close the database connection"""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            self.research_collection = None
            self.guide_collection = None
            logger.debug("MongoDB connection closed")

class LoggingService(LoggingService):
    """Logging service implementation"""
    def __init__(self):
        self.logger = logging.getLogger('research')
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
    async def log_interaction(self, service: str, step: str, query: str, response: str, tokens: int):
        """Log service interaction"""
        try:
            log_entry = {
                'timestamp': datetime.utcnow(),
                'service': service,
                'step': step,
                'query': query,
                'response': response,
                'tokens': tokens
            }
            self.logger.info(json.dumps(log_entry))
        except Exception as e:
            self.logger.error(f"Failed to log interaction: {str(e)}")

class GrokDeepSearchService(SearchService):
    """Implementation of Grok DeepSearch service"""
    def __init__(self, config: ResearchConfig):
        self.config = config
        self.session = None
        logger.debug("Initializing GrokDeepSearchService")
        logger.debug(f"Using API key: {self.config.xai_api_key[:5]}...")
    
    async def __aenter__(self):
        logger.debug("Creating aiohttp session for GrokDeepSearchService")
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            logger.debug("Closing aiohttp session for GrokDeepSearchService")
            await self.session.close()
    
    async def search(self, query: str) -> Dict[str, Any]:
        """Execute Grok DeepSearch API request"""
        logger.debug(f"GrokDeepSearchService.search called with query: {query}")
        
        if not self.session:
            logger.error("Session not initialized for GrokDeepSearchService")
            raise SearchError("Session not initialized")
            
        url = "https://api.x.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.xai_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "grok-3",
            "messages": [
                {
                    "role": "user",
                    "content": self._format_query(query)
                }
            ],
            "max_tokens": 3000,
            "temperature": 0.5
        }
        
        logger.debug(f"Making Grok API request to {url}")
        logger.debug(f"Request headers: {json.dumps({k: v[:5] + '...' if k == 'Authorization' else v for k, v in headers.items()}, indent=2)}")
        logger.debug(f"Request payload: {json.dumps(payload, indent=2)}")
        
        try:
            logger.debug("Sending POST request to Grok API")
            async with self.session.post(url, json=payload, headers=headers) as response:
                logger.debug(f"Grok API response status: {response.status}")
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Grok API error response: {error_text}")
                    raise SearchError(f"Grok API error: {response.status} - {error_text}")
                    
                data = await response.json()
                logger.debug(f"Grok API response data: {json.dumps(data, indent=2)}")
                
                if "choices" not in data:
                    logger.error("No choices in Grok API response")
                    raise SearchError("No response from Grok API")
                    
                content = data["choices"][0]["message"]["content"]
                logger.debug(f"Grok API content: {content}")
                
                try:
                    # Extract JSON if wrapped in markdown
                    if "```json" in content:
                        logger.debug("Extracting JSON from markdown code block")
                        content = content.split("```json")[1].split("```")[0]
                    elif "```" in content:
                        logger.debug("Extracting JSON from code block")
                        content = content.split("```")[1].split("```")[0]
                    
                    logger.debug("Parsing Grok API response as JSON")
                    structured_data = json.loads(content)
                    
                    # Validate required fields
                    required_fields = [
                        "summary", "key_points", "entities", "subtopics",
                        "timeline", "further_research", "references"
                    ]
                    
                    for field in required_fields:
                        if field not in structured_data:
                            logger.warning(f"Missing field in Grok response: {field}")
                            structured_data[field] = [] if field != "summary" else ""
                    
                    logger.debug("Successfully parsed and validated Grok API response")
                    logger.debug(f"Structured data: {json.dumps(structured_data, indent=2)}")
                    return structured_data
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse Grok response as JSON: {str(e)}")
                    logger.error(f"Raw content: {content}")
                    raise SearchError("Failed to parse Grok response as JSON")
        except Exception as e:
            logger.error(f"Grok DeepSearch failed: {str(e)}", exc_info=True)
            raise SearchError(f"Grok DeepSearch failed: {str(e)}")
            
    def _format_query(self, query: str) -> str:
        """Format the query for Grok API"""
        return f"""As an AI research assistant, analyze the following topic: {query}

        Provide a comprehensive analysis including:
        1. Summary
        2. Key points
        3. Important entities
        4. Subtopics for further research
        5. Timeline of events
        6. Areas for further research
        7. References
        
        Format your response as a JSON object with these fields.""" 