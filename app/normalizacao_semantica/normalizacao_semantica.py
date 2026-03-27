"""Orquestrador de normalização semântica.

Integra todas as classes de normalização e análise para processar
entrada do usuário de forma completa e estruturada.
"""

from dataclasses import dataclass, field
from typing import Optional

from .cid10_mapper import CID10Mapper, CID10Info
from .symptom_normalizer import SymptomNormalizer
from .semantic_analyzer import SemanticAnalyzer, VitalSigns
from .print_normalizacao import PrintNormalizacao


@dataclass
class NormalizedInput:
    """Entrada totalmente normalizada e estruturada."""

    # Dados originais
    sintomas_originais: str

    # Sintomas processados
    sintomas_normalizados: list[str] = field(default_factory=list)
    red_flags: list[dict] = field(default_factory=list)
    severidade: Optional[str] = None
    duracao: Optional[str] = None
    onset: Optional[str] = None

    # Dados demográficos extraídos
    idade_grupo: Optional[str] = None  # "pediatria", "adulto", "idoso"
    gestante: bool = False
    idade_gestacional_semanas: Optional[int] = None

    # Dados clínicos
    sinais_vitais: VitalSigns = field(default_factory=VitalSigns)
    comorbidades: list[str] = field(default_factory=list)
    medicacoes: list[str] = field(default_factory=list)

    # Mapeamentos
    cid10_suspeitas: list[CID10Info] = field(default_factory=list)

    # Qualidade da entrada
    confianca_normalizacao: float = 1.0  # 0-1
    alertas: list[str] = field(default_factory=list)  # Campos faltantes, ambiguidades, etc

    def print_resumo(self) -> None:
        """Imprime um resumo visual formatado da normalização."""
        PrintNormalizacao.imprimir_resumo(self)

    def print_comparacao(self) -> None:
        """Imprime uma comparação antes/depois da normalização."""
        PrintNormalizacao.imprimir_comparacao(self.sintomas_originais, self)

    def to_dict(self) -> dict:
        """Converte para dicionário para serialização."""
        return {
            "sintomas_originais": self.sintomas_originais,
            "sintomas_normalizados": self.sintomas_normalizados,
            "red_flags": self.red_flags,
            "severidade": self.severidade,
            "duracao": self.duracao,
            "onset": self.onset,
            "idade_grupo": self.idade_grupo,
            "gestante": self.gestante,
            "idade_gestacional_semanas": self.idade_gestacional_semanas,
            "sinais_vitais": {
                "temperatura": self.sinais_vitais.temperatura,
                "frequencia_cardiaca": self.sinais_vitais.frequencia_cardiaca,
                "frequencia_respiratoria": self.sinais_vitais.frequencia_respiratoria,
                "pressao_arterial": self.sinais_vitais.pressao_arterial,
                "saturacao_oxigenio": self.sinais_vitais.saturacao_oxigenio,
            },
            "comorbidades": self.comorbidades,
            "medicacoes": self.medicacoes,
            "cid10_suspeitas": [
                {
                    "cid": cid.cid,
                    "descricao": cid.descricao,
                    "sintoma_detectado": cid.sintoma_detectado,
                    "confianca": cid.confianca,
                }
                for cid in self.cid10_suspeitas
            ],
            "confianca_normalizacao": self.confianca_normalizacao,
            "alertas": self.alertas,
        }


class NormalizacaoSemantica:
    """Classe central que orquestra normalização semântica completa."""

    def __init__(self):
        self.symptom_normalizer = SymptomNormalizer()
        self.semantic_analyzer = SemanticAnalyzer()
        self.cid10_mapper = CID10Mapper()

    def processar(self, texto_entrada: str) -> NormalizedInput:
        """Pipeline completo de normalização.

        Passos:
        1. Normalizar texto e extrair sintomas
        2. Detectar red flags
        3. Extrair dados demográficos
        4. Extrair dados clínicos (sinais vitais, comorbidades, etc)
        5. Mapear para CID-10
        6. Calcular confiança geral

        Args:
            texto_entrada: Texto livre do usuário

        Returns:
            NormalizedInput completamente processado
        """

        # Inicializar resultado
        result = NormalizedInput(sintomas_originais=texto_entrada)

        # NORMALIZAR SINTOMAS

        result.sintomas_normalizados = self.symptom_normalizer.normalize_symptoms(
            texto_entrada
        )

        if not result.sintomas_normalizados:
            result.alertas.append(
                "Nenhum sintoma reconhecido. Verifique a redação ou use termos clínicos."
            )
            result.confianca_normalizacao = 0.3


        #  DETECTAR RED FLAGS
        result.red_flags = self.symptom_normalizer.detect_red_flags(texto_entrada)


        #EXTRAIR SEVERIDADE E DURAÇÃO
        result.severidade = self.symptom_normalizer.extract_intensity_indicators(
            texto_entrada
        )
        result.duracao = self.symptom_normalizer.extract_duration(texto_entrada)
        result.onset = self.semantic_analyzer.extract_onset(texto_entrada)

        # EXTRAIR DADOS DEMOGRÁFICOS
        result.idade_grupo = self.semantic_analyzer.extract_age_group(texto_entrada)

        result.gestante = self.semantic_analyzer.extract_pregnancy_status(
            texto_entrada
        )
        if result.gestante:
            ig = self.semantic_analyzer.extract_obstetric_info(texto_entrada)
            result.idade_gestacional_semanas = ig

        # EXTRAIR DADOS CLÍNICOS
        result.sinais_vitais = self.semantic_analyzer.extract_vital_signs(
            texto_entrada
        )
        result.comorbidades = self.semantic_analyzer.extract_comorbidities(
            texto_entrada
        )
        result.medicacoes = self.semantic_analyzer.extract_medications(texto_entrada)

        # Alertas se dados clínicos importantes faltam
        if not result.sinais_vitais.temperatura and result.idade_grupo == "pediatria":
            result.alertas.append("Temperatura não informada. Importante para triagem pediátrica.")

        # MAPEAR PARA CID-10

        result.cid10_suspeitas = self.cid10_mapper.map_symptoms(
            result.sintomas_normalizados
        )

        # CALCULAR CONFIANÇA GERAL
        result.confianca_normalizacao = self._calcular_confianca(result)

        return result

    def _calcular_confianca(self, result: NormalizedInput) -> float:
        """Calcula confiança da normalização (0-1).

        Fatores:
        - Sintomas foram encontrados
        - Sinais vitais foram informados
        - Duração foi informada
        - Red flags detectadas (reduz confiança pois esperamos intervenção)
        """
        confianca = 1.0

        # Sintomas não reconhecidos: -0.3
        if not result.sintomas_normalizados:
            confianca -= 0.3

        # Falta duração: -0.1
        if not result.duracao:
            confianca -= 0.1

        # Falta sinais vitais: -0.2
        if not result.sinais_vitais.temperatura and result.sinais_vitais.frequencia_cardiaca is None:
            confianca -= 0.2

        # Red flags presentes: -0.1 (pois há ambiguidade que precisa validação)
        if result.red_flags:
            confianca -= 0.1

        # Limitar entre 0.1 e 1.0
        return max(0.1, min(1.0, confianca))

    def gerar_prompt_enriquecido(self, normalized: NormalizedInput) -> str:
        """Gera um prompt enriquecido com dados estruturados para o modelo.

        Usa as informações normalizadas para melhorar o contexto
        do modelo Ollama.
        """
        linhas = []

        # Header
        linhas.append("=" * 70)
        linhas.append("ENTRADA NORMALIZADA E ESTRUTURADA")
        linhas.append("=" * 70)

        # Sintomas originais
        linhas.append("\nENTRADA ORIGINAL:")
        linhas.append(f"   {normalized.sintomas_originais}")

        # Sintomas normalizados
        linhas.append("\nSINTOMAS (FORMA CANÔNICA):")
        if normalized.sintomas_normalizados:
            for sintoma in normalized.sintomas_normalizados:
                linhas.append(f"   • {sintoma}")
        else:
            linhas.append("   (Nenhum sintoma reconhecido)")

        # Red flags
        if normalized.red_flags:
            linhas.append("\nRED FLAGS DETECTADAS:")
            for flag in normalized.red_flags:
                linhas.append(f"   • {flag['flag']} [{flag['color']}]")

        # Dados clínicos estruturados
        linhas.append("\n🔹 DADOS CLÍNICOS ESTRUTURADOS:")
        linhas.append(f"   Severidade: {normalized.severidade or 'não informada'}")
        linhas.append(f"   Duração: {normalized.duracao or 'não informada'}")
        linhas.append(f"   Onset: {normalized.onset or 'não informado'}")

        # Dados demográficos
        linhas.append("\n🔹 DADOS DEMOGRÁFICOS:")
        linhas.append(f"   Faixa etária: {normalized.idade_grupo or 'não detectada (assume adulto)'}")
        if normalized.gestante:
            ig = normalized.idade_gestacional_semanas
            linhas.append(f"   Gestante: SIM (IG: {ig} semanas)" if ig else "   Gestante: SIM (IG não especificada)")

        # Sinais vitais
        if any([
            normalized.sinais_vitais.temperatura,
            normalized.sinais_vitais.frequencia_cardiaca,
            normalized.sinais_vitais.frequencia_respiratoria,
            normalized.sinais_vitais.pressao_arterial,
            normalized.sinais_vitais.saturacao_oxigenio,
        ]):
            linhas.append("\nSINAIS VITAIS:")
            if normalized.sinais_vitais.temperatura:
                linhas.append(f"   Temperatura: {normalized.sinais_vitais.temperatura}°C")
            if normalized.sinais_vitais.frequencia_cardiaca:
                linhas.append(f"   FC: {normalized.sinais_vitais.frequencia_cardiaca} bpm")
            if normalized.sinais_vitais.frequencia_respiratoria:
                linhas.append(f"   FR: {normalized.sinais_vitais.frequencia_respiratoria} irpm")
            if normalized.sinais_vitais.pressao_arterial:
                linhas.append(f"   PA: {normalized.sinais_vitais.pressao_arterial} mmHg")
            if normalized.sinais_vitais.saturacao_oxigenio:
                linhas.append(f"   SpO2: {normalized.sinais_vitais.saturacao_oxigenio}%")

        # Comorbidades
        if normalized.comorbidades:
            linhas.append("\n🔹 COMORBIDADES:")
            for com in normalized.comorbidades:
                linhas.append(f"   • {com}")

        # Medicações
        if normalized.medicacoes:
            linhas.append("\nMEDICAÇÕES EM USO:")
            for med in normalized.medicacoes:
                linhas.append(f"   • {med}")

        # CID-10
        if normalized.cid10_suspeitas:
            linhas.append("\nCÓDIGOS CID-10 (SUSPEITOS):")
            for cid in normalized.cid10_suspeitas:
                linhas.append(f"   • {cid.cid}: {cid.descricao} (confiança: {cid.confianca:.0%})")

        # Alertas
        if normalized.alertas:
            linhas.append("\nALERTAS (DADOS FALTANTES):")
            for alerta in normalized.alertas:
                linhas.append(f"   • {alerta}")

        # Confiança
        linhas.append(f"\nCONFIANÇA GERAL: {normalized.confianca_normalizacao:.0%}")

        linhas.append("\n" + "=" * 70)

        return "\n".join(linhas)
