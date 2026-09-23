import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.service import normalization as normalization_module
from app.service import postgres_service
from app.service.normalization import NormalizationService
from app.service.normalization_pipeline import normalize_safely, complete_normalization


def make_service(matches, postgres):
    service = object.__new__(NormalizationService)
    service.ner_service = normalization_module.NERService()
    service.embedding_service = Mock()
    service.qdrant_service = Mock()
    service.qdrant_service.search.side_effect = matches
    service._postgres_service = postgres
    return service


@pytest.mark.parametrize("provider", ["groq", "ollama"])
def test_full_flow_from_ner_to_candidate(monkeypatch, provider):
    from app import groq_service, ollama_service

    repository = Mock()
    repository.get_sintoma_by_id.return_value = {"termo": "cefaleia"}
    repository.create_base_candidata.return_value = 42
    service = make_service([
        [{"score": 0.99, "payload": {"sintoma_id": 7, "termo_canonico": "stale"}}],
        [],
    ], repository)
    monkeypatch.setattr(normalization_module, "NormalizationService", lambda: service)
    monkeypatch.setattr(postgres_service, "PostgresService", lambda: repository)
    candidate = {"original": "caganeira leve", "normalizado": "diarreia", "confianca": "alta"}
    content = json.dumps({"normalizacao_llm": [candidate]})
    captured = {}

    async def completion(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])

    async def post(url, json):
        captured.update(json)
        return SimpleNamespace(raise_for_status=lambda: None, json=lambda: {"message": {"content": content}})

    if provider == "groq":
        client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=completion)))
        monkeypatch.setattr(groq_service, "AsyncGroq", lambda **kwargs: client)
        classify = groq_service.classify_symptoms
    else:
        client = AsyncMock()
        client.__aenter__.return_value = SimpleNamespace(post=post)
        monkeypatch.setattr(ollama_service.httpx, "AsyncClient", lambda **kwargs: client)
        classify = ollama_service.classify_symptoms

    text = "Tenho dor de cabeça e caganeira leve"
    result = asyncio.run(classify(text))
    payload = json.loads(captured["messages"][1]["content"].split("\n", 1)[1])
    assert payload["sintomas_originais"] == text
    assert payload["sintomas_normalizados"][0]["normalizado"] == "cefaleia"
    assert payload["sintomas_nao_normalizados"] == ["caganeira leve"]
    repository.get_sintoma_by_id.assert_called_once_with(7)
    repository.create_base_candidata.assert_called_once_with(
        input_original="caganeira leve", normalizado_sugerido="diarreia",
        score_e5=0.0, score_ollama_confianca="alta", origem="llm",
    )
    assert result["normalizacao_llm"] == [candidate]
    assert result["normalizacao_resultado"]["persistencia_base_candidata"] == {"ids": [42], "falhas": []}


def test_qdrant_initialization_failure_still_allows_candidate_save(monkeypatch):
    monkeypatch.setattr(normalization_module, "NormalizationService", Mock(side_effect=RuntimeError("offline")))
    repository = Mock()
    repository.create_base_candidata.return_value = 12
    monkeypatch.setattr(postgres_service, "PostgresService", lambda: repository)
    context = normalize_safely("Tenho caganeira")
    assert context["sintomas_nao_normalizados"][0]["original"] == "caganeira"
    parsed = {"normalizacao_llm": [{"original": "caganeira", "normalizado": "diarreia", "confianca": "alta"}]}
    complete_normalization(parsed, context, "Tenho caganeira")
    assert context["persistencia_base_candidata"]["ids"] == [12]


@pytest.mark.parametrize("symptom_id", [None, 7])
def test_unconfirmed_qdrant_hit_remains_unresolved(symptom_id):
    repository = Mock()
    repository.get_sintoma_by_id.return_value = None
    service = make_service([[{"score": 0.99, "payload": {"sintoma_id": symptom_id, "termo_canonico": "cefaleia"}}]], repository)
    result = service._normalize_single_symptom("dor de cabeça")
    assert result["tipo"] == "nao_normalizado"
    assert result["motivo"] == "sintoma_nao_confirmado_postgres"


@pytest.mark.parametrize("outcome", [None, RuntimeError("offline")])
def test_failed_save_and_missing_llm_items_are_visible(monkeypatch, outcome):
    repository = Mock()
    if isinstance(outcome, Exception):
        repository.create_base_candidata.side_effect = outcome
    else:
        repository.create_base_candidata.return_value = outcome
    monkeypatch.setattr(postgres_service, "PostgresService", lambda: repository)
    context = {"sintomas_nao_normalizados": [{"original": "caganeira"}, {"original": "dor na barriga"}]}
    parsed = {"normalizacao_llm": [{"original": "caganeira", "normalizado": "diarreia", "confianca": "alta"}]}
    complete_normalization(parsed, context, "caganeira e dor na barriga")
    assert context["persistencia_base_candidata"] == {"ids": [], "falhas": ["caganeira"]}
    assert context["normalizacoes_pendentes_llm"] == ["dor na barriga"]
    assert len(parsed["alertas"]) == 2
