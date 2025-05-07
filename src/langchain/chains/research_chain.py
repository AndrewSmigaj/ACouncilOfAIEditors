"""
Research Chain for AI Council Guide Creation Website
Task 3.1: Set up LangChain for research orchestration with pause

This module implements a LangChain-based orchestration for parallel research using:
1. Google Search API for web results
2. Grok's DeepSearch for AI-powered in-depth research

Results are combined and prepared for the next phase, with all interactions logged to MongoDB.
"""
import os
import sys
import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

import aiohttp
import tiktoken
from langchain.chains import SequentialChain
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from bson.objectid import ObjectId

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from src.database.mongodb import get_database

# Import config for API keys
try:
    import config
except ImportError:
    config = None

# Configure encoding for token counting
OPENAI_ENCODING = tiktoken.encoding_for_model("gpt-3.5-turbo")

class ResearchOrchestrator:
    """
    Orchestrates parallel research using Google Search API and Grok DeepSearch,
    with results processed by multiple AI models.
    """
    
    def __init__(self, topic: str, guide_id: str = None):
        """
        Initialize the research orchestrator
        
        Args:
            topic: The guide topic to research
            guide_id: Optional MongoDB guide ID if already created
        """
        self.topic = topic
        self.guide_id = guide_id
        self.db = get_database()
        self.results = {
            "google_search": None,
            "grok_deepsearch": None,
            "combined_research": None,
            "summaries": {}
        }
        
        # Load API keys from config or fall back to environment variables
        self.openai_api_key = getattr(config, 'OPENAI_KEY', None) or os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_KEY")
        self.anthropic_api_key = getattr(config, 'ANTHROPIC_API_KEY', None) or os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_API_KEY")
        self.google_api_key = getattr(config, 'GEMINI_API_KEY', None) or os.environ.get("GOOGLE_API_KEY")
        self.xai_api_key = getattr(config, 'XAI_API_KEY', None) or os.environ.get("XAI_API_KEY")
        self.google_search_api_key = getattr(config, 'GOOGLE_SEARCH_API_KEY', None) or os.environ.get("GOOGLE_SEARCH_API_KEY")
        self.google_search_engine_id = getattr(config, 'GOOGLE_SEARCH_ENGINE_ID', None) or os.environ.get("GOOGLE_SEARCH_ENGINE_ID")
        
        # Log available API keys for debugging
        print(f"API Keys loaded: OpenAI: {'✓' if self.openai_api_key else '✗'}, Anthropic: {'✓' if self.anthropic_api_key else '✗'}, " 
              f"Google: {'✓' if self.google_api_key else '✗'}, XAI: {'✓' if self.xai_api_key else '✗'}")

    async def run_research(self) -> Dict[str, Any]:
        """
        Execute the research process with parallel API calls
        
        Returns:
            Dict containing research results and guide ID
        """
        # Create a new guide document if none exists
        if not self.guide_id:
            self.guide_id = self._create_guide_document()
        
        # Run Google Search and Grok DeepSearch in parallel with error handling
        error_message = None
        try:
            search_tasks = [
                self._run_google_search(),
                self._run_grok_deepsearch()
            ]
            
            # Allow individual tasks to fail without stopping the whole process
            results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Check for exceptions in the results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    service_name = "Google Search" if i == 0 else "Grok DeepSearch"
                    print(f"Warning: {service_name} failed with error: {str(result)}")
                    if not error_message:
                        error_message = f"{service_name} error: {str(result)}"
            
            # Combine research results even if some components failed
            self._combine_research_results()
            
            # Update the guide document with research results
            self._update_guide_with_research()
            
            # Set status to paused for approval or error if both components failed
            if not self.results["google_search"] and not self.results["grok_deepsearch"]:
                self._update_guide_status("error", "All research components failed")
                raise Exception("All research components failed")
            elif error_message:
                # Partial success - some components failed but we have data
                self._update_guide_status("paused_research", f"Research completed with warnings: {error_message}")
            else:
                self._update_guide_status("paused_research")
            
            return {
                "guide_id": self.guide_id,
                "status": "paused_research",
                "message": "Research completed and paused for approval",
                "research_summary": self.results["combined_research"]["summary"] if self.results["combined_research"] else None,
                "warnings": error_message
            }
            
        except Exception as e:
            # Log error and update guide status
            error_message = f"Research error: {str(e)}"
            self._log_interaction("system", "error", error_message, error_message, 0)
            self._update_guide_status("error", error_message)
            raise

    async def _run_google_search(self) -> None:
        """
        Execute Google Search API request and process results
        """
        start_time = time.time()
        query = f"Comprehensive information about {self.topic}"
        
        try:
            # Build the Google Search API URL
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": self.google_search_api_key,
                "cx": self.google_search_engine_id,
                "q": query,
                "num": 10  # Number of results
            }
            
            # Execute the API call
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    response_data = await response.json()
                    
                    # Process the response
                    if response.status == 200 and "items" in response_data:
                        results = []
                        for item in response_data["items"]:
                            results.append({
                                "title": item.get("title", ""),
                                "link": item.get("link", ""),
                                "snippet": item.get("snippet", ""),
                                "source": "Google Search"
                            })
                        
                        # Store results
                        self.results["google_search"] = {
                            "raw_data": response_data,
                            "processed_results": results,
                            "query": query,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        
                        # Calculate token usage
                        input_tokens = len(OPENAI_ENCODING.encode(query))
                        output_tokens = len(OPENAI_ENCODING.encode(json.dumps(results)))
                        total_tokens = input_tokens + output_tokens
                        
                        # Log the interaction with token counts
                        self._log_interaction(
                            "Google Search API", 
                            "search", 
                            query, 
                            json.dumps(results), 
                            total_tokens
                        )
                    else:
                        error_message = response_data.get("error", {}).get("message", "Unknown error")
                        raise Exception(f"Google Search API error: {error_message}")
        
        except Exception as e:
            # Try to use cached data if available
            cached_data = self._get_cached_google_search()
            if cached_data:
                self.results["google_search"] = cached_data
                self._log_interaction(
                    "Cached Google Search", 
                    "cache_retrieval", 
                    query, 
                    "Retrieved from cache due to API error", 
                    0
                )
            else:
                # Log error and re-raise
                self._log_interaction(
                    "Google Search API", 
                    "error", 
                    query, 
                    f"Error: {str(e)}", 
                    0
                )
                raise
                
        finally:
            # Log execution time
            execution_time = time.time() - start_time
            print(f"Google Search completed in {execution_time:.2f}s")

    async def _run_grok_deepsearch(self) -> None:
        """
        Execute Grok's DeepSearch via x.ai API and process results
        """
        start_time = time.time()
        query = f"""Use DeepSearch to research {self.topic} and provide a detailed summary.
        
        IMPORTANT: Format your response as a valid JSON object with the following structure:
        {{
            "summary": "A concise 2-3 paragraph summary of the topic",
            "key_points": ["Point 1", "Point 2", "Point 3", ...],
            "entities": [
                {{
                    "name": "Entity Name",
                    "type": "person|organization|technology|concept|other",
                    "description": "Brief description",
                    "relevance": "How it relates to the main topic"
                }},
                ...
            ],
            "subtopics": [
                {{
                    "title": "Subtopic Title",
                    "summary": "Brief summary of this subtopic",
                    "importance": "High|Medium|Low"
                }},
                ...
            ],
            "timeline": [
                {{
                    "date": "YYYY-MM-DD or descriptive time period",
                    "event": "Description of what happened",
                    "significance": "Why this is important"
                }},
                ...
            ],
            "further_research": [
                {{
                    "topic": "Specific topic for further investigation",
                    "rationale": "Why this would be valuable to explore"
                }},
                ...
            ],
            "references": [
                {{
                    "title": "Reference title",
                    "source": "Where this information comes from",
                    "url": "Optional URL if available"
                }},
                ...
            ]
        }}
        
        Ensure your response is ONLY the JSON object and is properly formatted.
        """
        
        try:
            # Check if the API key is available
            if not self.xai_api_key:
                raise Exception("Grok API key (XAI_API_KEY) is not configured")
                
            # Build the x.ai API request
            url = "https://api.x.ai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.xai_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "grok-3",
                "messages": [
                    {
                        "role": "user",
                        "content": query
                    }
                ],
                "max_tokens": 3000,
                "temperature": 0.5
            }
            
            # Execute the API call
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    response_data = await response.json()
                    
                    # Process the response
                    if response.status == 200 and "choices" in response_data:
                        raw_content = response_data["choices"][0]["message"]["content"]
                        
                        # Attempt to parse the JSON content
                        try:
                            # Extract JSON if it's wrapped in markdown code blocks
                            if "```json" in raw_content and "```" in raw_content:
                                json_content = raw_content.split("```json")[1].split("```")[0]
                            elif "```" in raw_content:
                                json_content = raw_content.split("```")[1].split("```")[0]
                            else:
                                json_content = raw_content
                                
                            # Parse the JSON
                            content_json = json.loads(json_content)
                            
                            # Store both the structured JSON and the raw content
                            self.results["grok_deepsearch"] = {
                                "raw_data": response_data,
                                "content": raw_content,
                                "structured_data": content_json,
                                "query": query,
                                "timestamp": datetime.utcnow().isoformat()
                            }
                        except json.JSONDecodeError:
                            # If JSON parsing fails, store the raw content
                            print("Warning: Could not parse JSON from Grok DeepSearch response")
                            self.results["grok_deepsearch"] = {
                                "raw_data": response_data,
                                "content": raw_content,
                                "query": query,
                                "timestamp": datetime.utcnow().isoformat()
                            }
                        
                        # Get token counts from the response
                        input_tokens = response_data.get("usage", {}).get("prompt_tokens", 0)
                        output_tokens = response_data.get("usage", {}).get("completion_tokens", 0)
                        total_tokens = input_tokens + output_tokens
                        
                        # Log the interaction with detailed token info
                        self._log_interaction(
                            "Grok DeepSearch", 
                            "deepsearch", 
                            query, 
                            raw_content, 
                            total_tokens
                        )
                        
                        # Print token usage summary
                        print(f"Grok DeepSearch tokens - Input: {input_tokens}, Output: {output_tokens}, Total: {total_tokens}")
                    else:
                        error_message = response_data.get("error", {}).get("message", "Unknown error")
                        raise Exception(f"Grok API error: {error_message}")
        
        except Exception as e:
            # Try to use cached data if available
            cached_data = self._get_cached_grok_deepsearch()
            if cached_data:
                self.results["grok_deepsearch"] = cached_data
                self._log_interaction(
                    "Cached Grok DeepSearch", 
                    "cache_retrieval", 
                    query, 
                    "Retrieved from cache due to API error", 
                    0
                )
            else:
                # Create a fallback result using Google Search data
                if self.results["google_search"]:
                    fallback_content = "Unable to retrieve Grok DeepSearch results. Using Google Search data instead."
                    self.results["grok_deepsearch"] = {
                        "content": fallback_content,
                        "query": query,
                        "timestamp": datetime.utcnow().isoformat(),
                        "fallback": True
                    }
                    
                    # Log the error as an interaction
                    self._log_interaction(
                        "Grok DeepSearch", 
                        "error", 
                        query, 
                        f"Error: {str(e)}\nUsing fallback strategy.", 
                        0
                    )
                else:
                    # If we have no Google Search data either, raise the exception
                    self._log_interaction(
                        "Grok DeepSearch", 
                        "error", 
                        query, 
                        f"Error: {str(e)}", 
                        0
                    )
                    raise
                
        finally:
            # Log execution time
            execution_time = time.time() - start_time
            print(f"Grok DeepSearch completed in {execution_time:.2f}s")

    def _combine_research_results(self) -> None:
        """
        Combine Google Search and Grok DeepSearch results into a unified research document
        with structured data for future use by agents
        """
        combined_data = {
            "topic": self.topic,
            "timestamp": datetime.utcnow().isoformat(),
            "sources": [],
            "structured_data": {}
        }
        
        summary_parts = []
        
        # Add Google Search results
        if self.results["google_search"] and "processed_results" in self.results["google_search"]:
            google_results = self.results["google_search"]["processed_results"]
            if google_results:
                combined_data["sources"].extend(google_results)
                
                # Add summary from Google results
                google_summary = "Key findings from web search:\n"
                for idx, result in enumerate(google_results[:5], 1):
                    title = result.get('title', 'No title')
                    snippet = result.get('snippet', 'No snippet available')
                    google_summary += f"{idx}. {title}: {snippet}\n"
                summary_parts.append(google_summary)
                
                # Add structured data from Google results
                combined_data["structured_data"]["web_results"] = google_results
        
        # Add Grok DeepSearch results
        if self.results["grok_deepsearch"]:
            # Add the raw content to sources
            if "content" in self.results["grok_deepsearch"]:
                grok_content = self.results["grok_deepsearch"]["content"]
                if grok_content:
                    combined_data["sources"].append({
                        "title": f"Grok DeepSearch on {self.topic}",
                        "content": grok_content,
                        "source": "Grok DeepSearch"
                    })
                    
                    # Add Grok summary to text summary
                    summary_parts.append("Key findings from AI deep research:\n" + grok_content)
            
            # Add structured data if available
            if "structured_data" in self.results["grok_deepsearch"]:
                structured_data = self.results["grok_deepsearch"]["structured_data"]
                combined_data["structured_data"]["deep_research"] = structured_data
                
                # Store further research topics for potential recursive research
                if "further_research" in structured_data:
                    combined_data["further_research_topics"] = structured_data["further_research"]
        
        # Check if we have any summary parts
        if not summary_parts:
            # Create a default summary if no data was gathered
            summary_parts.append(f"No detailed research data was found for the topic: {self.topic}. Please try again later or refine your topic.")
        
        # Generate a combined summary
        combined_summary = "\n\n".join(summary_parts)
        combined_data["summary"] = combined_summary
        
        # Store the combined results
        self.results["combined_research"] = combined_data
        
        # Store in shared research collection
        self._store_in_research_collection()
    
    def _store_in_research_collection(self) -> None:
        """
        Store research results in a shared research collection that can be used by other agents
        """
        if not self.results["combined_research"]:
            return
            
        # Prepare the research document
        research_doc = {
            "topic": self.topic,
            "timestamp": datetime.utcnow(),
            "guide_id": self.guide_id,
            "summary": self.results["combined_research"]["summary"],
            "structured_data": self.results["combined_research"].get("structured_data", {}),
            "sources": self.results["combined_research"]["sources"],
        }
        
        # Add further research topics if available
        if "further_research_topics" in self.results["combined_research"]:
            research_doc["further_research_topics"] = self.results["combined_research"]["further_research_topics"]
            research_doc["recursive_research_completed"] = False
        
        try:
            # Check if research on this topic already exists
            existing = self.db.research.find_one({"topic": self.topic})
            
            if existing:
                # Update existing research
                self.db.research.update_one(
                    {"_id": existing["_id"]},
                    {"$set": research_doc}
                )
                print(f"Updated existing research in shared collection for topic: {self.topic}")
            else:
                # Insert new research
                result = self.db.research.insert_one(research_doc)
                print(f"Stored new research in shared collection with ID: {result.inserted_id}")
                
        except Exception as e:
            print(f"Error storing research in shared collection: {str(e)}")
    
    def _recursive_research(self) -> None:
        """
        Perform recursive research on subtopics identified in the initial research
        """
        if not self.results["combined_research"] or "further_research_topics" not in self.results["combined_research"]:
            return
            
        further_topics = self.results["combined_research"]["further_research_topics"]
        
        # Log the start of recursive research
        print(f"\n==== STARTING RECURSIVE RESEARCH ====")
        print(f"Found {len(further_topics)} topics for further investigation")
        
        # In the future, this would trigger additional research on each subtopic
        # For now, we just log that we found them
        for i, topic in enumerate(further_topics, 1):
            topic_name = topic.get("topic", f"Unnamed topic {i}")
            rationale = topic.get("rationale", "No rationale provided")
            print(f"Future recursive research topic {i}: {topic_name}")
            print(f"Rationale: {rationale}")
        
        print("==== RECURSIVE RESEARCH MARKED FOR FUTURE PROCESSING ====\n")
        
    async def research_selected_subtopics(self, selected_topics) -> Dict[str, Any]:
        """
        Perform research on specific subtopics selected by the user
        
        Args:
            selected_topics: List of topics with format [{"topic": "...", "rationale": "..."}, ...]
        
        Returns:
            Dictionary with results of research on selected subtopics
        """
        if not selected_topics:
            return {"status": "error", "message": "No topics selected", "subtopics_researched": 0}
        
        # Log the start of subtopic research
        print(f"\n==== STARTING SELECTED SUBTOPICS RESEARCH ====")
        print(f"Researching {len(selected_topics)} selected topics")
        
        # Store results for all subtopics
        subtopic_results = []
        total_topics = len(selected_topics)
        completed_topics = 0
        
        # Track progress in the database
        self._update_subtopic_research_progress(total_topics, completed_topics)
        
        # Process topics with concurrency limit
        concurrency_limit = 3  # Process 3 topics at a time
        for i in range(0, total_topics, concurrency_limit):
            batch = selected_topics[i:i+concurrency_limit]
            batch_tasks = []
            
            for topic_data in batch:
                topic_name = topic_data.get("topic", "")
                if not topic_name:
                    continue
                    
                # Create task for this topic
                task = self._research_subtopic(topic_name, topic_data)
                batch_tasks.append(task)
            
            # Run batch concurrently and collect results
            if batch_tasks:
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # Process batch results
                for j, result in enumerate(batch_results):
                    topic_data = batch[j]
                    topic_name = topic_data.get("topic", f"Unnamed topic {i+j+1}")
                    
                    if isinstance(result, Exception):
                        print(f"Error researching subtopic '{topic_name}': {str(result)}")
                        subtopic_results.append({
                            "topic": topic_name,
                            "status": "error",
                            "error": str(result)
                        })
                    else:
                        subtopic_results.append(result)
                    
                    # Update progress
                    completed_topics += 1
                    self._update_subtopic_research_progress(total_topics, completed_topics)
        
        # Store results in the database
        self._store_subtopic_research_results(subtopic_results)
        
        print(f"==== SELECTED SUBTOPICS RESEARCH COMPLETED: {completed_topics}/{total_topics} TOPICS ====\n")
        
        return {
            "status": "completed", 
            "subtopics_researched": completed_topics,
            "results": subtopic_results
        }

    async def _research_subtopic(self, topic_name, topic_data) -> Dict[str, Any]:
        """
        Research a single subtopic
        
        Args:
            topic_name: Name of the subtopic
            topic_data: Additional data about the subtopic
        
        Returns:
            Dictionary with research results
        """
        print(f"Researching subtopic: {topic_name}")
        
        try:
            # Create a new ResearchOrchestrator for this subtopic
            subtopic_orchestrator = ResearchOrchestrator(topic_name)
            
            # Store reference to parent research
            subtopic_orchestrator.parent_guide_id = self.guide_id
            subtopic_orchestrator.parent_topic = self.topic
            
            # Run research for this subtopic
            research_result = await subtopic_orchestrator.run_research()
            
            # Return result with link to parent
            return {
                "topic": topic_name,
                "guide_id": subtopic_orchestrator.guide_id,
                "parent_guide_id": self.guide_id,
                "status": "completed",
                "rationale": topic_data.get("rationale", ""),
                "research_summary": research_result.get("research_summary", "")
            }
        except Exception as e:
            print(f"Error in _research_subtopic for '{topic_name}': {str(e)}")
            # Log error but don't stop the whole process
            return {
                "topic": topic_name,
                "parent_guide_id": self.guide_id,
                "status": "error",
                "rationale": topic_data.get("rationale", ""),
                "error": str(e)
            }

    def _update_subtopic_research_progress(self, total_topics, completed_topics):
        """
        Update progress of subtopic research in the database
        """
        progress_percentage = 0
        if total_topics > 0:
            progress_percentage = (completed_topics / total_topics) * 100
        
        try:
            self.db.research.update_one(
                {"guide_id": self.guide_id},
                {
                    "$set": {
                        "subtopic_research_progress": {
                            "total_topics": total_topics,
                            "completed_topics": completed_topics,
                            "percentage": progress_percentage,
                            "last_updated": datetime.utcnow()
                        }
                    }
                }
            )
        except Exception as e:
            print(f"Error updating subtopic research progress: {str(e)}")

    def _store_subtopic_research_results(self, results):
        """
        Store the results of subtopic research in the database
        """
        try:
            # Update existing subtopic results or create new array
            self.db.research.update_one(
                {"guide_id": self.guide_id},
                {
                    "$push": {
                        "subtopic_results": {
                            "$each": results
                        }
                    },
                    "$set": {
                        "subtopic_research_update_time": datetime.utcnow(),
                        "subtopic_research_in_progress": False
                    }
                }
            )
            
            # Also update the guide document
            self.db.guides.update_one(
                {"_id": ObjectId(self.guide_id)},
                {
                    "$push": {
                        "research.subtopic_results": {
                            "$each": results
                        }
                    },
                    "$set": {
                        "metadata.updated": datetime.utcnow()
                    }
                }
            )
        except Exception as e:
            print(f"Error storing subtopic research results: {str(e)}")

    def _create_guide_document(self) -> str:
        """
        Create a new guide document in MongoDB
        
        Returns:
            str: The ObjectId of the created document as a string
        """
        guide = {
            "topic": self.topic,
            "status": "researching",
            "research": {},
            "metadata": {
                "created": datetime.utcnow(),
                "updated": datetime.utcnow(),
                "ais": ["Claude", "ChatGPT", "Gemini", "Grok"]
            },
            "ai_interactions": []
        }
        
        result = self.db.guides.insert_one(guide)
        return str(result.inserted_id)

    def _update_guide_with_research(self) -> None:
        """
        Update the guide document with research results
        """
        if not self.results["combined_research"]:
            return
            
        update_data = {
            "research": {
                "summary": self.results["combined_research"]["summary"],
                "sources": self.results["combined_research"]["sources"],
                "timestamp": self.results["combined_research"]["timestamp"]
            },
            "metadata.updated": datetime.utcnow()
        }
        
        self.db.guides.update_one(
            {"_id": ObjectId(self.guide_id)},
            {"$set": update_data}
        )

    def _update_guide_status(self, status: str, message: str = None) -> None:
        """
        Update the guide status
        
        Args:
            status: The new status
            message: Optional status message
        """
        update_data = {
            "status": status,
            "metadata.updated": datetime.utcnow()
        }
        
        if message:
            update_data["status_message"] = message
            
        self.db.guides.update_one(
            {"_id": ObjectId(self.guide_id)},
            {"$set": update_data}
        )
        
        # Print status change for debugging
        print(f"Guide status updated to: {status} {f'({message})' if message else ''}")
        
        # Verify that we are pausing for approval when expected
        if status == "paused_research":
            print("\n==== RESEARCH PAUSED FOR APPROVAL ====")
            print(f"The research for topic '{self.topic}' is now paused and awaiting approval.")
            print("Please review the research results and approve or provide feedback.")
            print("=======================================\n")

    def _log_interaction(self, ai: str, step: str, query: str, response: str, token_cost: int) -> None:
        """
        Log an AI interaction to MongoDB
        
        Args:
            ai: The AI service name
            step: The research step
            query: The query sent to the AI
            response: The AI response
            token_cost: The token cost
        """
        # Calculate input and output tokens when not provided
        input_tokens = 0
        output_tokens = 0
        
        if step in ["deepsearch", "search"] and token_cost == 0:
            try:
                # For API calls, estimate token counts
                if query:
                    input_tokens = len(OPENAI_ENCODING.encode(query))
                if response:
                    output_tokens = len(OPENAI_ENCODING.encode(response))
                token_cost = input_tokens + output_tokens
            except Exception as e:
                print(f"Error counting tokens: {str(e)}")
        
        interaction = {
            "step": step,
            "ai": ai,
            "query": query,
            "response": response,
            "token_cost": token_cost,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "timestamp": datetime.utcnow()
        }
        
        self.db.guides.update_one(
            {"_id": ObjectId(self.guide_id)},
            {"$push": {"ai_interactions": interaction}}
        )
        
        # Print token usage for debugging
        if token_cost > 0:
            print(f"{ai} {step}: {token_cost} tokens total (Input: {input_tokens}, Output: {output_tokens})")

    def _get_cached_google_search(self) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached Google Search results for similar topics
        
        Returns:
            Dict or None: Cached results if available
        """
        # Look for similar topics in the database
        similar_guide = self.db.guides.find_one({
            "topic": {"$regex": f".*{self.topic}.*", "$options": "i"},
            "research.sources.source": "Google Search"
        })
        
        if similar_guide and "ai_interactions" in similar_guide:
            # Find the Google Search interaction
            for interaction in similar_guide["ai_interactions"]:
                if interaction.get("ai") == "Google Search API" and interaction.get("step") == "search":
                    try:
                        results = json.loads(interaction.get("response", "[]"))
                        return {
                            "processed_results": results,
                            "query": interaction.get("query", ""),
                            "timestamp": interaction.get("timestamp", datetime.utcnow().isoformat()),
                            "cached": True
                        }
                    except:
                        pass
        
        return None

    def _get_cached_grok_deepsearch(self) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached Grok DeepSearch results for similar topics
        
        Returns:
            Dict or None: Cached results if available
        """
        # Look for similar topics in the database
        similar_guide = self.db.guides.find_one({
            "topic": {"$regex": f".*{self.topic}.*", "$options": "i"},
            "ai_interactions.ai": "Grok DeepSearch"
        })
        
        if similar_guide and "ai_interactions" in similar_guide:
            # Find the Grok DeepSearch interaction
            for interaction in similar_guide["ai_interactions"]:
                if interaction.get("ai") == "Grok DeepSearch" and interaction.get("step") == "deepsearch":
                    return {
                        "content": interaction.get("response", ""),
                        "query": interaction.get("query", ""),
                        "timestamp": interaction.get("timestamp", datetime.utcnow().isoformat()),
                        "cached": True
                    }
        
        return None

# Async wrapper for the Flask endpoint
async def research_topic(topic: str, guide_id: str = None) -> Dict[str, Any]:
    """
    Main entry point for research process
    
    Args:
        topic: The topic to research
        guide_id: Optional guide ID if already created
        
    Returns:
        Dict with research results and guide ID
    """
    orchestrator = ResearchOrchestrator(topic, guide_id)
    return await orchestrator.run_research() 