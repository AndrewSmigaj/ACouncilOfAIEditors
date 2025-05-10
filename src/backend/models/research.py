from datetime import datetime
from bson import ObjectId
import uuid
from typing import Optional, List, Dict, Any

class ResearchTopic:
    def __init__(
        self,
        topic: str,
        parent_id: Optional[str] = None,
        is_user_added: bool = False,
        context: Optional[Dict[str, Any]] = None,
        depth: int = 0
    ):
        self.topic = topic
        self.parent_id = parent_id
        self.is_user_added = is_user_added
        self.context = context or {}
        self.depth = depth
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.research_results = None
        self.status = 'pending'  # pending, in_progress, completed, error
        self.children: List[str] = []  # List of child topic IDs
        self.metadata = {
            'last_research_attempt': None,
            'research_attempts': 0,
            'error_count': 0,
            'success_count': 0
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            'topic': self.topic,
            'parent_id': self.parent_id,
            'is_user_added': self.is_user_added,
            'context': self.context,
            'depth': self.depth,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'research_results': self.research_results,
            'status': self.status,
            'children': self.children,
            'metadata': self.metadata
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'ResearchTopic':
        topic = ResearchTopic(
            topic=data['topic'],
            parent_id=data.get('parent_id'),
            is_user_added=data.get('is_user_added', False),
            context=data.get('context'),
            depth=data.get('depth', 0)
        )
        topic.created_at = data.get('created_at', datetime.utcnow())
        topic.updated_at = data.get('updated_at', datetime.utcnow())
        topic.research_results = data.get('research_results')
        topic.status = data.get('status', 'pending')
        topic.children = data.get('children', [])
        topic.metadata = data.get('metadata', {
            'last_research_attempt': None,
            'research_attempts': 0,
            'error_count': 0,
            'success_count': 0
        })
        return topic

    def add_child(self, child_id: str) -> None:
        """Add a child topic ID"""
        if child_id not in self.children:
            self.children.append(child_id)
            self.updated_at = datetime.utcnow()

    def remove_child(self, child_id: str) -> None:
        """Remove a child topic ID"""
        if child_id in self.children:
            self.children.remove(child_id)
            self.updated_at = datetime.utcnow()

    def update_status(self, status: str) -> None:
        """Update the research status"""
        self.status = status
        self.updated_at = datetime.utcnow()
        self.metadata['last_research_attempt'] = datetime.utcnow()
        self.metadata['research_attempts'] += 1

    def record_error(self) -> None:
        """Record a research error"""
        self.metadata['error_count'] += 1
        self.updated_at = datetime.utcnow()

    def record_success(self) -> None:
        """Record a successful research"""
        self.metadata['success_count'] += 1
        self.updated_at = datetime.utcnow()

class Node:
    """
    Node in a research tree following the new tree structure.
    Each node represents a research topic with associated AI research results.
    """
    def __init__(
        self,
        topic: str,
        node_id: Optional[str] = None,
        status: str = "initializing",
        research: Optional[Dict[str, Any]] = None,
        children: Optional[List['Node']] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.topic = topic
        self.node_id = node_id if node_id else uuid.uuid4().hex
        self.status = status
        self.research = research or {}
        self.children = children or []
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Node to dictionary for MongoDB storage"""
        return {
            "node_id": self.node_id,
            "topic": self.topic,
            "status": self.status,
            "research": self.research,
            "children": [child.to_dict() for child in self.children],
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Node':
        """Create Node from dictionary"""
        if not data:
            return None
            
        return Node(
            topic=data["topic"],
            node_id=data.get("node_id"),
            status=data.get("status", "initializing"),
            research=data.get("research", {}),
            children=[Node.from_dict(child) for child in data.get("children", [])],
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )
    
    def add_child(self, child: 'Node') -> None:
        """Add a child node"""
        self.children.append(child)
        self.updated_at = datetime.utcnow()
    
    def find_node_by_id(self, node_id: str) -> Optional['Node']:
        """Find a node by ID in this tree (recursive search)"""
        if self.node_id == node_id:
            return self
            
        for child in self.children:
            found = child.find_node_by_id(node_id)
            if found:
                return found
                
        return None 