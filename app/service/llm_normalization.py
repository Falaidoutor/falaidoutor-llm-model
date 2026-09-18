"""Helpers for validating normalization suggestions returned by an LLM."""

import unicodedata


def extract_llm_normalizations(parsed: dict, normalization: dict) -> list[dict]:
    unresolved = {
        _comparison_key(item.get("original")): str(item.get("original", "")).strip()
        for item in normalization.get("sintomas_nao_normalizados", [])
        if item.get("original") and _comparison_key(item.get("original"))
    }
    if not unresolved:
        return []

    raw_items = (
        parsed.get("normalizacao_llm")
        or parsed.get("normalizacao_ollama")
        or []
    )
    if isinstance(raw_items, dict):
        raw_items = [raw_items]
    if not isinstance(raw_items, list):
        return []

    result: list[dict] = []
    seen: set[str] = set()
    for index, item in enumerate(raw_items):
        if isinstance(item, str):
            continue
        if not isinstance(item, dict):
            continue

        original = _first_text(item, "original", "termo_original", "input", "termo")
        canonical = _first_text(
            item,
            "normalizado",
            "termo_canonico",
            "canonical",
            "sugestao",
            "sugestão",
        )
        key = _match_unresolved(original, unresolved)
        if key is None and not original and len(unresolved) == 1 and index == 0:
            key = next(iter(unresolved))
            original = unresolved[key]

        if key is None or not canonical or key in seen:
            continue
        confidence = str(
            item.get("confianca", item.get("confidence", "media"))
        ).strip().lower().replace("média", "media")
        if confidence not in {"alta", "media", "baixa"}:
            confidence = "media"
        result.append(
            {
                "original": unresolved[key],
                "normalizado": canonical,
                "confianca": confidence,
            }
        )
        seen.add(key)
    return result


def _first_text(item: dict, *keys: str) -> str:
    for key in keys:
        value = item.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _comparison_key(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(text.casefold().split())


def _match_unresolved(original: str, unresolved: dict[str, str]) -> str | None:
    key = _comparison_key(original)
    if not key:
        return None
    if key in unresolved:
        return key
    for unresolved_key in unresolved:
        if unresolved_key in key or key in unresolved_key:
            return unresolved_key
    return None
