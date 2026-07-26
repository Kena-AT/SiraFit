"""
Service for checking agent API connections (e.g., Anthropic, Gemini, etc.).
"""

import os
from typing import Optional

from pydantic import BaseModel
from app.core.config import settings


class AgentAPIStatus(BaseModel):
    connected: bool
    source: str  # "env" | "settings_ui" | "none"
    provider: Optional[str] = None
    error: Optional[str] = None


def check_agent_api_connection() -> AgentAPIStatus:
    """
    Check if the agent API is properly configured and reachable.
    
    Checks:
    1. Is an API key configured (via env or settings UI)?
    2. Can we make a lightweight authenticated call to the provider?
    
    Returns:
        AgentAPIStatus: Status of the agent API connection
    """
    # Check if API keys are configured
    env_key = _get_env_api_key()
    settings_key = _get_settings_api_key()  # Would come from DB in real implementation
    
    # Determine which key to use (settings UI key takes precedence)
    active_key = settings_key or env_key
    source = "settings_ui" if settings_key else "env" if env_key else "none"
    
    if not active_key:
        return AgentAPIStatus(
            connected=False,
            source="none",
            error="No API key configured",
        )
    
    # Try to make a lightweight call to the provider
    try:
        provider = _determine_provider(active_key)
        if provider == "anthropic":
            return _check_anthropic_connection(active_key, source)
        elif provider == "gemini":
            return _check_gemini_connection(active_key, source)
        elif provider == "openrouter":
            return _check_openrouter_connection(active_key, source)
        else:
            return AgentAPIStatus(
                connected=False,
                source=source,
                provider=provider,
                error="Unknown API provider",
            )
    except Exception as e:
        return AgentAPIStatus(
            connected=False,
            source=source,
            error=f"API check failed: {str(e)}",
        )


def _get_env_api_key() -> Optional[str]:
    """Get API key from environment variables."""
    # Check for any of the supported API keys
    if settings.ANTHROPIC_API_KEY:
        return settings.ANTHROPIC_API_KEY
    if settings.GEMINI_API_KEY:
        return settings.GEMINI_API_KEY
    if settings.OPENROUTER_API_KEY:
        return settings.OPENROUTER_API_KEY
    return None


def _get_settings_api_key() -> Optional[str]:
    """
    Get API key from settings UI (stored in database).
    
    In a real implementation, this would query the database for user/org
    specific API keys. For now, we'll return None.
    """
    return None


def _determine_provider(api_key: str) -> str:
    """Determine which API provider the key is for."""
    # This is a simplified heuristic - in production you'd want more robust detection
    if api_key.startswith("sk-ant-"):
        return "anthropic"
    elif api_key.startswith("AIza"):
        return "gemini"
    elif "openrouter" in api_key.lower():
        return "openrouter"
    return "unknown"


def _check_anthropic_connection(api_key: str, source: str) -> AgentAPIStatus:
    """Check Anthropic API connection."""
    try:
        # Import here to avoid requiring the dependency if not used
        from anthropic import Anthropic
        
        # Create client with the API key
        client = Anthropic(api_key=api_key)
        
        # Make a lightweight call (list models is usually cheap)
        models = client.models.list()
        
        # If we get here, the connection is working
        return AgentAPIStatus(
            connected=True,
            source=source,
            provider="anthropic",
        )
        
    except Exception as e:
        return AgentAPIStatus(
            connected=False,
            source=source,
            provider="anthropic",
            error=f"Anthropic API error: {str(e)}",
        )


def _check_gemini_connection(api_key: str, source: str) -> AgentAPIStatus:
    """Check Gemini API connection."""
    try:
        # Import here to avoid requiring the dependency if not used
        import google.generativeai as genai
        
        # Configure the API key
        genai.configure(api_key=api_key)
        
        # Make a lightweight call
        models = genai.list_models()
        
        return AgentAPIStatus(
            connected=True,
            source=source,
            provider="gemini",
        )
        
    except Exception as e:
        return AgentAPIStatus(
            connected=False,
            source=source,
            provider="gemini",
            error=f"Gemini API error: {str(e)}",
        )


def _check_openrouter_connection(api_key: str, source: str) -> AgentAPIStatus:
    """Check OpenRouter API connection."""
    try:
        import httpx
        
        # Make a lightweight call to OpenRouter API
        response = httpx.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10.0,
        )
        response.raise_for_status()
        
        return AgentAPIStatus(
            connected=True,
            source=source,
            provider="openrouter",
        )
        
    except Exception as e:
        return AgentAPIStatus(
            connected=False,
            source=source,
            provider="openrouter",
            error=f"OpenRouter API error: {str(e)}",
        )