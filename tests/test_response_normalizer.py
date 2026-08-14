from app.response_normalizer import normalize_triage_response


def test_normalizes_malformed_resource_and_population_fields():
    result = normalize_triage_response(
        {
            "recursos_estimados": "Avaliação médica imediata",
            "recursos_detalhados": "Oxigênio, medicação para febre, exames de imagem",
            "populacao_especial": False,
        }
    )

    assert result["recursos_estimados"] == 3
    assert result["recursos_detalhados"] == [
        "Oxigênio",
        "medicação para febre",
        "exames de imagem",
    ]
    assert result["populacao_especial"] is None
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
