# AI Council Research System

A Flask-based research system that coordinates multiple AI models to conduct collaborative research on topics.

## Features

- Coordinated research using multiple AI models
- Hierarchical research structure with parent-child relationships
- Token usage tracking
- MongoDB storage for research sessions and results
- RESTful API for research management

## Prerequisites

- Python 3.8+
- MongoDB
- API keys for AI models (currently supports Grok)

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
# Create a .env file with the following variables:
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=research_db
XAI_API_KEY=your_grok_api_key
```

## Running the Application

1. Start MongoDB:
```bash
mongod
```

2. Run the Flask application:
```bash
python src/app.py
```

The application will be available at `http://localhost:5000`.

## API Endpoints

### Research Sessions

- `POST /api/research/session` - Create a new research session
  - Body: `{"topic": "research topic"}`
  - Returns: `{"session_id": "..."}`

- `GET /api/research/session/<session_id>` - Get a research session
  - Returns: Session details

- `DELETE /api/research/session/<session_id>` - Delete a research session
  - Returns: `{"message": "Session deleted"}`

### Research Nodes

- `POST /api/research/node` - Create a new research node
  - Body: `{"topic": "research topic", "session_id": "...", "parent_id": "..."}`
  - Returns: `{"node_id": "..."}`

- `GET /api/research/node/<node_id>` - Get a research node
  - Returns: Node details

- `POST /api/research/node/<node_id>/expand` - Expand research with child nodes
  - Returns: `{"child_node_ids": [...]}`

- `GET /api/research/node/<node_id>/responses` - Get AI responses for a node
  - Returns: List of AI responses

- `GET /api/research/session/<session_id>/nodes` - Get all nodes in a session
  - Returns: List of nodes

## Project Structure

```
src/
├── app.py                 # Flask application
└── langchain/
    └── chains/
        ├── ai_council.py  # AI Council implementation
        ├── db_models.py   # Database models
        ├── db_service.py  # Database service
        ├── grok_wrapper.py # Grok AI wrapper
        └── token_counter.py # Token counting utilities
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.