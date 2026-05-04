import hmac
import os

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, status

from app.schemas import SymptomsRequest, TriageResponse

# --- Provedor ativo: Groq ---
from app.groq_service import classify_symptoms

# --- Provedor alternativo: Ollama (local) ---
# from app.ollama_service import classify_symptoms

load_dotenv()

app = FastAPI(
    title="Fala Doutor - Triagem Médica com IA",
    description="API de classificação de risco baseada no Protocolo ESI (Emergency Severity Index) usando LLM via Groq.",
    version="1.0.0",
)


async def validate_application_key(
    x_application_key: str | None = Header(default=None),
) -> None:
    expected_key = os.getenv("APPLICATION_KEY", "").strip()

    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Application key is not configured.",
        )

    if not x_application_key or not hmac.compare_digest(x_application_key, expected_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid application key.",
        )


@app.post("/triage", response_model=TriageResponse, dependencies=[Depends(validate_application_key)])
async def triage(request: SymptomsRequest):
    try:
        result = await classify_symptoms(request.symptoms)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erro ao comunicar com o Groq: {e}")

    return TriageResponse(**result)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
