from __future__ import annotations

import json

from openai import AsyncOpenAI
from pydantic import BaseModel, Field, ValidationError, field_validator
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import settings


_client: AsyncOpenAI | None = None


class LlmProviderNotConfiguredError(RuntimeError):
    pass


class GeneratedAnswer(BaseModel):
    answer: str
    points: list[str] = Field(default_factory=list)
    citation_block_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    insufficient_context: bool = False

    @field_validator("points", mode="before")
    @classmethod
    def normalize_points(cls, value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item) for item in value if str(item).strip()]
        return []


def _get_client() -> AsyncOpenAI:
    global _client
    if settings.groq_api_key is None:
        raise LlmProviderNotConfiguredError("GROQ_API_KEY is required for Q&A")
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.groq_api_key,
            base_url="https://api.groq.com/openai/v1",
        )
    return _client


@retry(
    retry=retry_if_exception_type(Exception),
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=1, max=6),
    reraise=True,
)
async def generate_answer(*, question: str, context: str) -> GeneratedAnswer:
    client = _get_client()
    response = await client.chat.completions.create(
        model=settings.qa_model,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "Answer only from the supplied context. "
                    "Return JSON with keys: answer, points, citation_block_ids, confidence, insufficient_context. "
                    "points must be an array of strings; use [] when there are no bullet points. "
                    "citation_block_ids must reference only block_id values from the supplied context. "
                    "If the context is insufficient, keep answer short and confidence below 0.35."
                ),
            },
            {
                "role": "user",
                "content": f"Question:\n{question}\n\nContext:\n{context}",
            },
        ],
    )
    content = response.choices[0].message.content or "{}"
    try:
        return GeneratedAnswer.model_validate(json.loads(content))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise RuntimeError("LLM returned an invalid answer contract") from exc
