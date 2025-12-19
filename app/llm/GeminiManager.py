from app.llm.runtime import get_gemini_client
from app.llm.prompts import build_rag_prompt


class GeminiManager:
    """
    Thin wrapper around Google GenAI Gemini client.
    Client lifecycle, TTL, and secret handling are managed elsewhere.
    """

    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.model_name = model_name

    async def generate_response(
        self,
        query: str,
        context: str,
    ) -> str:
        # 🔐 Get TTL-managed Gemini client
        client = await get_gemini_client()

        prompt = build_rag_prompt(
            query=query,
            context=context,
        )

        response = client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )

        text = getattr(response, "text", None)

        if not text or not text.strip():
            raise RuntimeError("LLM returned empty response")

        return text.strip()
