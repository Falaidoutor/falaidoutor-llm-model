"""
Validador de respostas de triagem MTS (Protocolo de Manchester).

Executa três camadas de validação:
  1. Estrutural — campos obrigatórios, tipos e valores permitidos
  2. Consistência lógica — cor ↔ prioridade ↔ tempo
  3. Regras de negócio — over-triage, confiança, discriminadores
"""

from dataclasses import dataclass, field

# ──────────────────────────────────────────────────────────────
# Constantes extraídas do Protocolo de Manchester (prompt.py)
# ──────────────────────────────────────────────────────────────

CLASSIFICACOES_VALIDAS = ("Vermelho", "Laranja", "Amarelo", "Verde", "Azul")

PRIORIDADES_VALIDAS = (
    "Emergência",
    "Muito urgente",
    "Urgente",
    "Pouco urgente",
    "Não urgente",
)

TEMPOS_VALIDOS = (0, 10, 60, 120, 240)

CONFIANCAS_VALIDAS = ("alta", "media", "baixa")

POPULACOES_VALIDAS = (None, "pediatria", "gestante", "idoso")

DISCLAIMER_ESPERADO = (
    "Classificação de apoio à decisão. "
    "A avaliação final é responsabilidade do profissional de saúde."
)

# Mapeamento bidirecional cor ↔ prioridade ↔ tempo
COR_PRIORIDADE = {
    "Vermelho": "Emergência",
    "Laranja": "Muito urgente",
    "Amarelo": "Urgente",
    "Verde": "Pouco urgente",
    "Azul": "Não urgente",
}

COR_TEMPO = {
    "Vermelho": 0,
    "Laranja": 10,
    "Amarelo": 60,
    "Verde": 120,
    "Azul": 240,
}

# Gravidade: menor índice = mais grave
GRAVIDADE = {cor: i for i, cor in enumerate(CLASSIFICACOES_VALIDAS)}

# Todos os 16 discriminadores gerais (seção 2 do prompt)
DISCRIMINADORES_GERAIS = [
    # Vermelho
    "Obstrução de via aérea",
    "Respiração inadequada",
    "Choque (sinais de hipoperfusão grave)",
    "Inconsciente ou não responsivo",
    "Convulsão ativa",
    "Hemorragia maciça incontrolável",
    # Laranja
    "Dor muito intensa (EVA 9–10)",
    "Hemorragia ativa significativa",
    "Febre muito alta (≥ 41°C)",
    "Hipotermia (< 35°C)",
    "Alteração aguda do nível de consciência (GCS < 15)",
    "Início agudo de sintomas neurológicos focais",
    # Amarelo
    "Dor intensa (EVA 7–8)",
    "Febre alta (38,5°C – 40,9°C)",
    "Vômitos persistentes",
    "Desidratação moderada",
]

# Mapeamento: discriminador geral → cor mínima que ele implica
DISCRIMINADOR_COR = {}
for d in DISCRIMINADORES_GERAIS[:6]:
    DISCRIMINADOR_COR[d] = "Vermelho"
for d in DISCRIMINADORES_GERAIS[6:12]:
    DISCRIMINADOR_COR[d] = "Laranja"
for d in DISCRIMINADORES_GERAIS[12:]:
    DISCRIMINADOR_COR[d] = "Amarelo"

FLUXOGRAMAS_VALIDOS = {
    "Dor Torácica",
    "Dor Abdominal",
    "Dispneia",
    "Cefaleia",
    "Febre no Adulto",
    "Febre na Criança",
    "Convulsões",
    "Trauma de Crânio",
    "Trauma de Membros",
    "Queimaduras",
    "Problemas Urinários",
    "Dor de Garganta",
    "Asma",
    "Diabetes",
    "Dor Lombar",
    "Feridas",
    "Problemas nos Olhos",
    "Mal-estar no Adulto",
    "Mal-estar na Criança",
    "Criança que Chora",
    "Criança Irritadiça",
    "Comportamento Estranho",
    "Overdose e Intoxicação",
    "Dor de Ouvido",
    "Erupções Cutâneas",
    "Problemas em Extremidades",
    "Dor Testicular",
    "Sangramento Vaginal",
    "Gravidez",
    "Infecções Locais e Abscessos",
    "Mordidas e Picadas",
    "Agressão",
    "Autoagressão",
}

TERMOS_PROIBIDOS_JUSTIFICATIVA = [
    "provavelmente",
    "pode ser",
    "suspeita de",
]


# ──────────────────────────────────────────────────────────────
# Resultado da validação
# ──────────────────────────────────────────────────────────────

@dataclass
class ValidationResult:
    """Resultado agregado de todas as validações."""
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)


# ──────────────────────────────────────────────────────────────
# 1. Validação estrutural
# ──────────────────────────────────────────────────────────────

def _validate_structural(data: dict, result: ValidationResult) -> None:
    """Campos obrigatórios, tipos e valores permitidos."""

    # --- classificacao ---
    cls = data.get("classificacao")
    if cls not in CLASSIFICACOES_VALIDAS:
        result.add_error(
            f"classificacao '{cls}' inválida. "
            f"Valores aceitos: {CLASSIFICACOES_VALIDAS}"
        )

    # --- prioridade ---
    pri = data.get("prioridade")
    if pri not in PRIORIDADES_VALIDAS:
        result.add_error(
            f"prioridade '{pri}' inválida. "
            f"Valores aceitos: {PRIORIDADES_VALIDAS}"
        )

    # --- tempo_atendimento_minutos ---
    tempo = data.get("tempo_atendimento_minutos")
    if not isinstance(tempo, int):
        result.add_error(
            f"tempo_atendimento_minutos deve ser int, recebido {type(tempo).__name__}."
        )
    elif tempo not in TEMPOS_VALIDOS:
        result.add_error(
            f"tempo_atendimento_minutos '{tempo}' inválido. "
            f"Valores aceitos: {TEMPOS_VALIDOS}"
        )

    # --- fluxograma_utilizado ---
    fluxo = data.get("fluxograma_utilizado")
    if not isinstance(fluxo, str) or not fluxo.strip():
        result.add_error("fluxograma_utilizado está vazio ou ausente.")
    elif fluxo not in FLUXOGRAMAS_VALIDOS:
        result.add_warning(
            f"fluxograma_utilizado '{fluxo}' não consta na lista oficial de fluxogramas."
        )

    # --- discriminadores_gerais_avaliados ---
    dga = data.get("discriminadores_gerais_avaliados")
    if not isinstance(dga, list):
        result.add_error("discriminadores_gerais_avaliados deve ser uma lista.")
    else:
        for i, item in enumerate(dga):
            if not isinstance(item, dict):
                result.add_error(
                    f"discriminadores_gerais_avaliados[{i}] deve ser um objeto "
                    f"{{'discriminador': str, 'presente': bool}}."
                )
                continue
            if "discriminador" not in item or "presente" not in item:
                result.add_error(
                    f"discriminadores_gerais_avaliados[{i}] está faltando "
                    f"'discriminador' ou 'presente'."
                )
            elif not isinstance(item["presente"], bool):
                result.add_error(
                    f"discriminadores_gerais_avaliados[{i}].presente "
                    f"deve ser bool, recebido {type(item['presente']).__name__}."
                )

    # --- discriminadores_especificos_ativados ---
    dea = data.get("discriminadores_especificos_ativados")
    if not isinstance(dea, list):
        result.add_error("discriminadores_especificos_ativados deve ser uma lista.")

    # --- populacao_especial ---
    pop = data.get("populacao_especial")
    if pop not in POPULACOES_VALIDAS:
        result.add_error(
            f"populacao_especial '{pop}' inválida. "
            f"Valores aceitos: {POPULACOES_VALIDAS}"
        )

    # --- over_triage_aplicado ---
    ot = data.get("over_triage_aplicado")
    if not isinstance(ot, bool):
        result.add_error(
            f"over_triage_aplicado deve ser bool, recebido {type(ot).__name__}."
        )

    # --- confianca ---
    conf = data.get("confianca")
    if conf not in CONFIANCAS_VALIDAS:
        result.add_error(
            f"confianca '{conf}' inválida. Valores aceitos: {CONFIANCAS_VALIDAS}"
        )

    # --- justificativa ---
    just = data.get("justificativa")
    if not isinstance(just, str) or not just.strip():
        result.add_error("justificativa está vazia ou ausente.")

    # --- alertas ---
    alertas = data.get("alertas")
    if alertas is None:
        result.add_error("alertas não pode ser null — deve ser lista (pode ser vazia).")
    elif not isinstance(alertas, list):
        result.add_error(f"alertas deve ser uma lista, recebido {type(alertas).__name__}.")

    # --- disclaimer ---
    disc = data.get("disclaimer")
    if disc != DISCLAIMER_ESPERADO:
        result.add_error(
            "disclaimer difere do texto fixo obrigatório."
        )


# ──────────────────────────────────────────────────────────────
# 2. Validação de consistência lógica
# ──────────────────────────────────────────────────────────────

def _validate_consistency(data: dict, result: ValidationResult) -> None:
    """Cor ↔ prioridade ↔ tempo devem ser coerentes entre si."""

    cls = data.get("classificacao")
    pri = data.get("prioridade")
    tempo = data.get("tempo_atendimento_minutos")

    if cls not in COR_PRIORIDADE:
        return  # já reportado na validação estrutural

    # Cor → prioridade esperada
    pri_esperada = COR_PRIORIDADE[cls]
    if pri != pri_esperada:
        result.add_error(
            f"Inconsistência: classificacao '{cls}' requer prioridade "
            f"'{pri_esperada}', mas recebido '{pri}'."
        )

    # Cor → tempo esperado
    tempo_esperado = COR_TEMPO[cls]
    if isinstance(tempo, int) and tempo != tempo_esperado:
        result.add_error(
            f"Inconsistência: classificacao '{cls}' requer "
            f"tempo_atendimento_minutos={tempo_esperado}, mas recebido {tempo}."
        )


# ──────────────────────────────────────────────────────────────
# 3. Validação de regras de negócio
# ──────────────────────────────────────────────────────────────

def _validate_business_rules(data: dict, result: ValidationResult) -> None:
    """Over-triage, confiança, discriminadores e regras do protocolo."""

    cls = data.get("classificacao")
    dga = data.get("discriminadores_gerais_avaliados", [])
    over_triage = data.get("over_triage_aplicado", False)
    confianca = data.get("confianca")
    justificativa = data.get("justificativa", "")
    alertas = data.get("alertas") or []

    # --- Todos os 16 discriminadores gerais devem ter sido avaliados ---
    if isinstance(dga, list):
        nomes_avaliados = {
            item["discriminador"]
            for item in dga
            if isinstance(item, dict) and "discriminador" in item
        }
        faltantes = set(DISCRIMINADORES_GERAIS) - nomes_avaliados
        if faltantes:
            result.add_warning(
                f"Discriminadores gerais não avaliados ({len(faltantes)}): "
                f"{', '.join(sorted(faltantes))}"
            )

    # --- Classificação coerente com discriminador mais grave ativado ---
    if isinstance(dga, list) and cls in GRAVIDADE:
        cor_minima_idx = GRAVIDADE.get("Azul", 4)  # menos grave possível

        for item in dga:
            if (
                isinstance(item, dict)
                and item.get("presente") is True
                and item.get("discriminador") in DISCRIMINADOR_COR
            ):
                cor_disc = DISCRIMINADOR_COR[item["discriminador"]]
                idx = GRAVIDADE[cor_disc]
                if idx < cor_minima_idx:
                    cor_minima_idx = idx

        cor_minima = CLASSIFICACOES_VALIDAS[cor_minima_idx]
        cls_idx = GRAVIDADE.get(cls, 4)

        # A classificação não pode ser MENOS grave que o discriminador mais grave
        # (exceto se over-triage eleva, o que é permitido)
        if cls_idx > cor_minima_idx and not over_triage:
            result.add_error(
                f"Classificação '{cls}' é menos grave que o discriminador "
                f"mais grave ativado (exige no mínimo '{cor_minima}'). "
                f"Isso viola a regra 7 do protocolo."
            )

    # --- Azul não permitido se discriminador Amarelo+ ativo ---
    if cls == "Azul" and isinstance(dga, list):
        for item in dga:
            if (
                isinstance(item, dict)
                and item.get("presente") is True
                and item.get("discriminador") in DISCRIMINADOR_COR
            ):
                result.add_error(
                    f"Classificação Azul inválida: discriminador geral "
                    f"'{item['discriminador']}' está presente "
                    f"(nível {DISCRIMINADOR_COR[item['discriminador']]})."
                )
                break

    # --- Verde é o máximo se nenhum discriminador grave foi ativado ---
    if cls in ("Vermelho", "Laranja", "Amarelo") and isinstance(dga, list):
        algum_grave_presente = any(
            isinstance(item, dict)
            and item.get("presente") is True
            and item.get("discriminador") in DISCRIMINADOR_COR
            for item in dga
        )
        dea = data.get("discriminadores_especificos_ativados", [])
        tem_especifico = isinstance(dea, list) and len(dea) > 0

        if not algum_grave_presente and not tem_especifico and not over_triage:
            result.add_warning(
                f"Classificação '{cls}' sem nenhum discriminador geral ou "
                f"específico ativado. Sem over-triage, o máximo seria Verde."
            )

    # --- Over-triage: justificativa deve explicar a dúvida ---
    if over_triage:
        if not justificativa or len(justificativa.strip()) < 10:
            result.add_error(
                "over_triage_aplicado=true mas justificativa está "
                "ausente ou muito curta. A justificativa deve explicar "
                "qual dúvida levou ao escalonamento."
            )

    # --- Confiança baixa deve ter alertas ---
    if confianca == "baixa":
        if not alertas:
            result.add_warning(
                "confianca='baixa' mas alertas está vazio. "
                "Quando a confiança é baixa, o campo alertas deveria listar "
                "perguntas/informações pendentes para o profissional."
            )

    # --- Termos proibidos na justificativa ---
    if isinstance(justificativa, str):
        just_lower = justificativa.lower()
        for termo in TERMOS_PROIBIDOS_JUSTIFICATIVA:
            if termo in just_lower:
                result.add_warning(
                    f"Justificativa contém termo proibido: '{termo}'. "
                    f"O protocolo proíbe termos como 'provavelmente', "
                    f"'pode ser', 'suspeita de'."
                )


# ──────────────────────────────────────────────────────────────
# Função pública
# ──────────────────────────────────────────────────────────────

def validate_triage_response(data: dict) -> ValidationResult:
    """
    Executa as 3 camadas de validação sobre o dict de triagem.

    Retorna um ValidationResult com errors (bloqueantes) e warnings
    (não bloqueantes mas relevantes para auditoria).
    """
    result = ValidationResult()
    _validate_structural(data, result)
    _validate_consistency(data, result)
    _validate_business_rules(data, result)
    return result
