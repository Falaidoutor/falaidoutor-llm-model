"""Normalização defensiva da saída estruturada do modelo."""

from collections.abc import Mapping
from typing import Any


def normalize_triage_response(result: Mapping[str, Any]) -> dict[str, Any]:
    """Converte variações comuns do LLM para o contrato da API.

    O modelo pode devolver uma lista como texto ou usar um texto descritivo
    em um campo numérico. Esses casos não devem derrubar a API; a resposta
    original continua preservada em ``rawModelOutput`` para auditoria.
    """

    normalized = dict(result)
    original = dict(result)
    warnings = list(normalized.get("validation_warnings") or [])

    detailed = _as_string_list(normalized.get("recursos_detalhados"))
    if normalized.get("recursos_detalhados") != detailed:
        warnings.append(
            "recursos_detalhados foi normalizado para uma lista de recursos."
        )
    normalized["recursos_detalhados"] = detailed

    estimated = normalized.get("recursos_estimados")
    if isinstance(estimated, bool):
        estimated = None
    elif isinstance(estimated, str):
        try:
            estimated = int(estimated.strip())
        except ValueError:
            estimated = None

    if not isinstance(estimated, int) or estimated < 0:
        estimated = len(detailed)
        warnings.append(
            "recursos_estimados foi inferido a partir de recursos_detalhados."
        )
    normalized["recursos_estimados"] = estimated

    vital_signs = normalized.get("sinais_vitais_zona_perigo")
    normalized_vital_signs = _as_bool(vital_signs)
    if vital_signs != normalized_vital_signs:
        warnings.append(
            "sinais_vitais_zona_perigo foi normalizado para booleano."
        )
    normalized["sinais_vitais_zona_perigo"] = normalized_vital_signs

    population = normalized.get("populacao_especial")
    if isinstance(population, bool) or population not in (
        None,
        "pediatria",
        "gestante",
        "idoso",
    ):
        normalized["populacao_especial"] = None
        warnings.append(
            "populacao_especial inválida foi normalizada para null."
        )

    normalized["validation_warnings"] = _unique(warnings)
    normalized["rawModelOutput"] = normalized.get("rawModelOutput") or original
    return normalized


def _as_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().casefold()
        if normalized in {"sim", "true", "verdadeiro", "yes", "1"}:
            return True
        if normalized in {
            "não",
            "nao",
            "não informado",
            "nao informado",
            "não informados",
            "nao informados",
            "false",
            "falso",
            "no",
            "0",
        }:
            return False
    return False


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))
