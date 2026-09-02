from app.validator import DISCLAIMER_ESPERADO, validate_triage_response


def _valid_response(**overrides) -> dict:
    response = {
        "classificacao": "ESI-3",
        "nivel": 3,
        "nome_nivel": "Urgente",
        "ponto_decisao_ativado": "D",
        "criterios_ponto_decisao": ["Dois ou mais recursos"],
        "recursos_estimados": 2,
        "recursos_detalhados": ["Exames laboratoriais", "Imagem"],
        "sinais_vitais_zona_perigo": False,
        "populacao_especial": None,
        "over_triage_aplicado": False,
        "confianca": "alta",
        "justificativa": "Dois recursos necessários direcionam ao ponto D e ESI-3.",
        "alertas": [],
        "disclaimer": DISCLAIMER_ESPERADO,
    }
    response.update(overrides)
    return response


def test_valid_esi_response_has_no_errors():
    result = validate_triage_response(_valid_response())

    assert result.is_valid
    assert result.errors == []


def test_level_and_classification_must_match():
    result = validate_triage_response(_valid_response(classificacao="ESI-4"))

    assert not result.is_valid
    assert any("nivel 3 requer classificacao" in error for error in result.errors)


def test_low_confidence_without_alerts_warns():
    result = validate_triage_response(_valid_response(confianca="baixa"))

    assert any("confianca='baixa'" in warning for warning in result.warnings)


def test_esi_4_with_wrong_resource_count_warns():
    result = validate_triage_response(
        _valid_response(
            classificacao="ESI-4",
            nivel=4,
            nome_nivel="Menos urgente",
            ponto_decisao_ativado="C",
            recursos_estimados=0,
            recursos_detalhados=[],
        )
    )

    assert result.is_valid
    assert any("ESI-4 indica 1 recurso" in warning for warning in result.warnings)


def test_forbidden_diagnostic_language_warns():
    result = validate_triage_response(
        _valid_response(justificativa="Pode ser uma condição clínica específica.")
    )

    assert any("termo proibido" in warning for warning in result.warnings)
