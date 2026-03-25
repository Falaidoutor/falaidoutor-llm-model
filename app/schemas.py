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
