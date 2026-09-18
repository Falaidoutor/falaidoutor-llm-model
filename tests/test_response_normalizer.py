from app.response_normalizer import normalize_triage_response


def test_normalizes_malformed_resource_and_population_fields():
    result = normalize_triage_response(
        {
            "recursos_estimados": "Avaliação médica imediata",
            "recursos_detalhados": "Oxigênio, medicação para febre, exames de imagem",
            "populacao_especial": False,
            "sinais_vitais_zona_perigo": "Não informados",
        }
    )

    assert result["recursos_estimados"] == 3
    assert result["recursos_detalhados"] == [
        "Oxigênio",
        "medicação para febre",
        "exames de imagem",
    ]
    assert result["populacao_especial"] is None
    assert result["sinais_vitais_zona_perigo"] is False
    assert "rawModelOutput" in result
    assert result["validation_warnings"]


def test_keeps_valid_contract_values():
    result = normalize_triage_response(
        {
            "recursos_estimados": 2,
            "recursos_detalhados": ["Exame", "Medicação"],
            "populacao_especial": "idoso",
        }
    )

    assert result["recursos_estimados"] == 2
    assert result["recursos_detalhados"] == ["Exame", "Medicação"]
    assert result["populacao_especial"] == "idoso"


def test_normalizes_confidence_to_percentage():
    result = normalize_triage_response({"confianca": 0.85})

    assert result["confianca"] == 85.0
    assert result["confidence"] == 85.0
    assert result["confidenceScore"] == 85.0
    assert any("percentual" in warning for warning in result["validation_warnings"])


def test_normalizes_single_string_list_fields_and_preserves_null():
    result = normalize_triage_response(
        {
            "criterios_ponto_decisao": "Sem sinais de alarme",
            "alertas": "Informações clínicas insuficientes",
            "recursos_detalhados": None,
        }
    )

    assert result["criterios_ponto_decisao"] == ["Sem sinais de alarme"]
    assert result["alertas"] == ["Informações clínicas insuficientes"]
    assert result["recursos_detalhados"] == []


def test_preserves_null_for_unknown_list_fields():
    result = normalize_triage_response(
        {"criterios_ponto_decisao": None, "alertas": None}
    )

    assert result["criterios_ponto_decisao"] is None
    assert result["alertas"] is None
