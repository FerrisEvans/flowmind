"""
LLM Provider: OpenAI-compatible API client for calling LLM services.
Supports OpenAI API and other compatible services (e.g. local models via OpenAI-compatible endpoints).
"""

import os
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletion

# Load environment variables from .env file
load_dotenv()


class LLMProvider:
    """
    LLM client wrapper that follows OpenAI API protocol.
    Can be used with OpenAI, Azure OpenAI, or any OpenAI-compatible service.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 60.0,
    ):
        """
        Initialize LLM provider.

        Args:
            api_key: OpenAI API key. If None, reads from OPENAI_API_KEY env var.
            model: Model name (e.g. 'gpt-4', 'gpt-3.5-turbo'). If None, reads from OPENAI_MODEL env var.
            base_url: Base URL for API. If None, reads from OPENAI_BASE_URL env var, or defaults to OpenAI official.
            timeout: Request timeout in seconds.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        self.timeout = timeout

        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY not provided. Set it via parameter or OPENAI_API_KEY environment variable."
            )

        # Initialize OpenAI client
        client_kwargs = {
            "api_key": self.api_key,
            "timeout": self.timeout,
        }
        if self.base_url:
            client_kwargs["base_url"] = self.base_url

        self.client = OpenAI(**client_kwargs)

    def call(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> str:
        """
        Call LLM with a prompt and return the response text.

        Args:
            prompt: User prompt/message.
            system_prompt: Optional system message (for chat models).
            temperature: Sampling temperature (0.0-2.0). Default 0.7.
            max_tokens: Maximum tokens in response. If None, model default.
            **kwargs: Additional parameters passed to chat.completions.create().

        Returns:
            Response text from LLM.

        Raises:
            openai.APIError: API-related errors (rate limit, invalid request, etc.)
            openai.APIConnectionError: Network/connection errors
            openai.APITimeoutError: Request timeout
            ValueError: Invalid parameters
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        params = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            **kwargs,
        }
        if max_tokens is not None:
            params["max_tokens"] = max_tokens

        try:
            response: ChatCompletion = self.client.chat.completions.create(**params)
            return response.choices[0].message.content or ""
        except Exception as e:
            # Re-raise with context
            raise type(e)(f"LLM call failed: {str(e)}") from e

    def completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> ChatCompletion:
        """
        Call LLM and return the full ChatCompletion object (for advanced usage).

        Args:
            prompt: User prompt/message.
            system_prompt: Optional system message.
            temperature: Sampling temperature (0.0-2.0). Default 0.7.
            max_tokens: Maximum tokens in response. If None, model default.
            **kwargs: Additional parameters passed to chat.completions.create().

        Returns:
            Full ChatCompletion response object.

        Raises:
            openai.APIError: API-related errors
            openai.APIConnectionError: Network/connection errors
            openai.APITimeoutError: Request timeout
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        params = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "extra_body": { "thinking": { "type": "enabled" } },
            **kwargs,
        }
        if max_tokens is not None:
            params["max_tokens"] = max_tokens

        return self.client.chat.completions.create(**params)


# Convenience function: create a default provider instance
def get_default_provider() -> LLMProvider:
    """
    Create a default LLMProvider instance using environment variables.
    Useful for quick setup without explicit initialization.
    """
    return LLMProvider()

