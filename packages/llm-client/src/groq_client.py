"""
Groq LLM Client — LangChain-backed abstraction for CareerCompiler agents.

Design:
- Primary model: llama-3.3-70b-versatile (strong reasoning)
- Fast model:    llama-3.1-8b-instant    (cheap extraction tasks)
- All calls use structured output (JSON schema-validated) where possible
- Retries handled by tenacity with exponential backoff
- Provider can be swapped by changing the underlying ChatModel

Usage:
    client = GroqClient.from_env()
    response = await client.chat("Summarize this resume section", system_prompt="...")
    structured = await client.structured_chat(prompt, schema=MyPydanticModel)
"""

from __future__ import annotations

import logging
import os
from typing import Any, Optional, Type, TypeVar

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_groq import ChatGroq
from pydantic import BaseModel
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# ─── Constants ────────────────────────────────────────────────────────────────
DEFAULT_PRIMARY_MODEL = "llama-3.3-70b-versatile"
DEFAULT_FAST_MODEL = "llama-3.1-8b-instant"
DEFAULT_TEMPERATURE = 0.1   # low temperature for factual, deterministic outputs
DEFAULT_MAX_TOKENS = 4096
MAX_RETRIES = 3


class LLMError(Exception):
    """Raised when LLM call fails after all retries."""


class GroqClient:
    """
    Thin wrapper around LangChain ChatGroq.
    Provides sync and async chat + structured-output helpers.
    """

    def __init__(
        self,
        api_key: str,
        primary_model: str = DEFAULT_PRIMARY_MODEL,
        fast_model: str = DEFAULT_FAST_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> None:
        self._api_key = api_key
        self._primary_model_name = primary_model
        self._fast_model_name = fast_model
        self._temperature = temperature
        self._max_tokens = max_tokens

        self._primary_llm = ChatGroq(
            api_key=api_key,
            model=primary_model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        self._fast_llm = ChatGroq(
            api_key=api_key,
            model=fast_model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    @classmethod
    def from_env(cls) -> "GroqClient":
        """Create client from environment variables."""
        try:
            from dotenv import load_dotenv, find_dotenv
            load_dotenv(find_dotenv())
        except ImportError:
            pass
            
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError("GROQ_API_KEY environment variable is not set")
        return cls(
            api_key=api_key,
            primary_model=os.environ.get("GROQ_MODEL_PRIMARY", DEFAULT_PRIMARY_MODEL),
            fast_model=os.environ.get("GROQ_MODEL_FAST", DEFAULT_FAST_MODEL),
        )

    def _build_messages(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> list:
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))
        return messages

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def chat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        use_fast_model: bool = False,
    ) -> str:
        """
        Synchronous chat call. Returns text response.
        Use use_fast_model=True for cheap extraction tasks.
        """
        llm = self._fast_llm if use_fast_model else self._primary_llm
        messages = self._build_messages(prompt, system_prompt)
        try:
            response = llm.invoke(messages)
            return response.content
        except Exception as exc:
            logger.error("Groq chat failed: %s", exc)
            raise LLMError(f"LLM call failed: {exc}") from exc

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def achat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        use_fast_model: bool = False,
    ) -> str:
        """Async chat call. Returns text response."""
        llm = self._fast_llm if use_fast_model else self._primary_llm
        messages = self._build_messages(prompt, system_prompt)
        try:
            response = await llm.ainvoke(messages)
            return response.content
        except Exception as exc:
            logger.error("Groq async chat failed: %s", exc)
            raise LLMError(f"LLM async call failed: {exc}") from exc

    def structured_chat(
        self,
        prompt: str,
        schema: Type[T],
        system_prompt: Optional[str] = None,
        use_fast_model: bool = False,
    ) -> T:
        """
        Chat call that parses the LLM response into a Pydantic model.
        The schema is serialized to JSON schema and injected into the prompt.
        """
        llm = self._fast_llm if use_fast_model else self._primary_llm
        parser = JsonOutputParser(pydantic_object=schema)
        format_instructions = parser.get_format_instructions()

        full_prompt = f"{prompt}\n\n{format_instructions}"
        messages = self._build_messages(full_prompt, system_prompt)

        try:
            response = llm.invoke(messages)
            parsed_dict = parser.parse(response.content)
            return schema(**parsed_dict)
        except Exception as exc:
            logger.error("Groq structured chat failed: %s", exc)
            raise LLMError(f"Structured LLM call failed: {exc}") from exc

    async def astructured_chat(
        self,
        prompt: str,
        schema: Type[T],
        system_prompt: Optional[str] = None,
        use_fast_model: bool = False,
    ) -> T:
        """Async structured chat call."""
        llm = self._fast_llm if use_fast_model else self._primary_llm
        parser = JsonOutputParser(pydantic_object=schema)
        format_instructions = parser.get_format_instructions()

        full_prompt = f"{prompt}\n\n{format_instructions}"
        messages = self._build_messages(full_prompt, system_prompt)

        try:
            response = await llm.ainvoke(messages)
            parsed_dict = parser.parse(response.content)
            return schema(**parsed_dict)
        except Exception as exc:
            logger.error("Groq async structured chat failed: %s", exc)
            raise LLMError(f"Async structured LLM call failed: {exc}") from exc

    def health_check(self) -> dict[str, Any]:
        """
        Verify Groq API connectivity. Called on startup.
        Returns a dict with status and model info.
        """
        try:
            response = self._fast_llm.invoke([HumanMessage(content="ping")])
            return {
                "status": "ok",
                "primary_model": self._primary_model_name,
                "fast_model": self._fast_model_name,
                "provider": "groq",
            }
        except Exception as exc:
            logger.warning("Groq health check failed: %s", exc)
            return {
                "status": "degraded",
                "error": str(exc),
                "provider": "groq",
            }


# ─── Module-level factory ─────────────────────────────────────────────────────
_client: Optional[GroqClient] = None


def get_llm_client() -> GroqClient:
    """
    Return the singleton GroqClient instance.
    Call this from FastAPI dependency injection.
    """
    global _client
    if _client is None:
        _client = GroqClient.from_env()
    return _client
