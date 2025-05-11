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
from src.backend.models.research import Node

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
            
            # Create root nodes for each enabled AI
            root_nodes = {}
            for ai_name, result in research_results["research_results"].items():
                # Create a node for this AI's research
                root_nodes[ai_name] = Node(
                    topic=topic,
                    status="completed",
                    research=result  # Direct mapping from AI results
                ).to_dict()
            
            # Create guide document with trees
            guide_doc = {
                "topic": topic,
                "status": "completed",
                "metadata": {
                    "created": datetime.utcnow(),
                    "updated": datetime.utcnow(),
                    "ais": [name for name, config in self.council.members.items() if config["enabled"]],
                    "depth": await self._get_topic_depth(guide_id)
                },
                "trees": root_nodes
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
            
            return {
                "topic": topic,
                "trees": root_nodes
            }
            
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
            
    async def research_subtopic(self, topic: str, ai: str, guide_id: str, parent_node_id: str) -> Dict[str, Any]:
        """Conduct research for a subtopic with a specific AI"""
        try:
            # Enable only the specified AI
            for member_name in self.council.members:
                self.council.members[member_name]["enabled"] = (member_name == ai)
            
            # Run research with just this AI
            logger.debug(f"Starting subtopic research for topic: {topic} with AI: {ai}")
            research_results = await self.council.conduct_research(topic)
            
            # Get the result for this AI
            ai_result = research_results["research_results"].get(ai, {})
            logger.debug(f"Got research result for AI {ai}: {json.dumps(ai_result, default=str)}")
            
            # Create a node for this research
            new_node = Node(
                topic=topic,
                status="completed",
                research=ai_result
            )
            
            return new_node.to_dict()
            
        except Exception as e:
            logger.error(f"Subtopic research failed: {str(e)}")
            await self.logging_service.log_interaction(
                'research',
                'error',
                topic,
                str(e),
                0
            )
            raise ResearchError(f"Subtopic research failed: {str(e)}")
    
    async def _get_topic_depth(self, parent_id: Optional[str]) -> int:
        """Get the depth of a topic based on its parent"""
        if not parent_id:
            return 0
            
        try:
            guide = await self.db_service.get_guide(parent_id)
            if not guide:
                return 0
                
            return guide.get("metadata", {}).get("depth", 0) + 1
        except Exception as e:
            logger.error(f"Failed to get topic depth: {str(e)}")
            return 0

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
                
            # Return the guide with trees structure
            return {
                "status": guide.get("status", "completed"),
                "trees": guide.get("trees", {})
            }
        except Exception as e:
            logger.error(f"Failed to get research results: {str(e)}", exc_info=True)
            raise DatabaseError(f"Failed to get research results: {str(e)}")
            
    async def store_research(self, research: Dict[str, Any], guide_id: Optional[str] = None) -> str:
        """Store research results"""
        try:
            await self.initialize()
            logger.debug(f"Storing research for guide_id: {guide_id}")
            logger.debug(f"Research data: {json.dumps(research, default=str)}")
            
            # Create a clean guide document
            guide_doc = {
                "topic": research["topic"],
                "status": research.get("status", "completed"),
                "metadata": research.get("metadata", {
                    "created": datetime.utcnow(),
                    "updated": datetime.utcnow()
                }),
                "updated_at": datetime.utcnow()
            }
            
            # Include trees directly
            if "trees" in research:
                guide_doc["trees"] = research["trees"]
                logger.debug(f"Included trees structure: {json.dumps(guide_doc['trees'], default=str)}")
            
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
            
    async def add_subtopic_node(self, guide_id: str, ai: str, parent_node_id: str, new_node: Dict[str, Any]) -> bool:
        """Add a subtopic node to a specific AI's research tree"""
        try:
            await self.initialize()
            logger.debug(f"[DEBUG MongoDBService] Adding subtopic node to guide {guide_id}, AI {ai}, parent {parent_node_id}")
            logger.debug(f"[DEBUG MongoDBService] New node data: {json.dumps(new_node, default=str)}")
            
            # Update the guide document to add the new node as a child of the specified parent
            logger.debug(f"[DEBUG MongoDBService] Attempting direct update at root level")
            
            # Log the current structure
            current_guide = await self.get_guide(guide_id)
            if current_guide:
                has_trees = "trees" in current_guide
                has_ai = has_trees and ai in current_guide.get("trees", {})
                logger.debug(f"[DEBUG MongoDBService] Current guide has trees: {has_trees}, has AI '{ai}': {has_ai}")
                
                if has_ai:
                    root_node_id = current_guide["trees"][ai].get("node_id")
                    logger.debug(f"[DEBUG MongoDBService] AI '{ai}' root node ID: {root_node_id}")
                    logger.debug(f"[DEBUG MongoDBService] Looking for parent node ID: {parent_node_id}")
                    
                    # Check if the root node is the parent
                    if root_node_id == parent_node_id:
                        logger.debug(f"[DEBUG MongoDBService] Parent node is the root node")
            
            # First attempt: Try updating at root level
            result = await self.guide_collection.update_one(
                {"_id": ObjectId(guide_id), f"trees.{ai}.node_id": parent_node_id},
                {"$push": {f"trees.{ai}.children": new_node}}
            )
            
            logger.debug(f"[DEBUG MongoDBService] Direct update result - matched: {result.matched_count}, modified: {result.modified_count}")
            
            if result.modified_count == 0:
                # Try to find the parent node deeper in the tree
                # This requires a more complex update using the aggregation pipeline
                logger.debug("[DEBUG MongoDBService] Parent node not found at root level, searching deeper in tree")
                
                # Get the current guide document
                guide = await self.get_guide(guide_id)
                if not guide or "trees" not in guide or ai not in guide["trees"]:
                    logger.error(f"[DEBUG MongoDBService] Could not find guide, trees, or AI '{ai}' in guide")
                    return False
                
                logger.debug(f"[DEBUG MongoDBService] Retrieved guide document, has trees for AI '{ai}': {ai in guide.get('trees', {})}")
                
                # Manually traverse the tree to find the parent node
                found = False
                async def traverse_and_update(node, path):
                    nonlocal found
                    if found:
                        return
                        
                    logger.debug(f"[DEBUG MongoDBService] Checking node: {node.get('node_id')} at path {path}")
                        
                    if node.get("node_id") == parent_node_id:
                        # Found the parent node, update it
                        logger.debug(f"[DEBUG MongoDBService] Found parent node at path {path}")
                        
                        if "children" not in node:
                            logger.debug(f"[DEBUG MongoDBService] Parent node has no children array, creating one")
                            node["children"] = []
                            
                        node["children"].append(new_node)
                        logger.debug(f"[DEBUG MongoDBService] Added new node to parent's children, new count: {len(node['children'])}")
                        
                        # Update the entire tree in the database
                        update_result = await self.guide_collection.update_one(
                            {"_id": ObjectId(guide_id)},
                            {"$set": {f"trees.{ai}": guide["trees"][ai]}}
                        )
                        found = update_result.modified_count > 0
                        logger.debug(f"[DEBUG MongoDBService] Updated entire tree - matched: {update_result.matched_count}, modified: {update_result.modified_count}")
                        return
                    
                    # Recursively search children
                    if "children" in node:
                        logger.debug(f"[DEBUG MongoDBService] Node has {len(node['children'])} children, searching recursively")
                        for i, child in enumerate(node["children"]):
                            await traverse_and_update(child, path + f".children.{i}")
                    else:
                        logger.debug(f"[DEBUG MongoDBService] Node has no children, skipping")
                
                # Start traversal from the root node of this AI's tree
                logger.debug(f"[DEBUG MongoDBService] Starting recursive traversal from root node")
                await traverse_and_update(guide["trees"][ai], f"trees.{ai}")
                
                if found:
                    logger.debug(f"[DEBUG MongoDBService] Successfully added node via recursive traversal")
                else:
                    logger.error(f"[DEBUG MongoDBService] Could not find parent node {parent_node_id} in the tree for AI {ai}")
                
                return found
            
            logger.debug(f"[DEBUG MongoDBService] Successfully added node at root level")
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"[DEBUG MongoDBService] Failed to add subtopic node: {str(e)}", exc_info=True)
            raise DatabaseError(f"Failed to add subtopic node: {str(e)}")
            
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