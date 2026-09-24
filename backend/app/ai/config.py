"""AI configuration for LangGraph agent."""

from typing import Dict, Any
from app.config import settings


class AIConfig:
    """AI configuration constants."""
    
    # Tool configuration
    TOOLS = {
        "log_interaction": {
            "enabled": True,
            "max_retries": 3,
            "description": "Log a new HCP interaction",
        },
        "edit_interaction": {
            "enabled": True,
            "max_retries": 3,
            "description": "Edit an existing interaction",
        },
        "view_history": {
            "enabled": True,
            "max_retries": 2,
            "description": "View interaction history",
        },
        "search_hcp": {
            "enabled": True,
            "max_retries": 2,
            "description": "Search for HCPs",
        },
        "schedule_followup": {
            "enabled": True,
            "max_retries": 3,
            "description": "Schedule a follow-up",
        },
        "analyze_trends": {
            "enabled": True,
            "max_retries": 2,
            "description": "Analyze interaction trends",
        },
        "generic_response": {
            "enabled": True,
            "max_retries": 1,
            "description": "Generate generic AI response",
        },
    }
    
    # Agent configuration
    AGENT_CONFIG = {
        "max_retries": 3,
        "confidence_threshold": 0.7,
        "max_messages": 50,
        "timeout_seconds": 30,
    }
    
    # LLM configuration
    LLM_CONFIG = {
        "model": settings.GROQ_MODEL,
        "temperature": settings.GROQ_TEMPERATURE,
        "max_tokens": settings.GROQ_MAX_TOKENS,
    }
    
    # Prompt configuration
    PROMPT_CONFIG = {
        "max_history": 10,
        "include_context": True,
        "include_entities": True,
    }
    
    # Intent mapping to tools
    INTENT_TO_TOOL = {
        "log_interaction": "log_interaction",
        "edit_interaction": "edit_interaction",
        "view_history": "view_history",
        "search_hcps": "search_hcp",
        "schedule_followup": "schedule_followup",
        "analyze_trends": "analyze_trends",
        "generic_query": "generic_response",
    }
    
    @classmethod
    def get_tool_config(cls, tool_name: str) -> Dict[str, Any]:
        """Get configuration for a specific tool."""
        return cls.TOOLS.get(tool_name, {})
    
    @classmethod
    def get_intent_for_tool(cls, tool_name: str) -> str:
        """Get the intent type for a tool."""
        for intent, tool in cls.INTENT_TO_TOOL.items():
            if tool == tool_name:
                return intent
        return "generic_query"