"""
Script de debug: testar normalização de um sintoma específico
"""

import logging
from app.service.normalization import NormalizationService
from app.service.embedding import EmbeddingService
from app.service.qdrant_service import QdrantService
from app.config.settings import SIMILARITY_THRESHOLD

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Teste 1: Verificar dados no Qdrant
print("\n" + "="*100)
print("TEST 1: Verificando dados no Qdrant")
print("="*100)

qdrant_svc = QdrantService()
client = qdrant_svc.client
from app.config.settings import QDRANT_COLLECTION_NAME

collection_info = client.get_collection(QDRANT_COLLECTION_NAME)
print(f"\nTotal de pontos no Qdrant: {collection_info.points_count}")

all_points = client.scroll(collection_name=QDRANT_COLLECTION_NAME, limit=1000)
pontos, _ = all_points

print(f"\nMapeamento de todos os termos no Qdrant:")
for point in sorted(pontos, key=lambda p: p.payload.get('termo', '')):
    payload = point.payload
    termo = payload.get('termo')
    tipo = payload.get('tipo')
    sintoma_id = payload.get('sintoma_id')
    print(f"  ID:{point.id:6d} | {termo:25s} | tipo: {tipo:18s} | sintoma_id: {sintoma_id}")

# Teste 2: Verificar embedding de "sensação de queda"
print("\n" + "="*100)
print("TEST 2: Testando 'sensação de queda'")
print("="*100)

embedding_svc = EmbeddingService()
sintoma = "sensação de queda"

embedding = embedding_svc.embed(sintoma)
print(f"\nBuscando similaridade para: '{sintoma}'")
print(f"Threshold configurado: {SIMILARITY_THRESHOLD}")

# Buscar top 5 resultados
results = qdrant_svc.search(embedding, top_k=10, score_threshold=None)

print(f"\nTop 10 resultados:")
for i, result in enumerate(results, 1):
    payload = result['payload']
    score = result['score']
    print(f"{i}. Score: {score:.4f} | Termo: '{payload.get('termo')}' | Tipo: {payload.get('tipo')} | sintoma_id: {payload.get('sintoma_id')}")

# Teste 3: Normalização completa
print("\n" + "="*100)
print("TEST 3: Pipeline de Normalização Completo")
print("="*100)

normalization_svc = NormalizationService()
resultado = normalization_svc.normalize_symptoms("estou com dor no cocoroco e sensação de queda")

print(f"\nSintomas normalizados:")
for s in resultado['sintomas_normalizados']:
    print(f"  - '{s['original']}' → '{s['normalizado']}' (score: {s['score']:.4f}, id: {s['sintoma_id']})")

print(f"\nSintomas não normalizados:")
for s in resultado['sintomas_nao_normalizados']:
    print(f"  - '{s['original']}' (motivo: {s['motivo']}, score: {s['score']:.4f})")
