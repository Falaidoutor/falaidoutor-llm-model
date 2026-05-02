"""Request models."""

from pydantic import BaseModel, Field


class SymptomsRequest(BaseModel):
    symptoms: str = Field(..., min_length=1, description="Sintomas do paciente")
    debug_mode: bool = Field(
        default=False, description="Ativa modo debug com metadata adicional"
    )
