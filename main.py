import hmac
import os

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.http_crypto import decrypt_payload, encrypt_payload, is_encrypted_payload
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


@app.post("/triage", dependencies=[Depends(validate_application_key)])
async def triage(request: Request):
    encrypted_header = request.headers.get("x-payload-encrypted") == "true"
    request.state.payload_encrypted = encrypted_header

    try:
        body = await request.json()
    except Exception:
        return _json_response(
            request,
            {"detail": "Invalid JSON body."},
            status.HTTP_400_BAD_REQUEST,
        )

    if is_encrypted_payload(body):
        request.state.payload_encrypted = True
        try:
            body = decrypt_payload(body)
        except HTTPException as exc:
            return _json_response(
                request,
                {"detail": exc.detail},
                exc.status_code,
            )
    elif _encryption_is_required():
        return _json_response(
            request,
            {"detail": "Encrypted HTTP payload is required."},
            status.HTTP_400_BAD_REQUEST,
        )

    try:
        symptoms_request = SymptomsRequest(**body)
    except (TypeError, ValidationError) as exc:
        detail = exc.errors() if isinstance(exc, ValidationError) else "Invalid request body."
        return _json_response(
            request,
            {"detail": detail},
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    try:
        result = await classify_symptoms(symptoms_request.symptoms)
    except Exception as e:
        return _json_response(
            request,
            {"detail": f"Erro ao comunicar com o Groq: {e}"},
            status.HTTP_502_BAD_GATEWAY,
        )

    response = TriageResponse(**result).model_dump()

    return _json_response(request, response)


def _json_response(
    request: Request,
    payload: dict,
    status_code: int = status.HTTP_200_OK,
) -> JSONResponse:
    content = (
        encrypt_payload(payload)
        if getattr(request.state, "payload_encrypted", False)
        else payload
    )

    return JSONResponse(status_code=status_code, content=content)


def _encryption_is_required() -> bool:
    return os.getenv("HTTP_CRYPTO_REQUIRED", "").strip().lower() == "true"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

