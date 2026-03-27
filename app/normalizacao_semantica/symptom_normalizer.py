"""Normalizador de sintomas em linguagem natural.

Converte variações de sintomas (sinônimos, abreviações, erros de digitação)
para forma canônica padronizada.
"""

import re
from typing import Optional


class SymptomNormalizer:
    """Normaliza sintomas de entrada do usuário para forma canônica."""

    # Mapeamento: variação → forma canonical
    # Inclui sinônimos, abreviações, erros comuns de digitação
    SYMPTOM_SYNONYMS = {
        # Dor de cabeça
        "dor de cabeça": [
            "cefaleia", "dor na cabeça", "enxaqueca",
            "dor cabeça", "dor cabeca", "dor de cabeca", "cabeça doendo",
            "duor de cabeça", "dor no cranio"
        ],
        # Falta de ar
        "falta de ar": [
            "dispneia", "falta ar", "não consigo respirar", "respiração difícil",
            "falta aer", "faltsde ar", "dificuldade de respirar", "airflow ruim",
            "respirar difícil"
        ],
        # Vômito
        "vômito": [
            "vomitando", "vomitou", "estou vomitando", "gorfada",
            "vomento", "vomindo", "vomido"
        ],
        # Febre
        "febre": [
            "temperatura alta", "quente", "febrento", "com febre", "febril",
            "temperatura elevada", "estou quente", "calor intenso", "temp alta"
        ],
        # Dor abdominal
        "dor abdominal": [
            "dor na barriga", "dor na abdomen", "dor de barriga", "barriga doendo",
            "dor na pança", "dor no abdome", "cólica", "dor ventral"
        ],
        # Dor torácica
        "dor torácica": [
            "dor no peito",  "dor no tórax",
            "aperto no peito", "peito doendo", "dor pectoral"
        ],
        # Tosse
        "tosse": [
            "tossindo", "tosindo", "tosse seca", "tosse com catarro",
            "tose", "tutia", "tussa"
        ],
        # Náusea
        "náusea": [
            "enjôo", "enjoo", "indisposição", "sentindo enjoado", "enjôado",
            "nauseado", "nausea", "indiposição"
        ],
        # Diarreia
        "diarreia": [
            "soltura", "soltura de barriga", "fezes soltas", "diarréia",
            "diareia", "intestino solto"
        ],
        # Sangramento
        "sangramento": [
            "sangue", "hemorragi", "hemorragia", "sangrando", "sangra",
            "sangramento vaginal", "sangramento nasal"
        ],
        # Tosse com sangue
        "tosse com sangue": [
            "cuspir sangue", "hemoptise", "tossindo sangue", "tussir sangue"
        ],
        # Desmaio
        "desmaio": [
            "desmaiou", "síncope", "perda de consciência", "apagou",
            "desmaiar", "desmaia", "sincope"
        ],
        # Confusão mental
        "confusão mental": [
            "confuso", "desorientado", "não sabe onde está", "delirium",
            "confundido", "confundimento", "desorientação"
        ],
        # Convulsão
        "convulsão": [
            "convulsionando", "ataque", "tremores", "convulsao",
            "convulsionado", "crise convulsiva"
        ],
        # Vertigem
        "vertigem": [
            "tontura", "tonteira", "mundo girar", "giro", "tonteura",
            "tonta", "vertigem postural"
        ],
        # Coceira
        "coceira": [
            "prurido", "coçando", "alergia", "comichão", "irritação",
            "cocera", "coçeira"
        ],
        # Erupção cutânea
        "erupção cutânea": [
            "rash", "mancha na pele", "alergia", "urticária", "manchas",
            "erupção", "erupçao"
        ],
    }

    # Red flags do protocolo Manchester
    RED_FLAG_PATTERNS = {
        r"não.*respirar|falta.*ar.*intensa|não.*consigo.*respirar": {
            "flag": "Respiração inadequada",
            "color": "VERMELHO"
        },
        r"pior.*dor.*vida|pior.*dor|insuportável": {
            "flag": "Dor extrema - possível Vermelho/Laranja",
            "color": "LARANJA"
        },
        r"dor.*peito.*(?:bra[çc]o|mandíbula|ombro)": {
            "flag": "Possível Síndrome Coronária Aguda",
            "color": "LARANJA"
        },
        r"(?:sangue|hemorragi).*(?:muito|intensa|abundante|muito)": {
            "flag": "Hemorragia significativa",
            "color": "LARANJA"
        },
        r"(?:desmaio|síncope|apagou|perda.*consciência)": {
            "flag": "Perda de consciência",
            "color": "LARANJA"
        },
        r"(?:confus|desorientad|não.*sabe.*onde)": {
            "flag": "Alteração do nível de consciência",
            "color": "LARANJA"
        },
        r"(?:convuls|ataque|tremor.*incontrolável)": {
            "flag": "Convulsão/Ataque",
            "color": "LARANJA"
        },
        r"toxin|veneno|droga|comprimido.*muitos|overdose": {
            "flag": "Possível intoxicação/overdose",
            "color": "LARANJA"
        },
    }

    def normalize_text(self, text: str) -> str:
        """Limpeza básica do texto.

        - Converter para lowercase
        - Remover caracteres especiais (exceto acentos)
        - Remover espaços múltiplos
        - Expandir abreviações comuns
        """
        # Lowercase
        text = text.lower()

        # Remover apenas caracteres muito especiais, manter acentos
        # Permite: letras (com acentos), números, espaços, hífen
        text = re.sub(r'[^a-záàâãéèêíïóôõöúçñ\d\s\-]', '', text)

        # Expandir abreviações comuns
        # "d " → "de " (dor d cabeca → dor de cabeca)
        text = re.sub(r'\bd\s+', 'de ', text)
        # "tá" → "está"
        text = re.sub(r'\btá\b', 'está', text)
        # "tô" → "estou"
        text = re.sub(r'\btô\b', 'estou', text)
        # "pra" → "para"
        text = re.sub(r'\bpra\b', 'para', text)
        # "pro" → "para o"
        text = re.sub(r'\bpro\b', 'para o', text)

        # Remover espaços múltiplos
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def normalize_symptoms(self, text: str) -> list[str]:
        """Extrai e normaliza sintomas do texto.

        Estratégia:
        1. Buscar cada variante de sintoma no texto
        2. Mapear para forma canonical
        3. Retornar lista de sintomas únicos

        Args:
            text: Texto de entrada do usuário

        Returns:
            Lista de sintomas em forma canonical
        """
        normalized = self.normalize_text(text)
        symptoms_found = set()

        # Para cada symptom canonical
        for canonical, variants in self.SYMPTOM_SYNONYMS.items():
            # Buscar canonical diretamente
            if self._find_symptom(canonical, normalized):
                symptoms_found.add(canonical)
                continue

            # Buscar variantes
            for variant in variants:
                if self._find_symptom(variant, normalized):
                    symptoms_found.add(canonical)
                    break

        return sorted(list(symptoms_found))

    def detect_red_flags(self, text: str) -> list[dict]:
        """Detecta red flags semânticas no texto.

        Red flags são padrões que indicam urgência máxima.

        Args:
            text: Texto de entrada

        Returns:
            Lista de red flags detectadas com formato:
            [
                {
                    "flag": "descrição",
                    "color": "VERMELHO|LARANJA",
                    "padrão_detectado": "..."
                }
            ]
        """
        normalized = self.normalize_text(text)
        red_flags = []
        detected_patterns = set()

        for pattern, flag_info in self.RED_FLAG_PATTERNS.items():
            if re.search(pattern, normalized):
                flag_key = flag_info["flag"]
                
                if flag_key not in detected_patterns:
                    red_flags.append({
                        "flag": flag_info["flag"],
                        "color": flag_info["color"],
                        "padrao": pattern
                    })
                    detected_patterns.add(flag_key)

        return red_flags

    @staticmethod
    def _find_symptom(symptom: str, text: str) -> bool:
        """Busca um sintoma no texto usando word boundaries.

        Evita false positives como "perna" dentro de "temperatura".
        """
        pattern = r'\b' + re.escape(symptom.lower()) + r'\b'
        return bool(re.search(pattern, text))

    def extract_intensity_indicators(self, text: str) -> Optional[str]:
        """Extrai indicadores de intensidade da dor/sintoma.

        Retorna: "leve", "moderada", "intensa" ou None

        Estratégia:
        1. Buscar EVA (0-10) explícita
        2. Buscar palavras-chave de intensidade
        """
        normalized = self.normalize_text(text)

        # Buscar EVA (0-10)
        eva_patterns = [
            r'eva?\s*[:/]?\s*([0-9]|10)',  # EVA 7, EVA: 7, EVA/7
            r'escala?\s*[:/]?\s*([0-9]|10)',  # escala 7
            r'([0-9]|10)\s*(?:em|\/)\s*10',  # 7/10, 7 em 10
        ]

        for pattern in eva_patterns:
            match = re.search(pattern, normalized)
            if match:
                score = int(match.group(1))
                if score <= 3:
                    return "leve"
                elif score <= 6:
                    return "moderada"
                else:
                    return "intensa"

        # Palavras-chave para intensidade
        intense_keywords = [
            "intensa", "extrema", "insuportável", "muito forte",
            "pior", "insuportável", "terrível", "aguda"
        ]
        mild_keywords = [
            "leve", "discreta", "pouca", "pequena", "levinha",
            "quase nada", "bem leve", "fraca"
        ]

        if any(re.search(r'\b' + kw + r'\b', normalized) for kw in intense_keywords):
            return "intensa"
        if any(re.search(r'\b' + kw + r'\b', normalized) for kw in mild_keywords):
            return "leve"

        # Default
        return "moderada"

    def extract_duration(self, text: str) -> Optional[str]:
        """Extrai duração dos sintomas.

        Retorna strings como "3 dias", "2 horas", etc.

        Exemplos:
        - "há 3 dias" → "3 dias"
        - "desde ontem" → "1 dia"
        - "1 semana" → "1 semana"
        """
        normalized = self.normalize_text(text)

        # Padrões: "há N dias", "desde N horas", etc
        duration_patterns = [
            r'(?:há|desde)\s+(\d+)\s+(dias?|horas?|semanas?|meses?)',
            r'(\d+)\s+(dias?|horas?|semanas?|meses?)\s+(?:atrás|passadas?)',
        ]

        for pattern in duration_patterns:
            match = re.search(pattern, normalized)
            if match:
                return f"{match.group(1)} {match.group(2)}"

        # Palavras-chave: ontem, hoje, recente
        if "ontem" in normalized:
            return "1 dia"
        if "hoje" in normalized or "agora" in normalized:
            return "Agudo (hoje)"
        if any(word in normalized for word in ["recentemente", "recente", "subitamente"]):
            return "Recente (onset agudo)"

        return None

    def get_all_canonical_symptoms(self) -> list[str]:
        """Retorna lista de todos os sintomas canonical."""
        return sorted(list(self.SYMPTOM_SYNONYMS.keys()))

    def get_symptom_variants(self, canonical: str) -> list[str]:
        """Retorna todas as variantes de um sintoma canonical."""
        if canonical not in self.SYMPTOM_SYNONYMS:
            return []
        return self.SYMPTOM_SYNONYMS[canonical]
