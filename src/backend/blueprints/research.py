"""
Research Blueprint for AI Council Guide Creation Website
"""
from quart import Blueprint, jsonify, request, current_app, render_template
from bson.objectid import ObjectId
import json
import re
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Import the research chain
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from src.langchain.chains.research_services import ResearchService
from src.database.mongodb import get_database
from ..models.research import ResearchTopic
from ...langchain.chains.research_base import ResearchResult, ResearchError

# Create blueprint
research_bp = Blueprint('research', __name__)

@research_bp.errorhandler(Exception)
async def handle_error(error):
    """Global error handler for the research blueprint"""
    logger.error(f"Research error: {str(error)}", exc_info=True)
    return jsonify({
        "status": "error",
        "message": str(error)
    }), 500

@research_bp.route('/', methods=['POST'])
async def start_research():
    """
    Start the research process for a given topic
    Uses LangChain orchestration with Google Search and Grok DeepSearch
    """
    logger.debug("Starting research process")
    try:
        # Get request data
        data = await request.get_json()
        logger.debug(f"Received request data: {data}")
        
        if not data or 'topic' not in data:
            logger.error("No topic provided in request")
            return jsonify({
                "status": "error",
                "message": "Topic is required"
            }), 400
        
        topic = data['topic']
        parent_id = data.get('parent_id')
        logger.debug(f"Processing topic: {topic}, parent_id: {parent_id}")
        
        # Enhanced validation
        validation_error = validate_topic(topic)
        if validation_error:
            logger.error(f"Topic validation failed: {validation_error}")
            return jsonify({
                "status": "error",
                "message": validation_error
            }), 400
        
        # Create a new guide document with initial status
        db = get_database()
        guide = {
            "topic": topic,
            "parent_id": parent_id,
            "status": "initializing",
            "metadata": {
                "created": datetime.utcnow(),
                "updated": datetime.utcnow(),
                "ais": ["Claude", "ChatGPT", "Gemini", "Grok"],
                "depth": 0 if not parent_id else await get_topic_depth(db, parent_id) + 1
            },
            "ai_interactions": []
        }
        
        logger.debug(f"Creating new guide document: {json.dumps(guide, default=str)}")
        result = await db.guides.insert_one(guide)
        guide_id = str(result.inserted_id)
        logger.debug(f"Created guide with ID: {guide_id}")
        
        # Initialize research service
        research_service = ResearchService(ResearchConfig.from_config())
        
        # Run research
        logger.debug(f"Starting research for guide_id: {guide_id}")
        research = await research_service.research_topic(topic, guide_id)
        logger.debug(f"Research completed for guide_id: {guide_id}")
        
        # Update guide with research results
        logger.debug(f"Updating guide {guide_id} with research results")
        await db.guides.update_one(
            {"_id": ObjectId(guide_id)},
            {
                "$set": {
                    "status": "completed",
                    "research": research.to_dict(),
                    "metadata.updated": datetime.utcnow()
                }
            }
        )
        logger.debug(f"Guide {guide_id} updated successfully")
        
        return jsonify({
            "status": "success",
            "guide_id": guide_id,
            "research": research.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Research failed: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@research_bp.route('/research', methods=['POST'])
async def initialize_research_document():
    """Initialize a new research document"""
    try:
        data = await request.get_json()
        topic = data.get('topic')
        guide_id = data.get('guide_id')
        parent_id = data.get('parent_id')
        
        if not topic:
            return jsonify({
                'status': 'error',
                'message': 'Topic is required'
            }), 400
            
        # Create research chain
        research_chain = await create_research_chain()
        
        # Run research
        research_results = await research_chain.run(topic, "")
        
        # Create research result
        research = ResearchResult(
            summary=research_results["summary"],
            key_points=research_results["key_points"],
            entities=research_results["entities"],
            subtopics=research_results["subtopics"],
            timeline=research_results["timeline"],
            further_research=research_results["further_research"],
            references=research_results["references"],
            web_results=research_results.get("web_results", [])
        )
        
        # Update parent if exists
        if parent_id:
            db = get_database()
            await db.guides.update_one(
                {"_id": ObjectId(parent_id)},
                {"$push": {"children": guide_id}}
            )
        
        return jsonify({
            'status': 'success',
            'message': 'Research completed successfully',
            'research': research.to_dict()
        })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@research_bp.route('/research/subtopic', methods=['POST'])
async def research_subtopic():
    """Research a subtopic"""
    try:
        data = await request.get_json()
        topic = data.get('topic')
        parent_topic = data.get('parent_topic')
        guide_id = data.get('guide_id')
        
        if not topic or not parent_topic:
            return jsonify({
                'status': 'error',
                'message': 'Topic and parent topic are required'
            }), 400
            
        # Create research chain
        research_chain = await create_research_chain()
        
        # Run research
        research_results = await research_chain.run(topic, "")
        
        # Create research result
        research = ResearchResult(
            summary=research_results["summary"],
            key_points=research_results["key_points"],
            entities=research_results["entities"],
            subtopics=research_results["subtopics"],
            timeline=research_results["timeline"],
            further_research=research_results["further_research"],
            references=research_results["references"],
            web_results=research_results.get("web_results", [])
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Subtopic research completed successfully',
            'research': research.to_dict()
        })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@research_bp.route('/results/<guide_id>', methods=['GET'])
async def get_research_results(guide_id: str):
    """Get research results for a guide"""
    try:
        db = get_database()
        guide = await db.guides.find_one({"_id": ObjectId(guide_id)})
        
        if not guide:
            return jsonify({
                'status': 'error',
                'message': 'Guide not found'
            }), 404
            
        return jsonify({
            'status': 'success',
            'research': guide.get('research', {})
        })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@research_bp.route('/topics/<topic_id>/research', methods=['POST'])
async def start_topic_research(topic_id):
    """Start research for a specific topic"""
    try:
        db = get_database()
        topic = await db.topics.find_one({"_id": ObjectId(topic_id)})
        
        if not topic:
            return jsonify({
                'status': 'error',
                'message': 'Topic not found'
            }), 404
            
        # Start research in background
        asyncio.create_task(run_topic_research(topic_id))
        
        return jsonify({
            'status': 'success',
            'message': 'Research started'
        })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

def validate_topic(topic: str) -> Optional[str]:
    """Validate a research topic"""
    if not topic or len(topic.strip()) == 0:
        return "Topic cannot be empty"
    if len(topic) > 500:
        return "Topic is too long (max 500 characters)"
    return None

async def get_topic_depth(db, parent_id: str) -> int:
    """Get the depth of a topic in the research tree"""
    depth = 0
    current_id = parent_id
    
    while current_id:
        parent = await db.guides.find_one({"_id": ObjectId(current_id)})
        if not parent or not parent.get("parent_id"):
            break
        current_id = parent["parent_id"]
        depth += 1
        
    return depth

async def run_topic_research(topic_id: str):
    """Run research for a topic in the background"""
    try:
        db = get_database()
        topic = await db.topics.find_one({"_id": ObjectId(topic_id)})
        
        if not topic:
            logger.error(f"Topic not found: {topic_id}")
            return
            
        # Initialize research service
        research_service = ResearchService(ResearchConfig.from_config())
        
        # Run research
        research = await research_service.research_topic(topic["name"], topic_id)
        
        # Update topic with research results
        await db.topics.update_one(
            {"_id": ObjectId(topic_id)},
            {
                "$set": {
                    "status": "completed",
                    "research": research.to_dict(),
                    "updated": datetime.utcnow()
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Research failed for topic {topic_id}: {str(e)}", exc_info=True)
        # Update topic with error status
        await db.topics.update_one(
            {"_id": ObjectId(topic_id)},
            {
                "$set": {
                    "status": "error",
                    "error": str(e),
                    "updated": datetime.utcnow()
                }
            }
        )

@research_bp.route('/topics', methods=['POST'])
async def add_topic():
    """Add a new research topic"""
    try:
        data = await request.get_json()
        name = data.get('name')
        parent_id = data.get('parent_id')
        
        if not name:
            return jsonify({
                'status': 'error',
                'message': 'Topic name is required'
            }), 400
            
        # Validate topic
        validation_error = validate_topic(name)
        if validation_error:
            return jsonify({
                'status': 'error',
                'message': validation_error
            }), 400
            
        # Create topic document
        db = get_database()
        topic = {
            "name": name,
            "parent_id": parent_id,
            "status": "pending",
            "created": datetime.utcnow(),
            "updated": datetime.utcnow()
        }
        
        result = await db.topics.insert_one(topic)
        topic_id = str(result.inserted_id)
        
        return jsonify({
            'status': 'success',
            'topic_id': topic_id
        })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@research_bp.route('/topics/<topic_id>', methods=['GET'])
async def get_topic(topic_id):
    """Get a specific topic"""
    try:
        db = get_database()
        topic = await db.topics.find_one({"_id": ObjectId(topic_id)})
        
        if not topic:
            return jsonify({
                'status': 'error',
                'message': 'Topic not found'
            }), 404
            
        return jsonify({
            'status': 'success',
            'topic': topic
        })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@research_bp.route('/topics/tree', methods=['GET'])
async def get_topic_tree():
    """Get the complete topic tree"""
    try:
        db = get_database()
        topics = await db.topics.find().to_list(length=None)
        
        # Build tree structure
        def build_tree(topics, parent_id=None):
            tree = []
            for topic in topics:
                if topic.get('parent_id') == parent_id:
                    node = {
                        'id': str(topic['_id']),
                        'name': topic['name'],
                        'status': topic['status'],
                        'children': build_tree(topics, str(topic['_id']))
                    }
                    tree.append(node)
            return tree
            
        tree = build_tree(topics)
        
        return jsonify({
            'status': 'success',
            'tree': tree
        })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@research_bp.route('/<guide_id>/subtopics', methods=['POST'])
async def research_subtopics(guide_id: str):
    """Research subtopics for a guide"""
    try:
        data = await request.get_json()
        subtopics = data.get('subtopics', [])
        
        if not subtopics:
            return jsonify({
                'status': 'error',
                'message': 'No subtopics provided'
            }), 400
            
        db = get_database()
        guide = await db.guides.find_one({"_id": ObjectId(guide_id)})
        
        if not guide:
            return jsonify({
                'status': 'error',
                'message': 'Guide not found'
            }), 404
            
        # Initialize research service
        research_service = ResearchService(ResearchConfig.from_config())
        
        # Research each subtopic
        results = []
        for subtopic in subtopics:
            try:
                # Create subtopic guide
                subtopic_guide = {
                    "topic": subtopic,
                    "parent_id": guide_id,
                    "status": "initializing",
                    "metadata": {
                        "created": datetime.utcnow(),
                        "updated": datetime.utcnow(),
                        "ais": ["Claude", "ChatGPT", "Gemini", "Grok"],
                        "depth": guide.get("metadata", {}).get("depth", 0) + 1
                    }
                }
                
                result = await db.guides.insert_one(subtopic_guide)
                subtopic_id = str(result.inserted_id)
                
                # Run research
                research = await research_service.research_topic(subtopic, subtopic_id)
                
                # Update guide with research results
                await db.guides.update_one(
                    {"_id": ObjectId(subtopic_id)},
                    {
                        "$set": {
                            "status": "completed",
                            "research": research.to_dict(),
                            "metadata.updated": datetime.utcnow()
                        }
                    }
                )
                
                # Add to parent's children
                await db.guides.update_one(
                    {"_id": ObjectId(guide_id)},
                    {"$push": {"children": subtopic_id}}
                )
                
                results.append({
                    "subtopic": subtopic,
                    "guide_id": subtopic_id,
                    "status": "success"
                })
                
            except Exception as e:
                logger.error(f"Failed to research subtopic {subtopic}: {str(e)}", exc_info=True)
                results.append({
                    "subtopic": subtopic,
                    "status": "error",
                    "error": str(e)
                })
        
        return jsonify({
            'status': 'success',
            'results': results
        })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@research_bp.route('/<guide_id>', methods=['GET'])
async def research_page(guide_id: str):
    """Get the research page for a guide"""
    try:
        db = get_database()
        guide = await db.guides.find_one({"_id": ObjectId(guide_id)})
        
        if not guide:
            return jsonify({
                'status': 'error',
                'message': 'Guide not found'
            }), 404
            
        # Get all children recursively
        async def get_children(parent_id):
            children = []
            cursor = db.guides.find({"parent_id": parent_id})
            async for child in cursor:
                child['children'] = await get_children(str(child['_id']))
                children.append(child)
            return children
            
        guide['children'] = await get_children(guide_id)
        
        return jsonify({
            'status': 'success',
            'guide': guide
        })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

async def run_guide_research(guide_id: str):
    """Run research for a guide in the background"""
    try:
        db = get_database()
        guide = await db.guides.find_one({"_id": ObjectId(guide_id)})
        
        if not guide:
            logger.error(f"Guide not found: {guide_id}")
            return
            
        # Initialize research service
        research_service = ResearchService(ResearchConfig.from_config())
        
        # Run research
        research = await research_service.research_topic(guide["topic"], guide_id)
        
        # Update guide with research results
        await db.guides.update_one(
            {"_id": ObjectId(guide_id)},
            {
                "$set": {
                    "status": "completed",
                    "research": research.to_dict(),
                    "metadata.updated": datetime.utcnow()
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Research failed for guide {guide_id}: {str(e)}", exc_info=True)
        # Update guide with error status
        await db.guides.update_one(
            {"_id": ObjectId(guide_id)},
            {
                "$set": {
                    "status": "error",
                    "error": str(e),
                    "metadata.updated": datetime.utcnow()
                }
            }
        ) 