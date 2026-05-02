"""Models package - Pydantic schemas organized by domain."""

# Re-export all models for ease of imports
from app.models.request import SymptomsRequest
from app.models.discriminador import DiscriminadorGeral
from app.models.sintoma import (
    SintomaProcessado,
    SintomaNormalizado,
    SintomaNaoNormalizado,
)
from app.models.normalizacao import NormalizacaoResultado, NormalizacaoOllama
from app.models.triage_response import TriageResponse

__all__ = [
    # Request
    "SymptomsRequest",
    # Discriminators
    "DiscriminadorGeral",
    # Symptoms
    "SintomaProcessado",
    "SintomaNormalizado",
    "SintomaNaoNormalizado",
    # Normalization
    "NormalizacaoResultado",
    "NormalizacaoOllama",
    # Response
    "TriageResponse",
]
