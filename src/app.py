"""
Quart application for the AI Council research system.
"""
from quart import Quart, request, jsonify, render_template, send_from_directory
from datetime import datetime
import os
from typing import Dict, Any
from quart_cors import cors
from config import Config, MONGO_URI, MONGO_DB_NAME, XAI_API_KEY
import logging
from pathlib import Path

from src.langchain.chains.ai_council import AICouncil, AICouncilMember
from src.langchain.chains.research_services import MongoDBService
from src.langchain.chains.research_base import ResearchConfig

def create_app(config_class=Config):
    """Create and configure the Quart application"""
    # Get the absolute path to the src directory
    src_dir = Path(__file__).parent
    
    app = Quart(__name__,
                static_folder=src_dir / 'frontend' / 'static',
                template_folder=src_dir / 'frontend' / 'templates')
    
    # Instantiate the config class
    config = config_class()
    app.config.from_object(config)
    cors(app)

    # Initialize configuration
    config = ResearchConfig.from_config(app)

    # Initialize database service using MongoDBService
    db_service = MongoDBService(config)

    # Initialize AI Council with config
    council = AICouncil(config)

    # Enable Grok member (it's already enabled by default, but being explicit)
    council.enable_member("grok")

    logger = logging.getLogger(__name__)

    @app.route("/")
    async def index():
        """Serve the main index page"""
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
            # Get guide data from guides collection
            logger.debug(f"Looking up guide in guides collection: {guide_id}")
            guide = await db_service.get_guide(guide_id)
            logger.debug(f"Guide lookup result: {guide}")
            
            if not guide:
                logger.error(f"Guide not found in guides collection: {guide_id}")
                return jsonify({"error": "Guide not found"}), 404
            
            # Get research results
            logger.debug(f"Getting research results for guide_id: {guide_id}")
            results = await db_service.get_research_results(guide_id)
            logger.debug(f"Research results lookup result: {results}")
            
            if not results:
                logger.debug(f"No research results found for guide_id: {guide_id}, returning initializing state")
                return jsonify({
                    "status": "initializing",
                    "research": {
                        "topic": guide["topic"],
                        "children": [],
                        "research_results": {}
                    }
                })
            
            logger.debug(f"Returning completed research results for guide_id: {guide_id}")
            return jsonify({
                "status": "completed",
                "research": results
            })
        except Exception as e:
            logger.error(f"Error getting guide research: {str(e)}", exc_info=True)
            return jsonify({"error": str(e)}), 500

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
            "topic": data["topic"],
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
        research_results = await council.conduct_research(data["topic"], session_id=session_id)
        logger.debug(f"Research completed for session {session_id}")
        
        # Store research results
        logger.debug(f"Storing research results for session {session_id}")
        await db_service.store_research(research_results, session_id)
        logger.debug(f"Research results stored for session {session_id}")
        
        return jsonify({"guide_id": session_id})

    @app.route("/api/research/results/<guide_id>", methods=["GET"])
    async def get_research_results(guide_id: str):
        """Get research results for a guide"""
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
                    "research": {
                        "topic": guide["topic"],
                        "children": [],
                        "research_results": {}
                    }
                })
                
            logger.debug(f"Returning completed research results for guide_id: {guide_id}")
            return jsonify({
                "status": "completed",
                "research": results
            })
        except Exception as e:
            logger.error(f"Error getting research results: {str(e)}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @app.route("/api/research/initialize/<guide_id>", methods=["POST"])
    async def initialize_research(guide_id: str):
        """Initialize research for a guide"""
        try:
            # Get guide data
            logger.debug(f"Getting guide data for guide_id: {guide_id}")
            guide = await db_service.get_guide(guide_id)
            if not guide:
                logger.error(f"Guide not found: {guide_id}")
                return jsonify({"error": "Guide not found"}), 404
                
            # Start research
            logger.debug(f"Starting research for guide_id: {guide_id}")
            research_results = await council.conduct_research(guide["topic"], session_id=guide_id)
            logger.debug(f"Research completed for guide_id: {guide_id}")
            
            # Store research results
            logger.debug(f"Storing research results for guide_id: {guide_id}")
            await db_service.store_research(research_results, guide_id)
            logger.debug(f"Research results stored for guide_id: {guide_id}")
            
            return jsonify({"status": "success"})
        except Exception as e:
            logger.error(f"Error initializing research: {str(e)}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @app.route("/api/research/<guide_id>/subtopics", methods=["POST"])
    async def research_subtopic(guide_id: str):
        """Research a subtopic"""
        try:
            data = await request.get_json()
            if not data or "topic" not in data:
                logger.error("No topic provided in request")
                return jsonify({"error": "Topic is required"}), 400
                
            # Get guide data
            logger.debug(f"Getting guide data for guide_id: {guide_id}")
            guide = await db_service.get_guide(guide_id)
            if not guide:
                logger.error(f"Guide not found: {guide_id}")
                return jsonify({"error": "Guide not found"}), 404
                
            # Start research
            logger.debug(f"Starting research for guide_id: {guide_id}")
            research_results = await council.conduct_research(data["topic"], session_id=guide_id)
            logger.debug(f"Research completed for guide_id: {guide_id}")
            
            # Store research results
            logger.debug(f"Storing research results for guide_id: {guide_id}")
            await db_service.store_research(research_results, guide_id)
            logger.debug(f"Research results stored for guide_id: {guide_id}")
            
            return jsonify({"status": "success"})
        except Exception as e:
            logger.error(f"Error researching subtopic: {str(e)}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True) 