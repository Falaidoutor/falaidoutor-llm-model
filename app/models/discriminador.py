"""Discriminator models for MTS protocol."""

from pydantic import BaseModel


class DiscriminadorGeral(BaseModel):
    discriminador: str
    presente: bool
