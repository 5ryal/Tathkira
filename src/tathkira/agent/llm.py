"""Gemini-backed llm function used by the draft step."""

import os

from dotenv import load_dotenv
from google import genai
from google.genai import types


def call_gemini(prompt: str) -> str:
    """Send a prompt to Gemini and return its raw text reply."""
    load_dotenv()
    api_key = os.getenv("LLM_API_KEY")
    model = os.getenv("LLM_MODEL")
    if not api_key or not model:
        raise ValueError("missing LLM_API_KEY or LLM_MODEL")

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    return response.text or ""
