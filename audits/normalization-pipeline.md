# Revisão do pipeline de normalização

Escopo: entrada de triagem, extração, Qdrant, tabela verdade PostgreSQL,
contexto da IA, leitura de `normalizacao_llm` e persistência de candidatos.

## Achados e correções

| Importância | Achado | Correção |
|---|---|---|
| 9/10 | `NormalizationService._normalize_single_symptom` aceitava `termo_canonico` do Qdrant sem consultar a tabela verdade; até o próprio texto podia virar normalizado quando faltavam dados. | Consultar `PostgresService.get_sintoma_by_id`, que exige sintoma ativo. Resultado sem confirmação permanece pendente. |
| 8/10 | `_normalize_safely` devolvia listas vazias se a inicialização falhasse; `extract_llm_normalizations` descartava todas as sugestões sem termos pendentes. | `normalization_pipeline.normalize_safely` preserva frases extraídas como pendentes no fallback. |
| 8/10 | `_save_candidates_safely` dependia da inicialização de Qdrant e ignorava o retorno `None` do INSERT. | `normalization_pipeline.save_candidates` acessa Postgres diretamente, verifica cada ID e continua após falha individual. |
| 7/10 | `ollama_service.classify_symptoms` não fazia busca nem persistência. | Groq e Ollama compartilham preparação e conclusão do pipeline. O endpoint de `main.py` continua selecionando Groq. |
| 7/10 | Itens omitidos pela IA e gravações falhas não eram informados na resposta. | `complete_normalization` inclui `normalizacoes_pendentes_llm` e `persistencia_base_candidata` em `normalizacao_resultado`, além de alertas. |

## Fluxo resultante

Texto → `NERService.extract_symptoms` → E5 remoto/Qdrant → confirmação do ID
em `falai_doutor_normalizacao.sintomas` → JSON com texto original, normalizados
e pendentes → IA → validação de `normalizacao_llm` contra os pendentes → INSERT
em `falai_doutor_normalizacao.base_candidata`, com `origem=llm`, `status=pendente`,
score da busca quando disponível e confiança da sugestão.

Não se promovem sugestões automaticamente à tabela verdade. A coluna SQL
`score_ollama_confianca` permanece com o nome existente; o contrato da IA usa
somente `normalizacao_llm`.

## Limitações verificadas

- **8/10 — extração heurística:** `NERService` separa e limpa frases; não é um
  modelo clínico de reconhecimento de entidades. Mantém intensidade/contexto nas
  frases, pode incluir trechos sem sintomas e descarta frases acima de 160 caracteres.
  A qualidade precisa de avaliação com relatos representativos antes de substituir
  a heurística por um extrator clínico. O texto completo sempre acompanha a IA.
- **7/10 — disponibilidade:** falha no Postgres produz alerta e lista de falhas;
  não há fila durável ou reprocessamento automático. A resposta de triagem continua
  disponível, mas não equivale a confirmação de gravação dos candidatos.
- **7/10 — resposta incompleta da IA:** o pipeline identifica termos omitidos,
  mas não inventa normalizações nem repete automaticamente a chamada.
- **Não verificado:** conectividade, permissões, conteúdo e compatibilidade do
  índice Qdrant e do schema PostgreSQL reais. São necessários Qdrant Cloud
  Inference habilitado, coleção populada com `sintoma_id` válido, modelo/dimensão
  compatíveis com a indexação, credenciais do provedor e DSN com SELECT/INSERT.

## Validação

27 testes passaram, incluindo o fluxo completo Groq e Ollama com serviços externos
simulados, confirmação no Postgres apesar de payload antigo no Qdrant, ID ausente
ou não encontrado, Qdrant indisponível, INSERT retornando None ou lançando exceção,
e resposta parcial da IA. Nenhum banco real foi alterado durante os testes.
