"""
Cliente HuggingFace Inference API.
Modelo: Qwen/Qwen2.5-7B-Instruct (multilingue, gratis)
"""

import os
from huggingface_hub import InferenceClient

HF_TOKEN = os.getenv("HF_TOKEN", "")
HF_MODEL = os.getenv("HF_MODEL", "Qwen/Qwen2.5-7B-Instruct")

_client: InferenceClient | None = None


def get_client() -> InferenceClient:
    global _client
    if _client is None:
        if not HF_TOKEN:
            raise ValueError("HF_TOKEN no configurado en .env")
        _client = InferenceClient(api_key=HF_TOKEN)
    return _client


def chat(messages: list[dict], max_tokens: int = 1024, temperature: float = 0.3) -> str:
    """
    Llama al modelo de HuggingFace y devuelve el texto generado.
    messages: lista de {"role": "system"|"user"|"assistant", "content": "..."}
    """
    client = get_client()
    response = client.chat_completion(
        model=HF_MODEL,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()


def is_available() -> bool:
    try:
        chat([{"role": "user", "content": "ok"}], max_tokens=5)
        return True
    except Exception:
        return False
