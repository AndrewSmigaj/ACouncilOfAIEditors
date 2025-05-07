"""
Research Blueprint for AI Council Guide Creation Website
"""
from flask import Blueprint, jsonify, request, current_app
from bson.objectid import ObjectId
import json
import re
import asyncio
from datetime import datetime

# Import the research orchestrator
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from src.langchain.chains.research_chain import research_topic, ResearchOrchestrator
from src.database.mongodb import get_database

# Create blueprint
research_bp = Blueprint('research', __name__)

@research_bp.route('/', methods=['POST'])
def start_research():
    """
    Start the research process for a given topic
    Uses LangChain orchestration with Google Search and Grok DeepSearch
    """
    # Get request data
    data = request.get_json()
    
    if not data or 'topic' not in data:
        return jsonify({"error": "Topic is required"}), 400
    
    topic = data['topic']
    
    # Enhanced validation
    validation_error = validate_topic(topic)
    if validation_error:
        return jsonify({"error": validation_error}), 400
    
    try:
        # Create a new guide document with initial status
        db = get_database()
        guide = {
            "topic": topic,
            "status": "initializing",
            "metadata": {
                "created": datetime.utcnow(),
                "updated": datetime.utcnow(),
                "ais": ["Claude", "ChatGPT", "Gemini", "Grok"]
            },
            "ai_interactions": []
        }
        
        result = db.guides.insert_one(guide)
        guide_id = str(result.inserted_id)
        
        # Start the research process asynchronously
        # We'll use a background task for this in production
        # For now, we'll block the request until it's done for testing purposes
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            research_result = loop.run_until_complete(research_topic(topic, guide_id))
        finally:
            loop.close()
        
        # Return the guide ID and status
        return jsonify({
            "guide_id": guide_id,
            "topic": topic,
            "status": "paused_research",
            "message": "Research completed and paused for approval"
        }), 201
        
    except Exception as e:
        # Log the error
        current_app.logger.error(f"Research error: {str(e)}")
        
        # Return error response
        return jsonify({
            "error": "An error occurred during research",
            "details": str(e)
        }), 500

def validate_topic(topic):
    """
    Validates a topic with enhanced validation rules
    Returns None if valid, or error message if invalid
    """
    # Check if topic is empty or only whitespace
    if not topic or topic.strip() == '':
        return "Topic cannot be empty"
    
    trimmed_topic = topic.strip()
    words = trimmed_topic.split()
    
    # Check if topic is too vague (less than 3 words)
    if len(words) < 3:
        return "Topic too vague, please provide at least 3 words"
    
    # Check if topic is too long (more than 100 characters)
    if len(trimmed_topic) > 100:
        return "Topic too long. Please limit to 100 characters"
    
    # Check if topic contains invalid characters
    valid_chars_regex = r'^[a-zA-Z0-9\s.,?!\'"():-]+$'
    if not re.match(valid_chars_regex, trimmed_topic):
        return "Topic contains invalid characters. Please use only letters, numbers, and basic punctuation"
    
    # Check if topic has at least 10 characters total
    if len(trimmed_topic) < 10:
        return "Topic too short. Please be more specific (at least 10 characters)"
    
    # Check if any word is excessively long
    max_word_length = 30
    for word in words:
        if len(word) > max_word_length:
            return f"Word '{word[:10]}...' is too long. Please use natural language"
    
    # Topic is valid
    return None

@research_bp.route('/<guide_id>', methods=['GET'])
def get_research_results(guide_id):
    """
    Get the current research results for a guide
    """
    try:
        db = get_database()
        guide = db.guides.find_one({"_id": ObjectId(guide_id)})
        
        if not guide:
            return jsonify({"error": "Guide not found"}), 404
        
        # Extract research data
        research_data = guide.get("research", {})
        status = guide.get("status", "unknown")
        
        # Get the AI interactions related to research
        research_interactions = []
        for interaction in guide.get("ai_interactions", []):
            if interaction.get("step") in ["search", "deepsearch"]:
                # Limit the size of the response for API interactions
                if len(interaction.get("response", "")) > 1000:
                    interaction["response"] = interaction["response"][:1000] + "... [truncated]"
                research_interactions.append(interaction)
        
        return jsonify({
            "guide_id": guide_id,
            "topic": guide.get("topic", ""),
            "status": status,
            "research": research_data,
            "interactions": research_interactions,
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@research_bp.route('/<guide_id>/approve', methods=['POST'])
def approve_research(guide_id):
    """
    Approve research results and move to outline stage
    """
    try:
        db = get_database()
        guide = db.guides.find_one({"_id": ObjectId(guide_id)})
        
        if not guide:
            return jsonify({"error": "Guide not found"}), 404
        
        # Check if the guide is in the correct state
        if guide.get("status") != "paused_research":
            return jsonify({
                "error": f"Guide is not in paused_research state, current state: {guide.get('status')}"
            }), 400
        
        # Update the guide status
        db.guides.update_one(
            {"_id": ObjectId(guide_id)},
            {
                "$set": {
                    "status": "paused_outline",
                    "metadata.updated": datetime.utcnow()
                }
            }
        )
        
        # In a future task, we would trigger the outline creation process here
        # For now, we'll just update the status
        
        return jsonify({
            "guide_id": guide_id,
            "status": "paused_outline",
            "message": "Research approved, moving to outline creation"
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@research_bp.route('/<guide_id>/feedback', methods=['POST'])
def add_feedback(guide_id):
    """
    Add feedback for research results
    """
    data = request.get_json()
    
    if not data or 'feedback' not in data:
        return jsonify({"error": "Feedback is required"}), 400
    
    feedback = data['feedback']
    
    try:
        db = get_database()
        guide = db.guides.find_one({"_id": ObjectId(guide_id)})
        
        if not guide:
            return jsonify({"error": "Guide not found"}), 404
        
        # Log the feedback as an interaction
        interaction = {
            "step": "feedback",
            "ai": "User",
            "query": "User feedback on research",
            "response": feedback,
            "token_cost": 0,  # No token cost for user feedback
            "timestamp": datetime.utcnow()
        }
        
        db.guides.update_one(
            {"_id": ObjectId(guide_id)},
            {"$push": {"ai_interactions": interaction}}
        )
        
        return jsonify({
            "guide_id": guide_id,
            "message": "Feedback received successfully"
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@research_bp.route('/shared', methods=['GET'])
def get_shared_research():
    """
    Get shared research from the research collection
    """
    try:
        topic = request.args.get('topic')
        db = get_database()
        
        # Default limit and page
        limit = int(request.args.get('limit', 10))
        page = int(request.args.get('page', 1))
        skip = (page - 1) * limit
        
        # Build the query
        query = {}
        if topic:
            query['topic'] = {'$regex': topic, '$options': 'i'}
        
        # Count total results
        total = db.research.count_documents(query)
        
        # Get paginated results
        results = list(db.research.find(
            query, 
            {'_id': 0}  # Don't include the MongoDB ID in results
        ).sort('timestamp', -1).skip(skip).limit(limit))
        
        return jsonify({
            'total': total,
            'page': page,
            'limit': limit,
            'results': results
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error retrieving shared research: {str(e)}")
        return jsonify({'error': str(e)}), 500

@research_bp.route('/recursive/<guide_id>', methods=['POST'])
def trigger_recursive_research(guide_id):
    """
    Trigger recursive research on subtopics identified in initial research
    """
    try:
        db = get_database()
        guide = db.guides.find_one({"_id": ObjectId(guide_id)})
        
        if not guide:
            return jsonify({"error": "Guide not found"}), 404
        
        # Get the research document
        research = db.research.find_one({"guide_id": guide_id})
        
        if not research:
            return jsonify({"error": "Research not found for this guide"}), 404
            
        if "further_research_topics" not in research or not research["further_research_topics"]:
            return jsonify({"error": "No further research topics identified"}), 400
            
        # Check if recursive research is already in progress
        if research.get("recursive_research_in_progress", False):
            return jsonify({
                "message": "Recursive research is already in progress",
                "further_topics": research["further_research_topics"]
            }), 200
        
        # Mark recursive research as in progress
        db.research.update_one(
            {"_id": research["_id"]},
            {"$set": {"recursive_research_in_progress": True}}
        )
        
        # In a production environment, you would trigger asynchronous research here
        # For now, we'll just return the list of topics
        
        return jsonify({
            "message": "Recursive research triggered",
            "guide_id": guide_id,
            "further_topics": research["further_research_topics"],
            "status": "queued"
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error triggering recursive research: {str(e)}")
        return jsonify({'error': str(e)}), 500
        
@research_bp.route('/structured/<guide_id>', methods=['GET'])
def get_structured_research(guide_id):
    """
    Get the structured JSON research data for a specific guide
    """
    try:
        db = get_database()
        guide = db.guides.find_one({"_id": ObjectId(guide_id)})
        
        if not guide:
            return jsonify({"error": "Guide not found"}), 404
            
        # Check if there's a research document for this guide
        research = db.research.find_one({"guide_id": guide_id})
        
        if research and "structured_data" in research:
            return jsonify({
                "guide_id": guide_id,
                "topic": guide.get("topic", ""),
                "structured_data": research["structured_data"]
            }), 200
            
        # If not found in research collection, check the guide document
        research_data = guide.get("research", {})
        if "structured_data" in research_data:
            return jsonify({
                "guide_id": guide_id,
                "topic": guide.get("topic", ""),
                "structured_data": research_data["structured_data"]
            }), 200
        
        return jsonify({
            "guide_id": guide_id,
            "topic": guide.get("topic", ""),
            "message": "No structured data available",
            "structured_data": {}
        }), 200 
        
    except Exception as e:
        current_app.logger.error(f"Error retrieving structured data: {str(e)}")
        return jsonify({'error': str(e)}), 500 

@research_bp.route('/initialize/<guide_id>', methods=['POST'])
def initialize_research_document(guide_id):
    """
    Initialize a research document in the research collection for a guide
    if it doesn't exist yet
    """
    try:
        data = request.get_json() or {}
        further_research_topics = data.get('further_research_topics', [])
        
        db = get_database()
        guide = db.guides.find_one({"_id": ObjectId(guide_id)})
        
        if not guide:
            return jsonify({"error": "Guide not found"}), 404
        
        # Check if research document already exists
        existing_research = db.research.find_one({"guide_id": guide_id})
        
        if existing_research:
            return jsonify({
                "message": "Research document already exists",
                "guide_id": guide_id
            }), 200
        
        # Create initial research document
        research_doc = {
            "guide_id": guide_id,
            "topic": guide.get("topic", ""),
            "timestamp": datetime.utcnow(),
            "subtopic_research_in_progress": False,
            "further_research_topics": further_research_topics,
            "subtopic_results": [],
            "subtopic_research_progress": {
                "total_topics": 0,
                "completed_topics": 0,
                "percentage": 0,
                "last_updated": datetime.utcnow()
            }
        }
        
        # Insert the new research document
        result = db.research.insert_one(research_doc)
        
        return jsonify({
            "message": "Research document initialized successfully",
            "guide_id": guide_id,
            "research_id": str(result.inserted_id)
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Error initializing research document: {str(e)}")
        return jsonify({"error": str(e)}), 500

@research_bp.route('/subtopics/<guide_id>', methods=['POST'])
def research_selected_subtopics(guide_id):
    """
    Trigger research on selected subtopics
    """
    try:
        data = request.get_json() or {}
        selected_topics = data.get('selected_topics', [])
        
        if not selected_topics:
            return jsonify({"error": "No topics selected"}), 400
            
        db = get_database()
        guide = db.guides.find_one({"_id": ObjectId(guide_id)})
        
        if not guide:
            return jsonify({"error": "Guide not found"}), 404
        
        # Get the research document
        research = db.research.find_one({"guide_id": guide_id})
        
        if not research:
            return jsonify({"error": "Research not found for this guide"}), 404
            
        # Check if subtopic research is already in progress
        if research.get("subtopic_research_in_progress", False):
            # Return current progress
            progress = research.get("subtopic_research_progress", {})
            return jsonify({
                "message": "Subtopic research is already in progress",
                "progress": progress
            }), 200
        
        # Mark subtopic research as in progress and initialize progress
        db.research.update_one(
            {"_id": research["_id"]},
            {
                "$set": {
                    "subtopic_research_in_progress": True,
                    "subtopic_research_progress": {
                        "total_topics": len(selected_topics),
                        "completed_topics": 0,
                        "percentage": 0,
                        "last_updated": datetime.utcnow()
                    }
                }
            }
        )
        
        # Start subtopic research in background
        topic = guide["topic"]
        
        def run_subtopic_research():
            """Run the subtopic research in a background thread with its own event loop"""
            async def start_subtopic_research():
                try:
                    # Create research orchestrator
                    orchestrator = ResearchOrchestrator(topic, guide_id)
                    
                    # Run subtopic research
                    await orchestrator.research_selected_subtopics(selected_topics)
                except Exception as e:
                    current_app.logger.error(f"Error in subtopic research: {str(e)}")
                    # Update status to error
                    db = get_database()
                    db.research.update_one(
                        {"guide_id": guide_id},
                        {
                            "$set": {
                                "subtopic_research_in_progress": False,
                                "subtopic_research_error": str(e)
                            }
                        }
                    )
            
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(start_subtopic_research())
            finally:
                loop.close()
        
        # Start the background thread
        import threading
        thread = threading.Thread(target=run_subtopic_research)
        thread.daemon = True  # Make thread daemon so it exits when main thread exits
        thread.start()
        
        return jsonify({
            "message": "Subtopic research triggered",
            "guide_id": guide_id,
            "selected_topics": len(selected_topics),
            "status": "in_progress"
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error triggering subtopic research: {str(e)}")
        return jsonify({'error': str(e)}), 500

@research_bp.route('/subtopics/<guide_id>/status', methods=['GET'])
def get_subtopic_research_status(guide_id):
    """
    Get the status of subtopic research for a guide
    """
    try:
        db = get_database()
        research = db.research.find_one({"guide_id": guide_id})
        
        if not research:
            return jsonify({"error": "Research not found"}), 404
            
        # Get status and progress
        in_progress = research.get("subtopic_research_in_progress", False)
        progress = research.get("subtopic_research_progress", {})
        error = research.get("subtopic_research_error")
        
        status = "not_started"
        if in_progress:
            status = "in_progress"
        elif error:
            status = "error"
        elif research.get("subtopic_results"):
            status = "completed"
        
        return jsonify({
            "guide_id": guide_id,
            "status": status,
            "progress": progress,
            "error": error,
            "in_progress": in_progress,
            "topics_count": progress.get("total_topics", 0)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting subtopic research status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@research_bp.route('/subtopics/<guide_id>/results', methods=['GET'])
def get_subtopic_research_results(guide_id):
    """
    Get the results of subtopic research for a guide
    """
    try:
        db = get_database()
        research = db.research.find_one({"guide_id": guide_id})
        
        if not research:
            return jsonify({"error": "Research not found"}), 404
            
        # Get subtopic results
        results = research.get("subtopic_results", [])
        
        # Get further research topics (potential future subtopics)
        further_topics = research.get("further_research_topics", [])
        
        # Create a list of already researched topic names
        researched_topics = [r.get("topic") for r in results]
        
        # Filter out topics that have already been researched
        available_topics = [t for t in further_topics if t.get("topic") not in researched_topics]
        
        return jsonify({
            "guide_id": guide_id,
            "subtopic_results": results,
            "available_topics": available_topics,  # Topics that can still be researched
            "in_progress": research.get("subtopic_research_in_progress", False)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting subtopic research results: {str(e)}")
        return jsonify({'error': str(e)}), 500 