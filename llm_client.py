"""
EY Incubator LLM Client
========================
A reusable client for accessing OpenAI models via the EY Incubator endpoint.
Supports both the raw `requests` approach and the official `openai` SDK.

Usage:
    from llm_client import EYLLMClient
    client = EYLLMClient()
    response = client.chat("What is quantum computing?")
    print(response)
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()


# ──────────────────────────────────────────────
#  Configuration (loaded once from .env)
# ──────────────────────────────────────────────
EYQ_ENDPOINT = os.getenv("EYQ_INCUBATOR_ENDPOINT")
EYQ_KEY = os.getenv("EYQ_INCUBATOR_KEY")
EYQ_MODEL = os.getenv("EYQ_MODEL", "gpt-5.1")
EYQ_API_VERSION = os.getenv("EYQ_API_VERSION", "2024-02-15-preview")


class EYLLMClient:
    """Client for EY Incubator OpenAI-compatible API."""

    def __init__(self, model=None, api_version=None):
        self.endpoint = EYQ_ENDPOINT
        self.api_key = EYQ_KEY
        self.model = model or EYQ_MODEL
        self.api_version = api_version or EYQ_API_VERSION

        if not self.endpoint or not self.api_key:
            raise ValueError(
                "Missing credentials. Set EYQ_INCUBATOR_ENDPOINT and "
                "EYQ_INCUBATOR_KEY in your .env file."
            )

    # ── Core: Chat Completion ────────────────
    def chat_completion(self, messages, temperature=0.7, max_tokens=None, stream=False):
        """
        Send a chat completion request to the EY Incubator API.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            temperature: Sampling temperature (0.0 – 2.0).
            max_tokens: Maximum tokens in the response (None = model default).
            stream: Whether to stream the response.

        Returns:
            dict: The full API response JSON on success.
            None: On failure.
        """
        base_url = self.endpoint.rstrip("/")
        url = f"{base_url}/openai/deployments/{self.model}/chat/completions"

        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
        }

        params = {"api-version": self.api_version}

        body = {
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            body["max_tokens"] = max_tokens

        try:
            response = requests.post(
                url, json=body, headers=headers, params=params, timeout=60
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            print(f"[EYLLMClient] HTTP {response.status_code}: {e}")
            try:
                err = response.json()
                print(f"[EYLLMClient] Error detail: {json.dumps(err, indent=2)}")
            except Exception:
                print(f"[EYLLMClient] Raw response: {response.text}")
            return None

        except requests.exceptions.ConnectionError:
            print("[EYLLMClient] Connection failed – check VPN / network access.")
            return None

        except Exception as e:
            print(f"[EYLLMClient] Unexpected error: {e}")
            return None

    # ── Convenience: Simple Chat ─────────────
    def chat(self, prompt, system_prompt=None, temperature=0.7, max_tokens=None):
        """
        Send a single user message and return the assistant's text.

        Args:
            prompt: The user's message string.
            system_prompt: Optional system instruction.
            temperature: Sampling temperature.
            max_tokens: Max tokens in response.

        Returns:
            str: The assistant's reply text, or None on failure.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        result = self.chat_completion(
            messages, temperature=temperature, max_tokens=max_tokens
        )

        if result and "choices" in result:
            return result["choices"][0]["message"]["content"]
        return None

    # ── Info ──────────────────────────────────
    def get_config(self):
        """Return the current client configuration (safe to log)."""
        return {
            "endpoint": self.endpoint,
            "model": self.model,
            "api_version": self.api_version,
            "key_set": bool(self.api_key),
        }


# ──────────────────────────────────────────────
#  Quick test
# ──────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("  EY Incubator LLM Client – Connection Test")
    print("=" * 50)

    client = EYLLMClient()
    config = client.get_config()
    print(f"\nConfig: {json.dumps(config, indent=2)}")

    print("\nSending test prompt to GPT-5.1 ...")
    reply = client.chat(
        prompt="Explain Newton's second law in exactly 20 words.",
        temperature=0.5,
    )

    if reply:
        print(f"\n✅ Success! Response:\n{reply}\n")
    else:
        print(
            "\n❌ Connection failed. Common fixes:\n"
            "  1. Ensure you are on the EY VPN / network.\n"
            "  2. Verify the API key is active.\n"
            "  3. Confirm the model 'gpt-5.1' is deployed.\n"
        )
