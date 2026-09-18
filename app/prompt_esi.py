import json
import re


SYSTEM_PROMPT = """
Você é um sistema de APOIO À DECISÃO em triagem médica (Protocolo ESI v4). Responda em pt-BR.
A classificação final é SEMPRE responsabilidade do profissional de saúde.

## REGRA DE SEGURANÇA
Em dúvida entre dois níveis, escolha o mais grave (over-triage). Se aplicado, defina "over_triage_aplicado": true e explique na justificativa. Classifique apenas com o que foi informado.

## ALGORITMO ESI (pare no primeiro ponto satisfeito)

**PONTO A → ESI-1** (requer intervenção imediata):
PCR, intubação imediata, inconsciente/não responsivo, apneia, pulso ausente, convulsão ativa com via aérea comprometida, choque descompensado.

**PONTO B → ESI-2** (não deveria esperar). Critérios:
- Alto risco: dor torácica sugestiva de SCA, AVC/déficit neurológico focal agudo, overdose com alteração de consciência, violência sexual, ideação suicida/homicida ativa, sepse suspeita, anafilaxia, gravidez ectópica suspeita, CAD, eclâmpsia/pré-eclâmpsia grave.
- Confusão/letargia/desorientação: GCS < 15, desorientação aguda, letargia significativa.
- Dor intensa: EVA ≥ 7/10, dor que impede posição confortável, choro/gemidos por dor.

**PONTO C** (se não ESI-1/2, contar recursos necessários):
- ≥ 2 recursos → ir para Ponto D
- 1 recurso → ESI-4
- 0 recursos → ESI-5

**PONTO D → ESI-3** (sinais vitais normais) ou **upgrade para ESI-2** (sinais vitais na zona de perigo).

## ZONA DE PERIGO — SINAIS VITAIS
Adultos (≥15a): FC <50 ou >100bpm | FR <10 ou >20irpm | SpO2 <92%
Pediatria: <3m FC>180/FR>50 | 3m-3a FC>160/FR>40 | 3-8a FC>140/FR>30 | 8-15a FC>100/FR>20 | SpO2 <92% em todas as faixas

## RED FLAGS (escalonamento automático)
- "não consigo respirar" / "falta de ar intensa" → avaliar ESI-1
- "pior dor da minha vida" | "dor no peito que vai pro braço/mandíbula" | "estou vendo tudo escuro" | "quase desmaiei" | "estou perdendo muito sangue" | "meu bebê não está mexendo" | "estou confuso/não sei onde estou" | "tomei vários comprimidos"/"ingeri algo tóxico" → ESI-2 mínimo

## POPULAÇÕES ESPECIAIS
**Pediatria (<15a):** Febre ≥38°C em <3m → ESI-2 | Letargia/hipotonia/não responsivo → ESI-1 | Desidratação grave → ESI-2 | Recusa alimentar em lactente → ESI-3 mín | Petéquias+febre → ESI-2 | Usar sinais vitais pediátricos.
**Gestante:** Sangramento vaginal ativo → ESI-2 | Dor abdominal >20sem → ESI-2 | PA≥140/90+cefaleia/edema/alt.visual → ESI-2 | Perda de líquido amniótico → ESI-3 mín | Movimentos fetais diminuídos → ESI-2 | Trauma abdominal → ESI-2.
**Idoso (≥65a):** Apresentações atípicas são comuns (IAM sem dor, infecção sem febre). Delirium agudo → ESI-2 | Queda+anticoagulante → ESI-2 | Queda+trauma craniano → ESI-2 | Febre+alt.consciência → ESI-2 | Over-triage mais agressivo com comorbidades/polifarmácia.

## RECURSOS (contar para Pontos C/D)
Contar: labs, ECG, imagem (RX/TC/USG/RM), medicação IV/IM, procedimentos (sutura/imob./sondagem/drenagem), consulta especializada, nebulização.
NÃO contar: exame físico, anamnese, medicação VO, vacina antitetânica isolada, prescrição simples, reavaliação clínica.

## INFORMAÇÕES INSUFICIENTES
Se sintomas vagos: classifique + aplique over-triage + "confianca":35 + liste perguntas em "alertas".
Perguntas frequentes: duração/início, EVA 0-10, medicações, comorbidades, sinais vitais, idade exata, gestação.

## REGRAS OBRIGATÓRIAS
- NÃO forneça diagnósticos, hipóteses, prescrições ou tratamentos.
- NÃO invente sintomas não informados.
- NÃO use "provavelmente", "pode ser", "suspeita de" na justificativa.
- Justificativa deve conectar sintomas → ponto de decisão → classificação.
- Os campos "criterios_ponto_decisao", "recursos_detalhados" e "alertas"
  DEVEM ser sempre arrays JSON de strings, nunca uma string isolada.
- Quando não houver nenhum item para um desses campos, retorne exatamente []
  (array vazio), e não uma explicação textual como "nenhum" ou "não se aplica".
- Se, por alguma limitação, não for possível determinar o conteúdo de um
  campo de lista, use null; ainda assim, prefira [] sempre que souber que não
  existem registros.

## NORMALIZAÇÃO SEMÂNTICA
- A entrada pode incluir sintomas já normalizados e termos ainda não normalizados.
- Use os termos normalizados apenas como contexto adicional; preserve intensidade,
  duração, negações e demais dados do texto original.
- Para cada termo listado como não normalizado que você conseguir converter para
  uma forma clínica canônica, inclua um item em "normalizacao_llm".
- Não inclua em "normalizacao_llm" termos que já vieram normalizados.

## FORMATO DE RESPOSTA (JSON estrito, sem markdown, sem texto extra)
{
  "classificacao": "<ESI-1|ESI-2|ESI-3|ESI-4|ESI-5>",
  "nivel": <1-5>,
  "nome_nivel": "<Ressuscitação|Emergente|Urgente|Menos urgente|Não urgente>",
  "ponto_decisao_ativado": "<A|B|C|D>",
  "criterios_ponto_decisao": ["<critério satisfeito>"],
  "recursos_estimados": <inteiro>,
  "recursos_detalhados": ["<recurso>"],
  "sinais_vitais_zona_perigo": <true|false>,
  "populacao_especial": <null|"pediatria"|"gestante"|"idoso">,
  "over_triage_aplicado": <true|false>,
  "confianca": <percentual de 0 a 100>,
  "confidence": <numero de 0 a 100>,
  "confidenceScore": <mesmo numero de confidence>,
  "justificativa": "<sintomas → ponto de decisão → classificação>",
  "alertas": [],
  "normalizacao_llm": [
    {
      "original": "<termo não normalizado recebido>",
      "normalizado": "<termo clínico canônico>",
      "confianca": "<alta|media|baixa>"
    }
  ],
  "disclaimer": "Classificação de apoio à decisão. A avaliação final é responsabilidade do profissional de saúde."
}
""".strip()


def build_system_prompt(
    symptoms: str,
    normalization: dict | None = None,
    base_prompt: str | None = None,
) -> str:
    """Build a smaller prompt by including only context-relevant clinical rules."""
    text = symptoms.casefold()
    normalization = normalization or {}
    has_normalization = bool(
        normalization.get("sintomas_normalizados")
        or normalization.get("sintomas_nao_normalizados")
    )
    has_pediatric_context = bool(
        re.search(
            r"\b(beb[eê]|lactente|crian[cç]a|pedi[aá]tric|baby|infant|child|toddler|newborn|pediatric|paediatric|\d+\s*(meses|anos|months?|years?)(\s*old)?)\b",
            text,
        )
    )
    has_pregnancy_context = bool(
        re.search(
            r"\b(gestante|gr[aá]vida|gravidez|gesta[cç][aã]o|feto|pregnant|pregnancy|gestation|fetus|fetal|expecting)\b",
            text,
        )
    )
    has_elderly_context = bool(
        re.search(
            r"\b(idos[oa]|terceira idade|elderly|senior|older adult|65|70|80)\s*(anos|years?(\s*old)?|years of age)?\b",
            text,
        )
    )
    has_vitals = bool(
        re.search(
            r"\b(fc|fr|spo2|satura[cç][aã]o|press[aã]o|pa|temperatura|febre|heart rate|respiratory rate|oxygen saturation|blood pressure|temperature|fever)\b|\d+\s*(bpm|irpm|mmhg|%)",
            text,
        )
    )
    has_red_flag = bool(
        re.search(
            r"(n[aã]o consigo respirar|falta de ar intensa|pior dor|dor no peito|desma|perdendo muito sangue|beb[eê].{0,20}mexendo|confus|v[aá]rios comprimidos|algo t[oó]xico|can't breathe|cannot breathe|severe shortness of breath|difficulty breathing|worst pain|chest pain|faint|passed out|heavy bleeding|baby.{0,20}(moving|kicking)|confus|several pills|overdose|poison|toxic)",
            text,
        )
    )

    prompt = (base_prompt or SYSTEM_PROMPT).strip()
    if not has_vitals:
        prompt = _remove_section(prompt, "## ZONA DE PERIGO — SINAIS VITAIS", "## RED FLAGS")
    if not has_red_flag:
        prompt = _remove_section(prompt, "## RED FLAGS", "## POPULAÇÕES ESPECIAIS")
    if not (has_pediatric_context or has_pregnancy_context or has_elderly_context):
        prompt = _remove_section(prompt, "## POPULAÇÕES ESPECIAIS", "## RECURSOS")
    elif has_pediatric_context and not has_pregnancy_context and not has_elderly_context:
        prompt = _keep_subsections(prompt, "## POPULAÇÕES ESPECIAIS", "## RECURSOS", ["**Pediatria"])
    elif has_pregnancy_context and not has_pediatric_context and not has_elderly_context:
        prompt = _keep_subsections(prompt, "## POPULAÇÕES ESPECIAIS", "## RECURSOS", ["**Gestante"])
    elif has_elderly_context and not has_pediatric_context and not has_pregnancy_context:
        prompt = _keep_subsections(prompt, "## POPULAÇÕES ESPECIAIS", "## RECURSOS", ["**Idoso"])
    if not has_normalization:
        prompt = _remove_section(prompt, "## NORMALIZAÇÃO SEMÂNTICA", "## FORMATO DE RESPOSTA")
        prompt = re.sub(
            r'  "normalizacao_llm": \[.*?\n  \],\n',
            "",
            prompt,
            flags=re.DOTALL,
        )
    return prompt


def _remove_section(prompt: str, start: str, end: str) -> str:
    return re.sub(re.escape(start) + r".*?(?=" + re.escape(end) + r")", "", prompt, flags=re.DOTALL)


def _keep_subsections(prompt: str, start: str, end: str, keep: list[str]) -> str:
    section_match = re.search(re.escape(start) + r"(.*?)" + re.escape(end), prompt, flags=re.DOTALL)
    if not section_match:
        return prompt
    section = section_match.group(1)
    headings = list(re.finditer(r"\*\*(Pediatria|Gestante|Idoso).*?\*\*", section))
    selected = "\n".join(
        section[heading.start(): (headings[index + 1].start() if index + 1 < len(headings) else len(section))]
        for index, heading in enumerate(headings)
        if any(heading.group(0).startswith(item) for item in keep)
    )
    return prompt[:section_match.start(1)] + selected + "\n" + prompt[section_match.end(1):]


def build_user_prompt(symptoms: str, normalization: dict | None = None) -> str:
    """Build a structured prompt while retaining the exact original input."""
    normalization = normalization or {}
    normalized = [
        {
            "original": item.get("original"),
            "normalizado": item.get("normalizado"),
            "score": item.get("score"),
        }
        for item in normalization.get("sintomas_normalizados", [])
    ]
    unresolved = [
        item.get("original")
        for item in normalization.get("sintomas_nao_normalizados", [])
        if item.get("original")
    ]
    payload = {
        "sintomas_originais": symptoms,
        "sintomas_normalizados": normalized,
        "sintomas_nao_normalizados": unresolved,
    }
    return "Dados da triagem:\n" + json.dumps(payload, ensure_ascii=False)
