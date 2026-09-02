"""Lightweight symptom extraction suitable for serverless runtimes."""

import re


class NERService:
    """Extract symptom phrases without shipping a local NLP model to Vercel."""

    _LEADING_WORDS = {
        "a",
        "as",
        "com",
        "de",
        "do",
        "da",
        "está",
        "estou",
        "eu",
        "meu",
        "minha",
        "o",
        "os",
        "sinto",
        "tenho",
        "teve",
        "tive",
    }
    _CONNECTORS = re.compile(r"\s+(?:e|ou)\s+|[,;\n]+|(?<=[.!?])\s+")
    _EDGE_NOISE = re.compile(r"^[\s:.-]+|[\s:.-]+$")

    def extract_symptoms(self, text: str) -> list[str]:
        if not isinstance(text, str) or not text.strip():
            return []

        parts = self._CONNECTORS.split(text.strip().lower())
        symptoms: list[str] = []
        for part in parts:
            phrase = self._clean_phrase(part)
            if 3 <= len(phrase) <= 160 and phrase not in symptoms:
                symptoms.append(phrase)

        return symptoms

    def extract_symptoms_with_confidence(self, text: str) -> list[dict]:
        return [
            {"text": symptom, "method": "heuristic", "confidence": 0.7}
            for symptom in self.extract_symptoms(text)
        ]

    def _clean_phrase(self, phrase: str) -> str:
        phrase = self._EDGE_NOISE.sub("", phrase)
        words = phrase.split()
        while words and words[0] in self._LEADING_WORDS:
            words.pop(0)
        return " ".join(words).strip()
