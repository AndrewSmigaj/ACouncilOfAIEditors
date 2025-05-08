"""
AI Council implementation using LangChain for orchestration.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
import logging
import json
from langchain.chains import SequentialChain, LLMChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_xai import ChatXAI
from .research_base import ResearchConfig, ResearchError

# Configure logging
logger = logging.getLogger(__name__)

class AICouncilMember:
    """A member of the AI Council using LangChain"""
    def __init__(self, name: str, config: ResearchConfig):
        self.name = name
        self.config = config
        self.chain = self._create_chain()
        
    def _create_chain(self) -> LLMChain:
        """Create LangChain chain for this member"""
        if self.name == "claude":
            llm = ChatAnthropic(
                anthropic_api_key=self.config.anthropic_api_key,
                model="claude-3-opus-20240229",
                temperature=0.7,
                max_tokens=4000
            )
        elif self.name == "chatgpt":
            llm = ChatOpenAI(
                openai_api_key=self.config.openai_api_key,
                model="gpt-4-turbo-preview",
                temperature=0.7,
                max_tokens=4000
            )
        elif self.name == "gemini":
            llm = ChatGoogleGenerativeAI(
                google_api_key=self.config.google_api_key,
                model="gemini-pro",
                temperature=0.7,
                max_tokens=4000
            )
        elif self.name == "grok":
            llm = ChatXAI(
                xai_api_key=self.config.xai_api_key,
                model="grok-2-1212",
                temperature=0.7,
                max_tokens=4000
            )
        else:
            raise ValueError(f"Unknown AI member: {self.name}")
            
        prompt = PromptTemplate(
            input_variables=["topic"],
            template="""As an AI research assistant, analyze the following topic: {topic}
            
            Provide a comprehensive analysis including:
            1. Summary
            2. Key points
            3. Important entities
            4. Timeline of events
            5. Areas for further research
            6. References
            
            Format your response as a JSON object with these fields."""
        )
        
        return LLMChain(
            llm=llm,
            prompt=prompt,
            memory=ConversationBufferMemory(),
            verbose=True
        )
        
    async def research(self, topic: str) -> Dict[str, Any]:
        """Conduct research using LangChain"""
        try:
            # Run chain
            result = await self.chain.arun(topic=topic)
            
            # Parse result
            try:
                # Extract JSON if wrapped in markdown
                if "```json" in result:
                    result = result.split("```json")[1].split("```")[0]
                elif "```" in result:
                    result = result.split("```")[1].split("```")[0]
                    
                structured_data = json.loads(result)
                
                # Validate required fields
                required_fields = [
                    "summary", "key_points", "entities",
                    "timeline", "further_research", "references"
                ]
                
                for field in required_fields:
                    if field not in structured_data:
                        structured_data[field] = [] if field != "summary" else ""
                        
                return {
                    "ai_name": self.name,
                    "result": structured_data,
                    "timestamp": datetime.utcnow()
                }
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse {self.name} response as JSON: {str(e)}")
                logger.error(f"Raw content: {result}")
                raise ResearchError(f"Failed to parse {self.name} response as JSON")
                
        except Exception as e:
            logger.error(f"{self.name} research failed: {str(e)}")
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
        tasks = []
        
        # Add tasks for all enabled members
        for member_name, member_config in self.members.items():
            if member_config["enabled"]:
                member = AICouncilMember(member_name, member_config["config"])
                tasks.append(member.research(topic))
                    
        # Run all research in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        research_results = {}
        
        for member_name, member_config in self.members.items():
            if member_config["enabled"]:
                result = results.pop(0)
                if isinstance(result, Exception):
                    logger.error(f"{member_name} research failed: {str(result)}")
                    research_results[member_name] = {
                        "summary": "",
                        "key_points": [],
                        "entities": [],
                        "timeline": [],
                        "further_research": [],
                        "references": []
                    }
                else:
                    research_results[member_name] = result["result"]
                    
        return {
            "topic": topic,
            "session_id": session_id,
            "parent_id": parent_id,
            "research_results": research_results,
            "timestamp": datetime.utcnow()
        }
        
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