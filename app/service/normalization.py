"""
Serviço de Normalização Semântica com NER + E5 + Qdrant.
Orquestrador principal do pipeline de normalização.
"""

import logging
from typing import Dict, List, Tuple
from app.service.ner_service import NERService
from app.service.embedding import EmbeddingService
from app.service.qdrant_service import QdrantService
from app.service.postgres_service import PostgresService
from app.config.settings import SIMILARITY_THRESHOLD

logger = logging.getLogger(__name__)


class NormalizationService:
    """
    Serviço de normalização semântica: NER → Embeddings → Qdrant Search.

    Pipeline:
    1. Extrai sintomas do texto com NER
    2. Gera embeddings E5 para cada sintoma
    3. Busca no Qdrant por similaridade
    4. Classifica como normalizado (score >= threshold) ou não normalizado
    5. Retorna dois arrays: normalizados + não_normalizados
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
            logger.info("Inicializando NormalizationService")

            self.ner_service = NERService()
            self.embedding_service = EmbeddingService()
            self.qdrant_service = QdrantService()
            self.postgres_service = PostgresService()

            self._initialized = True
            logger.info("NormalizationService inicializado com sucesso")

        except Exception as e:
            logger.error(f"Erro ao inicializar NormalizationService: {e}")
            raise

    def normalize_symptoms(
        self, text: str, include_metadata: bool = False
    ) -> Dict:
        """
        Pipeline completo de normalização de sintomas.

        Args:
            text: Texto do usuário com sintomas
            include_metadata: Se True, inclui metadata detalhada em cada sintoma

        Returns:
            {
                "sintomas_normalizados": [
                    {
                        "original": str,
                        "normalizado": str,
                        "sintoma_id": int,
                        "score": float,
                        "tipo": "normalizado",
                        ... (metadata se include_metadata=True)
                    }
                ],
                "sintomas_nao_normalizados": [
                    {
                        "original": str,
                        "score": float,
                        "tipo": "nao_normalizado",
                        "motivo": str,
                        ... (metadata se include_metadata=True)
                    }
                ],
                "total_extraidos": int,
                "taxa_normalizacao": float (0.0 - 1.0),
                "debug": {
                    "threshold": float,
                    "ner_time_ms": float,
                    ...
                }
            }
        """
        import time

        start_time = time.time()

        try:
            # Fase 1: NER - Extração de sintomas
            logger.info(f"Iniciando normalização para: '{text[:50]}...'")
            ner_start = time.time()

            sintomas_extraidos = self.ner_service.extract_symptoms(text)

            ner_time_ms = (time.time() - ner_start) * 1000
            logger.info(f"NER extraiu {len(sintomas_extraidos)} sintomas em {ner_time_ms:.2f}ms")

            if not sintomas_extraidos:
                logger.warning("Nenhum sintoma extraído pelo NER")
                return {
                    "sintomas_normalizados": [],
                    "sintomas_nao_normalizados": [],
                    "total_extraidos": 0,
                    "taxa_normalizacao": 0.0,
                    "debug": {
                        "threshold": SIMILARITY_THRESHOLD,
                        "ner_time_ms": ner_time_ms,
                        "message": "NER não extraiu sintomas",
                    },
                }

            # Fase 2: Normalização de cada sintoma
            sintomas_normalizados = []
            sintomas_nao_normalizados = []

            embedding_start = time.time()

            for sintoma_original in sintomas_extraidos:
                resultado = self._normalize_single_symptom(
                    sintoma_original, include_metadata
                )

                if resultado["tipo"] == "normalizado":
                    sintomas_normalizados.append(resultado)
                else:
                    sintomas_nao_normalizados.append(resultado)

            embedding_time_ms = (time.time() - embedding_start) * 1000

            # Calcular taxa de normalização
            total = len(sintomas_extraidos)
            taxa_normalizacao = (
                len(sintomas_normalizados) / total if total > 0 else 0.0
            )

            total_time_ms = (time.time() - start_time) * 1000

            resultado_final = {
                "sintomas_normalizados": sintomas_normalizados,
                "sintomas_nao_normalizados": sintomas_nao_normalizados,
                "total_extraidos": total,
                "taxa_normalizacao": taxa_normalizacao,
                "debug": {
                    "threshold": SIMILARITY_THRESHOLD,
                    "ner_time_ms": ner_time_ms,
                    "embedding_time_ms": embedding_time_ms,
                    "total_time_ms": total_time_ms,
                },
            }

            logger.info(
                f"Normalização concluída: "
                f"{len(sintomas_normalizados)} normalizados, "
                f"{len(sintomas_nao_normalizados)} não normalizados "
                f"({taxa_normalizacao*100:.1f}%) em {total_time_ms:.2f}ms"
            )

            return resultado_final

        except Exception as e:
            logger.error(f"Erro ao normalizar sintomas: {e}")
            return {
                "sintomas_normalizados": [],
                "sintomas_nao_normalizados": [],
                "total_extraidos": 0,
                "taxa_normalizacao": 0.0,
                "debug": {
                    "error": str(e),
                },
            }

    def _normalize_single_symptom(
        self, sintoma: str, include_metadata: bool = False
    ) -> Dict:
        """
        Normaliza um sintoma individual.

        Returns:
            Dict com um dos dois formatos:
            - Normalizado: {
                "original": str,
                "normalizado": str,
                "sintoma_id": int,
                "sinonimo_id": int,
                "score": float,
                "tipo": "normalizado"
              }
            - Não normalizado: {
                "original": str,
                "score": float,
                "tipo": "nao_normalizado",
                "motivo": str
              }
        """
        try:
            # 1. Gerar embedding
            
            embedding = self.embedding_service.embed(sintoma)

            # 2. Buscar no Qdrant
            resultados_qdrant = self.qdrant_service.search(
                embedding, top_k=5, score_threshold=SIMILARITY_THRESHOLD
            )

            if not resultados_qdrant:
                # Nenhum resultado encontrado
                return {
                    "original": sintoma,
                    "score": 0.0,
                    "tipo": "nao_normalizado",
                    "motivo": "nenhum_resultado_qdrant",
                }

            resultado_top = resultados_qdrant[0]
            score = resultado_top["score"]
            payload = resultado_top["payload"]

            # 3. Classificar por threshold
            if score >= SIMILARITY_THRESHOLD:
                # Normalizado ✓
                sinonimo_id = payload.get("sinonimo_id")
                sintoma_id = payload.get("sintoma_id")
                termo_encontrado = payload.get("termo")

                # Buscar o sintoma canônico no PostgreSQL usando o sintoma_id
                sintoma_data = self.postgres_service.get_sintoma_by_id(sintoma_id)
                termo_normalizado = sintoma_data.get("termo") if sintoma_data else termo_encontrado

                print(f"SINTOMA: {sintoma}")
                print(f"SCORE: {score}")
                print(f"TERMO ORIGINAL ENCONTRADO: {termo_encontrado}")
                print(f"TERMO NORMALIZADO: {termo_normalizado}")

                resultado = {
                    "original": sintoma,
                    "normalizado": termo_normalizado,
                    "sintoma_id": sintoma_id,
                    "sinonimo_id": sinonimo_id,
                    "score": score,
                    "tipo": "normalizado",
                }

                #  Sintoma já normalizado: apenas retornar, SEM inserir em base_candidata
                # (base_candidata é apenas para NOVOS candidatos aguardando auditoria)

                logger.debug(
                    f"Sintoma '{sintoma}' → '{termo_normalizado}' (score: {score:.3f})"
                )

                return resultado

            else:
                # Não normalizado
                resultado = {
                    "original": sintoma,
                    "score": score,
                    "tipo": "nao_normalizado",
                    "motivo": "score_baixo",
                }

                logger.debug(f"Sintoma '{sintoma}' não normalizado (score: {score:.3f})")

                return resultado

        except Exception as e:
            logger.error(f"Erro ao normalizar sintoma '{sintoma}': {e}")
            return {
                "original": sintoma,
                "score": 0.0,
                "tipo": "nao_normalizado",
                "motivo": f"erro: {str(e)}",
            }

    def get_normalization_stats(self) -> Dict:
        """
        Retorna estatísticas de normalização (debug/admin).
        """
        try:
            return {
                "similarity_threshold": SIMILARITY_THRESHOLD,
                "modelo_e5": self.embedding_service.get_model_name(),
                "embedding_dimension": self.embedding_service.get_embedding_dimension(),
                "qdrant_info": self.qdrant_service.collection_info(),
            }
        except Exception as e:
            logger.error(f"Erro ao obter normalization stats: {e}")
            return {"error": str(e)}
