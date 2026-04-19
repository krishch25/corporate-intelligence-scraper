"""
EY Incubator LLM Client – OpenAI SDK Version
=============================================
Uses the official `openai` Python SDK configured for
the EY Incubator Azure-compatible endpoint.

Usage:
    from llm_client_openai import EYOpenAIClient
    client = EYOpenAIClient()
    print(client.chat("What is quantum computing?"))
"""

import os
import json
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()


# ──────────────────────────────────────────────
#  Configuration
# ──────────────────────────────────────────────
EYQ_ENDPOINT = os.getenv("EYQ_INCUBATOR_ENDPOINT")
EYQ_KEY = os.getenv("EYQ_INCUBATOR_KEY")
EYQ_MODEL = os.getenv("EYQ_MODEL", "gpt-5.1")
EYQ_API_VERSION = os.getenv("EYQ_API_VERSION", "2024-02-15-preview")


class EYOpenAIClient:
    """OpenAI SDK-based client for EY Incubator."""

    def __init__(self, model=None, api_version=None):
        self.model = model or EYQ_MODEL
        self.api_version = api_version or EYQ_API_VERSION

        if not EYQ_ENDPOINT or not EYQ_KEY:
            raise ValueError(
                "Missing credentials. Set EYQ_INCUBATOR_ENDPOINT and "
                "EYQ_INCUBATOR_KEY in your .env file."
            )

        self.client = AzureOpenAI(
            azure_endpoint=EYQ_ENDPOINT,
            api_key=EYQ_KEY,
            api_version=self.api_version,
        )

    def chat_completion(self, messages, temperature=0.7, max_tokens=None):
        """
        Send a chat completion request via the OpenAI SDK.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            temperature: Sampling temperature.
            max_tokens: Max tokens in response.

        Returns:
            The ChatCompletion response object on success, None on failure.
        """
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
            }
            if max_tokens:
                kwargs["max_tokens"] = max_tokens

            response = self.client.chat.completions.create(**kwargs)
            return response

        except Exception as e:
            print(f"[EYOpenAIClient] Error: {e}")
            return None

    def chat(self, prompt, system_prompt=None, temperature=0.7, max_tokens=None):
        """
        Send a single user message and return the assistant's text.

        Args:
            prompt: The user's message.
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

        if result and result.choices:
            return result.choices[0].message.content
        return None

    def get_config(self):
        """Return the current client configuration."""
        return {
            "endpoint": EYQ_ENDPOINT,
            "model": self.model,
            "api_version": self.api_version,
            "key_set": bool(EYQ_KEY),
        }


# ──────────────────────────────────────────────
#  Quick test
# ──────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("  EY Incubator – OpenAI SDK Test")
    print("=" * 50)

    client = EYOpenAIClient()
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
