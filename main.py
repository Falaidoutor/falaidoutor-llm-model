from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager

from app.schemas import SymptomsRequest, TriageResponse
from app.service.ollama_service import classify_symptoms
from app.config import test_connection, init_db, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerenciar ciclo de vida da aplicação (startup e shutdown)."""
    # Startup
    print("🚀 Iniciando Fala Doutor...")
    
    # Testar conexão com banco de dados
    if test_connection():
        # Inicializar schema se necessário
        init_db()
    else:
        print("Aviso: Banco de dados não está acessível. Usando modo sem persistência.")
    
    yield
    
    # Shutdown
    print("Encerrando Falai Doutor...")
    engine.dispose()


app = FastAPI(
    title="Fala Doutor - Triagem Médica com IA",
    description="API de classificação de risco baseada no Protocolo de Manchester usando LLM via Ollama.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """Verificação de saúde da aplicação."""
    try:
        test_connection()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}


@app.post("/triage", response_model=TriageResponse)
async def triage(request: SymptomsRequest):
    try:
        result = await classify_symptoms(request.symptoms)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erro ao comunicar com o Ollama: {e}")

    return TriageResponse(**result)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
