from __future__ import annotations

from openai import AsyncOpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import settings


BATCH_SIZE = 100
_client: AsyncOpenAI | None = None


class EmbeddingProviderNotConfiguredError(RuntimeError):
    pass


def _get_client() -> AsyncOpenAI:
    global _client
    if settings.openai_api_key is None:
        raise EmbeddingProviderNotConfiguredError("OPENAI_API_KEY is required for embeddings")
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


@retry(
    retry=retry_if_exception_type(Exception),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
async def _embed_batch(client: AsyncOpenAI, batch: list[str]) -> list[list[float]]:
    response = await client.embeddings.create(
        model=settings.embedding_model,
        input=batch,
        dimensions=settings.embedding_dimensions,
    )
    return [item.embedding for item in response.data]


async def embed_texts(texts: list[str]) -> list[list[float]]:
    cleaned = [" ".join(text.split()).strip() for text in texts]
    if any(not text for text in cleaned):
        raise ValueError("Cannot embed blank text")

    client = _get_client()
    results: list[list[float]] = []

    for index in range(0, len(cleaned), BATCH_SIZE):
        batch = cleaned[index : index + BATCH_SIZE]
        results.extend(await _embed_batch(client, batch))

    if len(results) != len(cleaned):
        raise RuntimeError("Embedding provider returned an unexpected number of vectors")
    return results
