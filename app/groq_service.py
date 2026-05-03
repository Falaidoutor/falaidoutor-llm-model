import asyncio
import os

from dotenv import load_dotenv
from groq import AsyncGroq, RateLimitError

load_dotenv()

from app.ollama_service import parse_response
from app.prompt import SYSTEM_PROMPT, build_user_prompt
from app.validator import validate_triage_response

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# Modelos disponíveis no Groq
MODEL_GPT_OSS = "openai/gpt-oss-120b"  # GPT OSS 120b equivalent via Groq
MODEL_QWEN3 = "qwen/qwen3-32b"  # Qwen3 via Groq

# Modelo ativo
MODEL_NAME = MODEL_GPT_OSS

_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 10.0  # segundos


async def classify_symptoms(symptoms: str) -> dict:
    client = AsyncGroq(api_key=GROQ_API_KEY)

    last_error: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            response = await client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": build_user_prompt(symptoms)},
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            break
        except RateLimitError as e:
            last_error = e
            if attempt < _MAX_RETRIES - 1:
                delay = _RETRY_BASE_DELAY * (2 ** attempt)
                await asyncio.sleep(delay)
    else:
        raise last_error

    content = response.choices[0].message.content

    parsed = parse_response(content)

    validation = validate_triage_response(parsed)
    parsed["validation_errors"] = validation.errors
    parsed["validation_warnings"] = validation.warnings

    return parsed
