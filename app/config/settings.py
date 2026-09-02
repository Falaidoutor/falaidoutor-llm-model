"""Configuration for the cloud semantic-normalization pipeline."""

import os
from pathlib import Path

from dotenv import load_dotenv


_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(_ENV_FILE, encoding="utf-8", override=False)


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


QDRANT_URL = _env("QDRANT_URL", "http://localhost")
QDRANT_PORT = int(_env("QDRANT_PORT", "6333"))
QDRANT_API_KEY = _env("QDRANT_API_KEY") or None
QDRANT_COLLECTION_NAME = _env(
    "QDRANT_COLLECTION_NAME", "sintomas_embeddings_v2"
)
QDRANT_CLOUD_INFERENCE = _env(
    "QDRANT_CLOUD_INFERENCE", "true"
).lower() == "true"
QDRANT_INFERENCE_MODEL = _env(
    "QDRANT_INFERENCE_MODEL", "intfloat/multilingual-e5-small"
)
EMBEDDING_DIMENSION = int(_env("EMBEDDING_DIMENSION", "384"))

POSTGRES_DSN = _env("POSTGRES_DSN")
POSTGRES_POOL_SIZE = int(_env("POSTGRES_POOL_SIZE", "2"))

SUPABASE_URL = _env("SUPABASE_URL")
SUPABASE_KEY = _env("SUPABASE_KEY")

SIMILARITY_THRESHOLD = float(_env("SIMILARITY_THRESHOLD", "0.92"))
TOP_K_SEARCH = int(_env("TOP_K_SEARCH", "1"))

DEBUG = _env("DEBUG", "false").lower() == "true"
LOG_LEVEL = _env("LOG_LEVEL", "INFO")
