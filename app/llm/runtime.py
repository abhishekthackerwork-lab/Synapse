import time
import google.genai as genai
from typing import Optional

from app.security.vault_client import vault_client
from app.security.secret_buffer import SecretBuffer

_GEMINI_TTL = 60 * 60  # 1 hour

_gemini_client: Optional[genai.Client] = None
_gemini_expiry: float = 0.0
_secret_buf: Optional[SecretBuffer] = None


async def get_gemini_client() -> genai.Client:
    global _gemini_client, _gemini_expiry, _secret_buf

    now = time.time()

    # Reuse valid client
    if _gemini_client is not None and now < _gemini_expiry:
        return _gemini_client

    # Invalidate old state
    if _secret_buf is not None:
        _secret_buf.wipe()
        _secret_buf = None

    _gemini_client = None
    _gemini_expiry = 0.0

    # Fetch LLM secret (KV v1)
    secret = await vault_client.read_kv_secret("llm/google_genai")

    api_key = secret.get("value")
    if not api_key:
        raise RuntimeError("Google GenAI API key not found in Vault")

    _secret_buf = SecretBuffer(api_key)

    _gemini_client = genai.Client(
        api_key=_secret_buf.get().decode("utf-8")
    )

    _gemini_expiry = now + _GEMINI_TTL

    return _gemini_client
