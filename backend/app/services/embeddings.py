from langchain_openai import OpenAIEmbeddings

from app.config import settings

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536

_embeddings: OpenAIEmbeddings | None = None


def is_available() -> bool:
    """True when an OpenAI API key is configured."""
    return bool(settings.openai_api_key)


def get_embeddings() -> OpenAIEmbeddings:
    global _embeddings
    if _embeddings is None:
        if not is_available():
            raise RuntimeError(
                "OPENAI_API_KEY is not set — vector search is unavailable"
            )
        _embeddings = OpenAIEmbeddings(
            model=EMBEDDING_MODEL,
            openai_api_key=settings.openai_api_key,
        )
    return _embeddings


def build_search_text(name: str, category: str, description: str | None = None) -> str:
    """Combine service type fields into a single string for embedding."""
    parts = [name, category]
    if description:
        parts.append(description)
    return " — ".join(parts)
