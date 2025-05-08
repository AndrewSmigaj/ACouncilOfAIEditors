"""
Database models for the research system.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from bson import ObjectId

@dataclass
class ResearchNode:
    """A node in the research tree"""
    topic: str
    parent_id: Optional[str] = None
    status: str = "initializing"
    summary: str = ""
    key_points: List[str] = None
    entities: List[Dict[str, str]] = None
    subtopics: List[Dict[str, str]] = None
    timeline: List[Dict[str, str]] = None
    further_research: List[Dict[str, str]] = None
    references: List[Dict[str, str]] = None
    web_results: List[Dict[str, str]] = None
    ai_responses: List[Dict[str, Any]] = None
    token_usage: Dict[str, int] = None
    created_at: datetime = None
    updated_at: datetime = None
    _id: Optional[str] = None
    
    def __post_init__(self):
        """Initialize default values"""
        if self.key_points is None:
            self.key_points = []
        if self.entities is None:
            self.entities = []
        if self.subtopics is None:
            self.subtopics = []
        if self.timeline is None:
            self.timeline = []
        if self.further_research is None:
            self.further_research = []
        if self.references is None:
            self.references = []
        if self.web_results is None:
            self.web_results = []
        if self.ai_responses is None:
            self.ai_responses = []
        if self.token_usage is None:
            self.token_usage = {}
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        data = asdict(self)
        # Remove _id if it's None to let MongoDB generate one
        if self._id is None:
            data.pop('_id', None)
        else:
            data['_id'] = ObjectId(self._id)
        return data
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResearchNode':
        """Create from dictionary format"""
        if '_id' in data:
            data['_id'] = str(data['_id'])
        return cls(**data)
        
@dataclass
class AIResponse:
    """Response from an AI in the council"""
    ai_name: str
    role: str
    prompt: str
    response: str
    token_usage: Dict[str, int]
    timestamp: datetime = None
    
    def __post_init__(self):
        """Initialize default values"""
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return asdict(self)
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AIResponse':
        """Create from dictionary format"""
        return cls(**data)
        
@dataclass
class ResearchSession:
    """A research session with multiple nodes"""
    topic: str
    status: str = "initializing"
    nodes: List[ResearchNode] = None
    created_at: datetime = None
    updated_at: datetime = None
    _id: Optional[str] = None
    
    def __post_init__(self):
        """Initialize default values"""
        if self.nodes is None:
            self.nodes = []
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        data = asdict(self)
        # Remove _id if it's None to let MongoDB generate one
        if self._id is None:
            data.pop('_id', None)
        else:
            data['_id'] = ObjectId(self._id)
        data['nodes'] = [node.to_dict() for node in self.nodes]
        return data
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResearchSession':
        """Create from dictionary format"""
        if '_id' in data:
            data['_id'] = str(data['_id'])
        if 'nodes' in data:
            data['nodes'] = [ResearchNode.from_dict(node) for node in data['nodes']]
        return cls(**data) 