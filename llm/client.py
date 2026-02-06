"""
LLM client interface for approval stage reasoning.

Supports:
- xAI Grok via OpenAI-compatible API
- Deterministic mock fallback for local testing

Environment variable:
- XAI_API_KEY: API key for xAI Grok (optional, auto-loaded from .env)

If XAI_API_KEY is not set, the system falls back to a deterministic mock
so the pipeline can run end-to-end without external dependencies.
"""

import json
import os
import urllib.request
from pathlib import Path
from typing import Dict, List


def load_env_file(env_path: str = ".env"):
    """
    Load environment variables from .env file if it exists.

    Simple stdlib parser for KEY=VALUE format.
    Skips comments (#) and empty lines.
    """
    env_file = Path(env_path)
    if not env_file.exists():
        return

    with open(env_file) as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue
            # Parse KEY=VALUE
            if "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()


class LLMClient:
    """
    Interface for LLM-based reasoning.

    Automatically selects Grok or mock backend based on XAI_API_KEY.
    Auto-loads .env file on initialization.
    """

    def __init__(self):
        # Auto-load .env file
        load_env_file()

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

        """
        if self.backend == "grok":
            return self._grok_completion(messages, model)
        else:
            return self._mock_completion(messages)

    def _grok_completion(self, messages: List[Dict[str, str]], model: str) -> str:
        """
        Call xAI Grok API (OpenAI-compatible).

        Uses stdlib urllib for HTTP requests (no external dependencies).
        Falls back to mock on error.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {"model": model, "messages": messages, "temperature": 0.3}

        req = urllib.request.Request(
            "https://api.x.ai/v1/chat/completions",
            data=json.dumps(data).encode(),
            headers=headers,
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read())
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            # Fallback to mock on error
            print(f"Grok API error: {e}, falling back to mock")
            return self._mock_completion(messages)

    def _mock_completion(self, messages: List[Dict[str, str]]) -> str:
        """
        Deterministic mock LLM for testing.

        Provides rule-based responses for reflection/critique scenarios.
        """
        content = messages[-1]["content"].lower()

        # Detect reflection scenario
        if "contradiction" in content or "review" in content:
            if "approved despite" in content and "error" in content:
                return "REVISED: Reject due to ERROR-level validation findings. Policy requires rejection when errors are present."
            elif "missing scrutiny" in content or "high" in content:
                return "REVISED: Add reason - High-value invoice requires additional review per policy."
            elif "rejected without" in content:
                return "REVISED: Add clear rejection reason based on validation findings or missing data."

        # Default approval reasoning
        return "Approved: All validation checks passed and invoice data is complete."
