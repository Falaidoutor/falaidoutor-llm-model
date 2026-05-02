"""Normalization result models."""

from pydantic import BaseModel, Field
from typing import Optional

from app.models.sintoma import SintomaNormalizado, SintomaNaoNormalizado


class NormalizacaoResultado(BaseModel):
    """Result of semantic normalization pipeline."""

    sintomas_normalizados: list[SintomaNormalizado] = Field(
        default_factory=list, description="Sintomas que foram normalizados"
    )
    sintomas_nao_normalizados: list[SintomaNaoNormalizado] = Field(
        default_factory=list, description="Sintomas que NÃO foram normalizados"
    )
    total_extraidos: int = Field(..., description="Total de sintomas extraídos")
    taxa_normalizacao: float = Field(
        ..., description="Percentual de sintomas normalizados (0.0-1.0)"
    )
    debug: Optional[dict] = Field(
        None, description="Metadata de debug (timing, threshold, etc)"
    )


class NormalizacaoOllama(BaseModel):
    """Normalization performed by Ollama for non-normalized symptoms."""

    original: str = Field(..., description="Sintoma original não normalizado")
    normalizado: str = Field(..., description="Normalização sugerida pelo Ollama")
    confianca: str = Field(
        default="media",
        description="Confiança da normalização: alta|media|baixa",
    )
