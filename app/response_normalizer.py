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

    for field_name, label in (
        ("criterios_ponto_decisao", "criterios_ponto_decisao"),
        ("alertas", "alertas"),
    ):
        value = normalized.get(field_name)
        normalized_value = _as_optional_string_list(value)
        if value != normalized_value:
            warnings.append(f"{label} foi normalizado para uma lista ou null.")
        normalized[field_name] = normalized_value

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

    confidence = normalized.get("confianca")
    confidence_percentage = _confidence_percentage(confidence)
    if confidence_percentage is None:
        for key in ("confidence", "confidenceScore", "confidence_score", "score"):
            confidence_percentage = _confidence_percentage(normalized.get(key))
            if confidence_percentage is not None:
                normalized["confianca"] = confidence_percentage
                warnings.append(
                    f"confianca foi preenchida a partir de {key} e normalizada para percentual."
                )
                break
    if confidence_percentage is not None and confidence != confidence_percentage:
        normalized["confianca"] = confidence_percentage
        if confidence is not None:
            warnings.append("confianca foi normalizada para percentual.")

    # Keep the numeric aliases consistent for consumers that read either field.
    for key in ("confidence", "confidenceScore"):
        alias_percentage = _confidence_percentage(normalized.get(key))
        if alias_percentage is not None:
            normalized[key] = alias_percentage
    if confidence_percentage is not None:
        normalized.setdefault("confidence", confidence_percentage)
        normalized.setdefault("confidenceScore", confidence_percentage)

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


def _as_optional_string_list(value: Any) -> list[str] | None:
    """Aceita array, string única ou null nos campos de múltiplos itens.

    Arrays vazios continuam sendo arrays vazios; null continua sendo null para
    representar explicitamente que o modelo não encontrou registros.
    """
    if value is None:
        return None
    if isinstance(value, list):
        return [item for item in (str(item).strip() for item in value) if item]
    if isinstance(value, str):
        value = value.strip()
        return [value] if value else None
    return [str(value).strip()] if str(value).strip() else None


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


def _confidence_percentage(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None

    if isinstance(value, str) and value.strip().casefold() in {"alta", "high"}:
        return 95.0
    if isinstance(value, str) and value.strip().casefold() in {"media", "média", "medium"}:
        return 80.0
    if isinstance(value, str) and value.strip().casefold() in {"baixa", "low"}:
        return 35.0

    if isinstance(value, (int, float)):
        numeric = float(value)
    elif isinstance(value, str):
        try:
            numeric = float(value.strip().replace("%", "").replace(",", "."))
        except ValueError:
            return None
    else:
        return None

    if numeric <= 1:
        numeric *= 100
    if numeric < 0 or numeric > 100:
        return None
    return round(numeric, 2)


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))
