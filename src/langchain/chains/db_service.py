"""
Database service for MongoDB operations.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from .db_models import ResearchNode, AIResponse, ResearchSession

class DatabaseService:
    """Service for handling MongoDB operations"""
    
    def __init__(self, connection_string: str, database_name: str = "research_db"):
        """Initialize database connection"""
        self.client = MongoClient(connection_string)
        self.db: Database = self.client[database_name]
        self.research_sessions: Collection = self.db.research_sessions
        self.research_nodes: Collection = self.db.research_nodes
        self.ai_responses: Collection = self.db.ai_responses
        
    def create_research_session(self, topic: str) -> str:
        """Create a new research session"""
        session = ResearchSession(topic=topic)
        result = self.research_sessions.insert_one(session.to_dict())
        return str(result.inserted_id)
        
    def get_research_session(self, session_id: str) -> Optional[ResearchSession]:
        """Get a research session by ID"""
        data = self.research_sessions.find_one({"_id": session_id})
        if data:
            return ResearchSession.from_dict(data)
        return None
        
    def update_research_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update a research session"""
        updates["updated_at"] = datetime.utcnow()
        result = self.research_sessions.update_one(
            {"_id": session_id},
            {"$set": updates}
        )
        return result.modified_count > 0
        
    def store_research_results(self, session_id: str, results: Dict[str, Any]) -> bool:
        """Store research results in a session"""
        # Create a research node for the results
        node = ResearchNode(
            topic=results["topic"],
            status="completed",
            summary=results.get("summary", ""),
            key_points=results.get("key_points", []),
            entities=results.get("entities", []),
            subtopics=results.get("subtopics", []),
            timeline=results.get("timeline", []),
            further_research=results.get("further_research", []),
            references=results.get("references", []),
            web_results=results.get("web_results", []),
            ai_responses=results.get("ai_responses", []),
            token_usage=results.get("token_usage", {})
        )
        
        # Store the node
        node_id = self.create_research_node(node)
        
        # Update the session with the node
        return self.update_research_session(session_id, {
            "status": "completed",
            "nodes": [node.to_dict()]
        })
        
    def create_research_node(self, node: ResearchNode) -> str:
        """Create a new research node"""
        result = self.research_nodes.insert_one(node.to_dict())
        return str(result.inserted_id)
        
    def get_research_node(self, node_id: str) -> Optional[ResearchNode]:
        """Get a research node by ID"""
        data = self.research_nodes.find_one({"_id": node_id})
        if data:
            return ResearchNode.from_dict(data)
        return None
        
    def update_research_node(self, node_id: str, updates: Dict[str, Any]) -> bool:
        """Update a research node"""
        updates["updated_at"] = datetime.utcnow()
        result = self.research_nodes.update_one(
            {"_id": node_id},
            {"$set": updates}
        )
        return result.modified_count > 0
        
    def add_ai_response(self, node_id: str, response: AIResponse) -> str:
        """Add an AI response to a research node"""
        response_dict = response.to_dict()
        result = self.ai_responses.insert_one(response_dict)
        response_id = str(result.inserted_id)
        
        # Update the node with the response
        self.research_nodes.update_one(
            {"_id": node_id},
            {
                "$push": {"ai_responses": response_dict},
                "$inc": {"token_usage": response.token_usage}
            }
        )
        
        return response_id
        
    def get_node_responses(self, node_id: str) -> List[AIResponse]:
        """Get all AI responses for a node"""
        node = self.get_research_node(node_id)
        if node and node.ai_responses:
            return [AIResponse.from_dict(response) for response in node.ai_responses]
        return []
        
    def get_child_nodes(self, parent_id: str) -> List[ResearchNode]:
        """Get all child nodes of a parent node"""
        cursor = self.research_nodes.find({"parent_id": parent_id})
        return [ResearchNode.from_dict(node) for node in cursor]
        
    def get_session_nodes(self, session_id: str) -> List[ResearchNode]:
        """Get all nodes in a research session"""
        cursor = self.research_nodes.find({"session_id": session_id})
        return [ResearchNode.from_dict(node) for node in cursor]
        
    def delete_research_session(self, session_id: str) -> bool:
        """Delete a research session and all its nodes"""
        # Delete all nodes in the session
        self.research_nodes.delete_many({"session_id": session_id})
        
        # Delete the session
        result = self.research_sessions.delete_one({"_id": session_id})
        return result.deleted_count > 0
        
    def close(self):
        """Close the database connection"""
        self.client.close() 