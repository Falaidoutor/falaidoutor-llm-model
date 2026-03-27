import json
import re

import httpx

from app.prompt import SYSTEM_PROMPT, build_user_prompt
from app.validator import validate_triage_response
from app.normalizacao_semantica import NormalizacaoSemantica

OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "qwen3"

# Orquestrador de normalização
normalizador = NormalizacaoSemantica()


async def classify_symptoms(symptoms: str) -> dict:

    # NORMALIZAR ENTRADA
    normalized_input = normalizador.processar(symptoms)
    
    #CONSTRUIR PROMPT ENRIQUECIDO
    prompt_enriquecido = normalizador.gerar_prompt_enriquecido(normalized_input)
    user_message = f"{prompt_enriquecido}\n\n{build_user_prompt(symptoms)}"

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "stream": False,
        "format": "json",
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload)
        response.raise_for_status()

    data = response.json()
    content = data["message"]["content"]

    parsed = parse_response(content)

    validation = validate_triage_response(parsed)
    parsed["validation_errors"] = validation.errors
    parsed["validation_warnings"] = validation.warnings

    # ENRIQUECER RESPOSTA COM DADOS DE NORMALIZAÇÃO
    parsed["normalizacao_entrada"] = normalized_input.to_dict()

    return parsed


def parse_response(content: str) -> dict:
    # Try to parse as JSON directly
    try:
        result = json.loads(content)
        return _validate_fields(result)
    except json.JSONDecodeError:
        pass

    # Fallback: try to extract JSON from markdown code blocks or surrounding text
    json_match = re.search(r"\{[\s\S]*\}", content)
    if json_match:
        try:
            result = json.loads(json_match.group())
            return _validate_fields(result)
        except json.JSONDecodeError:
            pass

    # Last resort: return a minimal valid response
    return {
        "classificacao": "Indeterminado",
        "prioridade": "Indeterminado",
        "tempo_atendimento_minutos": 0,
        "fluxograma_utilizado": "Indeterminado",
        "discriminadores_gerais_avaliados": [],
        "discriminadores_especificos_ativados": [],
        "populacao_especial": None,
        "over_triage_aplicado": False,
        "confianca": "baixa",
        "justificativa": content,
        "alertas": ["Resposta do modelo não pôde ser interpretada como JSON válido."],
        "disclaimer": "Classificação de apoio à decisão. A avaliação final é responsabilidade do profissional de saúde.",
    }


def _validate_fields(result: dict) -> dict:
    """Ensure all required fields exist with sensible defaults."""
    defaults = {
        "classificacao": "Indeterminado",
        "prioridade": "Indeterminado",
        "tempo_atendimento_minutos": 0,
        "fluxograma_utilizado": "Indeterminado",
        "discriminadores_gerais_avaliados": [],
        "discriminadores_especificos_ativados": [],
        "populacao_especial": None,
        "over_triage_aplicado": False,
        "confianca": "baixa",
        "justificativa": "",
        "alertas": [],
        "disclaimer": "Classificação de apoio à decisão. A avaliação final é responsabilidade do profissional de saúde.",
    }
    for key, default in defaults.items():
        if key not in result:
            result[key] = default

    # Ensure alertas is never null
    if result["alertas"] is None:
        result["alertas"] = []

    return result
