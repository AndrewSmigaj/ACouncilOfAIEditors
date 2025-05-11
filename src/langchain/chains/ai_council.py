"""
AI Council implementation using LangChain for orchestration.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
import logging
import json
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.utilities import GoogleSearchAPIWrapper
from .research_base import ResearchConfig, ResearchError

# Configure logging
logger = logging.getLogger(__name__)

class ResearchOutput(BaseModel):
    """Structure for research output"""
    summary: str = Field(description="Detailed summary of the research")
    key_points: List[str] = Field(description="List of key points from the research")
    entities: List[Dict[str, str]] = Field(description="List of important entities with their types and descriptions")
    timeline: List[Dict[str, str]] = Field(description="Timeline of events with dates and descriptions")
    further_research: List[Dict[str, str]] = Field(description="Topics that need further research with reasons")
    references: List[Dict[str, str]] = Field(description="List of references with titles and URLs")

class AICouncilMember:
    """A member of the AI Council using LangChain"""
    def __init__(self, name: str, config: ResearchConfig):
        self.name = name
        self.config = config
        self.chain = self._create_chain()
        logger.debug(f"Initialized {name} council member")
        
    def _create_chain(self) -> RunnableSequence:
        """Create the LangChain for this AI member"""
        logger.debug(f"Creating chain for {self.name}")
        try:
            # Select the appropriate LLM based on AI member name
            if self.name == "grok":
                llm = ChatOpenAI(
                    model="grok-beta",
                    openai_api_base="https://api.x.ai/v1",
                    api_key=self.config.XAI_API_KEY,
                    temperature=0.7,
                    max_tokens=2000
                )
            elif self.name == "claude":
                llm = ChatAnthropic(
                    api_key=self.config.anthropic_api_key,
                    model="claude-3-opus-20240229",
                    temperature=0.7,
                    max_tokens=4000
                )
            elif self.name == "chatgpt":
                llm = ChatOpenAI(
                    api_key=self.config.openai_api_key,
                    model="gpt-4-turbo-preview",
                    temperature=0.7,
                    max_tokens=4000
                )
            elif self.name == "gemini":
                llm = ChatGoogleGenerativeAI(
                    api_key=self.config.google_api_key,
                    model="gemini-pro",
                    temperature=0.7,
                    max_tokens=4000
                )
            else:
                raise ValueError(f"Unknown AI member: {self.name}")

            # Create the prompt template
            prompt = PromptTemplate(
                input_variables=["topic", "web_results"],
                template="""Analyze the following topic using the provided search results:

Topic: {topic}

Web Search Results:
{web_results}

Provide a comprehensive analysis in the following JSON format:
{{
    "summary": "detailed summary",
    "key_points": ["point 1", "point 2", ...],
    "entities": [{{"name": "entity name", "type": "entity type", "description": "..."}}],
    "timeline": [{{"date": "YYYY-MM-DD", "event": "description"}}],
    "further_research": [{{"topic": "subtopic", "reason": "why this needs research"}}],
    "references": [{{"title": "source title", "url": "source url"}}]
}}

Ensure your response is ONLY the JSON object, with no additional text."""
            )

            # Create the output parser
            output_parser = JsonOutputParser(pydantic_object=ResearchOutput)

            # Create the chain
            chain = prompt | llm | output_parser

            logger.debug(f"Chain created successfully for {self.name}")
            return chain

        except Exception as e:
            logger.error(f"Failed to create chain for {self.name}: {str(e)}", exc_info=True)
            raise ResearchError(f"Failed to create chain for {self.name}: {str(e)}")
            
    async def research(self, topic: str) -> Dict[str, Any]:
        """Conduct research using LangChain"""
        try:
            logger.debug(f"{self.name} starting research for topic: {topic}")
            
            # Initialize Google Search
            google_search = GoogleSearchAPIWrapper(
                google_api_key=self.config.google_search_api_key,
                google_cse_id=self.config.google_search_engine_id
            )
            
            # Perform Google search
            logger.debug("Running Google search")
            web_results = await asyncio.to_thread(
                google_search.run,
                topic
            )
            
            # Run the research chain
            logger.debug(f"Running {self.name} research chain")
            result = await self.chain.ainvoke({
                "topic": topic,
                "web_results": web_results
            })
            
            # Add web results to the response
            result_dict = result  # Result is already a dict from JsonOutputParser
            result_dict["web_results"] = [
                {"title": r.split(" - ")[0].strip(), "url": r.split(" - ")[1].strip()}
                for r in web_results.split("\n")
                if " - " in r
            ]
            
            return {
                "ai_name": self.name,
                "result": result_dict,
                "timestamp": datetime.utcnow()
            }
                
        except Exception as e:
            logger.error(f"{self.name} research failed: {str(e)}", exc_info=True)
            raise ResearchError(f"{self.name} research failed: {str(e)}")

class AICouncil:
    """Council of AI members coordinated through LangChain"""
    def __init__(self, config: ResearchConfig):
        self.config = config
        self.members = {
            "claude": {"enabled": False, "config": config},
            "chatgpt": {"enabled": False, "config": config},
            "gemini": {"enabled": False, "config": config},
            "grok": {"enabled": True, "config": config}  # Only Grok is enabled by default
        }
        
    async def conduct_research(self, topic: str, session_id: Optional[str] = None, parent_id: Optional[str] = None) -> Dict[str, Any]:
        """Conduct research with all enabled members"""
        logger.debug(f"[DEBUG AICouncil] Starting conduct_research for topic: {topic}")
        logger.debug(f"[DEBUG AICouncil] Session ID: {session_id}, Parent ID: {parent_id}")
        
        tasks = []
        enabled_members = []
        
        # Add tasks for all enabled members
        for member_name, member_config in self.members.items():
            if member_config["enabled"]:
                logger.debug(f"[DEBUG AICouncil] Adding research task for enabled member: {member_name}")
                enabled_members.append(member_name)
                member = AICouncilMember(member_name, member_config["config"])
                tasks.append(member.research(topic))
            else:
                logger.debug(f"[DEBUG AICouncil] Member {member_name} is disabled, skipping")
                    
        # Run all research in parallel
        logger.debug(f"[DEBUG AICouncil] Starting parallel research with {len(tasks)} tasks")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        logger.debug(f"[DEBUG AICouncil] Gathered {len(results)} results")
        
        # Process results and create trees structure
        trees = {}
        
        for i, member_name in enumerate(enabled_members):
            result = results[i]
            logger.debug(f"[DEBUG AICouncil] Processing result for {member_name}")
            
            if isinstance(result, Exception):
                logger.error(f"[DEBUG AICouncil] {member_name} research failed: {str(result)}")
                trees[member_name] = {
                    "node_id": session_id,  # Important to include node_id for tree structure
                    "topic": topic,
                    "status": "completed",
                    "research": {
                        "summary": "",
                        "key_points": [],
                        "entities": [],
                        "timeline": [],
                        "further_research": [],
                        "references": []
                    },
                    "children": []  # Important to include children array
                }
            else:
                logger.debug(f"[DEBUG AICouncil] {member_name} research succeeded")
                # Log some stats about the result
                if isinstance(result, dict) and "result" in result:
                    further_research_count = len(result["result"].get("further_research", []))
                    logger.debug(f"[DEBUG AICouncil] {member_name} found {further_research_count} further research topics")
                    
                    if further_research_count > 0:
                        topics = [item.get("topic", "Unknown") for item in result["result"].get("further_research", [])]
                        logger.debug(f"[DEBUG AICouncil] Further research topics: {topics}")
                
                trees[member_name] = {
                    "node_id": session_id,  # Important to include node_id for tree structure
                    "topic": topic,
                    "status": "completed",
                    "research": result["result"],
                    "children": []  # Important to include children array
                }
            
        logger.debug(f"[DEBUG AICouncil] Created trees structure with {len(trees)} AIs")
                    
        result_obj = {
            "topic": topic,
            "session_id": session_id,
            "parent_id": parent_id,
            "trees": trees,
            "timestamp": datetime.utcnow()
        }
        
        logger.debug(f"[DEBUG AICouncil] Research complete for topic: {topic}")
        return result_obj
        
    def enable_member(self, member_name: str):
        """Enable a council member"""
        if member_name not in self.members:
            raise ResearchError(f"Unknown member: {member_name}")
        self.members[member_name]["enabled"] = True
        
    def disable_member(self, member_name: str):
        """Disable a council member"""
        if member_name not in self.members:
            raise ResearchError(f"Unknown member: {member_name}")
        self.members[member_name]["enabled"] = False 