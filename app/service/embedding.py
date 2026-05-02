"""
Serviço de Embedding usando modelo E5 (intfloat/multilingual-e5-*).
Responsável por gerar vetores normalizados para sintomas.
"""

import logging
from typing import List
from sentence_transformers import SentenceTransformer
from app.config.settings import E5_MODEL_NAME, E5_CACHE_DIR, EMBEDDING_DIMENSION

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Gerencia carregamento do modelo E5 e geração de embeddings.
    Singleton pattern para evitar múltiplos carregamentos em memória.
    """

    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        try:
            logger.info(f"Carregando modelo E5: {E5_MODEL_NAME}")

            self._model = SentenceTransformer(
                E5_MODEL_NAME, cache_folder=E5_CACHE_DIR
            )

            # Verificar dimensão do modelo
            model_dim = self._model.get_sentence_embedding_dimension()
            logger.info(f"Modelo E5 carregado. Dimensão: {model_dim}")

            if model_dim != EMBEDDING_DIMENSION:
                logger.warning(
                    f"Dimensão configurada ({EMBEDDING_DIMENSION}) "
                    f"difere da dimensão do modelo ({model_dim}). "
                    f"Atualizando configuração..."
                )

            self._initialized = True
            logger.info("EmbeddingService inicializado com sucesso")

        except Exception as e:
            logger.error(f"Erro ao carregar modelo E5: {e}")
            raise

    def embed(self, text: str, normalize: bool = True) -> List[float]:
        """
        Gera embedding normalizado para um texto.

        Args:
            text: Texto para gerar embedding
            normalize: Se True, normaliza o vetor (recomendado para cosine similarity)

        Returns:
            Lista de float representando o embedding
        """
        if not text or not isinstance(text, str):
            raise ValueError("Texto inválido para embedding")

        text = text.strip()
        if not text:
            raise ValueError("Texto vazio após limpeza")

        # Adicionar prefixo "query:" conforme recomendação de E5 para busca semântica
        query_text = f"query: {text}"

        embedding = self._model.encode(
            query_text, convert_to_tensor=False, normalize_embeddings=normalize
        )

        return embedding.tolist()

    def embed_batch(
        self, texts: List[str], normalize: bool = True
    ) -> List[List[float]]:
        """
        Gera embeddings para múltiplos textos (mais eficiente que loop).

        Args:
            texts: Lista de textos
            normalize: Se True, normaliza os vetores

        Returns:
            Lista de embeddings
        """
        if not texts:
            return []

        # Adicionar prefixo query: para todos
        query_texts = [f"query: {t.strip()}" for t in texts]

        embeddings = self._model.encode(
            query_texts, convert_to_tensor=False, normalize_embeddings=normalize
        )

        return [emb.tolist() for emb in embeddings]

    def embed_corpus(
        self, texts: List[str], normalize: bool = True
    ) -> List[List[float]]:
        """
        Gera embeddings para corpus (textos de referência/índice).
        Usa prefixo "passage:" conforme recomendação E5.

        Args:
            texts: Lista de textos de corpus
            normalize: Se True, normaliza os vetores

        Returns:
            Lista de embeddings
        """
        if not texts:
            return []

        # Adicionar prefixo passage: para corpus
        passage_texts = [f"passage: {t.strip()}" for t in texts]

        embeddings = self._model.encode(
            passage_texts, convert_to_tensor=False, normalize_embeddings=normalize
        )

        return [emb.tolist() for emb in embeddings]

    def get_embedding_dimension(self) -> int:
        """Retorna a dimensão dos embeddings gerados."""
        return self._model.get_sentence_embedding_dimension()

    def get_model_name(self) -> str:
        """Retorna o nome do modelo E5 carregado."""
        return E5_MODEL_NAME
