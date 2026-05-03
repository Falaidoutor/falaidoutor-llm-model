from pydantic import BaseModel, Field


class SymptomsRequest(BaseModel):
    symptoms: str = Field(..., min_length=1, description="Sintomas do paciente")


class TriageResponse(BaseModel):
    classificacao: str = Field(
        ..., description="ESI-1|ESI-2|ESI-3|ESI-4|ESI-5"
    )
    nivel: int = Field(
        ..., description="1|2|3|4|5"
    )
    nome_nivel: str = Field(
        ...,
        description="Ressuscitação|Emergente|Urgente|Menos urgente|Não urgente",
    )
    ponto_decisao_ativado: str = Field(
        ..., description="A|B|C|D"
    )
    criterios_ponto_decisao: list[str] = Field(default_factory=list)
    recursos_estimados: int = Field(
        ..., description="Número de recursos estimados"
    )
    recursos_detalhados: list[str] = Field(default_factory=list)
    sinais_vitais_zona_perigo: bool = False
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
