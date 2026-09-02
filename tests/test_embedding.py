import pytest

from app.service.embedding import EmbeddingService


def test_query_uses_e5_prefix_and_cloud_model():
    service = EmbeddingService()

    document = service.embed("  dor de cabeça  ")

    assert document.text == "query: dor de cabeça"
    assert document.model == "intfloat/multilingual-e5-small"
    assert service.get_embedding_dimension() == 384


def test_corpus_uses_passage_prefix():
    service = EmbeddingService()

    documents = service.embed_corpus(["cefaleia", "falta de ar"])

    assert [document.text for document in documents] == [
        "passage: cefaleia",
        "passage: falta de ar",
    ]


@pytest.mark.parametrize("text", ["", "   ", None])
def test_invalid_text_is_rejected(text):
    service = EmbeddingService()

    with pytest.raises(ValueError):
        service.embed(text)
