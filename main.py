import logging
from fastapi import FastAPI, HTTPException

from app.models import SymptomsRequest, TriageResponse
from app.service.ollama_service import classify_symptoms

# ──────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# FastAPI App
# ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="Fala Doutor - Triagem Médica com IA + Normalização Semântica",
    description="API de classificação de risco baseada no Protocolo de Manchester com E5 + Qdrant + NER.",
    version="2.0.0",
)


# ──────────────────────────────────────────────────────────────
# Eventos de Startup/Shutdown
# ──────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    """Inicialização na startup: carregar modelos e inicializar Qdrant."""
    logger.info("=" * 70)
    logger.info("Iniciando aplicação Fala Doutor 2.0...")
    logger.info("=" * 70)

    try:
        # 1. Carregar NER Service
        logger.info("[1/3] Carregando NER Service...")
        from app.service.ner_service import NERService
        ner_svc = NERService()
        logger.info("✓ NER Service carregado")

        # 2. Carregar Embedding Service
        logger.info("[2/3] Carregando Embedding E5 Service...")
        from app.service.embedding import EmbeddingService
        embedding_svc = EmbeddingService()
        logger.info(
            f"✓ E5 Service carregado (dimensão: {embedding_svc.get_embedding_dimension()})"
        )

        # 3. Inicializar Qdrant
        logger.info("[3/3] Verificando Qdrant...")
        from app.service.qdrant_service import QdrantService
        qdrant_svc = QdrantService()
        qdrant_svc.initialize_collection()
        logger.info("✓ Qdrant collection verificada/criada")

        # 4. Verificar se collection está vazia e oferecedor script de init
        try:
            info = qdrant_svc.collection_info()
            if info.get("points_count", 0) == 0:
                logger.warning(
                    "⚠️ Collection Qdrant está vazia. "
                    "Execute 'python -m app.scripts.init_qdrant' para carregar dados do PostgreSQL."
                )
        except Exception as e:
            logger.debug(f"Erro ao verificar collection info: {e}")

        logger.info("=" * 70)
        logger.info("✓ Aplicação iniciada com sucesso!")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"✗ Erro durante startup: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup na shutdown."""
    logger.info("Encerrando aplicação...")
    try:
        from app.service.postgres_service import PostgresService
        postgres_svc = PostgresService()
        postgres_svc.close_pool()
        logger.info("✓ Pool PostgreSQL fechado")
    except Exception as e:
        logger.debug(f"Erro ao fechar conexões: {e}")


# ──────────────────────────────────────────────────────────────
# Rotas
# ──────────────────────────────────────────────────────────────
@app.post("/triage", response_model=TriageResponse)
async def triage(request: SymptomsRequest):
    """
    Endpoint principal de triagem com normalização semântica.

    Args:
        request: SymptomsRequest com symptoms e debug_mode

    Returns:
        TriageResponse com classificação + normalização semântica
    """
    try:
        logger.info(f"Requisição /triage recebida: '{request.symptoms[:50]}...'")
        result = await classify_symptoms(
            request.symptoms, debug_mode=request.debug_mode
        )
        logger.info("Resposta gerada com sucesso")
        return TriageResponse(**result)

    except ValueError as e:
        logger.error(f"Erro de validação: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Erro ao comunicar com Ollama/serviços: {e}")
        raise HTTPException(status_code=502, detail=f"Erro no processamento: {e}")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "version": "2.0.0"}


@app.get("/debug/normalization-stats")
async def normalization_stats():
    """Retorna estatísticas do serviço de normalização (debug)."""
    try:
        from app.service.normalization import NormalizationService
        norm_svc = NormalizationService()
        return norm_svc.get_normalization_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
