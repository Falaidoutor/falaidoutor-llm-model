"""Testes para normalização semântica da entrada do usuário."""

import pytest

from app.service.normalizacao_semantica import (
    NormalizacaoSemantica,
)
from app.service.cid10_mapper import CID10Mapper
from app.service.symptom_normalizer import SymptomNormalizer
from app.service.semantic_analyzer import SemanticAnalyzer



class TestSymptomNormalizer:
    """Testa normalização de sintomas."""

    def setup_method(self):
        self.normalizer = SymptomNormalizer()

    def test_normalize_text_basic_cleanup(self):
        """Testa limpeza básica de texto."""
        text = "Dor DE Cabeça!!!"
        result = self.normalizer.normalize_text(text)
        assert result == "dor de cabeça"

    def test_normalize_symptoms_canonical_form(self):
        """Testa mapeamento para forma canônica."""
        text = "Estou com cefaleia e vomitando"
        result = self.normalizer.normalize_symptoms(text)
        assert "dor de cabeça" in result
        assert "vômito" in result

    def test_normalize_symptoms_synonyms(self):
        """Testa reconhecimento de sinônimos."""
        text = "dor na cabeça, enjôo e falta aer"
        result = self.normalizer.normalize_symptoms(text)
        assert "dor de cabeça" in result
        assert "náusea" in result
        assert "falta de ar" in result

    def test_extract_intensity_eva_scale(self):
        """Testa extração de intensidade via EVA."""
        # EVA baixa
        assert self.normalizer.extract_intensity_indicators("dor eva 2") == "leve"
        # EVA média
        assert self.normalizer.extract_intensity_indicators("dor eva 5") == "moderada"
        # EVA alta
        assert self.normalizer.extract_intensity_indicators("dor eva 9") == "intensa"

    def test_extract_intensity_keywords(self):
        """Testa extração de intensidade via palavras-chave."""
        assert self.normalizer.extract_intensity_indicators("dor muito intensa") == "intensa"
        assert self.normalizer.extract_intensity_indicators("dor levinha") == "leve"
        assert self.normalizer.extract_intensity_indicators("dor normal") == "moderada"

    def test_extract_duration(self):
        """Testa extração de duração."""
        assert self.normalizer.extract_duration("há 3 dias") == "3 dias"
        assert self.normalizer.extract_duration("desde 2 horas") == "2 horas"
        assert self.normalizer.extract_duration("ontem") == "1 dia"
        assert self.normalizer.extract_duration("hoje") == "Agudo (hoje)"

    def test_detect_red_flags(self):
        """Testa detecção de red flags."""
        # Red flag: não consigo respirar
        flags = self.normalizer.detect_red_flags("não consigo respirar")
        assert len(flags) > 0
        assert any("Respiração" in f["flag"] for f in flags)

        # Red flag: pior dor da vida
        flags = self.normalizer.detect_red_flags("pior dor da minha vida")
        assert len(flags) > 0

        # Sem red flags
        flags = self.normalizer.detect_red_flags("dor de cabeça leve")
        assert len(flags) == 0


# ──────────────────────────────────────────────────────────────
# TESTES: SemanticAnalyzer
# ──────────────────────────────────────────────────────────────


class TestSemanticAnalyzer:
    """Testa análise semântica."""

    def setup_method(self):
        self.analyzer = SemanticAnalyzer()

    def test_extract_age_group_numeric(self):
        """Testa extração de faixa etária por número."""
        assert self.analyzer.extract_age_group("criança de 8 anos") == "pediatria"
        assert self.analyzer.extract_age_group("paciente 45 anos") == "adulto"
        assert self.analyzer.extract_age_group("idosa de 70 anos") == "idoso"

    def test_extract_age_group_keywords(self):
        """Testa extração de faixa etária por palavras-chave."""
        assert self.analyzer.extract_age_group("meu bebê está com febre") == "pediatria"
        assert self.analyzer.extract_age_group("idoso com dor") == "idoso"
        assert self.analyzer.extract_age_group("dor de cabeça") == "adulto"  # default

    def test_extract_pregnancy_status(self):
        """Testa detecção de gravidez."""
        assert self.analyzer.extract_pregnancy_status("gestante com dor abdominal") is True
        assert self.analyzer.extract_pregnancy_status("grávida 28 semanas") is True
        assert self.analyzer.extract_pregnancy_status("mulher com dor de cabeça") is False

    def test_extract_obstetric_info(self):
        """Testa extração de idade gestacional."""
        assert self.analyzer.extract_obstetric_info("gestante 20 semanas") == 20
        assert self.analyzer.extract_obstetric_info("no quinto mês de gravidez") == 20  # ~5 meses
        assert self.analyzer.extract_obstetric_info("sem nenhuma informação") is None

    def test_extract_comorbidities(self):
        """Testa extração de comorbidades."""
        text = "sou diabético e hipertenso"
        comorbidities = self.analyzer.extract_comorbidities(text)
        assert "diabetes" in comorbidities
        assert "hipertensão" in comorbidities

    def test_extract_medications(self):
        """Testa extração de medicações."""
        text = "tomo dipirona todo dia e metformina"
        meds = self.analyzer.extract_medications(text)
        assert "dipirona" in meds
        assert "metformina" in meds

    def test_extract_onset(self):
        """Testa classificação do onset."""
        assert self.analyzer.extract_onset("começou hoje") == "agudo"
        assert self.analyzer.extract_onset("há 3 dias") == "subagudo"
        assert self.analyzer.extract_onset("tenho isso há anos") == "crônico"


class TestVitalSignsExtractor:
    """Testa extração de sinais vitais."""

    def setup_method(self):
        self.extractor = VitalSignsExtractor()

    def test_extract_temperature(self):
        """Testa extração de temperatura."""
        vitals = self.extractor.extract("temperatura 37.5")
        assert vitals.temperatura == 37.5

        vitals = self.extractor.extract("febre 39 graus")
        assert vitals.temperatura == 39.0

    def test_extract_heart_rate(self):
        """Testa extração de frequência cardíaca."""
        vitals = self.extractor.extract("FC 80 bpm")
        assert vitals.frequencia_cardiaca == 80

        vitals = self.extractor.extract("pulso de 95")
        assert vitals.frequencia_cardiaca == 95

    def test_extract_blood_pressure(self):
        """Testa extração de pressão arterial."""
        vitals = self.extractor.extract("PA 140/90")
        assert vitals.pressao_arterial == "140/90"

    def test_extract_oxygen_saturation(self):
        """Testa extração de saturação de oxigênio."""
        vitals = self.extractor.extract("SpO2 95%")
        assert vitals.saturacao_oxigenio == 95


# ──────────────────────────────────────────────────────────────
# TESTES: CID10Mapper
# ──────────────────────────────────────────────────────────────


class TestCID10Mapper:
    """Testa mapeamento para CID-10."""

    def setup_method(self):
        self.mapper = CID10Mapper()

    def test_map_single_symptom(self):
        """Testa mapeamento de um sintoma."""
        result = self.mapper.map_symptoms(["dor de cabeça"])
        assert len(result) > 0
        assert result[0].cid == "R51"

    def test_map_multiple_symptoms(self):
        """Testa mapeamento de múltiplos sintomas."""
        result = self.mapper.map_symptoms(["dor de cabeça", "febre"])
        assert len(result) >= 2
        cids = [r.cid for r in result]
        assert "R51" in cids
        assert "R50.9" in cids

    def test_get_symptom_variants(self):
        """Testa recuperação de variantes de um sintoma."""
        variants = self.mapper.get_symptom_variants("dor de cabeça")
        assert "cefaleia" in variants
        assert "enxaqueca" in variants


# ──────────────────────────────────────────────────────────────
# TESTES: NormalizacaoSemantica (Orquestrador)
# ──────────────────────────────────────────────────────────────


class TestNormalizacaoSemantica:
    """Testa orquestração completa de normalização."""

    def setup_method(self):
        self.normalizador = NormalizacaoSemantica()

    def test_processar_simple_case(self):
        """Testa processamento de caso simples."""
        entrada = "dor de cabeça há 2 dias"
        result = self.normalizador.processar(entrada)

        assert result.sintomas_originais == entrada
        assert "dor de cabeça" in result.sintomas_normalizados
        assert result.duracao == "2 dias"
        assert result.idade_grupo == "adulto"

    def test_processar_with_demographics(self):
        """Testa processamento com dados demográficos."""
        entrada = "criança de 5 anos com febre 39 graus"
        result = self.normalizador.processar(entrada)

        assert result.idade_grupo == "pediatria"
        assert "febre" in result.sintomas_normalizados
        assert result.sinais_vitais.temperatura == 39.0

    def test_processar_with_red_flags(self):
        """Testa processamento com red flags."""
        entrada = "não consigo respirar e tenho dor no peito"
        result = self.normalizador.processar(entrada)

        assert len(result.red_flags) > 0

    def test_processar_pregnant_patient(self):
        """Testa processamento de gestante."""
        entrada = "gestante 28 semanas com dor abdominal"
        result = self.normalizador.processar(entrada)

        assert result.gestante is True
        assert result.idade_gestacional_semanas == 28
        assert "dor abdominal" in result.sintomas_normalizados

    def test_processar_with_comorbidities(self):
        """Testa processamento com comorbidades."""
        entrada = "diabético com febre persistente"
        result = self.normalizador.processar(entrada)

        assert "diabetes" in result.comorbidades
        assert "febre" in result.sintomas_normalizados

    def test_processar_confidence_calculation(self):
        """Testa cálculo de confiança."""
        # Caso com muitos dados: alta confiança
        entrada_boa = "dor de cabeça eva 7 há 2 dias, temp 38.5, PA 120/80"
        result_boa = self.normalizador.processar(entrada_boa)
        assert result_boa.confianca_normalizacao >= 0.7

        # Caso com poucos dados: baixa confiança
        entrada_ruim = "xxx yyy zzz"
        result_ruim = self.normalizador.processar(entrada_ruim)
        assert result_ruim.confianca_normalizacao <= 0.5

    def test_processar_cid10_mapping(self):
        """Testa mapeamento para CID-10."""
        entrada = "dor de cabeça e tosse"
        result = self.normalizador.processar(entrada)

        assert len(result.cid10_suspeitas) > 0
        cids = [c.cid for c in result.cid10_suspeitas]
        assert "R51" in cids  # CID para dor de cabeça

    def test_gerar_prompt_enriquecido(self):
        """Testa geração de prompt enriquecido."""
        entrada = "dor de cabeça eva 8"
        normalized = self.normalizador.processar(entrada)
        prompt = self.normalizador.gerar_prompt_enriquecido(normalized)

        # Verificar que o prompt contém as seções esperadas
        assert "ENTRADA NORMALIZADA" in prompt
        assert "SINTOMAS (FORMA CANÔNICA)" in prompt
        assert "DADOS CLÍNICOS" in prompt


# ──────────────────────────────────────────────────────────────
# TESTES DE INTEGRAÇÃO
# ──────────────────────────────────────────────────────────────


class TestIntegration:
    """Testes de integração entre componentes."""

    def test_full_pipeline_complex_case(self):
        """Testa pipeline completo com caso complexo."""
        entrada = """
        Criança de 8 anos, diabética, com vômito persistente
        há 2 dias, febre 39.5°C, não consegue comer nada.
        A mãe relata que a criança está irritada e confusa.
        PA 110/70, FC 120.
        """

        normalizador = NormalizacaoSemantica()
        result = normalizador.processar(entrada)

        # Verificações
        assert result.idade_grupo == "pediatria"
        assert "diabetes" in result.comorbidades
        assert "vômito" in result.sintomas_normalizados
        assert "febre" in result.sintomas_normalizados
        assert "confusão mental" in result.sintomas_normalizados
        assert result.sinais_vitais.temperatura == 39.5
        assert result.sinais_vitais.frequencia_cardiaca == 120
        assert len(result.red_flags) > 0  # Criança confusa é red flag
        assert result.confianca_normalizacao > 0.7
