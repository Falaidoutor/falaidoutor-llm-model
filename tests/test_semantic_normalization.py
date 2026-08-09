from app.service.llm_normalization import extract_llm_normalizations
from app.service.ner_service import NERService
from app.service.normalization import NormalizationService


def test_lightweight_ner_splits_and_cleans_symptoms():
    service = NERService()

    assert service.extract_symptoms("Tenho dor de cabeça e falta de ar, febre") == [
        "dor de cabeça",
        "falta de ar",
        "febre",
    ]


def test_llm_candidates_are_limited_to_unresolved_symptoms():
    normalization = {
        "sintomas_nao_normalizados": [{"original": "caganeira"}],
    }
    parsed = {
        "normalizacao_llm": [
            {
                "original": "caganeira",
                "normalizado": "diarreia",
                "confianca": "alta",
            },
            {
                "original": "dor no peito",
                "normalizado": "dor torácica",
                "confianca": "alta",
            },
        ]
    }

    assert extract_llm_normalizations(parsed, normalization) == [
        {
            "original": "caganeira",
            "normalizado": "diarreia",
            "confianca": "alta",
        }
    ]


def test_qdrant_canonical_payload_avoids_postgres_lookup():
    class EmbeddingStub:
        def embed(self, text):
            return text

    class QdrantStub:
        def search(self, vector, top_k, score_threshold):
            return [
                {
                    "score": 0.99,
                    "payload": {
                        "sintoma_id": 7,
                        "sinonimo_id": 11,
                        "termo": "dor de cabeça",
                        "termo_canonico": "cefaleia",
                    },
                }
            ]

    service = object.__new__(NormalizationService)
    service.embedding_service = EmbeddingStub()
    service.qdrant_service = QdrantStub()
    service._postgres_service = None

    result = service._normalize_single_symptom("dor de cabeça")

    assert result["normalizado"] == "cefaleia"
    assert service._postgres_service is None
