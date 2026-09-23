import asyncio
import logging
import os
import time

from dotenv import load_dotenv
from groq import AsyncGroq, RateLimitError

load_dotenv()

from app.ollama_service import parse_response
from app.prompt import build_system_prompt, build_user_prompt
from app.schemas import ModelConfig
from app.service.normalization_pipeline import normalize_safely, complete_normalization
from app.validator import validate_triage_response


GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

MODEL_GPT_OSS = "openai/gpt-oss-120b"
MODEL_GPT_OSS_20B = "openai/gpt-oss-20b"
MODEL_QWEN3_8_27B = "qwen/qwen3.8-27b"
MODEL_ORDER = (MODEL_GPT_OSS, MODEL_GPT_OSS_20B, MODEL_QWEN3_8_27B)
MODEL_NAME = MODEL_GPT_OSS
LEGACY_MODEL_ALIASES = {
    "qwen/qwen3-32b": MODEL_QWEN3_8_27B,
    "llama-3.3-70b-versatile": MODEL_NAME,
}

_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 2.0
logger = logging.getLogger(__name__)


async def classify_symptoms(
    symptoms: str,
    model_config: ModelConfig | None = None,
) -> dict:
    client = AsyncGroq(api_key=GROQ_API_KEY)
    config = model_config or ModelConfig()
    started_at = time.perf_counter()
    logger.info(
        "triage.start input_chars=%s configured_model=%s configured_order=%s",
        len(symptoms),
        config.model_name or MODEL_NAME,
        config.model_order or MODEL_ORDER,
    )
    normalization = await asyncio.to_thread(normalize_safely, symptoms)
    configured_model = LEGACY_MODEL_ALIASES.get(config.model_name or MODEL_NAME, config.model_name or MODEL_NAME)
    # Configurações antigas podem ainda conter o modelo removido.
    if configured_model not in MODEL_ORDER:
        configured_model = MODEL_NAME
    configured_order = [
        LEGACY_MODEL_ALIASES.get(model, model)
        for model in (config.model_order or MODEL_ORDER)
    ]
    model_candidates = tuple(dict.fromkeys(
        model for model in configured_order if model in MODEL_ORDER
    ))
    if configured_model not in model_candidates:
        model_candidates = (configured_model,) + model_candidates
    system_prompt = build_system_prompt(
        symptoms,
        normalization,
        config.system_prompt,
    )
    logger.info(
        "triage.context_ready input_chars=%s prompt_chars=%s normalized=%s unresolved=%s prompt_source=%s normalization_contract=llm_v1",
        len(symptoms),
        len(system_prompt),
        len(normalization.get("sintomas_normalizados", [])),
        len(normalization.get("sintomas_nao_normalizados", [])),
        "custom" if config.system_prompt else "default",
    )

    response = None
    model_used = configured_model
    fallback_activated = False
    last_error: Exception | None = None
    for candidate_index, candidate_model in enumerate(model_candidates):
        for attempt in range(_MAX_RETRIES):
            try:
                response = await client.chat.completions.create(
                    model=candidate_model,
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
                model_used = candidate_model
                logger.info(
                    "triage.model_success model=%s attempt=%s fallback=%s elapsed_ms=%.0f",
                    candidate_model,
                    attempt + 1,
                    fallback_activated,
                    (time.perf_counter() - started_at) * 1000,
                )
                break
            except RateLimitError as error:
                last_error = error
                if attempt < _MAX_RETRIES - 1:
                    delay = _retry_delay(error, attempt)
                    logger.warning(
                        "Rate limit no modelo %s (tentativa %s/%s); retry em %.1fs",
                        candidate_model,
                        attempt + 1,
                        _MAX_RETRIES,
                        delay,
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.warning(
                        "triage.model_rate_limit_exhausted model=%s attempts=%s",
                        candidate_model,
                        _MAX_RETRIES,
                    )
        if response is not None:
            break
        if candidate_index < len(model_candidates) - 1:
            fallback_activated = True
            logger.warning(
                "Rate limit persistente no modelo %s; alternando para %s",
                candidate_model,
                model_candidates[candidate_index + 1],
            )

    if response is None:
        if last_error is None:
            raise RuntimeError("Groq request failed without a reported error")
        raise last_error

    content = response.choices[0].message.content
    parsed = parse_response(content)
    logger.info(
        "triage.response_parsed model=%s output_chars=%s elapsed_ms=%.0f",
        model_used,
        len(content or ""),
        (time.perf_counter() - started_at) * 1000,
    )

    await asyncio.to_thread(complete_normalization, parsed, normalization, symptoms)
    parsed["modelo_usado"] = model_used
    parsed["fallback_modelo_ativado"] = fallback_activated

    validation = validate_triage_response(parsed)
    parsed["validation_errors"] = validation.errors
    parsed["validation_warnings"] = validation.warnings
    return parsed


def _retry_delay(error: RateLimitError, attempt: int) -> float:
    """Use the provider hint when available, otherwise exponential backoff."""
    response = getattr(error, "response", None)
    headers = getattr(response, "headers", None)
    retry_after = headers.get("retry-after") if headers else None
    try:
        if retry_after is not None:
            return max(0.0, min(float(retry_after), 60.0))
    except (TypeError, ValueError):
        pass
    return _RETRY_BASE_DELAY * (2**attempt)
