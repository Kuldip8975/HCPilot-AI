"""Agent state management for LangGraph."""

from typing import List, Dict, Any, Optional, TypedDict, Literal
from datetime import datetime
from enum import Enum

from app.core.constants import IntentType


class MessageRole(str, Enum):
    """Message role enum."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class Message(TypedDict):
    """Message structure for agent conversations."""
    role: MessageRole
    content: str
    timestamp: str
    metadata: Optional[Dict[str, Any]]


class AgentState(TypedDict):
    """
    Agent state for LangGraph workflow.
    """
    # Conversation
    messages: List[Message]
    session_id: str
    user_id: str
    
    # Intent
    intent: Optional[IntentType]
    confidence: float
    extracted_entities: Dict[str, Any]
    
    # Tool execution
    selected_tool: Optional[str]
    tool_input: Optional[Dict[str, Any]]
    tool_output: Optional[Dict[str, Any]]
    tool_execution_history: List[Dict[str, Any]]
    
    # Context
    context: Dict[str, Any]
    hcp_context: Optional[Dict[str, Any]]
    interaction_context: Optional[Dict[str, Any]]
    
    # Validation
    validation_passed: bool
    validation_errors: List[str]
    retry_count: int
    
    # Response
    response: Optional[str]
    should_end: bool
    
    # Metadata
    start_time: str
    last_updated: str
    error: Optional[str]


def create_initial_state(
    user_id: str,
    session_id: str,
    message: str,
    context: Optional[Dict[str, Any]] = None
) -> AgentState:
    """
    Create initial agent state.
    
    Args:
        user_id: User identifier
        session_id: Session identifier
        message: User message
        context: Additional context
        
    Returns:
        Initial agent state
    """
    now = datetime.utcnow().isoformat()
    
    return AgentState(
        messages=[
            {
                "role": MessageRole.USER,
                "content": message,
                "timestamp": now,
                "metadata": None,
            }
        ],
        session_id=session_id,
        user_id=user_id,
        intent=None,
        confidence=0.0,
        extracted_entities={},
        selected_tool=None,
        tool_input=None,
        tool_output=None,
        tool_execution_history=[],
        context=context or {},
        hcp_context=None,
        interaction_context=None,
        validation_passed=False,
        validation_errors=[],
        retry_count=0,
        response=None,
        should_end=False,
        start_time=now,
        last_updated=now,
        error=None,
    )


def add_message(
    state: AgentState,
    role: MessageRole,
    content: str,
    metadata: Optional[Dict[str, Any]] = None
) -> AgentState:
    """
    Add a message to the agent state.
    
    Args:
        state: Current agent state
        role: Message role
        content: Message content
        metadata: Additional metadata
        
    Returns:
        Updated agent state
    """
    messages = state.get("messages", [])
    messages.append({
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat(),
        "metadata": metadata,
    })
    
    state["messages"] = messages
    state["last_updated"] = datetime.utcnow().isoformat()
    
    return state