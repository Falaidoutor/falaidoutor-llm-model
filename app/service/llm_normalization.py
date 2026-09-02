"""Helpers for validating normalization suggestions returned by an LLM."""


def extract_llm_normalizations(parsed: dict, normalization: dict) -> list[dict]:
    unresolved = {
        str(item.get("original", "")).strip().lower()
        for item in normalization.get("sintomas_nao_normalizados", [])
        if item.get("original")
    }
    if not unresolved:
        return []

    raw_items = (
        parsed.get("normalizacao_llm")
        or parsed.get("normalizacao_ollama")
        or []
    )
    if not isinstance(raw_items, list):
        return []

    result: list[dict] = []
    seen: set[str] = set()
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        original = str(item.get("original", "")).strip()
        canonical = str(item.get("normalizado", "")).strip()
        key = original.lower()
        if key not in unresolved or not canonical or key in seen:
            continue
        confidence = str(item.get("confianca", "media")).strip().lower()
        if confidence not in {"alta", "media", "baixa"}:
            confidence = "media"
        result.append(
            {
                "original": original,
                "normalizado": canonical,
                "confianca": confidence,
            }
        )
        seen.add(key)
    return result
