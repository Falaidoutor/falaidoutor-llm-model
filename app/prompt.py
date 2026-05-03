"""
Prompt de triagem ativo.

Protocolo atual: ESI (Emergency Severity Index) v4
Protocolo anterior: Manchester (MTS) — disponível em prompt_manchester.py
"""

from app.prompt_esi import SYSTEM_PROMPT, build_user_prompt

__all__ = ["SYSTEM_PROMPT", "build_user_prompt"]
