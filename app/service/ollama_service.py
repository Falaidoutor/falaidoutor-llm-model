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
        # Preparar dados com formato esperado: lista de dicts com 'original' e 'normalizado'
        sintomas_normalizados_com_original = [
            {
                "original": s["original"],
                "normalizado": s["normalizado"]
            }
            for s in normalizacao_resultado.get("sintomas_normalizados", [])
        ]
        
        sintomas_nao_normalizados = [
            s["original"]
            for s in normalizacao_resultado.get("sintomas_nao_normalizados", [])
        ]

        user_prompt = build_user_prompt(
            sintomas_normalizados_com_original,
            sintomas_nao_normalizados,
            input_original=symptoms,
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
        #print(SYSTEM_PROMPT)

        print("USER PROMPT:")
        print(user_prompt)
       

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

        # 5. EXTRAIR NORMALIZAÇÕES DO OLLAMA (apenas para sintomas não normalizados)
        normalizacao_ollama = _extract_ollama_normalization(
            parsed, sintomas_nao_normalizados, sintomas_normalizados_com_original
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
        parsed["sintomas_normalizados"] = [s["normalizado"] for s in sintomas_normalizados_com_original]

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


def _extract_ollama_normalization(parsed: dict, sintomas_nao_normalizados: list, sintomas_normalizados_com_original: list = None) -> list:
    """
    Extrai as normalizações feitas pelo Ollama para sintomas não normalizados.
    
    CRÍTICO: Salva APENAS normalizações de termos que estavam em sintomas_nao_normalizados.
    Não salva normalizações de sintomas que já vieram em sintomas_normalizados (pré-normalizados).

    Procura em locais comuns na resposta:
    - Campo "normalizacao_ollama" (se Ollama seguir formato)
    - Campo "justificativa" (análise textual - fallback)

    Args:
        parsed: Resposta JSON do Ollama já parseada
        sintomas_nao_normalizados: Lista de strings com termos NÃO normalizados originais
        sintomas_normalizados_com_original: Lista de dicts com 'original' e 'normalizado' (pre-normalizados)

    Returns:
        Lista de {"original": str, "normalizado": str, "confianca": str}
    """
    normalizacoes = []
    
    # Extrair lista de originais já normalizados para evitar duplicatas
    originais_ja_normalizados = set()
    if sintomas_normalizados_com_original:
        for item in sintomas_normalizados_com_original:
            if isinstance(item, dict) and "original" in item:
                originais_ja_normalizados.add(item["original"].lower())

    logger.info("=" * 80)
    logger.info(f"[_extract_ollama_normalization] Procurando normalizações")
    logger.info(f"[_extract_ollama_normalization] Sintomas já normalizados (filtro): {originais_ja_normalizados}")
    logger.info(f"[_extract_ollama_normalization] Campos disponíveis: {list(parsed.keys())}")
    logger.info(f"[_extract_ollama_normalization] Sintomas não normalizados: {sintomas_nao_normalizados}")
    
    # 1. Verificar se Ollama retornou campo específico de normalizações
    normalizacao_ollama = parsed.get("normalizacao_ollama", [])
    if isinstance(normalizacao_ollama, list) and len(normalizacao_ollama) > 0:
        logger.info(f"[_extract_ollama_normalization] Campo 'normalizacao_ollama' encontrado com {len(normalizacao_ollama)} itens")
        for norm in normalizacao_ollama:
            if isinstance(norm, dict):
                original = norm.get("original", "")
                # FILTRO CRÍTICO: Verificar se este original já estava em sintomas_normalizados
                if original.lower() not in originais_ja_normalizados:
                    normalizacoes.append(
                        {
                            "original": original,
                            "normalizado": norm.get("normalizado", ""),
                            "confianca": norm.get("confianca", "media"),
                        }
                    )
                    logger.info(f"[_extract_ollama_normalization] Incluído: '{original}' → '{norm.get('normalizado')}'")
                else:
                    logger.warning(f"[_extract_ollama_normalization] Ignorado (já em sintomas_normalizados): '{original}'")
    else:
        # 2. Fallback: Se campo está vazio mas há sintomas_nao_normalizados, tentar extrair da justificativa
        if sintomas_nao_normalizados:
            logger.warning(f"[_extract_ollama_normalization] Campo 'normalizacao_ollama' vazio! Tentando extrair da justificativa...")
            justificativa = parsed.get("justificativa", "")
            
            # Tentar extrair padrões como "X foi normalizado para Y" ou "X → Y"
            for original in sintomas_nao_normalizados:
                if not isinstance(original, str):
                    continue
                
                # FILTRO: Não processar se já estava em sintomas_normalizados
                if original.lower() in originais_ja_normalizados:
                    logger.warning(f"[_extract_ollama_normalization] Pulando (já normalizado): '{original}'")
                    continue
                
                # Padrões para capturar: 
                # - "foi normalizado para X"
                # - "normalizado em X"
                # - "→ X"
                # - "como X"
                patterns = [
                    rf"'{re.escape(original)}'\s+foi normalizado para\s+'?([a-z_]+)'?",
                    rf"'{re.escape(original)}'\s+normalizado em\s+'?([a-z_]+)'?",
                    rf"{re.escape(original)}\s+→\s+([a-z_]+)",
                    rf"{re.escape(original)}\s+como\s+([a-z_]+)",
                ]
                
                normalizado = None
                for pattern in patterns:
                    match = re.search(pattern, justificativa, re.IGNORECASE)
                    if match:
                        normalizado = match.group(1)
                        break
                
                if normalizado:
                    logger.info(f"[_extract_ollama_normalization] Extraído da justificativa: '{original}' → '{normalizado}'")
                    normalizacoes.append({
                        "original": original,
                        "normalizado": normalizado,
                        "confianca": "media",  # Confiança reduzida pois foi extraído da justificativa
                    })
        else:
            logger.info(f"[_extract_ollama_normalization] Nenhum sintoma não normalizado para processar")
    
    logger.info(f"[_extract_ollama_normalization] Total extraído (após filtro): {len(normalizacoes)}")
    logger.info("=" * 80)
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
