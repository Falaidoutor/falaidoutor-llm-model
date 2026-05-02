import pytest

from app.service.validator import (
    CLASSIFICACOES_VALIDAS,
    DISCLAIMER_ESPERADO,
    DISCRIMINADORES_GERAIS,
    validate_triage_response,
)


# ──────────────────────────────────────────────────────────────
# Helper: resposta válida completa
# ──────────────────────────────────────────────────────────────

def _build_valid_response(**overrides) -> dict:
    """Retorna um dict de triagem 100% válido. Sobreescreva campos via kwargs."""
    base = {
        "classificacao": "Amarelo",
        "prioridade": "Urgente",
        "tempo_atendimento_minutos": 60,
        "fluxograma_utilizado": "Dor Abdominal",
        "discriminadores_gerais_avaliados": [
            {"discriminador": d, "presente": d == "Dor intensa (EVA 7–8)"}
            for d in DISCRIMINADORES_GERAIS
        ],
        "discriminadores_especificos_ativados": ["Dor abdominal aguda"],
        "populacao_especial": None,
        "over_triage_aplicado": False,
        "confianca": "alta",
        "justificativa": (
            "Paciente relata dor abdominal intensa (EVA 7), ativando o "
            "discriminador geral 'Dor intensa (EVA 7–8)' de nível Amarelo."
        ),
        "alertas": [],
        "disclaimer": DISCLAIMER_ESPERADO,
    }
    base.update(overrides)
    return base


# ──────────────────────────────────────────────────────────────
# Testes: resposta totalmente válida
# ──────────────────────────────────────────────────────────────

class TestValidResponse:
    def test_valid_response_passes(self):
        result = validate_triage_response(_build_valid_response())
        assert result.is_valid
        assert result.errors == []

    def test_valid_response_no_warnings(self):
        result = validate_triage_response(_build_valid_response())
        assert result.warnings == []


# ──────────────────────────────────────────────────────────────
# Testes: 1. Validação estrutural
# ──────────────────────────────────────────────────────────────

class TestStructuralValidation:
    def test_classificacao_invalida(self):
        data = _build_valid_response(classificacao="Roxo")
        result = validate_triage_response(data)
        assert not result.is_valid
        assert any("classificacao" in e for e in result.errors)

    def test_prioridade_invalida(self):
        data = _build_valid_response(prioridade="Super urgente")
        result = validate_triage_response(data)
        assert not result.is_valid
        assert any("prioridade" in e for e in result.errors)

    def test_tempo_invalido(self):
        data = _build_valid_response(tempo_atendimento_minutos=45)
        result = validate_triage_response(data)
        assert not result.is_valid
        assert any("tempo_atendimento_minutos" in e for e in result.errors)

    def test_tempo_tipo_errado(self):
        data = _build_valid_response(tempo_atendimento_minutos="60")
        result = validate_triage_response(data)
        assert not result.is_valid
        assert any("int" in e for e in result.errors)

    def test_fluxograma_vazio(self):
        data = _build_valid_response(fluxograma_utilizado="")
        result = validate_triage_response(data)
        assert not result.is_valid

    def test_fluxograma_nao_oficial_gera_warning(self):
        data = _build_valid_response(fluxograma_utilizado="Dor de Barriga Genérica")
        result = validate_triage_response(data)
        assert result.is_valid  # warning, não erro
        assert any("fluxograma" in w for w in result.warnings)

    def test_discriminadores_gerais_tipo_errado(self):
        data = _build_valid_response(discriminadores_gerais_avaliados="nenhum")
        result = validate_triage_response(data)
        assert not result.is_valid

    def test_discriminador_geral_sem_campo_presente(self):
        data = _build_valid_response(
            discriminadores_gerais_avaliados=[{"discriminador": "Choque"}]
        )
        result = validate_triage_response(data)
        assert not result.is_valid

    def test_populacao_invalida(self):
        data = _build_valid_response(populacao_especial="adulto")
        result = validate_triage_response(data)
        assert not result.is_valid
        assert any("populacao_especial" in e for e in result.errors)

    def test_over_triage_tipo_errado(self):
        data = _build_valid_response(over_triage_aplicado="sim")
        result = validate_triage_response(data)
        assert not result.is_valid

    def test_confianca_invalida(self):
        data = _build_valid_response(confianca="muito alta")
        result = validate_triage_response(data)
        assert not result.is_valid

    def test_justificativa_vazia(self):
        data = _build_valid_response(justificativa="")
        result = validate_triage_response(data)
        assert not result.is_valid

    def test_alertas_null(self):
        data = _build_valid_response(alertas=None)
        result = validate_triage_response(data)
        assert not result.is_valid
        assert any("alertas" in e for e in result.errors)

    def test_disclaimer_diferente(self):
        data = _build_valid_response(disclaimer="Outra coisa.")
        result = validate_triage_response(data)
        assert not result.is_valid
        assert any("disclaimer" in e for e in result.errors)


# ──────────────────────────────────────────────────────────────
# Testes: 2. Validação de consistência lógica
# ──────────────────────────────────────────────────────────────

class TestConsistencyValidation:
    @pytest.mark.parametrize(
        "cor,prioridade,tempo",
        [
            ("Vermelho", "Emergência", 0),
            ("Laranja", "Muito urgente", 10),
            ("Amarelo", "Urgente", 60),
            ("Verde", "Pouco urgente", 120),
            ("Azul", "Não urgente", 240),
        ],
    )
    def test_todas_combinacoes_validas(self, cor, prioridade, tempo):
        dga = [{"discriminador": d, "presente": False} for d in DISCRIMINADORES_GERAIS]
        data = _build_valid_response(
            classificacao=cor,
            prioridade=prioridade,
            tempo_atendimento_minutos=tempo,
            discriminadores_gerais_avaliados=dga,
            discriminadores_especificos_ativados=[],
        )
        result = validate_triage_response(data)
        assert not any("Inconsistência" in e for e in result.errors)

    def test_cor_prioridade_inconsistente(self):
        data = _build_valid_response(
            classificacao="Vermelho",
            prioridade="Urgente",  # deveria ser Emergência
            tempo_atendimento_minutos=0,
        )
        result = validate_triage_response(data)
        assert not result.is_valid
        assert any("Inconsistência" in e and "prioridade" in e for e in result.errors)

    def test_cor_tempo_inconsistente(self):
        data = _build_valid_response(
            classificacao="Laranja",
            prioridade="Muito urgente",
            tempo_atendimento_minutos=60,  # deveria ser 10
        )
        result = validate_triage_response(data)
        assert not result.is_valid
        assert any("Inconsistência" in e and "tempo" in e for e in result.errors)


# ──────────────────────────────────────────────────────────────
# Testes: 3. Validação de regras de negócio
# ──────────────────────────────────────────────────────────────

class TestBusinessRulesValidation:
    def test_discriminadores_gerais_faltantes_gera_warning(self):
        data = _build_valid_response(
            discriminadores_gerais_avaliados=[
                {"discriminador": "Obstrução de via aérea", "presente": False},
            ]
        )
        result = validate_triage_response(data)
        assert any("não avaliados" in w for w in result.warnings)

    def test_classificacao_menos_grave_que_discriminador(self):
        """Verde quando discriminador Vermelho está ativo → erro."""
        dga = [
            {"discriminador": d, "presente": d == "Obstrução de via aérea"}
            for d in DISCRIMINADORES_GERAIS
        ]
        data = _build_valid_response(
            classificacao="Verde",
            prioridade="Pouco urgente",
            tempo_atendimento_minutos=120,
            discriminadores_gerais_avaliados=dga,
            discriminadores_especificos_ativados=[],
        )
        result = validate_triage_response(data)
        assert not result.is_valid
        assert any("menos grave" in e for e in result.errors)

    def test_over_triage_permite_classificacao_mais_grave(self):
        """Over-triage permite elevar a classificação acima do discriminador."""
        dga = [
            {"discriminador": d, "presente": d == "Dor intensa (EVA 7–8)"}
            for d in DISCRIMINADORES_GERAIS
        ]
        data = _build_valid_response(
            classificacao="Laranja",
            prioridade="Muito urgente",
            tempo_atendimento_minutos=10,
            discriminadores_gerais_avaliados=dga,
            over_triage_aplicado=True,
            justificativa=(
                "Paciente idoso com dor intensa e comorbidades. "
                "Dúvida entre Amarelo e Laranja — aplicado over-triage."
            ),
        )
        result = validate_triage_response(data)
        # Não deve ter erro de "menos grave"
        assert not any("menos grave" in e for e in result.errors)

    def test_azul_com_discriminador_ativo_gera_erro(self):
        dga = [
            {"discriminador": d, "presente": d == "Vômitos persistentes"}
            for d in DISCRIMINADORES_GERAIS
        ]
        data = _build_valid_response(
            classificacao="Azul",
            prioridade="Não urgente",
            tempo_atendimento_minutos=240,
            discriminadores_gerais_avaliados=dga,
            discriminadores_especificos_ativados=[],
        )
        result = validate_triage_response(data)
        assert not result.is_valid
        assert any("Azul" in e for e in result.errors)

    def test_over_triage_sem_justificativa_gera_erro(self):
        data = _build_valid_response(
            over_triage_aplicado=True,
            justificativa="",
        )
        result = validate_triage_response(data)
        assert not result.is_valid
        assert any("over_triage" in e.lower() for e in result.errors)

    def test_confianca_baixa_sem_alertas_gera_warning(self):
        data = _build_valid_response(confianca="baixa", alertas=[])
        result = validate_triage_response(data)
        assert any("baixa" in w for w in result.warnings)

    def test_confianca_baixa_com_alertas_ok(self):
        data = _build_valid_response(
            confianca="baixa",
            alertas=["Qual a duração dos sintomas?"],
        )
        result = validate_triage_response(data)
        assert not any("baixa" in w for w in result.warnings)

    def test_termos_proibidos_na_justificativa(self):
        data = _build_valid_response(
            justificativa="Provavelmente é um quadro de gastrite aguda."
        )
        result = validate_triage_response(data)
        assert any("proibido" in w for w in result.warnings)

    def test_classificacao_grave_sem_discriminadores_gera_warning(self):
        """Vermelho sem nenhum discriminador ativo e sem over-triage → warning."""
        dga = [{"discriminador": d, "presente": False} for d in DISCRIMINADORES_GERAIS]
        data = _build_valid_response(
            classificacao="Vermelho",
            prioridade="Emergência",
            tempo_atendimento_minutos=0,
            discriminadores_gerais_avaliados=dga,
            discriminadores_especificos_ativados=[],
            over_triage_aplicado=False,
        )
        result = validate_triage_response(data)
        assert any("sem nenhum discriminador" in w.lower() for w in result.warnings)

    def test_verde_sem_discriminadores_ok(self):
        """Verde sem nenhum discriminador é perfeitamente válido."""
        dga = [{"discriminador": d, "presente": False} for d in DISCRIMINADORES_GERAIS]
        data = _build_valid_response(
            classificacao="Verde",
            prioridade="Pouco urgente",
            tempo_atendimento_minutos=120,
            discriminadores_gerais_avaliados=dga,
            discriminadores_especificos_ativados=[],
        )
        result = validate_triage_response(data)
        assert result.is_valid
