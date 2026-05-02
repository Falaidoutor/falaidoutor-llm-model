"""Symptom models from semantic normalization pipeline."""

from pydantic import BaseModel, Field
from typing import Optional


class SintomaProcessado(BaseModel):
    """Base model for processed symptom."""

    original: str = Field(..., description="Termo original extraído pelo NER")
    score: float = Field(..., description="Score de similaridade Qdrant (0.0-1.0)")


class SintomaNormalizado(SintomaProcessado):
    """Symptom that was successfully normalized (score >= threshold)."""

    normalizado: str = Field(..., description="Termo normalizado encontrado")
    sintoma_id: int = Field(..., description="ID do sintoma no PostgreSQL")
    sinonimo_id: Optional[int] = Field(
        None, description="ID do sinonimo Qdrant (se aplicável)"
    )
    tipo: str = Field(default="normalizado", description="Sempre 'normalizado'")


class SintomaNaoNormalizado(SintomaProcessado):
    """Symptom that was NOT normalized (score < threshold)."""

    tipo: str = Field(default="nao_normalizado", description="Sempre 'nao_normalizado'")
    motivo: str = Field(
        default="",
        description="Motivo: 'score_baixo', 'nenhum_resultado_qdrant', etc",
    )
