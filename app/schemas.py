from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SymptomsRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    symptoms: str = Field(..., min_length=1, description="Sintomas do paciente")
    triage_id: str | int | None = Field(
        default=None, alias="triageId", description="Identificador da triagem no backend"
    )
    patient_context: dict[str, Any] | None = Field(default=None, alias="patientContext")


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
    summary: str | None = None
    suggestedRiskClassification: str | None = None
    suggestedRiskColor: str | None = None
    reasoning: str | None = None
    recommendedAction: str | None = None
    rawModelOutput: dict[str, Any] | None = None
    confidence: float | None = Field(
        default=None, description="Confiança numérica normalizada de 0 a 100"
    )
    confidenceScore: float | None = Field(
        default=None, description="Alias numérico de confidence, de 0 a 100"
    )
    confidenceLabel: str | None = Field(
        default=None, description="Rótulo original de confiança: alta|media|baixa"
    )
    triageId: str | int | None = None
