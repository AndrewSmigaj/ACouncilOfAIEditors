"""
Quart application for the AI Council research system.
"""
from quart import Quart, request, jsonify, render_template, send_from_directory
from datetime import datetime
import os
from typing import Dict, Any
from quart_cors import cors
from config import Config as AppCustomConfig # Your custom config class from src/config.py
import logging # Ensure logging is imported if logger is used
from pathlib import Path

from src.langchain.chains.ai_council import AICouncil, AICouncilMember
from src.langchain.chains.research_services import MongoDBService
from src.langchain.chains.research_base import ResearchConfig
from src.backend.blueprints.research import research_bp

# No need to set Quart.config_class as we're monkey-patching Quart's Config class directly
# in config.py before any Quart app is instantiated

def create_app():
    print("[DEBUG app.py] create_app called.")
    src_dir = Path(__file__).parent
    
    print("[DEBUG app.py] About to instantiate Quart app.")
    app = Quart(__name__,
                static_folder=src_dir / 'frontend' / 'static',
                template_folder=src_dir / 'frontend' / 'templates')
    print("[DEBUG app.py] Quart app instantiated.")
    
    # Load our custom config
    app.config.from_object(AppCustomConfig())
    print(f"[DEBUG app.py] Custom config loaded, PROVIDE_AUTOMATIC_OPTIONS: {app.config.get('PROVIDE_AUTOMATIC_OPTIONS')}")
    
    cors(app, 
     allow_origin="*", 
     allow_methods=["GET", "POST", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"],
     expose_headers=["Content-Type", "Authorization"],
     max_age=3600,
     send_origin_wildcard=True)
    print("[DEBUG app.py] CORS configured.")

    # Initialize service infrastructure
    research_config_instance = ResearchConfig.from_config()
    db_service = MongoDBService(research_config_instance) 
    council = AICouncil(research_config_instance)
    council.enable_member("grok")
    logger = logging.getLogger(__name__)
    print("[DEBUG app.py] Services initialized.")

    app.register_blueprint(research_bp, url_prefix='/api')
    print("[DEBUG app.py] Blueprint registered.")

    @app.route("/")
    async def index():
        return await render_template("index.html")

    @app.route("/research")
    async def research():
        """Serve the research page"""
        return await render_template("research.html")

    @app.route("/guide/<guide_id>/research")
    async def get_guide_research(guide_id: str):
        """Get research results for a guide"""
        logger.debug(f"Attempting to get research for guide_id: {guide_id}")
        
        try:
            # Check if guide exists
            logger.debug(f"Looking up guide in guides collection: {guide_id}")
            guide = await db_service.get_guide(guide_id)
            
            if not guide:
                logger.error(f"Guide not found in guides collection: {guide_id}")
                return "Guide not found", 404
            
            # Render the template with guide_id
            logger.debug(f"Rendering research.html template for guide_id: {guide_id}")
            return await render_template("research.html", guide_id=guide_id)
            
        except Exception as e:
            logger.error(f"Error getting guide research: {str(e)}", exc_info=True)
            return f"Error: {str(e)}", 500

    @app.route("/api/research", methods=["POST"])
    async def create_research():
        """Create a new research session and start research"""
        logger.debug("Received request to create new research")
        data = await request.get_json()
        logger.debug(f"Request data: {data}")
        
        if not data or "topic" not in data:
            logger.error("No topic provided in request")
            return jsonify({"error": "Topic is required"}), 400
            
        # Create session in database
        logger.debug(f"Creating research session for topic: {data['topic']}")
        session_id = await db_service.store_research({
            "topic": data['topic'],
            "status": "initializing",
            "metadata": {
                "created": datetime.utcnow(),
                "updated": datetime.utcnow()
            },
            "research": {},
            "children": []
        })
        logger.debug(f"Created session with ID: {session_id}")
        
        # Start research
        logger.debug(f"Starting research for session {session_id}")
        research_results_obj = await council.conduct_research(data["topic"], session_id=session_id)
        logger.debug(f"Research completed for session {session_id}")
        
        # Store research results
        logger.debug(f"Storing research results for session {session_id}")
        # Assuming conduct_research returns an object that can be converted to dict or is already a dict
        await db_service.store_research(research_results_obj.to_dict() if hasattr(research_results_obj, 'to_dict') else research_results_obj, session_id)
        logger.debug(f"Research results stored for session {session_id}")
        
        return jsonify({"guide_id": session_id})

    @app.route("/api/research/results/<guide_id>", methods=["GET"])
    async def get_research_results_api(guide_id: str): # Renamed to avoid conflict with other get_research_results
        """Get research results for a guide via API"""
        try:
            # Get guide data
            logger.debug(f"Getting guide data for guide_id: {guide_id}")
            guide = await db_service.get_guide(guide_id)
            if not guide:
                logger.error(f"Guide not found: {guide_id}")
                return jsonify({"error": "Guide not found"}), 404
                
            # Get research results
            logger.debug(f"Getting research results for guide_id: {guide_id}")
            results = await db_service.get_research_results(guide_id)
            if not results:
                logger.debug(f"No research results found for guide_id: {guide_id}, returning initializing state")
                return jsonify({
                    "status": "initializing",
                    "topic": guide["topic"],
                    "trees": {}
                })
                
            logger.debug(f"Returning completed research results for guide_id: {guide_id}")
            return jsonify({
                "status": "completed",
                "topic": guide["topic"],
                "trees": results.get("trees", {})
            })
        except Exception as e:
            logger.error(f"Error getting research results: {str(e)}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @app.route("/api/research/initialize/<guide_id>", methods=["POST"])
    async def initialize_research_api(guide_id: str): # Renamed for clarity
        """Initialize research for a guide via API"""
        try:
            # Get guide data
            logger.debug(f"Getting guide data for guide_id: {guide_id}")
            guide = await db_service.get_guide(guide_id)
            if not guide:
                logger.error(f"Guide not found: {guide_id}")
                return jsonify({"error": "Guide not found"}), 404
                
            # Start research
            logger.debug(f"Starting research for guide_id: {guide_id}")
            research_results_obj = await council.conduct_research(guide["topic"], session_id=guide_id)
            logger.debug(f"Research completed for guide_id: {guide_id}")
            
            # Store research results
            logger.debug(f"Storing research results for guide_id: {guide_id}")
            await db_service.store_research(research_results_obj.to_dict() if hasattr(research_results_obj, 'to_dict') else research_results_obj, guide_id)
            logger.debug(f"Research results stored for guide_id: {guide_id}")
            
            return jsonify({"status": "success"})
        except Exception as e:
            logger.error(f"Error initializing research: {str(e)}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @app.route("/api/research/<guide_id>/subtopics", methods=["POST"])
    async def research_subtopic_api(guide_id: str):
        try:
            logger.debug(f"[DEBUG] Subtopic API request received for guide_id: {guide_id}")
            data = await request.get_json()
            logger.debug(f"[DEBUG] Request data: {data}")
            
            if not data or "topic" not in data:
                logger.error(f"[DEBUG] Missing required field 'topic' in request data: {data}")
                return jsonify({"error": "Topic is required", "status": "error"}), 400
                
            if "ai" not in data:
                logger.error(f"[DEBUG] Missing required field 'ai' in request data: {data}")
                return jsonify({"error": "AI identifier is required", "status": "error"}), 400
                
            if "parent_node_id" not in data:
                logger.error(f"[DEBUG] Missing required field 'parent_node_id' in request data: {data}")
                return jsonify({"error": "Parent node ID is required", "status": "error"}), 400
            
            logger.debug(f"[DEBUG] All required fields present: topic={data['topic']}, ai={data['ai']}, parent_node_id={data['parent_node_id']}")
                
            guide = await db_service.get_guide(guide_id)
            if not guide:
                logger.error(f"[DEBUG] Guide not found: {guide_id}")
                return jsonify({"error": "Guide not found", "status": "error"}), 404
                
            logger.debug(f"[DEBUG] Found guide: {guide_id}, topic: {guide.get('topic', 'unknown')}")
                
            # Create a new research session for the subtopic
            subtopic_session_id = await db_service.store_research({
                "topic": data['topic'],
                "parent_guide_id": guide_id, 
                "status": "initializing",
                "metadata": {"created": datetime.utcnow(), "updated": datetime.utcnow()},
                "trees": {}
            })
            logger.debug(f"[DEBUG] Created new research session for subtopic: {subtopic_session_id}")
            
            # Enable only the specified AI for research
            logger.debug(f"[DEBUG] Available AI members: {list(council.members.keys())}")
            for member_name in council.members:
                enabled = (member_name == data["ai"])
                council.members[member_name]["enabled"] = enabled
                logger.debug(f"[DEBUG] AI {member_name} enabled: {enabled}")
                
            # Conduct research
            logger.debug(f"[DEBUG] Starting research for topic: {data['topic']}")
            research_results_obj = await council.conduct_research(data["topic"], session_id=subtopic_session_id)
            logger.debug(f"[DEBUG] Research completed for subtopic session: {subtopic_session_id}")
            
            # Store research results
            logger.debug(f"[DEBUG] Storing research results")
            await db_service.store_research(research_results_obj.to_dict() if hasattr(research_results_obj, 'to_dict') else research_results_obj, subtopic_session_id)
            logger.debug(f"[DEBUG] Research results stored successfully")
            
            # Create node with generated results
            ai_results = research_results_obj.get("trees", {}).get(data["ai"], {})
            logger.debug(f"[DEBUG] Retrieved AI results for {data['ai']}")
            
            new_node = {
                "node_id": subtopic_session_id,
                "topic": data["topic"],
                "status": "completed",
                "research": ai_results.get("research", {}),
                "children": []
            }
            logger.debug(f"[DEBUG] Created new node: {new_node}")
            
            # Add node to parent's children
            logger.debug(f"[DEBUG] Adding subtopic node to guide {guide_id}, AI {data['ai']}, parent node {data['parent_node_id']}")
            result = await db_service.add_subtopic_node(guide_id, data["ai"], data["parent_node_id"], new_node)
            logger.debug(f"[DEBUG] Add subtopic node result: {result}")
            
            logger.debug(f"[DEBUG] Returning successful response with new node")
            return jsonify({
                "status": "success", 
                "node": new_node
            })
        except Exception as e:
            logger.error(f"[DEBUG] Error researching subtopic: {str(e)}", exc_info=True)
            return jsonify({"error": str(e), "status": "error"}), 500

    print("[DEBUG app.py] create_app finished.")
    return app

if __name__ == "__main__":
    print("[DEBUG app.py] Starting __main__ block.")
    app = create_app()
    print(f"[DEBUG app.py] Final app.config before run, PROVIDE_AUTOMATIC_OPTIONS: {app.config.get('PROVIDE_AUTOMATIC_OPTIONS')}")
    app.run(debug=True, use_reloader=True)

    # Use a production-ready ASGI server like Hypercorn directly for Quart in production
    # For development, app.run() is okay but ensure it's using an ASGI loop.
    # Quart's app.run() by default tries to use Hypercorn if available. 