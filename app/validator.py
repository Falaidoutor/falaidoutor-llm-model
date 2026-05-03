"""
Validador de respostas de triagem ESI (Emergency Severity Index).

Executa três camadas de validação:
  1. Estrutural — campos obrigatórios, tipos e valores permitidos
  2. Consistência lógica — nível ↔ nome ↔ ponto de decisão
  3. Regras de negócio — over-triage, confiança, recursos
"""

from dataclasses import dataclass, field

# ──────────────────────────────────────────────────────────────
# Constantes extraídas do Protocolo ESI (prompt_esi.py)
# ──────────────────────────────────────────────────────────────

CLASSIFICACOES_VALIDAS = ("ESI-1", "ESI-2", "ESI-3", "ESI-4", "ESI-5")

NIVEIS_VALIDOS = (1, 2, 3, 4, 5)

NOMES_NIVEL_VALIDOS = (
    "Ressuscitação",
    "Emergente",
    "Urgente",
    "Menos urgente",
    "Não urgente",
)

PONTOS_DECISAO_VALIDOS = ("A", "B", "C", "D")

CONFIANCAS_VALIDAS = ("alta", "media", "baixa")

POPULACOES_VALIDAS = (None, "pediatria", "gestante", "idoso")

DISCLAIMER_ESPERADO = (
    "Classificação de apoio à decisão. "
    "A avaliação final é responsabilidade do profissional de saúde."
)

# Mapeamento nível ↔ nome ↔ classificação
NIVEL_NOME = {
    1: "Ressuscitação",
    2: "Emergente",
    3: "Urgente",
    4: "Menos urgente",
    5: "Não urgente",
}

NIVEL_CLASSIFICACAO = {
    1: "ESI-1",
    2: "ESI-2",
    3: "ESI-3",
    4: "ESI-4",
    5: "ESI-5",
}

# Ponto de decisão esperado por nível
NIVEL_PONTO_DECISAO = {
    1: ("A",),
    2: ("B", "D"),  # D pode upgradar para ESI-2
    3: ("C", "D"),
    4: ("C",),
    5: ("C",),
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

    # --- nivel ---
    nivel = data.get("nivel")
    if not isinstance(nivel, int):
        result.add_error(
            f"nivel deve ser int, recebido {type(nivel).__name__}."
        )
    elif nivel not in NIVEIS_VALIDOS:
        result.add_error(
            f"nivel '{nivel}' inválido. Valores aceitos: {NIVEIS_VALIDOS}"
        )

    # --- nome_nivel ---
    nome = data.get("nome_nivel")
    if nome not in NOMES_NIVEL_VALIDOS:
        result.add_error(
            f"nome_nivel '{nome}' inválido. "
            f"Valores aceitos: {NOMES_NIVEL_VALIDOS}"
        )

    # --- ponto_decisao_ativado ---
    ponto = data.get("ponto_decisao_ativado")
    if ponto not in PONTOS_DECISAO_VALIDOS:
        result.add_error(
            f"ponto_decisao_ativado '{ponto}' inválido. "
            f"Valores aceitos: {PONTOS_DECISAO_VALIDOS}"
        )

    # --- criterios_ponto_decisao ---
    criterios = data.get("criterios_ponto_decisao")
    if not isinstance(criterios, list):
        result.add_error("criterios_ponto_decisao deve ser uma lista.")
    elif len(criterios) == 0:
        result.add_warning(
            "criterios_ponto_decisao está vazio. "
            "Deveria listar os critérios satisfeitos."
        )

    # --- recursos_estimados ---
    recursos = data.get("recursos_estimados")
    if not isinstance(recursos, int):
        result.add_error(
            f"recursos_estimados deve ser int, recebido {type(recursos).__name__}."
        )
    elif recursos < 0:
        result.add_error("recursos_estimados não pode ser negativo.")

    # --- recursos_detalhados ---
    rec_det = data.get("recursos_detalhados")
    if not isinstance(rec_det, list):
        result.add_error("recursos_detalhados deve ser uma lista.")

    # --- sinais_vitais_zona_perigo ---
    sv = data.get("sinais_vitais_zona_perigo")
    if not isinstance(sv, bool):
        result.add_error(
            f"sinais_vitais_zona_perigo deve ser bool, recebido {type(sv).__name__}."
        )

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
    """Nível ↔ classificação ↔ nome_nivel devem ser coerentes entre si."""

    nivel = data.get("nivel")
    cls = data.get("classificacao")
    nome = data.get("nome_nivel")
    ponto = data.get("ponto_decisao_ativado")

    if not isinstance(nivel, int) or nivel not in NIVEIS_VALIDOS:
        return  # já reportado na validação estrutural

    # Nível → classificação esperada
    cls_esperada = NIVEL_CLASSIFICACAO[nivel]
    if cls != cls_esperada:
        result.add_error(
            f"Inconsistência: nivel {nivel} requer classificacao "
            f"'{cls_esperada}', mas recebido '{cls}'."
        )

    # Nível → nome esperado
    nome_esperado = NIVEL_NOME[nivel]
    if nome != nome_esperado:
        result.add_error(
            f"Inconsistência: nivel {nivel} requer nome_nivel "
            f"'{nome_esperado}', mas recebido '{nome}'."
        )

    # Nível → ponto de decisão compatível
    if ponto in PONTOS_DECISAO_VALIDOS:
        pontos_esperados = NIVEL_PONTO_DECISAO.get(nivel, ())
        if ponto not in pontos_esperados:
            result.add_warning(
                f"ponto_decisao_ativado '{ponto}' é incomum para "
                f"nivel {nivel}. Esperado: {pontos_esperados}."
            )


# ──────────────────────────────────────────────────────────────
# 3. Validação de regras de negócio
# ──────────────────────────────────────────────────────────────

def _validate_business_rules(data: dict, result: ValidationResult) -> None:
    """Over-triage, confiança, recursos e regras do protocolo ESI."""

    nivel = data.get("nivel")
    recursos = data.get("recursos_estimados", 0)
    rec_det = data.get("recursos_detalhados", [])
    over_triage = data.get("over_triage_aplicado", False)
    confianca = data.get("confianca")
    justificativa = data.get("justificativa", "")
    alertas = data.get("alertas") or []
    sv_perigo = data.get("sinais_vitais_zona_perigo", False)

    if not isinstance(nivel, int) or nivel not in NIVEIS_VALIDOS:
        return

    # --- ESI-4 deve ter exatamente 1 recurso ---
    if nivel == 4 and isinstance(recursos, int) and recursos != 1:
        result.add_warning(
            f"ESI-4 indica 1 recurso necessário, mas "
            f"recursos_estimados={recursos}."
        )

    # --- ESI-5 deve ter 0 recursos ---
    if nivel == 5 and isinstance(recursos, int) and recursos != 0:
        result.add_warning(
            f"ESI-5 indica 0 recursos necessários, mas "
            f"recursos_estimados={recursos}."
        )

    # --- ESI-3 deve ter >= 2 recursos ---
    if nivel == 3 and isinstance(recursos, int) and recursos < 2:
        result.add_warning(
            f"ESI-3 indica ≥ 2 recursos necessários, mas "
            f"recursos_estimados={recursos}."
        )

    # --- Recursos detalhados devem ser coerentes com estimados ---
    if isinstance(recursos, int) and isinstance(rec_det, list):
        if len(rec_det) != recursos and nivel in (3, 4, 5):
            result.add_warning(
                f"recursos_estimados={recursos} mas "
                f"recursos_detalhados tem {len(rec_det)} itens."
            )

    # --- Sinais vitais em zona de perigo + ESI-3 → deveria considerar upgrade ---
    if sv_perigo and nivel == 3 and not over_triage:
        result.add_warning(
            "sinais_vitais_zona_perigo=true com ESI-3. "
            "O protocolo recomenda considerar upgrade para ESI-2."
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
    Executa as 3 camadas de validação sobre o dict de triagem ESI.

    Retorna um ValidationResult com errors (bloqueantes) e warnings
    (não bloqueantes mas relevantes para auditoria).
    """
    result = ValidationResult()
    _validate_structural(data, result)
    _validate_consistency(data, result)
    _validate_business_rules(data, result)
    return result
