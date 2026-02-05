"""
LLM client interface for approval stage reasoning.

Supports:
- xAI Grok via OpenAI-compatible API
- Deterministic mock fallback for local testing

Environment variable:
- XAI_API_KEY: API key for xAI Grok (optional)

If XAI_API_KEY is not set, the system falls back to a deterministic mock
so the pipeline can run end-to-end without external dependencies.

TODO: [Slice 5] Implement actual Grok integration
TODO: [Slice 5] Implement deterministic mock LLM
"""

import os
from typing import Dict, List


class LLMClient:
    """
    Interface for LLM-based reasoning.

    Automatically selects Grok or mock backend based on XAI_API_KEY.
    """

    def __init__(self):
        self.api_key = os.getenv("XAI_API_KEY")
        self.backend = "grok" if self.api_key else "mock"

    def chat_completion(
        self, messages: List[Dict[str, str]], model: str = "grok-beta"
    ) -> str:
        """
        Generate a chat completion response.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (default: grok-beta)

        Returns:
            String response from LLM

        TODO: [Slice 5] Implement actual Grok API call
        TODO: [Slice 5] Implement deterministic mock response
        """
        if self.backend == "grok":
            return self._grok_completion(messages, model)
        else:
            return self._mock_completion(messages)

    def _grok_completion(self, messages: List[Dict[str, str]], model: str) -> str:
        """
        Call xAI Grok API (OpenAI-compatible).

        TODO: [Slice 5] Implement actual API call
        - Use openai library with base_url="https://api.x.ai/v1"
        - Handle errors gracefully
        - Log token usage
        """
        return "[Grok not implemented yet]"

    def _mock_completion(self, messages: List[Dict[str, str]]) -> str:
        """
        Deterministic mock LLM for testing.

        TODO: [Slice 5] Implement rule-based mock responses
        - Parse message content for approval/rejection keywords
        - Return deterministic reasoning based on input
        - Support reflection/critique scenarios
        """
        return "[Mock LLM not implemented yet]"
