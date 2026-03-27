"""Analisador semântico de entrada do usuário.

Extrai informações estruturadas como idade, população especial,
sinais vitais e outros dados clínicos relevantes.
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class VitalSigns:
    """Sinais vitais extraídos."""
    temperatura: Optional[float] = None
    frequencia_cardiaca: Optional[int] = None
    frequencia_respiratoria: Optional[int] = None
    pressao_arterial: Optional[str] = None
    saturacao_oxigenio: Optional[int] = None


class SemanticAnalyzer:
    """Analisa semântica da entrada para extrair dados estruturados."""

    # Palavras-chave para faixas etárias
    PEDIATRIC_KEYWORDS = [
        "bebê", "bebe", "lactente", "criança", "menino", "menina",
        "filho", "filha", "infant", "child", "neonato"
    ]

    ELDERLY_KEYWORDS = [
        "idoso", "idosa", "velho", "velha", "avô", "avó",
        "terceira idade", "elderly", "aged"
    ]

    PREGNANT_KEYWORDS = [
        "grávida", "gravida", "gestante", "gravidez", "gravidez",
        "pregnant", "semana gestacional", "semanas", "embora", "bebezinho"
    ]

    def __init__(self):
        self.vital_signs_extractor = VitalSignsExtractor()

    def extract_age_group(self, text: str) -> Optional[str]:
        """Extrai faixa etária: "pediatria", "adulto", "idoso".

        Estratégia:
        1. Buscar idade numérica
        2. Buscar palavras-chave
        3. Default: "adulto"
        """
        text_lower = text.lower()

        # 1. Buscar numero que parece idade (1-150)
        ages = re.findall(r'\b([1-9]|[1-9]\d|1[0-4]\d)\b', text_lower)
        if ages:
            age = int(ages[0])
            if age < 12:
                return "pediatria"
            elif age >= 65:
                return "idoso"
            else:
                return "adulto"

        # 2. Buscar palavras-chave
        for keyword in self.PEDIATRIC_KEYWORDS:
            if keyword in text_lower:
                return "pediatria"

        for keyword in self.ELDERLY_KEYWORDS:
            if keyword in text_lower:
                return "idoso"

        # Default
        return "adulto"

    def extract_pregnancy_status(self, text: str) -> bool:
        """Detecta se a paciente é gestante."""
        text_lower = text.lower()
        for keyword in self.PREGNANT_KEYWORDS:
            if keyword in text_lower:
                return True
        return False

    def extract_obstetric_info(self, text: str) -> Optional[int]:
        """Extrai idade gestacional se disponível.

        Busca padrões como "20 semanas", "5 meses", etc.

        Returns:
            Idade gestacional em semanas ou None
        """
        text_lower = text.lower()

        # Padrão: "N semanas"
        weeks_match = re.search(r'(\d{1,2})\s+semanas?', text_lower)
        if weeks_match:
            weeks = int(weeks_match.group(1))
            if 1 <= weeks <= 44:  # Intervalo válido
                return weeks

        # Padrão: "N meses"
        months_match = re.search(r'(\d{1,2})\s+m[eê]s(?:es)?', text_lower)
        if months_match:
            months = int(months_match.group(1))
            if 1 <= months <= 9:
                return months * 4  # Conversão aproximada para semanas

        return None

    def extract_vital_signs(self, text: str) -> VitalSigns:
        """Extrai sinais vitais do texto.

        Procura por:
        - Temperatura (ex: "37.5°C", "39 graus")
        - FC (ex: "80 bpm", "frequência 100")
        - FR (ex: "16 respirações")
        - PA (ex: "140/90", "PA 120/80")
        - SpO2 (ex: "95% oxigênio", "SpO2 92")
        """
        return self.vital_signs_extractor.extract(text)

    def extract_comorbidities(self, text: str) -> list[str]:
        """Extrai doenças/comorbidades mencionadas.

        Procura por:
        - "diabético", "diabetes"
        - "hipertenso", "hipertensão"
        - "asma", "asmático"
        - "alergia"
        - etc.
        """
        text_lower = text.lower()

        comorbidities_keywords = {
            "diabetes": ["diabético", "diabetico", "diabetes", "glicose"],
            "hipertensão": ["hipertenso", "hipertensão", "hipertensao"],
            "asma": ["asma", "asmático", "asmatico"],
            "alergia": ["alergia", "alérgico", "alergico", "alergias"],
            "cardiopatia": ["coração", "coracao", "cardiaco", "cardíaco"],
            "insuficiência renal": ["rim", "renal", "insuficiência renal"],
            "HIV/AIDS": ["hiv", "aids", "vih"],
            "epilepsia": ["epilepsia", "epilético"],
        }

        found_comorbidities = []
        for medical_condition, keywords in comorbidities_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    found_comorbidities.append(medical_condition)
                    break

        return found_comorbidities

    def extract_medications(self, text: str) -> list[str]:
        """Extrai medicações mencionadas.

        Procura por nomes comuns de medicamentos.
        """
        text_lower = text.lower()

        common_medications = [
            "dipirona", "paracetamol", "ibuprofeno", "aspirina",
            "dipropionato", "hidroclorotiazida", "metformina",
            "insulina", "amoxicilina", "azitromicina", "antidepressivo",
        ]

        found_meds = [med for med in common_medications if med in text_lower]
        return found_meds

    def extract_onset(self, text: str) -> Optional[str]:
        """Classifica o onset dos sintomas.

        Retorna: "agudo", "subagudo", "crônico"
        """
        text_lower = text.lower()

        # Agudo: hoje, agora, súbito, repentino, começou agora
        acute_keywords = [
            "agora", "hoje", "súbito", "subito", "repentino",
            "começou agora", "comecou agora", "de repente"
        ]

        if any(kw in text_lower for kw in acute_keywords):
            return "agudo"

        # Subagudo: dias, semana
        subacute_keywords = [
            "dias", "dia", "semana", "semanas"
        ]

        if any(kw in text_lower for kw in subacute_keywords):
            return "subagudo"

        # Crônico: meses, anos, sempre, desde
        chronic_keywords = [
            "meses", "mês", "mes", "anos", "ano", "sempre", "desde",
            "há tempos", "faz tempo", "cronico", "crónico"
        ]

        if any(kw in text_lower for kw in chronic_keywords):
            return "crônico"

        return None


class VitalSignsExtractor:
    """Especialista em extração de sinais vitais."""

    def extract(self, text: str) -> VitalSigns:
        """Extrai todos os sinais vitais do texto."""
        return VitalSigns(
            temperatura=self._extract_temperature(text),
            frequencia_cardiaca=self._extract_heart_rate(text),
            frequencia_respiratoria=self._extract_respiratory_rate(text),
            pressao_arterial=self._extract_blood_pressure(text),
            saturacao_oxigenio=self._extract_oxygen_saturation(text),
        )

    @staticmethod
    def _extract_temperature(text: str) -> Optional[float]:
        """Extrai temperatura. Padrões: "37.5°C", "39 graus", "temp 38" """
        text_lower = text.lower()

        patterns = [
            r'(?:temp|temperatura|febre)\s*[:/]?\s*(\d{2}(?:[.,]\d)?)\s*[°cgraus]?',
            r'(\d{2}(?:[.,]\d)?)\s*[°c]',
            r'(\d{2}(?:[.,]\d)?)\s*graus',
        ]

        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                temp_str = match.group(1).replace(',', '.')
                try:
                    temp = float(temp_str)
                    if 34 <= temp <= 42:  # Intervalo realista
                        return temp
                except ValueError:
                    pass

        return None

    @staticmethod
    def _extract_heart_rate(text: str) -> Optional[int]:
        """Extrai frequência cardíaca. Padrões: "80 bpm", "FC 100", etc."""
        text_lower = text.lower()

        patterns = [
            r'(?:fc|frequência cardiaca|freq cardiaca)\s*[:/]?\s*(\d{2,3})',
            r'(\d{2,3})\s*bpm',
            r'pulso\s*(?:de|em|é)?\s*(\d{2,3})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    hr = int(match.group(1))
                    if 30 <= hr <= 200:  # Intervalo realista
                        return hr
                except ValueError:
                    pass

        return None

    @staticmethod
    def _extract_respiratory_rate(text: str) -> Optional[int]:
        """Extrai frequência respiratória. Padrões: "16 irpm", "FR 20", etc."""
        text_lower = text.lower()

        patterns = [
            r'(?:fr|frequência respiratoria|freq resp)\s*[:/]?\s*(\d{1,2})',
            r'(\d{1,2})\s*(?:irpm|resp)',
            r'respira[çc]ão\s*(?:de|em|é)?\s*(\d{1,2})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    rr = int(match.group(1))
                    if 8 <= rr <= 40:  # Intervalo realista
                        return rr
                except ValueError:
                    pass

        return None

    @staticmethod
    def _extract_blood_pressure(text: str) -> Optional[str]:
        """Extrai pressão arterial. Padrão: "140/90", "PA 120/80", etc."""
        text_lower = text.lower()

        patterns = [
            r'(?:pa|pressão|pressao)\s*[:/]?\s*(\d{2,3})\s*[/\\]\s*(\d{2,3})',
            r'(\d{2,3})\s*[/\\]\s*(\d{2,3})\s*(?:mmhg)?',
        ]

        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                sys = match.group(1)
                dia = match.group(2)
                try:
                    if 70 <= int(sys) <= 200 and 40 <= int(dia) <= 130:
                        return f"{sys}/{dia}"
                except ValueError:
                    pass

        return None

    @staticmethod
    def _extract_oxygen_saturation(text: str) -> Optional[int]:
        """Extrai saturação de oxigênio. Padrões: "95%", "SpO2 92", etc."""
        text_lower = text.lower()

        patterns = [
            r'(?:spo?2|saturação|saturacao)\s*[:/]?\s*(\d{2})\s*%?',
            r'(\d{2})\s*%\s*(?:oxigênio|oxigenio|o2)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    spo2 = int(match.group(1))
                    if 50 <= spo2 <= 100:  # Intervalo realista
                        return spo2
                except ValueError:
                    pass

        return None
