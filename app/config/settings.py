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
    # Variáveis injetadas pelo ambiente de execução (Docker/hosting/secrets)
    # devem ter prioridade sobre os valores locais do arquivo .env.
    load_dotenv(env_file, encoding='utf-8', override=False)
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
QDRANT_COLLECTION_NAME = _get_env("QDRANT_COLLECTION_NAME", "sintomas_embeddings_v2")
QDRANT_CLOUD_INFERENCE = _get_env("QDRANT_CLOUD_INFERENCE", "true").lower() == "true"
QDRANT_INFERENCE_MODEL = _get_env(
    "QDRANT_INFERENCE_MODEL", "intfloat/multilingual-e5-small"
)
EMBEDDING_DIMENSION = int(_get_env("EMBEDDING_DIMENSION", "384"))

# ──────────────────────────────────────────────────────────────
# PostgreSQL Configuration
# ──────────────────────────────────────────────────────────────
POSTGRES_DSN = _get_env("POSTGRES_DSN", "")
POSTGRES_POOL_SIZE = int(_get_env("POSTGRES_POOL_SIZE", "2"))

if not POSTGRES_DSN:
    raise RuntimeError("POSTGRES_DSN é obrigatório")

# Supabase Data API (chave publicável; não substitui POSTGRES_DSN)
SUPABASE_URL = _get_env("SUPABASE_URL", "")
SUPABASE_KEY = _get_env("SUPABASE_KEY", "")

# ──────────────────────────────────────────────────────────────
# E5 Embedding Model Configuration
# ──────────────────────────────────────────────────────────────
# Alias mantido para respostas de diagnóstico e compatibilidade interna.
E5_MODEL_NAME = QDRANT_INFERENCE_MODEL

# ──────────────────────────────────────────────────────────────
# spaCy NER Configuration
# ──────────────────────────────────────────────────────────────
SPACY_MODEL_NAME = _get_env("SPACY_MODEL_NAME", "pt_core_news_md")
# If using custom medical NER model, set this path
SPACY_CUSTOM_MODEL_PATH = _get_env("SPACY_CUSTOM_MODEL_PATH", None) or None

# ──────────────────────────────────────────────────────────────
# Normalization Settings
# ──────────────────────────────────────────────────────────────
SIMILARITY_THRESHOLD = float(_get_env("SIMILARITY_THRESHOLD", "0.92"))
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
