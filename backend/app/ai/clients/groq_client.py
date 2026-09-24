"""Groq API client for LLM inference."""

import json
import logging
from typing import Optional, Dict, Any, List
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from groq import AsyncGroq
from app.config import settings
from app.core.exceptions import GroqAPIError

logger = logging.getLogger(__name__)


class GroqClient:
    """Async client for Groq API with retry logic."""

    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.default_model = settings.GROQ_MODEL
        self.alternative_model = settings.GROQ_ALTERNATIVE_MODEL
        self.max_tokens = settings.GROQ_MAX_TOKENS
        self.temperature = settings.GROQ_TEMPERATURE
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is required")
        
        self._client = AsyncGroq(api_key=self.api_key)
        logger.info(f"Groq client initialized with model: {self.default_model}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> str:
        """Send chat completion request to Groq."""
        try:
            model = model or self.default_model
            temperature = temperature or self.temperature
            max_tokens = max_tokens or self.max_tokens
            
            request_params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                **kwargs,
            }
            
            if response_format:
                request_params["response_format"] = response_format
            
            response = await self._client.chat.completions.create(**request_params)
            
            if not response.choices:
                raise GroqAPIError("No choices returned from Groq")
            
            content = response.choices[0].message.content
            if not content:
                raise GroqAPIError("Empty response from Groq")
            
            return content
            
        except Exception as e:
            logger.error(f"Groq API error: {str(e)}")
            raise GroqAPIError(f"Groq API request failed: {str(e)}")

    async def extract_json(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Get JSON response from Groq."""
        response = await self.chat_completion(
            messages=messages,
            response_format={"type": "json_object"},
            **kwargs
        )
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {response[:200]}...")
            raise GroqAPIError(f"Invalid JSON response: {str(e)}")