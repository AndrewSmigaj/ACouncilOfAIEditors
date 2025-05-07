# AI Council Guide Creation Website

A web application that enables users to create comprehensive guides on any topic by collaborating with an AI council (e.g., Claude, ChatGPT, Gemini, Grok). Users input a topic, and the app orchestrates a multi-step process: research, outline creation, section drafting, editing, creative passes, and final review.

## Features

- **Parallel Research**: Uses Google Search API and Grok DeepSearch to gather comprehensive information about topics.
- **Pause at Each Step**: The app pauses after each step to show AI queries, responses, and token costs, requiring user approval to proceed.
- **AI Interaction Tracking**: Queries sent to each AI, their responses, and token costs are logged and displayed for transparency.
- **User Approval**: Users review AI outputs and approve via a button before moving to the next step.
- **Creative Passes**: Optional creative passes using random words to generate innovative ideas.
- **Customization**: Customize the AI council and word lists for creative passes.

## Technology Stack

- **Frontend**: D3.js (v7) for data visualization and DOM manipulation
- **Backend**: Flask (v2.3) for the API endpoints
- **Database**: MongoDB (v6) for storing guides, research, and AI interactions
- **AI Orchestration**: LangChain (v0.2) for managing the AI workflow
- **API Integrations**: Google Search API, Grok (x.ai API), ChatGPT, Claude, and Gemini

## Getting Started

### Prerequisites

- Python 3.9+
- MongoDB
- API keys for:
  - Google Search API & Custom Search Engine ID
  - OpenAI (ChatGPT)
  - Anthropic (Claude)
  - Google AI (Gemini)
  - x.ai (Grok)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ai-council-guide-creation.git
   cd ai-council-guide-creation
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your API keys:
   ```
   # Copy from .env.example
   cp .env.example .env
   # Then edit the .env file with your API keys
   ```

5. Set up your MongoDB database:
   ```
   # Update the MONGODB_URI in .env or config.py
   ```

### Running the Application

1. Start the Flask server:
   ```bash
   python run_server.py
   ```

2. Open your browser and navigate to http://localhost:5000/

### Usage

1. Enter a guide topic (at least 3 words) in the form
2. The system will perform parallel research using Google Search and Grok DeepSearch
3. Review the research results, interactions, and token costs
4. Provide feedback or approve to move to the next step
5. Repeat the process for outline creation, drafting, editing, and final review

## Project Structure

- `src/` - Main source code
  - `frontend/` - Frontend files (HTML, CSS, JavaScript with D3.js)
  - `backend/` - API endpoints and business logic
  - `langchain/` - LangChain orchestration for AI interactions
  - `database/` - MongoDB integration

## Development

### Running Tests

```bash
# Unit tests
pytest src/tests/

# Test the research orchestrator specifically
pytest src/tests/test_research_orchestrator.py
```

### Available Endpoints

- `GET /api/health` - Health check endpoint
- `POST /api/research` - Start research with a topic
- `GET /api/research/<guide_id>` - Get research results
- `POST /api/research/<guide_id>/approve` - Approve research results
- `POST /api/research/<guide_id>/feedback` - Provide feedback on research

## Implemented Tasks

- **Task 2.1** (Complete): Enhanced topic input form with error feedback and examples
- **Task 3.1** (Complete): Parallel research orchestration using Google Search API and Grok DeepSearch

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with LangChain, a powerful framework for composing language models
- Inspired by the concept of AI collaboration for content creation