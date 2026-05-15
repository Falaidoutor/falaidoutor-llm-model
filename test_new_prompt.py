#!/usr/bin/env python
"""
Script de teste para verificar o novo formato do prompt
"""

import json
from app.prompt.prompt import build_user_prompt

# Simular dados como viriam da normalização
sintomas_normalizados = [
    {"original": "dor de cocoroco forte", "normalizado": "cefaleia"},
    {"original": "caganeira", "normalizado": "diarreia"},
]

sintomas_nao_normalizados = [
    "tontura",
    "náusea",
]

input_original = "estou com dor de cocoroco forte, caganeira, tontura e náusea"

# Chamar a função
prompt = build_user_prompt(
    sintomas_normalizados,
    sintomas_nao_normalizados,
    input_original=input_original,
    debug_mode=False
)

print("=" * 80)
print("NOVO FORMATO DO PROMPT:")
print("=" * 80)
print(prompt)
print("\n" + "=" * 80)

# Extrair a parte JSON para validar
lines = prompt.split("\n")
json_part = "\n".join(lines[:2])  # Pega as primeiras 2 linhas que contêm o JSON

print("\nPARTE JSON EXTRAÍDA (primeiras linhas):")
print(json_part)
