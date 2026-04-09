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
        # ========== SISTEMA RESPIRATÓRIO (>75 sintomas) ==========
        "tosse noturna": {
            "cid": "R05.9",
            "descricao": "Tosse noturna",
            "keywords": ["tosse noturna", "tosse à noite"],
        },
        "pigarro": {
            "cid": "R05.9",
            "descricao": "Pigarro/Raspagem na garganta",
            "keywords": ["pigarro", "raspagem na garganta", "na garganta"],
        },
        "rouquidão": {
            "cid": "R49.0",
            "descricao": "Rouquidão",
            "keywords": ["rouquidão", "rouco", "voz rouca"],
        },
        "dor de garganta": {
            "cid": "R04.2",
            "descricao": "Dor de garganta",
            "keywords": ["dor de garganta", "garganta inflamada", "faringite"],
        },
        "dificuldade ao engolir": {
            "cid": "R13",
            "descricao": "Disfagia",
            "keywords": ["disfagia", "dificuldade ao engolir", "engolir dói"],
        },
        "espirro frequente": {
            "cid": "R06.7",
            "descricao": "Espirro",
            "keywords": ["espirro", "espirros", "espirrando"],
        },
        "congestão nasal": {
            "cid": "R06.0",
            "descricao": "Congestão nasal",
            "keywords": ["congestão", "nariz entupido", "rinorreia"],
        },
        "coriza": {
            "cid": "R09.3",
            "descricao": "Coriza",
            "keywords": ["coriza", "muco nasal", "nariz escorrendo"],
        },
        "sinusite": {
            "cid": "J01.9",
            "descricao": "Sinusite aguda não especificada",
            "keywords": ["sinusite", "seios nasais inflamados"],
        },
        "bronquite": {
            "cid": "J20.9",
            "descricao": "Bronquite aguda não especificada",
            "keywords": ["bronquite", "bronquite aguda"],
        },
        "pneumonia": {
            "cid": "J18.9",
            "descricao": "Pneumonia não especificada",
            "keywords": ["pneumonia", "pneumonite"],
        },
        "asma": {
            "cid": "J45.9",
            "descricao": "Asma não especificada",
            "keywords": ["asma", "crise asmática"],
        },
        "sibilância": {
            "cid": "R06.0",
            "descricao": "Chiado no peito",
            "keywords": ["sibilância", "chiado", "chiado no peito", "rânco"],
        },
        "hemoptise": {
            "cid": "R04.1",
            "descricao": "Tosse com sangue/Hemoptise",
            "keywords": ["hemoptise", "cuspe sangue"],
        },
        "afonia": {
            "cid": "R49.1",
            "descricao": "Afonia (perda da voz)",
            "keywords": ["afonia", "perda de voz", "sem voz"],
        },
        # ========== SISTEMA CARDIOVASCULAR ==========
        "palpitação": {
            "cid": "R00.2",
            "descricao": "Palpitações",
            "keywords": ["palpitação", "coração acelerado", "coração disparado"],
        },
        "taquicardia": {
            "cid": "R00.0",
            "descricao": "Taquicardia",
            "keywords": ["taquicardia", "ritmo cardíaco rápido"],
        },
        "bradicardia": {
            "cid": "R00.1",
            "descricao": "Bradicardia",
            "keywords": ["bradicardia", "ritmo cardíaco lento"],
        },
        "arritmia cardíaca": {
            "cid": "R00.8",
            "descricao": "Arritmia cardíaca",
            "keywords": ["arritmia", "batida irregular", "batida faltando"],
        },
        "pressão alta": {
            "cid": "R03.0",
            "descricao": "Pressão arterial elevada (sem diagnóstico de hipertensão)",
            "keywords": ["pressão alta", "hipertensão", "pressão elevada"],
        },
        "pressão baixa": {
            "cid": "R03.1",
            "descricao": "Pressão arterial baixa",
            "keywords": ["pressão baixa", "hipotensão", "pressão reduzida"],
        },
        "edema": {
            "cid": "R60.9",
            "descricao": "Edema não especificado",
            "keywords": ["edema", "inchaço", "inchação"],
        },
        "varizes": {
            "cid": "I83",
            "descricao": "Varizes",
            "keywords": ["varizes", "varicosidade", "veias inchadas"],
        },
        # ========== SISTEMA GASTROINTESTINAL ==========
        "constipação": {
            "cid": "K59.0",
            "descricao": "Constipação",
            "keywords": ["constipação", "prisão de ventre", "intestino preso"],
        },
        "flatulência": {
            "cid": "R14",
            "descricao": "Flatulência",
            "keywords": ["flatulência", "gases", "intestino preso de gases"],
        },
        "dispepsia": {
            "cid": "K30",
            "descricao": "Indigestão (dispepsia)",
            "keywords": ["dispepsia", "indigestão", "dificuldade digerir"],
        },
        "azia": {
            "cid": "K21",
            "descricao": "Refluxo gastroesofágico",
            "keywords": ["azia", "queimação", "âcido"],
        },
        "úlcera gástrica": {
            "cid": "K25",
            "descricao": "Úlcera gástrica",
            "keywords": ["úlcera", "úlcera gástrica"],
        },
        "hérnia": {
            "cid": "K46.9",
            "descricao": "Hérnia não especificada",
            "keywords": ["hérnia", "hérnias"],
        },
        "apendicite": {
            "cid": "K35",
            "descricao": "Apendicite",
            "keywords": ["apendicite", "apêndice inflamado"],
        },
        "cólica intestinal": {
            "cid": "R10.4",
            "descricao": "Cólica intestinal",
            "keywords": ["cólica", "espasmo intestinal"],
        },
        "coledocolitíase": {
            "cid": "K80.5",
            "descricao": "Cálculo biliar",
            "keywords": ["cálculo", "pedra na vesícula", "colelitíase"],
        },
        "pancreatite": {
            "cid": "K85.9",
            "descricao": "Pancreatite aguda não especificada",
            "keywords": ["pancreatite", "pâncreas inflamado"],
        },
        "hepatite": {
            "cid": "K75.9",
            "descricao": "Hepatite não especificada",
            "keywords": ["hepatite", "fígado inflamado"],
        },
        # ========== SISTEMA GENITURINÁRIO ==========
        "poliúria": {
            "cid": "R35",
            "descricao": "Poliúria (micção frequente)",
            "keywords": ["poliúria", "urina frequente", "urina muita"],
        },
        "disúria": {
            "cid": "R30.0",
            "descricao": "Disúria (dor ao urinar)",
            "keywords": ["disúria", "dor ao urinar", "ardência ao urinar"],
        },
        "retenção urinária": {
            "cid": "R33.9",
            "descricao": "Retenção urinária",
            "keywords": ["retenção", "dificuldade urinar", "não consegue urinar"],
        },
        "incontinência urinária": {
            "cid": "R32",
            "descricao": "Incontinência urinária",
            "keywords": ["incontinência", "perda urina", "urina na roupa"],
        },
        "hematúria": {
            "cid": "R31.9",
            "descricao": "Hematúria",
            "keywords": ["sangue na urina", "hematúria", "urina vermelha"],
        },
        "infecção urinária": {
            "cid": "N39.0",
            "descricao": "Infecção do trato urinário",
            "keywords": ["infecção urinária", "urinária infecção", "cistite"],
        },
        "cálculo renal": {
            "cid": "N20.0",
            "descricao": "Cálculo renal",
            "keywords": ["cálculo", "pedra", "rim", "nefrolitíase"],
        },
        "dor renal": {
            "cid": "N23",
            "descricao": "Cólica renal",
            "keywords": ["cólica renal", "dor nas costas inferior"],
        },
        "insuficiência renal": {
            "cid": "N19",
            "descricao": "Insuficiência renal não especificada",
            "keywords": ["insuficiência renal", "rim não funciona"],
        },
        # ========== SISTEMA MUSCULOESQUELÉTICO ==========
        "artralgia": {
            "cid": "M25.5",
            "descricao": "Dor articular",
            "keywords": ["artralgia", "dor na articulação", "dor junta"],
        },
        "artrite": {
            "cid": "M19.9",
            "descricao": "Artrite não especificada",
            "keywords": ["artrite", "articulação inflamada"],
        },
        "reumatismo": {
            "cid": "M79.0",
            "descricao": "Reumatismo",
            "keywords": ["reumatismo", "artrite reumatoide"],
        },
        "gota": {
            "cid": "M10.9",
            "descricao": "Gota não especificada",
            "keywords": ["gota", "cristal no pé"],
        },
        "entorse": {
            "cid": "S93.4",
            "descricao": "Entorse de tornozelo",
            "keywords": ["entorse", "torção", "pé torcido"],
        },
        "luxação": {
            "cid": "S43.0",
            "descricao": "Luxação de ombro",
            "keywords": ["luxação", "deslocação", "articulação saiu"],
        },
        "fraturaoss": {
            "cid": "S42.9",
            "descricao": "Fratura não especificada",
            "keywords": ["fratura", "osso quebrado", "quebra"],
        },
        "distensão muscular": {
            "cid": "M62.0",
            "descricao": "Distensão muscular",
            "keywords": ["distensão", "músculo esticado"],
        },
        "mialgia": {
            "cid": "M79.1",
            "descricao": "Dor muscular",
            "keywords": ["mialgia", "dor muscular", "músculo dói"],
        },
        "fraqueza muscular": {
            "cid": "M62.8",
            "descricao": "Fraqueza muscular",
            "keywords": ["fraqueza muscular", "fraco", "sem força"],
        },
        "espasmo muscular": {
            "cid": "M62.8",
            "descricao": "Espasmo muscular",
            "keywords": ["espasmo", "câimbra", "traval"],
        },
        "rigidez de nuca": {
            "cid": "M48.0",
            "descricao": "Rigidez de nuca",
            "keywords": ["rigidez nuca", "pescoço rígido", "nuca travada"],
        },
        # ========== SISTEMA NEUROLÓGICO ==========
        "parestesia": {
            "cid": "R20.2",
            "descricao": "Parestesia (formigamento)",
            "keywords": ["parestesia", "formigamento", "dormência"],
        },
        "neuropatia": {
            "cid": "G62.9",
            "descricao": "Neuropatia periférica",
            "keywords": ["neuropatia", "nervo inflamado"],
        },
        "migrações": {
            "cid": "G43",
            "descricao": "Enxaqueca com aura",
            "keywords": ["aura", "enxaqueca com aura", "piscada"],
        },
        "hemiplegia": {
            "cid": "G81",
            "descricao": "Hemiplegia",
            "keywords": ["hemiplegia", "palesia", "lado paralisado"],
        },
        "paraplegia": {
            "cid": "G82",
            "descricao": "Paraplegia",
            "keywords": ["paraplegia", "pernas paralisadas"],
        },
        "tremor": {
            "cid": "R25.1",
            "descricao": "Tremor",
            "keywords": ["tremor", "tremendo", "mão tremendo"],
        },
        "discinesia": {
            "cid": "G24",
            "descricao": "Discinesia",
            "keywords": ["discinesia", "movimento involuntário"],
        },
        # ========== PELE E ANEXOS ==========
        "dermatite": {
            "cid": "L30.9",
            "descricao": "Dermatite não especificada",
            "keywords": ["dermatite", "pele inflamada"],
        },
        "eczema": {
            "cid": "L20",
            "descricao": "Eczema atópico",
            "keywords": ["eczema", "alergia de pele"],
        },
        "urticária": {
            "cid": "L50.9",
            "descricao": "Urticária não especificada",
            "keywords": ["urticária", "alergia", "coceira vermelha"],
        },
        "acne": {
            "cid": "L70",
            "descricao": "Acne",
            "keywords": ["acne", "espinha"],
        },
        "psoriase": {
            "cid": "L40",
            "descricao": "Psoríase",
            "keywords": ["psoriase", "pele descamando"],
        },
        "vitiligo": {
            "cid": "L80",
            "descricao": "Vitiligo",
            "keywords": ["vitiligo", "mancha branca pele"],
        },
        "alopecia": {
            "cid": "L65.9",
            "descricao": "Alopecia (queda cabelo)",
            "keywords": ["alopecia", "queda cabelo", "calvície"],
        },
        "caspa": {
            "cid": "L21",
            "descricao": "Seborreia (caspa)",
            "keywords": ["caspa", "descamação couro"],
        },
        "verruga": {
            "cid": "B07",
            "descricao": "Verruga",
            "keywords": ["verruga", "bolinha de pele"],
        },
        "micose": {
            "cid": "B35.9",
            "descricao": "Micose",
            "keywords": ["micose", "fungos", "pele com bolor"],
        },
        "ferida": {
            "cid": "T14.1",
            "descricao": "Ferida aberta",
            "keywords": ["ferida", "corte", "machucado"],
        },
        # ========== OFTALMOLOGIA ==========
        "visão turva": {
            "cid": "H53.8",
            "descricao": "Visão turva",
            "keywords": ["visão turva", "vista turva", "enxerga turvo"],
        },
        "diplopia": {
            "cid": "H53.2",
            "descricao": "Diplopia (visão dupla)",
            "keywords": ["diplopia", "enxerga duplo", "visão dupla"],
        },
        "fotofobia": {
            "cid": "H53.1",
            "descricao": "Fotofobia (sensibilidade à luz)",
            "keywords": ["fotofobia", "sensível luz", "luz machuca olho"],
        },
        "lacrimejamento": {
            "cid": "H04.2",
            "descricao": "Lacrimejamento",
            "keywords": ["lacrimejamento", "olho lagrimando", "lágrima"],
        },
        "conjuntivite": {
            "cid": "H10.9",
            "descricao": "Conjuntivite não especificada",
            "keywords": ["conjuntivite", "olho inflamado", "olho vermelho"],
        },
        "presbiopia": {
            "cid": "H52.4",
            "descricao": "Presbiopia (vista cansada)",
            "keywords": ["presbiopia", "vista cansada"],
        },
        "miopia": {
            "cid": "H52.1",
            "descricao": "Miopia (miopia)",
            "keywords": ["miopia", "míope", "perto poucofoco"],
        },
        "hipermetropia": {
            "cid": "H52.0",
            "descricao": "Hipermetropia",
            "keywords": ["hipermetropia", "hipermétrope"],
        },
        # ========== OTOLOGIA ==========
        "otalgia": {
            "cid": "H92.0",
            "descricao": "Dor de ouvido",
            "keywords": ["otalgia", "dor ouvido", "ouvido dói"],
        },
        "otite": {
            "cid": "H66.9",
            "descricao": "Otite média não especificada",
            "keywords": ["otite", "ouvido inflamado", "inflamação ouvido"],
        },
        "zumbido": {
            "cid": "H93.1",
            "descricao": "Zumbido auditivo",
            "keywords": ["zumbido", "chiado ouvido", "som na orelha"],
        },
        "surdez": {
            "cid": "H90.9",
            "descricao": "Surdez não especificada",
            "keywords": ["surdez", "surdo", "não ouve"],
        },
        # ========== METABÓLICO/ENDÓCRINA ==========
        "diabetes": {
            "cid": "E11.9",
            "descricao": "Diabetes tipo 2",
            "keywords": ["diabetes", "diabético"],
        },
        "hipoglicemia": {
            "cid": "E16.2",
            "descricao": "Hipoglicemia",
            "keywords": ["hipoglicemia", "açúcar baixo"],
        },
        "hiperglicemia": {
            "cid": "R73.9",
            "descricao": "Hiperglicemia",
            "keywords": ["hiperglicemia", "açúcar alto"],
        },
        "obesidade": {
            "cid": "E66.9",
            "descricao": "Obesidade não especificada",
            "keywords": ["obesidade", "gordo", "sobrepeso"],
        },
        "desnutrição": {
            "cid": "E46",
            "descricao": "Desnutrição não especificada",
            "keywords": ["desnutrição", "magro demais"],
        },
        "anemia": {
            "cid": "D64.9",
            "descricao": "Anemia não especificada",
            "keywords": ["anemia", "sangue fraco", "hemoglobina baixa"],
        },
        "hipotireoidismo": {
            "cid": "E03.9",
            "descricao": "Hipotireoidismo não especificado",
            "keywords": ["hipotireoidismo", "tireoide baixa"],
        },
        "hipertireoidismo": {
            "cid": "E05.9",
            "descricao": "Hipertireoidismo não especificado",
            "keywords": ["hipertireoidismo", "tireoide alta"],
        },
        # ========== INFECÇÕES ==========
        "dengue": {
            "cid": "A90",
            "descricao": "Dengue",
            "keywords": ["dengue", "fever"],
        },
        "zika": {
            "cid": "A92.5",
            "descricao": "Zika",
            "keywords": ["zika", "zika vírus"],
        },
        "malária": {
            "cid": "B54",
            "descricao": "Malária",
            "keywords": ["malária", "paludismo"],
        },
        "tuberculose": {
            "cid": "A19",
            "descricao": "Tuberculose",
            "keywords": ["tuberculose", "tb", "bacilo"],
        },
        "covid-19": {
            "cid": "U07.1",
            "descricao": "COVID-19",
            "keywords": ["covid", "coronavirus", "covid-19"],
        },
        "gripe": {
            "cid": "J11",
            "descricao": "Influenza (gripe)",
            "keywords": ["gripe", "influenza", "flu"],
        },
        "resfriado": {
            "cid": "J00",
            "descricao": "Resfriado comum",
            "keywords": ["resfriado", "catarro", "constipado"],
        },
        "doenças sexualmente transmissíveis": {
            "cid": "A64",
            "descricao": "Doença sexualmente transmissível não especificada",
            "keywords": ["dst", "doença sexualmente transmissível", "sti"],
        },
        # ========== PSIQUIÁTRICA/MENTAL ==========
        "ansiedade": {
            "cid": "F41.1",
            "descricao": "Transtorno de ansiedade generalizada",
            "keywords": ["ansiedade", "ansioso", "nervoso"],
        },
        "depressão": {
            "cid": "F32.9",
            "descricao": "Episódio depressivo maior não especificado",
            "keywords": ["depressão", "deprimido", "triste"],
        },
        "insônia": {
            "cid": "G47.0",
            "descricao": "Insônia",
            "keywords": ["insônia", "sono ruim", "não consegue dormir"],
        },
        "fadiga": {
            "cid": "R53.8",
            "descricao": "Fadiga",
            "keywords": ["fadiga", "cansaço", "exaustão"],
        },
        "agorafobia": {
            "cid": "F40.0",
            "descricao": "Agorafobia",
            "keywords": ["agorafobia", "medo multidão"],
        },
        "fobia": {
            "cid": "F40.8",
            "descricao": "Fobia específica",
            "keywords": ["fobia", "medo irracional"],
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
                        sintoma_detectado=symptom_input
                    ))
                    mapped_symptoms.add(symptom_input.lower())
                    break

        return cids

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
                    sintoma_detectado=symptom
                )

        return None

    def get_all_cid_codes(self) -> list[str]:
        """Retorna lista de todos os CIDs cadastrados."""
        return [data["cid"] for data in self.SYMPTOM_TO_CID10.values()]

    def get_symptom_variants(self, canonical: str) -> list[str]:
        """Retorna todas as variantes de um sintoma canonical."""
        if canonical not in self.SYMPTOM_TO_CID10:
            return []
        return self.SYMPTOM_TO_CID10[canonical].get("keywords", [])
