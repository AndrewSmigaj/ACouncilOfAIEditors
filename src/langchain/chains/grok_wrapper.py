"""
Grok wrapper for LangChain.
"""
import json
import logging
from typing import Any, Dict, List, Optional, Union
import aiohttp
from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.schema import LLMResult, Generation

logger = logging.getLogger(__name__)

class GrokChat(LLM):
    """Grok API wrapper for LangChain"""
    
    api_key: str
    """The Grok API key."""
    
    temperature: float = 0.7
    """The temperature to use for sampling."""
    
    max_tokens: int = 2000
    """The maximum number of tokens to generate."""
    
    base_url: str = "https://api.x.ai/v1/chat/completions"
    """The base URL for the Grok API."""
    
    model: str = "grok-3"
    """The model to use."""
    
    def __init__(
        self,
        api_key: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs: Any,
    ):
        """Initialize the Grok wrapper."""
        super().__init__(**kwargs)
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
        if base_url:
            self.base_url = base_url
        if model:
            self.model = model
            
    @property
    def _llm_type(self) -> str:
        """Return the type of LLM."""
        return "grok"
        
    async def _agenerate(
        self,
        prompts: List[str],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> LLMResult:
        """Generate text from the model."""
        generations = []
        
        for prompt in prompts:
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                    
                    payload = {
                        "model": self.model,
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "max_tokens": self.max_tokens,
                        "temperature": self.temperature
                    }
                    
                    if stop:
                        payload["stop"] = stop
                        
                    async with session.post(
                        self.base_url,
                        headers=headers,
                        json=payload
                    ) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            raise Exception(f"Grok API error: {response.status} - {error_text}")
                            
                        data = await response.json()
                        
                        if "choices" not in data:
                            raise Exception("No choices in Grok API response")
                            
                        content = data["choices"][0]["message"]["content"]
                        generations.append([Generation(text=content)])
                        
            except Exception as e:
                logger.error(f"Grok API call failed: {str(e)}")
                raise Exception(f"Grok API call failed: {str(e)}")
                
        return LLMResult(generations=generations)
        
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Get the identifying parameters."""
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "base_url": self.base_url
        } 