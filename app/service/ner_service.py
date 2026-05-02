"""
Serviço de Named Entity Recognition (NER) para extração de sintomas.
Utiliza spaCy modelo pt-BR. Pode ser estendido com fine-tuning customizado.
"""

import logging
import spacy
from typing import List
from app.config.settings import SPACY_MODEL_NAME, SPACY_CUSTOM_MODEL_PATH

logger = logging.getLogger(__name__)


class NERService:
    """
    Extrai sintomas de texto em português usando spaCy.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        try:
            # Tentar carregar modelo customizado se disponível
            if SPACY_CUSTOM_MODEL_PATH:
                logger.info(f"Carregando modelo spaCy customizado de {SPACY_CUSTOM_MODEL_PATH}")
                self.nlp = spacy.load(SPACY_CUSTOM_MODEL_PATH)
            else:
                # Carregar modelo padrão pt-BR
                logger.info(f"Carregando modelo spaCy padrão: {SPACY_MODEL_NAME}")
                try:
                    self.nlp = spacy.load(SPACY_MODEL_NAME)
                except OSError:
                    logger.warning(
                        f"Modelo {SPACY_MODEL_NAME} não encontrado. "
                        "Baixando... Execute: python -m spacy download pt_core_news_md"
                    )
                    raise

            self._initialized = True
            logger.info("NERService inicializado com sucesso")

        except Exception as e:
            logger.error(f"Erro ao inicializar NERService: {e}")
            raise

    def extract_symptoms(self, text: str) -> List[str]:
        """
        Extrai sintomas de um texto usando NER e heurísticas.

        Args:
            text: Texto de entrada do usuário

        Returns:
            Lista de sintomas extraídos (deduplica, ordena por frequência)
        """
        if not text or not isinstance(text, str):
            return []

        # Limpeza básica
        cleaned_text = text.strip().lower()
        if not cleaned_text:
            return []

        doc = self.nlp(cleaned_text)

        symptoms = []

        # Estratégia 1: Entidades rotuladas como SYMPTOM (se fine-tuned)
        for ent in doc.ents:
            if ent.label_ in ["SYMPTOM", "DISEASE", "CONDITION"]:
                symptoms.append(ent.text.strip())

        # Estratégia 2: Heurística — noun phrases e sintagmas nominais
        # Extrair chunks que frequentemente represetam sintomas
        for chunk in doc.noun_chunks:
            chunk_text = chunk.text.strip()
            # Filtrar muito curto ou muito longo
            if 2 <= len(chunk_text) <= 50:
                symptoms.append(chunk_text)

        # Estratégia 3: Split por conectores comuns (e, ou, vírgula)
        # Se nenhuma entidade foi encontrada
        if not symptoms:
            alternative_symptoms = self._split_by_connectors(cleaned_text)
            symptoms.extend(alternative_symptoms)

        # Deduplicação e normalização
        symptoms = list(dict.fromkeys(symptoms))  # Preserva ordem, remove duplicatas
        symptoms = [s.strip() for s in symptoms if s.strip()]

        logger.debug(f"Sintomas extraídos de '{text[:50]}...': {symptoms}")

        return symptoms

    def _split_by_connectors(self, text: str) -> List[str]:
        """
        Fallback: split por conectores comuns (e, ou, vírgula).
        """
        import re

        # Dividir por "e", "ou", "," ou ";"
        pattern = r"\s+(?:e|ou)\s+|[,;]\s+"
        parts = re.split(pattern, text)

        # Limpar e filtrar
        return [p.strip() for p in parts if p.strip()]

    def extract_symptoms_with_confidence(
        self, text: str
    ) -> List[dict]:
        """
        Versão estendida que retorna sintomas com metadata de confiança.

        Returns:
            Lista de dicts com {"text": str, "method": str, "confidence": float}
        """
        if not text or not isinstance(text, str):
            return []

        cleaned_text = text.strip().lower()
        if not cleaned_text:
            return []

        doc = self.nlp(cleaned_text)
        results = []

        # Entidades (alta confiança)
        for ent in doc.ents:
            if ent.label_ in ["SYMPTOM", "DISEASE", "CONDITION"]:
                results.append(
                    {
                        "text": ent.text.strip(),
                        "method": ent.label_,
                        "confidence": 0.95,
                    }
                )

        # Noun chunks (média confiança)
        for chunk in doc.noun_chunks:
            chunk_text = chunk.text.strip()
            if 2 <= len(chunk_text) <= 50:
                results.append(
                    {
                        "text": chunk_text,
                        "method": "noun_chunk",
                        "confidence": 0.70,
                    }
                )

        # Deduplicação por texto
        seen = {r["text"] for r in results}
        results = [dict(t) for t in {tuple(d.items()) for d in results}]

        logger.debug(f"Sintomas with confidence: {len(results)}")
        return results
