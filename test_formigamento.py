"""
Script para testar um sintoma específico com o novo threshold.
"""

from app.service.normalization import NormalizationService
from app.service.embedding import EmbeddingService
from app.service.qdrant_service import QdrantService
from app.config.settings import SIMILARITY_THRESHOLD

import logging
logging.basicConfig(level=logging.INFO)

print(f"\n{'='*80}")
print(f"THRESHOLD ATUAL: {SIMILARITY_THRESHOLD}")
print(f"{'='*80}\n")

# Teste 1: Buscar similaridade para "formigamento"
embedding_svc = EmbeddingService()
qdrant_svc = QdrantService()

sintoma = "formigamento"
embedding = embedding_svc.embed(sintoma)

print(f"Buscando para: '{sintoma}'")
results = qdrant_svc.search(embedding, top_k=10, score_threshold=None)

print(f"\nTop 10 resultados:")
for i, result in enumerate(results, 1):
    payload = result['payload']
    score = result['score']
    status = "✓ PASS" if score >= SIMILARITY_THRESHOLD else "✗ FAIL"
    print(f"{i}. {status} | Score: {score:.4f} | Termo: '{payload.get('termo')}' | sintoma_id: {payload.get('sintoma_id')}")

# Teste 2: Normalização completa
print(f"\n{'='*80}")
print("NORMALIZAÇÃO COMPLETA")
print(f"{'='*80}\n")

normalization_svc = NormalizationService()
resultado = normalization_svc.normalize_symptoms(f"estou com {sintoma}")

print(f"Sintomas normalizados:")
for s in resultado['sintomas_normalizados']:
    print(f"  ✓ '{s['original']}' → '{s['normalizado']}' (score: {s['score']:.4f})")

print(f"\nSintomas não normalizados:")
for s in resultado['sintomas_nao_normalizados']:
    print(f"  ✗ '{s['original']}' (motivo: {s['motivo']}, score: {s['score']:.4f})")

if not resultado['sintomas_normalizados'] and not resultado['sintomas_nao_normalizados']:
    print("  (nenhum sintoma extraído)")
