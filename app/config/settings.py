"""
Configurações centralizadas para Normalização Semântica com Qdrant + E5 + NER.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Garante que o Python está usando UTF-8
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Encontra o arquivo .env e carrega com UTF-8
env_file = Path(__file__).parent.parent.parent / '.env'
if env_file.exists():
    load_dotenv(env_file, encoding='utf-8', override=True)
else:
    # Tenta o arquivo .env.example se o .env não existir
    env_example = Path(__file__).parent.parent.parent / '.env.example'
    if env_example.exists():
        load_dotenv(env_example, encoding='utf-8')

# Função auxiliar para garantir strings UTF-8
def _get_env(key: str, default: str = "") -> str:
    """Obtém variável de ambiente e garante que é UTF-8."""
    value = os.getenv(key, default)
    if isinstance(value, bytes):
        try:
            return value.decode('utf-8')
        except (UnicodeDecodeError, AttributeError):
            return value.decode('utf-8', errors='replace') if isinstance(value, bytes) else str(value)
    if value is None:
        return default
    return str(value)

# ──────────────────────────────────────────────────────────────
# QDRANT Configuration
# ──────────────────────────────────────────────────────────────
QDRANT_URL = _get_env("QDRANT_URL", "http://localhost")
QDRANT_PORT = int(_get_env("QDRANT_PORT", "6333"))
QDRANT_API_KEY = _get_env("QDRANT_API_KEY", None) or None
QDRANT_COLLECTION_NAME = _get_env("QDRANT_COLLECTION_NAME", "sintomas_embeddings")
EMBEDDING_DIMENSION = int(_get_env("EMBEDDING_DIMENSION", "1024"))

# ──────────────────────────────────────────────────────────────
# PostgreSQL Configuration
# ──────────────────────────────────────────────────────────────
POSTGRES_HOST = _get_env("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(_get_env("POSTGRES_PORT", "5432"))
POSTGRES_DB = _get_env("POSTGRES_DB", "falai")
POSTGRES_USER = _get_env("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = _get_env("POSTGRES_PASSWORD", "postgres")
POSTGRES_POOL_SIZE = int(_get_env("POSTGRES_POOL_SIZE", "10"))

# Full DSN for asyncpg
POSTGRES_DSN = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
    f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

# ──────────────────────────────────────────────────────────────
# E5 Embedding Model Configuration
# ──────────────────────────────────────────────────────────────
E5_MODEL_NAME = _get_env(
    "E5_MODEL_NAME", "intfloat/multilingual-e5-large-instruct"
)
E5_CACHE_DIR = _get_env("E5_CACHE_DIR", "./models")

# ──────────────────────────────────────────────────────────────
# spaCy NER Configuration
# ──────────────────────────────────────────────────────────────
SPACY_MODEL_NAME = _get_env("SPACY_MODEL_NAME", "pt_core_news_md")
# If using custom medical NER model, set this path
SPACY_CUSTOM_MODEL_PATH = _get_env("SPACY_CUSTOM_MODEL_PATH", None) or None

# ──────────────────────────────────────────────────────────────
# Normalization Settings
# ──────────────────────────────────────────────────────────────
SIMILARITY_THRESHOLD = float(_get_env("SIMILARITY_THRESHOLD", "0.65"))
TOP_K_SEARCH = int(_get_env("TOP_K_SEARCH", "1"))

# ──────────────────────────────────────────────────────────────
# Ollama Configuration
# ──────────────────────────────────────────────────────────────
OLLAMA_BASE_URL = _get_env("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL_NAME = _get_env("OLLAMA_MODEL_NAME", "qwen3")

# ──────────────────────────────────────────────────────────────
# Application Settings
# ──────────────────────────────────────────────────────────────
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
