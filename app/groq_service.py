import asyncio
import logging
import os

from dotenv import load_dotenv
from groq import AsyncGroq, RateLimitError

load_dotenv()

from app.ollama_service import parse_response
from app.prompt import SYSTEM_PROMPT, build_user_prompt
from app.schemas import ModelConfig
from app.service.llm_normalization import extract_llm_normalizations
from app.validator import validate_triage_response


GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

MODEL_GPT_OSS = "openai/gpt-oss-120b"
MODEL_QWEN3 = "qwen/qwen3-32b"
MODEL_LLAMA_3_3_70b = "llama-3.3-70b-versatile"
MODEL_NAME = MODEL_LLAMA_3_3_70b

_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 10.0
logger = logging.getLogger(__name__)


async def classify_symptoms(
    symptoms: str,
    model_config: ModelConfig | None = None,
) -> dict:
    client = AsyncGroq(api_key=GROQ_API_KEY)
    config = model_config or ModelConfig()
    model_name = config.model_name or MODEL_NAME
    system_prompt = config.system_prompt or SYSTEM_PROMPT
    normalization = await asyncio.to_thread(_normalize_safely, symptoms)

    last_error: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            response = await client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": build_user_prompt(symptoms, normalization),
                    },
                ],
                temperature=config.temperature,
                top_p=config.top_p,
                response_format={"type": "json_object"},
            )
            break
        except RateLimitError as error:
            last_error = error
            if attempt < _MAX_RETRIES - 1:
                await asyncio.sleep(_RETRY_BASE_DELAY * (2**attempt))
    else:
        if last_error is None:
            raise RuntimeError("Groq request failed without a reported error")
        raise last_error

    content = response.choices[0].message.content
    parsed = parse_response(content)

    llm_normalizations = extract_llm_normalizations(parsed, normalization)
    if llm_normalizations:
        await asyncio.to_thread(_save_candidates_safely, llm_normalizations)

    parsed["texto_original"] = symptoms
    parsed["normalizacao_resultado"] = normalization
    parsed["normalizacao_llm"] = llm_normalizations
    parsed["normalizacao_ollama"] = llm_normalizations
    parsed["sintomas_normalizados"] = [
        item["normalizado"]
        for item in normalization.get("sintomas_normalizados", [])
        if item.get("normalizado")
    ]

    validation = validate_triage_response(parsed)
    parsed["validation_errors"] = validation.errors
    parsed["validation_warnings"] = validation.warnings
    return parsed


def _empty_normalization(status: str) -> dict:
    return {
        "sintomas_normalizados": [],
        "sintomas_nao_normalizados": [],
        "total_extraidos": 0,
        "taxa_normalizacao": 0.0,
        "debug": {"status": status},
    }


def _normalize_safely(symptoms: str) -> dict:
    """Keep triage available if Qdrant or PostgreSQL is unavailable."""
    try:
        from app.service.normalization import NormalizationService

        return NormalizationService().normalize_symptoms(symptoms)
    except Exception:
        logger.warning("Normalização semântica indisponível; usando texto original")
        return _empty_normalization("unavailable")


def _save_candidates_safely(normalizations: list[dict]) -> None:
    try:
        from app.service.normalization import NormalizationService

        repository = NormalizationService().postgres_service
        for item in normalizations:
            repository.create_base_candidata(
                input_original=item["original"],
                normalizado_sugerido=item["normalizado"],
                score_ollama_confianca=item["confianca"],
                origem="llm",
            )
    except Exception:
        logger.warning("Não foi possível persistir candidatos de normalização")
