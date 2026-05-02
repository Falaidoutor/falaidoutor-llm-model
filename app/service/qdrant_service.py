"""
Serviço de integração com Qdrant para busca de sintomas por similaridade semântica.
"""

import logging
from typing import Dict, List, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from app.config.settings import (
    QDRANT_URL,
    QDRANT_PORT,
    QDRANT_API_KEY,
    QDRANT_COLLECTION_NAME,
    EMBEDDING_DIMENSION,
)

logger = logging.getLogger(__name__)


class QdrantService:
    """
    Gerencia operações com Qdrant: conectar, buscar, inserir vetores.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        try:
            logger.info(f"Conectando ao Qdrant: {QDRANT_URL}:{QDRANT_PORT}")

            self.client = QdrantClient(
                url=QDRANT_URL,
                port=QDRANT_PORT,
                api_key=QDRANT_API_KEY,
                timeout=30,
            )

            # Verificar conexão
            collections = self.client.get_collections()
            logger.info(f"Conectado ao Qdrant. Collections: {len(collections.collections)}")

            self._initialized = True
            logger.info("QdrantService inicializado com sucesso")

        except Exception as e:
            logger.error(f"Erro ao conectar ao Qdrant: {e}")
            raise

    def initialize_collection(
        self,
        collection_name: str = QDRANT_COLLECTION_NAME,
        vector_size: int = EMBEDDING_DIMENSION,
        similarity: str = "Cosine",
    ) -> bool:
        """
        Cria ou verifica collection no Qdrant.

        Args:
            collection_name: Nome da collection
            vector_size: Dimensão dos vetores (1024 para E5-large)
            similarity: Tipo de similaridade (Cosine, Euclid, Manhattan)

        Returns:
            True se collection foi criada/existe
        """
        try:
            # Verificar se collection existe
            try:
                self.client.get_collection(collection_name)
                logger.info(f"Collection '{collection_name}' já existe")
                return True
            except Exception:
                logger.info(f"Collection '{collection_name}' não existe. Criando...")

            # Criar collection
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance[similarity.upper()],
                ),
            )

            logger.info(
                f"Collection '{collection_name}' criada com sucesso "
                f"(dimensão: {vector_size}, similaridade: {similarity})"
            )
            return True

        except Exception as e:
            logger.error(f"Erro ao inicializar collection: {e}")
            raise

    def search(
        self,
        vector: List[float],
        collection_name: str = QDRANT_COLLECTION_NAME,
        top_k: int = 1,
        score_threshold: Optional[float] = None,
    ) -> List[Dict]:
        """
        Busca vetores similares no Qdrant.

        Args:
            vector: Embedding (lista de floats)
            collection_name: Nome da collection
            top_k: Número de resultados a retornar
            score_threshold: Score mínimo de similaridade (opcional)

        Returns:
            Lista de dicts com formato:
            [
                {
                    "id": int,
                    "score": float,
                    "payload": dict
                }
            ]
        """
        try:
            response = self.client.query_points(
                collection_name=collection_name,
                query=vector,
                limit=top_k,
                score_threshold=score_threshold,
            )
            results = response.points

            output = []
            for point in results:
                output.append(
                    {
                        "id": point.id,
                        "score": point.score,
                        "payload": point.payload,
                    }
                )

            logger.debug(f"Search retornou {len(output)} resultados")
            return output

        except Exception as e:
            logger.error(f"Erro ao buscar no Qdrant: {e}")
            raise

    def upsert_vector(
        self,
        vector_id: int,
        vector: List[float],
        payload: Dict,
        collection_name: str = QDRANT_COLLECTION_NAME,
    ) -> bool:
        """
        Insere ou atualiza um vetor no Qdrant.

        Args:
            vector_id: ID único do vetor
            vector: Embedding (lista de floats)
            payload: Metadata associada (ex: sintoma_id, sinonimo_id, termo)
            collection_name: Nome da collection

        Returns:
            True se operação foi bem-sucedida
        """
        try:
            points = [
                PointStruct(
                    id=vector_id,
                    vector=vector,
                    payload=payload,
                )
            ]

            self.client.upsert(
                collection_name=collection_name,
                points=points,
            )

            logger.debug(f"Vector {vector_id} upserted com sucesso")
            return True

        except Exception as e:
            logger.error(f"Erro ao fazer upsert de vector: {e}")
            raise

    def upsert_batch(
        self,
        vectors: List[Dict],  # [{"id": int, "vector": List[float], "payload": Dict}]
        collection_name: str = QDRANT_COLLECTION_NAME,
    ) -> bool:
        """
        Insere/atualiza múltiplos vetores em batch (mais eficiente).

        Args:
            vectors: Lista de dicts com id, vector, payload
            collection_name: Nome da collection

        Returns:
            True se operação foi bem-sucedida
        """
        try:
            points = [
                PointStruct(
                    id=v["id"],
                    vector=v["vector"],
                    payload=v["payload"],
                )
                for v in vectors
            ]

            self.client.upsert(
                collection_name=collection_name,
                points=points,
            )

            logger.info(f"{len(points)} vetores inseridos em batch")
            return True

        except Exception as e:
            logger.error(f"Erro ao fazer batch upsert: {e}")
            raise

    def delete_vector(
        self,
        vector_id: int,
        collection_name: str = QDRANT_COLLECTION_NAME,
    ) -> bool:
        """
        Remove um vetor do Qdrant.
        """
        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=vector_id,
            )
            logger.info(f"Vector {vector_id} deletado")
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar vector: {e}")
            raise

    def collection_info(self, collection_name: str = QDRANT_COLLECTION_NAME) -> Dict:
        """
        Retorna informações sobre a collection (tamanho, config, etc).
        """
        try:
            info = self.client.get_collection(collection_name)
            return {
                "name": collection_name,
                "points_count": info.points_count,
                "vectors_count": info.vectors_count if hasattr(info, "vectors_count") else None,
            }
        except Exception as e:
            logger.error(f"Erro ao obter informações da collection: {e}")
            raise
