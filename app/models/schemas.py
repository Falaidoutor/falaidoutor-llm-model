"""
Schemas module - re-exports all models for backward compatibility.

Use specific imports for better organization:
  from app.models.request import SymptomsRequest
  from app.models.triage_response import TriageResponse
  from app.models.normalizacao import NormalizacaoResultado
  from app.models.sintoma import SintomaNormalizado, SintomaNaoNormalizado
"""

# Re-export all models from individual modules
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
    "SymptomsRequest",
    "DiscriminadorGeral",
    "SintomaProcessado",
    "SintomaNormalizado",
    "SintomaNaoNormalizado",
    "NormalizacaoResultado",
    "NormalizacaoOllama",
    "TriageResponse",
]

