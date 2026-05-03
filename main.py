from fastapi import FastAPI, HTTPException

from app.schemas import SymptomsRequest, TriageResponse

# --- Provedor ativo: Groq ---
from app.groq_service import classify_symptoms

# --- Provedor alternativo: Ollama (local) ---
# from app.ollama_service import classify_symptoms

app = FastAPI(
    title="Fala Doutor - Triagem Médica com IA",
    description="API de classificação de risco baseada no Protocolo ESI (Emergency Severity Index) usando LLM via Groq.",
    version="1.0.0",
)


@app.post("/triage", response_model=TriageResponse)
async def triage(request: SymptomsRequest):
    try:
        result = await classify_symptoms(request.symptoms)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erro ao comunicar com o Groq: {e}")

    return TriageResponse(**result)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
