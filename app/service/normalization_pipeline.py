"""Shared semantic-normalization lifecycle for Groq and Ollama."""

import logging

from app.service.ner_service import NERService
from app.service.llm_normalization import extract_llm_normalizations

logger = logging.getLogger(__name__)


def normalize_safely(symptoms: str) -> dict:
    """Keep unresolved phrases available to the LLM when retrieval fails."""
    try:
        from app.service.normalization import NormalizationService

        result = NormalizationService().normalize_symptoms(symptoms)
        if result.get("sintomas_normalizados") or result.get("sintomas_nao_normalizados"):
            return result
    except Exception:
        logger.exception("triage.semantic_normalization_failed")

    phrases = NERService().extract_symptoms(symptoms)
    if not phrases and symptoms.strip():
        phrases = [symptoms.strip()]
    return {
        "sintomas_normalizados": [],
        "sintomas_nao_normalizados": [
            {"original": phrase, "score": 0.0, "tipo": "nao_normalizado",
             "motivo": "normalizacao_indisponivel"}
            for phrase in phrases
        ],
        "total_extraidos": len(phrases),
        "taxa_normalizacao": 0.0,
        "debug": {"status": "fallback"},
    }


def save_candidates(normalizations: list[dict], normalization: dict) -> dict:
    """Report confirmed inserts, without depending on Qdrant initialization."""
    saved_ids = []
    failed = []
    scores = {
        item["original"]: item.get("score")
        for item in normalization.get("sintomas_nao_normalizados", [])
    }
    if not normalizations:
        return {"ids": [], "falhas": []}
    try:
        from app.service.postgres_service import PostgresService

        repository = PostgresService()
    except Exception:
        logger.exception("triage.candidate_repository_unavailable")
        return {"ids": [], "falhas": [item["original"] for item in normalizations]}
    for item in normalizations:
        try:
            candidate_id = repository.create_base_candidata(
                input_original=item["original"],
                normalizado_sugerido=item["normalizado"],
                score_e5=scores.get(item["original"]),
                score_ollama_confianca=item["confianca"],
                origem="llm",
            )
            if candidate_id is None:
                failed.append(item["original"])
            else:
                saved_ids.append(candidate_id)
        except Exception:
            logger.exception("triage.candidate_insert_failed")
            failed.append(item["original"])
    logger.info("triage.candidates saved=%s failed=%s", len(saved_ids), len(failed))
    return {"ids": saved_ids, "falhas": failed}


def complete_normalization(parsed: dict, normalization: dict, symptoms: str) -> None:
    """Validate LLM candidates, persist them and expose incomplete processing."""
    candidates = extract_llm_normalizations(parsed, normalization)
    logger.info(
        "triage.response_normalization unresolved=%s accepted=%s",
        len(normalization.get("sintomas_nao_normalizados", [])), len(candidates),
    )
    persistence = save_candidates(candidates, normalization)
    accepted = {item["original"] for item in candidates}
    missing = [
        item["original"] for item in normalization.get("sintomas_nao_normalizados", [])
        if item["original"] not in accepted
    ]
    normalization["persistencia_base_candidata"] = persistence
    normalization["normalizacoes_pendentes_llm"] = missing
    alerts = parsed.get("alertas") or []
    if not isinstance(alerts, list):
        alerts = [str(alerts)]
    if missing:
        logger.warning("triage.normalization_incomplete missing=%s", len(missing))
        alerts.append("A IA não retornou normalização válida para todos os termos pendentes.")
    if persistence["falhas"]:
        alerts.append("Não foi possível salvar todas as normalizações na base candidata.")
    parsed["alertas"] = alerts
    parsed["texto_original"] = symptoms
    parsed["normalizacao_resultado"] = normalization
    parsed["normalizacao_llm"] = candidates
    parsed["sintomas_normalizados"] = [
        item["normalizado"] for item in normalization.get("sintomas_normalizados", [])
        if item.get("normalizado")
    ]
