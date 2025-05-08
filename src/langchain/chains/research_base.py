"""
Base classes and interfaces for the research system.
"""
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Protocol
from dataclasses import dataclass
from flask import Flask

# Custom Exceptions
class ResearchError(Exception): 
    """Base exception for research-related errors"""
    pass

class SearchError(ResearchError): 
    """Exception for search-related errors"""
    pass

class DatabaseError(ResearchError): 
    """Exception for database-related errors"""
    pass

class ValidationError(ResearchError): 
    """Exception for validation-related errors"""
    pass

# Data Models
@dataclass
class ResearchConfig:
    """Configuration for research services"""
    openai_api_key: str
    anthropic_api_key: str
    google_api_key: str  # This is for Gemini
    xai_api_key: str
    google_search_api_key: str  # This is for Google Search
    google_search_engine_id: str
    mongo_connection: str
    research_timeout: int = 300  # 5 minutes default timeout
    max_retries: int = 3  # Maximum number of retries for failed requests
    retry_delay: int = 2  # Base delay between retries in seconds
    
    @classmethod
    def from_config(cls, app: Flask) -> 'ResearchConfig':
        """Create config from Flask config"""
        return cls(
            openai_api_key=app.config.get("OPENAI_API_KEY", ""),
            anthropic_api_key=app.config.get("ANTHROPIC_API_KEY", ""),
            google_api_key=app.config.get("GEMINI_API_KEY", ""),  # For Gemini AI
            xai_api_key=app.config.get("XAI_API_KEY", ""),
            google_search_api_key=app.config.get("GOOGLE_SEARCH_API_KEY", ""),  # For Google Search
            google_search_engine_id=app.config.get("GOOGLE_SEARCH_ENGINE_ID", ""),
            mongo_connection=app.config.get("MONGODB_URI", "mongodb://localhost:27017"),
            research_timeout=int(app.config.get('RESEARCH_TIMEOUT', '300')),
            max_retries=int(app.config.get('MAX_RETRIES', '3')),
            retry_delay=int(app.config.get('RETRY_DELAY', '2'))
        )

@dataclass
class ResearchResult:
    """Structured research results"""
    summary: str
    key_points: List[str]
    entities: List[Dict[str, str]]
    subtopics: List[Dict[str, str]]
    timeline: List[Dict[str, str]]
    further_research: List[Dict[str, str]]
    references: List[Dict[str, str]]
    web_results: List[Dict[str, str]]
    timestamp: datetime = datetime.utcnow()
    
    def validate(self) -> None:
        """Validate the research result structure"""
        if not self.summary:
            raise ValidationError("Summary is required")
        if not isinstance(self.key_points, list):
            raise ValidationError("Key points must be a list")
        if not isinstance(self.entities, list):
            raise ValidationError("Entities must be a list")
        if not isinstance(self.subtopics, list):
            raise ValidationError("Subtopics must be a list")
        if not isinstance(self.timeline, list):
            raise ValidationError("Timeline must be a list")
        if not isinstance(self.further_research, list):
            raise ValidationError("Further research must be a list")
        if not isinstance(self.references, list):
            raise ValidationError("References must be a list")
        if not isinstance(self.web_results, list):
            raise ValidationError("Web results must be a list")
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert research result to dictionary format"""
        return {
            "summary": self.summary,
            "key_points": self.key_points,
            "entities": self.entities,
            "subtopics": self.subtopics,
            "timeline": self.timeline,
            "further_research": self.further_research,
            "references": self.references,
            "web_results": self.web_results,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

# Service Interfaces
class SearchService(Protocol):
    """Interface for search services"""
    async def search(self, query: str) -> Dict[str, Any]: ...

class DatabaseService(Protocol):
    """Interface for database services"""
    async def get_guide(self, guide_id: str) -> Optional[Dict[str, Any]]: ...
    async def get_research_results(self, guide_id: str) -> Optional[Dict[str, Any]]: ...
    async def store_research(self, research: Dict[str, Any], guide_id: Optional[str] = None) -> str: ...
    async def get_cached_research(self, topic: str) -> Optional[Dict[str, Any]]: ...
    async def update_guide_status(self, guide_id: str, status: str, message: Optional[str] = None): ...

class LoggingService(Protocol):
    """Interface for logging services"""
    async def log_interaction(self, service: str, step: str, query: str, response: str, tokens: int): ... 