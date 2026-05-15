import json
import logging
import re

import httpx

from app.config.settings import OLLAMA_BASE_URL, OLLAMA_MODEL_NAME
from app.prompt.prompt import SYSTEM_PROMPT, build_user_prompt
from app.service.validator import validate_triage_response
from app.service.normalization import NormalizationService

logger = logging.getLogger(__name__)


async def classify_symptoms(symptoms: str, debug_mode: bool = False) -> dict:
    """
    Classificação de triagem com normalização semântica de sintomas.

    Pipeline:
    1. Normalização semântica (NER + E5 + Qdrant)
    2. Construir prompt com sintomas normalizados/não normalizados
    3. Enviar ao Ollama/Manchester
    4. Parsear resposta e validar
    5. Registrar normalizações do Ollama em base_candidata

    Args:
        symptoms: Texto com sintomas do usuário
        debug_mode: Se True, inclui metadata de debug

    Returns:
        TriageResponse completa com normalização
    """
    try:
        # 1. NORMALIZAÇÃO SEMÂNTICA
        logger.info(f"Iniciando classificação de sintomas: '{symptoms[:50]}...'")

        normalization_svc = NormalizationService()
        normalizacao_resultado = normalization_svc.normalize_symptoms(symptoms)

        logger.info(
            f"Normalização concluída: {normalizacao_resultado['total_extraidos']} sintomas, "
            f"taxa: {normalizacao_resultado['taxa_normalizacao']*100:.1f}%"
        )

        # 2. CONSTRUIR PROMPT COM SINTOMAS NORMALIZADOS E NÃO NORMALIZADOS
        sintomas_normalizados = [
            s["normalizado"]
            for s in normalizacao_resultado.get("sintomas_normalizados", [])
        ]
        sintomas_nao_normalizados = [
            s["original"]
            for s in normalizacao_resultado.get("sintomas_nao_normalizados", [])
        ]

        user_prompt = build_user_prompt(
            sintomas_normalizados,
            sintomas_nao_normalizados,
            debug_mode=debug_mode,
        )

        # 3. ENVIAR AO OLLAMA
        payload = {
            "model": OLLAMA_MODEL_NAME,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "format": "json",
        }

        # Log detalhado do prompt
        logger.info("=" * 80)
        logger.info("SYSTEM PROMPT (primeiras 500 chars):")
        logger.info(SYSTEM_PROMPT[:500] + "...")
        logger.info("=" * 80)
        logger.info("USER PROMPT COMPLETO:")
        logger.info(user_prompt)
        logger.info("=" * 80)
        logger.info("PAYLOAD COMPLETO (sem system prompt):")
        logger.info(json.dumps({
            "model": payload["model"],
            "messages": [
                {"role": "system", "content": "[...SYSTEM_PROMPT OMITIDO...]"},
                {"role": "user", "content": payload["messages"][1]["content"]}
            ],
            "stream": payload["stream"],
            "format": payload["format"]
        }, ensure_ascii=False, indent=2))
        logger.info("=" * 80)

        logger.info("Enviando requisição ao Ollama...")
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat", json=payload
            )
            response.raise_for_status()

        data = response.json()
        content = data["message"]["content"]

        # 4. PARSEAR RESPOSTA
        parsed = parse_response(content)

        # 5. EXTRAIR NORMALIZAÇÕES DO OLLAMA
        normalizacao_ollama = _extract_ollama_normalization(
            parsed, sintomas_nao_normalizados
        )

        if normalizacao_ollama:
            # Registrar em base_candidata (sem sintoma_id - será correlacionado por serviço posterior)
            for normalizacao in normalizacao_ollama:
                normalization_svc.postgres_service.create_base_candidata(
                    input_original=normalizacao["original"],
                    normalizado_sugerido=normalizacao["normalizado"],
                    score_ollama_confianca=normalizacao.get("confianca", "media"),
                    origem="ollama",
                )

        # 6. POPULAR CAMPOS DE NORMALIZAÇÃO NA RESPOSTA
        parsed["normalizacao_resultado"] = normalizacao_resultado
        parsed["normalizacao_ollama"] = normalizacao_ollama
        parsed["texto_original"] = symptoms
        parsed["sintomas_normalizados"] = sintomas_normalizados

        # 7. VALIDAÇÃO
        validation = validate_triage_response(parsed)
        parsed["validation_errors"] = validation.errors
        parsed["validation_warnings"] = validation.warnings

        logger.info("Classificação concluída com sucesso")
        return parsed

    except Exception as e:
        logger.error(f"Erro ao classificar sintomas: {e}")
        return _minimal_error_response(
            f"Erro ao processar sintomas: {str(e)}"
        )


def _extract_ollama_normalization(parsed: dict, sintomas_nao_normalizados: list) -> list:
    """
    Extrai as normalizações feitas pelo Ollama para sintomas não normalizados.

    Procura em locais comuns na resposta:
    - Campo "normalizacao_ollama" (se Ollama seguir formato)
    - Campo "justificativa" (análise textual)

    Returns:
        Lista de {"original": str, "normalizado": str, "confianca": str}
    """
    normalizacoes = []

    # Verificar se Ollama retornou campo específico de normalizações
    if "normalizacao_ollama" in parsed:
        normalizacoes_raw = parsed.get("normalizacao_ollama", [])
        if isinstance(normalizacoes_raw, list):
            for norm in normalizacoes_raw:
                if isinstance(norm, dict):
                    normalizacoes.append(
                        {
                            "original": norm.get("original", ""),
                            "normalizado": norm.get("normalizado", ""),
                            "confianca": norm.get("confianca", "media"),
                        }
                    )

    # Se nenhuma normalização foi extraída explicitamente,
    # deixar vazio (Ollama pode não ter normalizado os sintomas não normalizados)
    return normalizacoes
def parse_response(content: str) -> dict:
    """Parseia resposta JSON do Ollama com tratamento de erros."""
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
    logger.warning("Não foi possível parsear resposta JSON do Ollama")
    return _minimal_error_response(content)


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
        "normalizacao_resultado": None,
        "normalizacao_ollama": [],
    }
    for key, default in defaults.items():
        if key not in result:
            result[key] = default

    # Ensure alertas is never null
    if result["alertas"] is None:
        result["alertas"] = []

    return result


def _minimal_error_response(message: str) -> dict:
    """Retorna resposta mínima válida em caso de erro."""
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
        "justificativa": message,
        "alertas": ["Resposta do modelo não pôde ser interpretada como JSON válido."],
        "disclaimer": "Classificação de apoio à decisão. A avaliação final é responsabilidade do profissional de saúde.",
        "normalizacao_resultado": None,
        "normalizacao_ollama": [],
    }
