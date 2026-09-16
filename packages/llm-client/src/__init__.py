"""
CareerCompiler LLM Client Package
Provides a provider-agnostic LLM abstraction backed by Groq (primary).
"""

from .groq_client import GroqClient, get_llm_client

__all__ = ["GroqClient", "get_llm_client"]
