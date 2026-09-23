import pytest

from app.prompt_esi import build_system_prompt


@pytest.mark.parametrize("normalization", [None, {
    "sintomas_nao_normalizados": [{"original": "caganeira"}],
}])
def test_custom_prompt_keeps_mandatory_normalization_contract(normalization):
    custom = 'Classifique a triagem. Retorne apenas {"classificacao": "ESI-3"}.'
    result = build_system_prompt("caganeira", normalization, custom)
    assert result.startswith(custom)
    assert "CONTRATO OBRIGATÓRIO DE NORMALIZAÇÃO DO BACKEND" in result
    assert 'inclua SEMPRE "normalizacao_llm"' in result
    assert 'Para CADA termo listado em "sintomas_nao_normalizados"' in result
    assert '"normalizado": "<termo_canônico em snake_case>"' in result
    assert '"normalizacao_llm": []' in result


def test_default_prompt_keeps_original_normalization_instructions():
    result = build_system_prompt("caganeira")
    assert '"normalizacao_llm": [' in result
    assert "## NORMALIZAÇÃO SEMÂNTICA" in result
    assert "CONTRATO OBRIGATÓRIO DE NORMALIZAÇÃO DO BACKEND" not in result
