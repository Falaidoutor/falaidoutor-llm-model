"""
Script de inicialização do Qdrant com dados do PostgreSQL.
Carrega sinonimos aprovados + sintomas canônicos e gera embeddings E5.

Uso:
    python -m app.scripts.init_qdrant
"""

import logging
import sys
from typing import List, Dict

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def validate_postgres_connection():
    """Valida conexão com PostgreSQL."""
    try:
        from app.service.postgres_service import PostgresService

        postgres_svc = PostgresService()
        logger.info("✓ Conexão com PostgreSQL validada")
        return postgres_svc

    except Exception as e:
        logger.error(f"✗ Erro ao conectar ao PostgreSQL: {e}")
        sys.exit(1)


def validate_qdrant_connection():
    """Valida conexão com Qdrant."""
    try:
        from app.service.qdrant_service import QdrantService

        qdrant_svc = QdrantService()
        logger.info("✓ Conexão com Qdrant validada")
        return qdrant_svc

    except Exception as e:
        logger.error(f"✗ Erro ao conectar ao Qdrant: {e}")
        sys.exit(1)


def validate_embedding_service():
    """Valida modelo E5."""
    try:
        from app.service.embedding import EmbeddingService

        embedding_svc = EmbeddingService()
        dim = embedding_svc.get_embedding_dimension()
        logger.info(f"✓ Modelo E5 carregado (dimensão: {dim})")
        return embedding_svc

    except Exception as e:
        logger.error(f"✗ Erro ao carregar modelo E5: {e}")
        sys.exit(1)


def initialize_qdrant_collection(qdrant_svc, embedding_dim):
    """Inicializa a collection no Qdrant."""
    try:
        qdrant_svc.initialize_collection(vector_size=embedding_dim)
        logger.info("✓ Collection Qdrant inicializada/verificada")
        return True

    except Exception as e:
        logger.error(f"✗ Erro ao inicializar collection: {e}")
        sys.exit(1)


def load_sinonimos_from_postgres(postgres_svc) -> List[Dict]:
    """Carrega sinonimos aprovados do PostgreSQL."""
    try:
        sinonimos = postgres_svc.get_all_sinonimos()
        logger.info(f"✓ Carregados {len(sinonimos)} sinonimos de PostgreSQL")
        return sinonimos

    except Exception as e:
        logger.error(f"✗ Erro ao carregar sinonimos: {e}")
        return []


def load_sintomas_from_postgres(postgres_svc) -> List[Dict]:
    """Carrega sintomas canônicos do PostgreSQL."""
    try:
        sintomas = postgres_svc.get_all_sintomas()
        logger.info(f"✓ Carregados {len(sintomas)} sintomas canônicos de PostgreSQL")
        return sintomas

    except Exception as e:
        logger.error(f"✗ Erro ao carregar sintomas: {e}")
        return []


def generate_embeddings(embedding_svc, textos: List[str]) -> List[List[float]]:
    """Gera embeddings E5 para múltiplos textos."""
    try:
        embeddings = embedding_svc.embed_corpus(textos)
        logger.info(f"✓ Gerados {len(embeddings)} embeddings")
        return embeddings

    except Exception as e:
        logger.error(f"✗ Erro ao gerar embeddings: {e}")
        return []


def upsert_to_qdrant(qdrant_svc, vectors_data: List[Dict]) -> bool:
    """Faz upsert de múltiplos vetores ao Qdrant."""
    try:
        qdrant_svc.upsert_batch(vectors_data)
        logger.info(f"✓ {len(vectors_data)} vetores inseridos ao Qdrant")
        return True

    except Exception as e:
        logger.error(f"✗ Erro ao fazer upsert: {e}")
        return False


def main():
    """Executa pipeline completo de inicialização."""

    logger.info("=" * 70)
    logger.info("Iniciando carregamento de dados: PostgreSQL → Qdrant")
    logger.info("=" * 70)

    # 1. Validar conexões
    logger.info("\n[1/6] Validando conexões...")
    postgres_svc = validate_postgres_connection()
    qdrant_svc = validate_qdrant_connection()
    embedding_svc = validate_embedding_service()

    # 2. Obter dimensão de embedding
    embedding_dim = embedding_svc.get_embedding_dimension()

    # 3. Inicializar collection
    logger.info("\n[2/6] Inicializando collection no Qdrant...")
    initialize_qdrant_collection(qdrant_svc, embedding_dim)

    # 4. Carregar dados
    logger.info("\n[3/6] Carregando dados de PostgreSQL...")
    sinonimos = load_sinonimos_from_postgres(postgres_svc)
    sintomas = load_sintomas_from_postgres(postgres_svc)

    if not sinonimos and not sintomas:
        logger.warning("⚠ Nenhum sinonimo ou sintoma encontrado no PostgreSQL")
        logger.info("Verifique se as tabelas foram populadas com dados de seed")
        return False

    # 5. Preparar vectors para Qdrant
    logger.info("\n[4/6] Gerando dados de embedding...")

    vectors_to_upsert = []

    # Vetores para sinonimos
    if sinonimos:
        textos_sinonimos = [s["termo"] for s in sinonimos]
        embeddings_sinonimos = generate_embeddings(embedding_svc, textos_sinonimos)

        for i, (sin, emb) in enumerate(zip(sinonimos, embeddings_sinonimos)):
            # ID = 1000000 + sinonimo_id (para evitar conflito com sintomas)
            vector_id = 1000000 + sin["id"]

            vectors_to_upsert.append(
                {
                    "id": vector_id,
                    "vector": emb,
                    "payload": {
                        "tipo": "sinonimo",
                        "sinonimo_id": sin["id"],
                        "sintoma_id": sin["sintoma_id"],
                        "termo": sin["termo"],
                    },
                }
            )

    # Vetores para sintomas canônicos
    if sintomas:
        textos_sintomas = [s["termo"] for s in sintomas]
        embeddings_sintomas = generate_embeddings(embedding_svc, textos_sintomas)

        for sin, emb in zip(sintomas, embeddings_sintomas):
            # ID = sintoma_id
            vector_id = sin["id"]

            vectors_to_upsert.append(
                {
                    "id": vector_id,
                    "vector": emb,
                    "payload": {
                        "tipo": "sintoma_canonico",
                        "sintoma_id": sin["id"],
                        "termo": sin["termo"],
                        "categoria": sin.get("categoria"),
                    },
                }
            )

    logger.info(f"Total de vetores para upsert: {len(vectors_to_upsert)}")

    # 6. Fazer upsert ao Qdrant
    logger.info("\n[5/6] Fazendo upsert ao Qdrant...")
    success = upsert_to_qdrant(qdrant_svc, vectors_to_upsert)

    if not success:
        logger.error("✗ Erro ao fazer upsert. Abortando.")
        return False

    # 7. Verificar resultado
    logger.info("\n[6/6] Verificando resultado...")
    try:
        info = qdrant_svc.collection_info()
        logger.info(f"✓ Collection info: {info}")
    except Exception as e:
        logger.error(f"Erro ao obter informações: {e}")

    logger.info("\n" + "=" * 70)
    logger.info("✓ Inicialização concluída com sucesso!")
    logger.info("=" * 70)

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
