"""
Token counting utilities for tracking LLM usage.
"""
import logging
from typing import Dict, Any, Optional
import tiktoken
from langchain.schema import LLMResult

logger = logging.getLogger(__name__)

class TokenCounter:
    """Utility for counting tokens in LLM interactions"""
    
    def __init__(self):
        """Initialize the token counter."""
        self.encodings = {
            'gpt-3.5-turbo': tiktoken.encoding_for_model('gpt-3.5-turbo'),
            'gpt-4': tiktoken.encoding_for_model('gpt-4'),
            'claude-2': tiktoken.encoding_for_model('claude-2'),
            'gemini-pro': tiktoken.encoding_for_model('gpt-3.5-turbo'),  # Using GPT-3.5 as approximation
            'grok-3': tiktoken.encoding_for_model('gpt-3.5-turbo')  # Using GPT-3.5 as approximation
        }
        
    def count_tokens(self, text: str, model: str = 'gpt-3.5-turbo') -> int:
        """Count tokens in text for a specific model."""
        try:
            encoding = self.encodings.get(model, self.encodings['gpt-3.5-turbo'])
            return len(encoding.encode(text))
        except Exception as e:
            logger.error(f"Failed to count tokens: {str(e)}")
            return 0
            
    def count_llm_result_tokens(self, result: LLMResult, model: str = 'gpt-3.5-turbo') -> Dict[str, int]:
        """Count tokens in an LLM result."""
        try:
            total_tokens = 0
            prompt_tokens = 0
            completion_tokens = 0
            
            # Count tokens in each generation
            for generation_list in result.generations:
                for generation in generation_list:
                    completion_tokens += self.count_tokens(generation.text, model)
                    
            # If we have prompt information, count those tokens
            if hasattr(result, 'llm_output') and result.llm_output:
                if isinstance(result.llm_output, dict):
                    if 'prompt_tokens' in result.llm_output:
                        prompt_tokens = result.llm_output['prompt_tokens']
                    if 'total_tokens' in result.llm_output:
                        total_tokens = result.llm_output['total_tokens']
                        
            return {
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_tokens': total_tokens or (prompt_tokens + completion_tokens)
            }
            
        except Exception as e:
            logger.error(f"Failed to count LLM result tokens: {str(e)}")
            return {
                'prompt_tokens': 0,
                'completion_tokens': 0,
                'total_tokens': 0
            }
            
    def count_interaction_tokens(
        self,
        prompt: str,
        response: str,
        model: str = 'gpt-3.5-turbo'
    ) -> Dict[str, int]:
        """Count tokens in a complete interaction."""
        try:
            prompt_tokens = self.count_tokens(prompt, model)
            completion_tokens = self.count_tokens(response, model)
            
            return {
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_tokens': prompt_tokens + completion_tokens
            }
            
        except Exception as e:
            logger.error(f"Failed to count interaction tokens: {str(e)}")
            return {
                'prompt_tokens': 0,
                'completion_tokens': 0,
                'total_tokens': 0
            } 