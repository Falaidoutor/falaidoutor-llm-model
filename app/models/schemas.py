from typing import Optional

from pydantic import BaseModel, Field


class SymptomsRequest(BaseModel):
    symptoms: str = Field(..., min_length=1, description="Sintomas do paciente")


class DiscriminadorGeral(BaseModel):
    discriminador: str
    presente: bool


class TriageResponse(BaseModel):
    classificacao: str = Field(
        ..., description="Vermelho|Laranja|Amarelo|Verde|Azul"
    )
    prioridade: str = Field(
        ...,
        description="Emergência|Muito urgente|Urgente|Pouco urgente|Não urgente",
    )
    tempo_atendimento_minutos: int = Field(
        ..., description="0|10|60|120|240"
    )
    fluxograma_utilizado: str
    discriminadores_gerais_avaliados: list[DiscriminadorGeral]
    discriminadores_especificos_ativados: list[str]
    populacao_especial: str | None = None
    over_triage_aplicado: bool
    confianca: str = Field(..., description="alta|media|baixa")
    justificativa: str
    alertas: list[str] = Field(default_factory=list)
    disclaimer: str = Field(
        default="Classificação de apoio à decisão. A avaliação final é responsabilidade do profissional de saúde."
    )
    validation_errors: list[str] = Field(
        default_factory=list,
        description="Erros de validação encontrados na resposta do modelo.",
    )
    validation_warnings: list[str] = Field(
        default_factory=list,
        description="Avisos de validação (não bloqueantes) encontrados na resposta do modelo.",
    )


# ────────────────────────────────────────────────────────────
# SCHEMAS PARA NORMALIZAÇÃO SEMÂNTICA
# ────────────────────────────────────────────────────────────


class CID10Info(BaseModel):
    """Informação de um código CID-10."""

    cid: str = Field(..., description="Código CID-10 (ex: R51)")
    descricao: str = Field(..., description="Descrição do CID-10")
    sintoma_detectado: str = Field(..., description="Sintoma que levou ao CID")
    confianca: float = Field(default=0.8, description="Confiança do mapeamento (0-1)")


class VitalSignsResponse(BaseModel):
    """Sinais vitais extraídos do texto."""

    temperatura: Optional[float] = Field(
        None, description="Temperatura em °C"
    )
    frequencia_cardiaca: Optional[int] = Field(
        None, description="Frequência cardíaca em bpm"
    )
    frequencia_respiratoria: Optional[int] = Field(
        None, description="Frequência respiratória em irpm"
    )
    pressao_arterial: Optional[str] = Field(
        None, description="Pressão arterial (ex: 120/80)"
    )
    saturacao_oxigenio: Optional[int] = Field(
        None, description="Saturação de oxigênio em %"
    )


class NormalizedInputResponse(BaseModel):
    """Entrada do usuário completamente normalizada."""

    # Dados originais
    sintomas_originais: str = Field(..., description="Texto original do usuário")

    # Sintomas processados
    sintomas_normalizados: list[str] = Field(
        default_factory=list,
        description="Sintomas em forma canônica"
    )
    red_flags: list[dict] = Field(
        default_factory=list,
        description="Red flags de urgência detectadas"
    )
    severidade: Optional[str] = Field(
        None,
        description="Severidade detectada: leve, moderada, intensa"
    )
    duracao: Optional[str] = Field(
        None,
        description="Duração dos sintomas (ex: 3 dias)"
    )
    onset: Optional[str] = Field(
        None,
        description="Tipo de onset: agudo, subagudo, crônico"
    )

    # Dados demográficos
    idade_grupo: Optional[str] = Field(
        None,
        description="Faixa etária: pediatria, adulto, idoso"
    )
    gestante: bool = Field(
        default=False,
        description="Se a paciente é gestante"
    )
    idade_gestacional_semanas: Optional[int] = Field(
        None,
        description="Idade gestacional em semanas"
    )

    # Dados clínicos
    sinais_vitais: VitalSignsResponse = Field(
        default_factory=VitalSignsResponse,
        description="Sinais vitais extraídos"
    )
    comorbidades: list[str] = Field(
        default_factory=list,
        description="Doenças/condições mencionadas"
    )
    medicacoes: list[str] = Field(
        default_factory=list,
        description="Medicações em uso mencionadas"
    )

    # Mapeamentos
    cid10_suspeitas: list[CID10Info] = Field(
        default_factory=list,
        description="Códigos CID-10 mapeados dos sintomas"
    )

    # Qualidade
    confianca_normalizacao: float = Field(
        default=1.0,
        description="Confiança geral da normalização (0-1)"
    )
    alertas: list[str] = Field(
        default_factory=list,
        description="Alertas sobre dados faltantes ou ambiguidades"
    )


class EnrichedTriageResponse(TriageResponse):
    """Resposta de triagem enriquecida com dados de normalização."""

    normalizacao_entrada: NormalizedInputResponse = Field(
        ...,
        description="Dados de normalização da entrada do usuário"
    )
