"""
AI Council Guide Creation Website - Main Flask Application
"""
import os
import sys
from flask import Flask, jsonify, render_template
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Try to import from config.py
try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    import config
    MONGO_URI = getattr(config, 'MONGO_URI', None)
except (ImportError, AttributeError):
    MONGO_URI = None

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__, 
                static_folder='frontend/static',
                template_folder='frontend/templates')
    
    # Configure logging
    app.logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    app.logger.addHandler(handler)
    
    # Basic configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    
    # Set MongoDB URI from config.py or environment variables
    if MONGO_URI:
        app.config['MONGO_URI'] = MONGO_URI
    else:
        app.config['MONGO_URI'] = os.environ.get('MONGO_URI') or os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/ai_council')
    
    # Register blueprints
    from src.backend.blueprints.research import research_bp
    # from src.backend.blueprints.guide_output import guide_output_bp
    app.register_blueprint(research_bp, url_prefix='/api/research')
    # app.register_blueprint(guide_output_bp, url_prefix='/api/output')
    
    # Basic route for testing
    @app.route('/api/health', methods=['GET'])
    def health_check():
        # Try to import config
        try:
            import config
            api_keys = {
                "openai": hasattr(config, 'OPENAI_KEY') and bool(getattr(config, 'OPENAI_KEY')),
                "anthropic": hasattr(config, 'ANTHROPIC_API_KEY') and bool(getattr(config, 'ANTHROPIC_API_KEY')),
                "google": hasattr(config, 'GEMINI_API_KEY') and bool(getattr(config, 'GEMINI_API_KEY')),
                "xai": hasattr(config, 'XAI_API_KEY') and bool(getattr(config, 'XAI_API_KEY')),
            }
        except ImportError:
            api_keys = {
                "openai": bool(os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_KEY")),
                "anthropic": bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_API_KEY")),
                "google": bool(os.environ.get("GOOGLE_API_KEY")),
                "xai": bool(os.environ.get("XAI_API_KEY")),
            }
            
        return jsonify({
            "status": "ok", 
            "message": "AI Council Guide Creation Website is running",
            "api_keys": api_keys
        })
    
    # API config status route
    @app.route('/api/config/status', methods=['GET'])
    def config_status():
        # Try to import config
        try:
            import config
            api_keys = {
                "openai": hasattr(config, 'OPENAI_KEY') and bool(getattr(config, 'OPENAI_KEY')),
                "anthropic": hasattr(config, 'ANTHROPIC_API_KEY') and bool(getattr(config, 'ANTHROPIC_API_KEY')),
                "google": hasattr(config, 'GEMINI_API_KEY') and bool(getattr(config, 'GEMINI_API_KEY')),
                "xai": hasattr(config, 'XAI_API_KEY') and bool(getattr(config, 'XAI_API_KEY')),
            }
        except ImportError:
            api_keys = {
                "openai": bool(os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_KEY")),
                "anthropic": bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_API_KEY")),
                "google": bool(os.environ.get("GOOGLE_API_KEY")),
                "xai": bool(os.environ.get("XAI_API_KEY")),
            }
            
        return jsonify({"api_keys": api_keys})
    
    # Frontend routes
    @app.route('/')
    def index():
        return render_template('research.html')
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 5000))
    
    print(f"Starting AI Council Guide Creation Website on port {port}...")
    print(f"Open your browser and navigate to http://localhost:{port}/")
    
    # Enable debug mode for development
    app.run(debug=True, host='0.0.0.0', port=port) 