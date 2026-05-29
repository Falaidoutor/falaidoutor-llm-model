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
            {
                "detail": "Invalid JSON body.",
                "errorType": "INVALID_JSON",
                "retryable": False,
            },
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
            {
                "detail": "Encrypted HTTP payload is required.",
                "errorType": "ENCRYPTION_REQUIRED",
                "retryable": False,
            },
            status.HTTP_400_BAD_REQUEST,
        )

    try:
        symptoms_request = SymptomsRequest(**body)
    except (TypeError, ValidationError) as exc:
        detail = exc.errors() if isinstance(exc, ValidationError) else "Invalid request body."
        return _json_response(
            request,
            {
                "detail": detail,
                "errorType": "VALIDATION_ERROR",
                "retryable": False,
            },
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    try:
        result = await classify_symptoms(symptoms_request.symptoms)
    except Exception as e:
        return _json_response(
            request,
            {
                "detail": f"Erro ao comunicar com o Groq: {e}",
                "errorType": "GROQ_ERROR",
                "retryable": True,
            },
            status.HTTP_502_BAD_GATEWAY,
        )

    response = TriageResponse(
        **_with_async_contract_fields(
            result,
            triage_id=symptoms_request.triage_id,
        )
    ).model_dump()

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


def _with_async_contract_fields(result: dict, triage_id: str | int | None) -> dict:
    classification = result.get("classificacao")
    justification = result.get("justificativa")

    return {
        **result,
        "summary": result.get("summary") or justification,
        "suggestedRiskClassification": (
            result.get("suggestedRiskClassification") or classification
        ),
        "suggestedRiskColor": (
            result.get("suggestedRiskColor") or _risk_color(classification)
        ),
        "reasoning": result.get("reasoning") or justification,
        "recommendedAction": (
            result.get("recommendedAction")
            or "Encaminhar para avaliacao da equipe de saude."
        ),
        "rawModelOutput": result.get("rawModelOutput") or result,
        "confidence": result.get("confidence") or result.get("confianca"),
        "triageId": triage_id,
    }


def _risk_color(classification: str | None) -> str:
    colors = {
        "ESI-1": "#a30000",
        "ESI-2": "#fe0000",
        "ESI-3": "#ffd900",
        "ESI-4": "#28a745",
        "ESI-5": "#00e5ff",
    }
    return colors.get((classification or "").strip().upper(), "#6c757d")


def _encryption_is_required() -> bool:
    return os.getenv("HTTP_CRYPTO_REQUIRED", "").strip().lower() == "true"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

