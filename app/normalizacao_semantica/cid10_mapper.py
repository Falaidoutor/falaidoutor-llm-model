"""Mapeador de sintomas para CID-10.

Fornece funcionalidade de tradução de sintomas em texto livre para
códigos CID-10 baseado em padrões de reconhecimento e dicionário.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CID10Info:
    """Informação de um código CID-10."""
    cid: str
    descricao: str
    sintoma_detectado: str
    confianca: float = 0.8  # 0-1, confiança do mapeamento


class CID10Mapper:
    """Mapeia sintomas em linguagem natural para códigos CID-10."""

    # Dicionário: sintoma canonical → informação CID-10
    SYMPTOM_TO_CID10 = {
        "dor de cabeça": {
            "cid": "R51",
            "descricao": "Cefaleia",
            "keywords": ["cefaleia", "dor na cabeça", "dor de cabeça", "enxaqueca"],
            "subtipos": {
                "enxaqueca": {"cid": "G43", "descricao": "Enxaqueca"},
                "cefaleia tensional": {"cid": "G44.2", "descricao": "Cefaleia tipo tensão"},
                "cefaleia em salvas": {"cid": "G44.0", "descricao": "Cefaleia em salvas"},
            }
        },
        "febre": {
            "cid": "R50.9",
            "descricao": "Febre não especificada",
            "keywords": ["febre", "temperatura alta", "quente", "febrento"],
            "subtipos": {
                "febre alta": {"cid": "R50.1", "descricao": "Febre alta (≥ 38,5°C)"},
                "febre muito alta": {"cid": "R50.1", "descricao": "Febre muito alta (≥ 41°C)"},
            }
        },
        "tosse": {
            "cid": "R05",
            "descricao": "Tosse",
            "keywords": ["tosse", "tossindo", "tosindo"],
            "subtipos": {
                "tosse seca": {"cid": "R05.0", "descricao": "Tosse seca"},
                "tosse com catarro": {"cid": "R05.1", "descricao": "Tosse com catarro"},
                "tosse persistente": {"cid": "R05.9", "descricao": "Tosse não especificada"},
            }
        },
        "falta de ar": {
            "cid": "R06.0",
            "descricao": "Dispneia",
            "keywords": ["dispneia", "falta de ar", "falta ar", "dificuldade respiratória"],
            "subtipos": {
                "falta de ar ao repouso": {"cid": "R06.01", "descricao": "Dispneia ao repouso"},
                "falta de ar ao esforço": {"cid": "R06.02", "descricao": "Dispneia ao esforço"},
            }
        },
        "dor abdominal": {
            "cid": "R10.9",
            "descricao": "Dor abdominal não especificada",
            "keywords": ["dor abdominal", "dor na barriga", "dor na abdômen", "dor de barriga"],
            "subtipos": {
                "dor epigástrica": {"cid": "R10.1", "descricao": "Dor epigástrica"},
                "dor periumbilical": {"cid": "R10.3", "descricao": "Dor periumbilical"},
                "dor no quadrante inferior": {"cid": "R10.4", "descricao": "Dor no quadrante inferior"},
            }
        },
        "dor torácica": {
            "cid": "R07.9",
            "descricao": "Dor torácica não especificada",
            "keywords": ["dor torácica", "dor no peito", "dor no petto"],
            "subtipos": {
                "dor precordial": {"cid": "R07.2", "descricao": "Dor precordial"},
                "dor pleurítica": {"cid": "R07.1", "descricao": "Dor pleurítica"},
            }
        },
        "náusea": {
            "cid": "R11.0",
            "descricao": "Náusea",
            "keywords": ["náusea", "enjôo", "enjoo", "indisposição gástrica"],
        },
        "vômito": {
            "cid": "R11.1",
            "descricao": "Vômito",
            "keywords": ["vômito", "vomitando", "puxada", "golfada"],
            "subtipos": {
                "vômito persistente": {"cid": "R11.1", "descricao": "Vômito persistente"},
                "vômito com sangue": {"cid": "R11.0", "descricao": "Hematemese"},
            }
        },
        "diarreia": {
            "cid": "R19.7",
            "descricao": "Diarreia não especificada",
            "keywords": ["diarreia", "soltura", "evacuar frequentemente"],
            "subtipos": {
                "diarreia aquosa": {"cid": "K59.1", "descricao": "Diarreia aquosa"},
                "diarreia com sangue": {"cid": "K59.1", "descricao": "Diarreia disentérica"},
            }
        },
        "sangramento": {
            "cid": "R02",
            "descricao": "Hemorragia de locais não especificados",
            "keywords": ["sangramento", "sangue", "hemorragi", "hemorragia"],
            "subtipos": {
                "sangramento nasal": {"cid": "R04.0", "descricao": "Epistaxe"},
                "sangramento gengival": {"cid": "K06.8", "descricao": "Sangramento gengival"},
            }
        },
        "tosse com sangue": {
            "cid": "R04.1",
            "descricao": "Hemoptise",
            "keywords": ["tosse com sangue", "cuspir sangue", "hemoptise"],
        },
        "desmaio": {
            "cid": "R55",
            "descricao": "Síncope",
            "keywords": ["desmaio", "desmaiou", "síncope", "perda de consciência"],
            "subtipos": {
                "quase desmaio": {"cid": "R55.1", "descricao": "Pré-síncope"},
            }
        },
        "confusão mental": {
            "cid": "R41.0",
            "descricao": "Desorientação",
            "keywords": ["confusão", "confuso", "desorientado", "não sabe onde está"],
            "subtipos": {
                "confusão aguda": {"cid": "F05", "descricao": "Delirium"},
            }
        },
        "convulsão": {
            "cid": "R56",
            "descricao": "Convulsão",
            "keywords": ["convulsão", "convulsionando", "ataque", "tremores"],
            "subtipos": {
                "convulsão generalizada": {"cid": "G40", "descricao": "Epilepsia"},
            }
        },
        "vertigem": {
            "cid": "R42",
            "descricao": "Tontura e vertigem",
            "keywords": ["vertigem", "tontura", "tonteira", "mundo girar"],
            "subtipos": {
                "vertigem posicional": {"cid": "H81", "descricao": "Vertigem posicional"},
            }
        },
    }

    def map_symptoms(self, symptoms_list: list[str]) -> list[CID10Info]:
        """Mapeia uma lista de sintomas para CID-10.

        Args:
            symptoms_list: Lista de sintomas em forma canônica

        Returns:
            Lista de CID10Info encontrados
        """
        cids = []
        mapped_symptoms = set()

        for symptom_input in symptoms_list:
            if symptom_input.lower() in mapped_symptoms:
                continue

            for canonical_symptom, cid_data in self.SYMPTOM_TO_CID10.items():
                if self._matches(symptom_input, canonical_symptom, cid_data):
                    # Adicionar CID principal
                    cids.append(CID10Info(
                        cid=cid_data["cid"],
                        descricao=cid_data["descricao"],
                        sintoma_detectado=symptom_input,
                        confianca=0.9
                    ))
                    mapped_symptoms.add(symptom_input.lower())
                    break

        return cids

    def search_specific_subtypes(self, symptom: str, text: str) -> Optional[CID10Info]:
        """Busca subtipos específicos de um sintoma no texto.

        Exemplo: se o texto contém "tosse seca", retorna o CID específico para tosse seca.

        Args:
            symptom: Sintoma canonical (ex: "tosse")
            text: Texto para buscar subtipos

        Returns:
            CID10Info mais específico ou None
        """
        if symptom not in self.SYMPTOM_TO_CID10:
            return None

        cid_data = self.SYMPTOM_TO_CID10[symptom]
        subtipos = cid_data.get("subtipos", {})

        # Buscar subtipo no texto
        for subtipo_name, subtipo_cid in subtipos.items():
            if subtipo_name.lower() in text.lower():
                return CID10Info(
                    cid=subtipo_cid["cid"],
                    descricao=subtipo_cid["descricao"],
                    sintoma_detectado=symptom,
                    confianca=0.95
                )

        return None

    @staticmethod
    def _matches(input_text: str, canonical: str, cid_data: dict) -> bool:
        """Verifica se o input coincide com o sintoma canonical."""
        input_lower = input_text.lower()
        
        # Correspondência direta
        if input_lower == canonical.lower():
            return True
        
        # Correspondência em keywords
        keywords = cid_data.get("keywords", [])
        if any(kw.lower() == input_lower for kw in keywords):
            return True
        
        return False

    def get_all_cid_codes(self) -> list[str]:
        """Retorna lista de todos os CIDs cadastrados."""
        return [data["cid"] for data in self.SYMPTOM_TO_CID10.values()]

    def get_symptom_variants(self, canonical: str) -> list[str]:
        """Retorna todas as variantes de um sintoma canonical."""
        if canonical not in self.SYMPTOM_TO_CID10:
            return []
        return self.SYMPTOM_TO_CID10[canonical].get("keywords", [])
