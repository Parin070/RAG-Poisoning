"""
app/llm_client.py

LLM client using OpenRouter via the OpenAI-compatible API.
Reads configuration from environment variables (via .env).
"""

import os
from openai import OpenAI, APIError, RateLimitError, APIConnectionError


def get_llm_client() -> OpenAI:
    """Create an OpenAI client pointed at OpenRouter."""
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY is not set. "
            "Copy .env.example to .env and add your key."
        )
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )


def get_model_name() -> str:
    """Return the configured model name, with a sensible default."""
    return os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-001")


def build_rag_prompt(query: str, context_chunks: list[tuple[str, str, float]]) -> str:
    """
    Build the system + user prompt for the RAG chatbot.
    Instructs the LLM to answer ONLY from the provided context.
    """
    context_block = "\n\n---\n\n".join(
        f"[Source: {source}]\n{text}" for text, source, _score in context_chunks
    )

    system_message = (
        "You are the Acme Corp internal AI assistant. "
        "Answer the employee's question using ONLY the context provided below. "
        "If the context does not contain enough information to answer, say "
        "\"I don't have enough information in the knowledge base to answer that.\" "
        "Do not make up information. Cite the source document when possible."
    )

    user_message = (
        f"Context:\n{context_block}\n\n"
        f"Question: {query}\n\n"
        f"Answer:"
    )

    return system_message, user_message


def ask_llm(query: str, context_chunks: list[tuple[str, str, float]]) -> str:
    """
    Send a RAG query to the LLM and return the response text.
    Handles API errors gracefully, returning an error message string
    instead of raising.
    """
    try:
        client = get_llm_client()
    except ValueError as e:
        return f"⚠️ Configuration error: {e}"

    model = get_model_name()
    system_message, user_message = build_rag_prompt(query, context_chunks)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            temperature=0,
            max_tokens=512,
        )
        return response.choices[0].message.content.strip()

    except RateLimitError:
        return (
            "⚠️ Rate limit exceeded on OpenRouter. "
            "Please wait a moment and try again, or switch to a free model "
            "in your .env file (OPENROUTER_MODEL)."
        )
    except APIConnectionError:
        return (
            "⚠️ Could not connect to OpenRouter. "
            "Check your internet connection and try again."
        )
    except APIError as e:
        return f"⚠️ OpenRouter API error: {e.message}"
    except Exception as e:
        return f"⚠️ Unexpected error: {e}"

