#!/usr/bin/env python3
"""
Run script for AI Council Guide Creation Website
"""
import os
import sys
from src.app import create_app

# Check if MongoDB connection is available
try:
    from src.database.mongodb import get_database, initialize_collections
    db = get_database()
    initialize_collections()
    print("MongoDB connection successful!")
except Exception as e:
    print(f"Warning: MongoDB connection failed: {str(e)}")
    print("The application may not function correctly without MongoDB.")

# Create and run the Flask app
app = create_app()

if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 5000))
    
    print(f"Starting AI Council Guide Creation Website on port {port}...")
    print("Open your browser and navigate to http://localhost:{port}/")
    
    # Enable debug mode for development
    app.run(debug=True, host="0.0.0.0", port=port) 