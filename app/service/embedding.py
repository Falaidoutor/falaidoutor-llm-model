"""Constrói documentos para a inferência remota do Qdrant Cloud."""

import logging
from typing import List

from qdrant_client.models import Document

from app.config.settings import (
    EMBEDDING_DIMENSION,
    QDRANT_CLOUD_INFERENCE,
    QDRANT_INFERENCE_MODEL,
)

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Prepara entradas E5 sem carregar modelos de embedding localmente."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        if not QDRANT_CLOUD_INFERENCE:
            raise RuntimeError(
                "QDRANT_CLOUD_INFERENCE deve estar habilitado para gerar embeddings "
                "pelo Qdrant Cloud"
            )

        self._initialized = True
        logger.info(
            "Inferência remota configurada: modelo=%s, dimensão=%s",
            QDRANT_INFERENCE_MODEL,
            EMBEDDING_DIMENSION,
        )

    @staticmethod
    def _validate_text(text: str) -> str:
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Texto inválido para embedding")
        return text.strip()

    def _document(self, text: str, prefix: str) -> Document:
        clean_text = self._validate_text(text)
        return Document(
            text=f"{prefix}: {clean_text}",
            model=QDRANT_INFERENCE_MODEL,
        )

    def embed(self, text: str, normalize: bool = True) -> Document:
        """Prepara uma consulta para a inferência remota do E5."""
        return self._document(text, "query")

    def embed_batch(self, texts: List[str], normalize: bool = True) -> List[Document]:
        """Prepara múltiplas consultas para a inferência remota do E5."""
        return [self._document(text, "query") for text in texts]

    def embed_corpus(self, texts: List[str], normalize: bool = True) -> List[Document]:
        """Prepara textos de referência para indexação com o prefixo E5 correto."""
        return [self._document(text, "passage") for text in texts]

    def get_embedding_dimension(self) -> int:
        """Retorna a dimensão declarada pelo modelo configurado."""
        return EMBEDDING_DIMENSION

    def get_model_name(self) -> str:
        """Retorna o modelo utilizado pelo Qdrant Cloud Inference."""
        return QDRANT_INFERENCE_MODEL
