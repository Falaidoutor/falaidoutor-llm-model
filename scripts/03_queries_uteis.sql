-- ================================================================
-- QUERIES ÚTEIS: Consultas para gerenciar dados
-- Database: falai
-- ================================================================

-- ================================================================
-- 1. VERIFICAR SAÚDE DO BANCO
-- ================================================================

-- Total de sintomas ativos
SELECT COUNT(*) as total_sintomas_ativos 
FROM falai_doutor_normalizacao.sintomas 
WHERE ativo = TRUE;

-- Total de sinonimos aprovados
SELECT COUNT(*) as total_sinonimos_aprovados 
FROM falai_doutor_normalizacao.sinonimos 
WHERE aprovado = TRUE;

-- Sinonimos por sintoma
SELECT 
    s.termo as sintoma,
    COUNT(sin.id) as quantidade_sinonimos
FROM falai_doutor_normalizacao.sintomas s
LEFT JOIN falai_doutor_normalizacao.sinonimos sin ON s.id = sin.sintoma_id AND sin.aprovado = TRUE
WHERE s.ativo = TRUE
GROUP BY s.id, s.termo
ORDER BY quantidade_sinonimos DESC;


-- ================================================================
-- 2. BUSCAR SINONIMOS
-- ================================================================

-- Encontrar todos os sinonimos de um sintoma
SELECT 
    sin.id,
    sin.termo,
    s.termo as sintoma_canonico,
    sin.aprovado,
    sin.origem,
    sin.criado_em
FROM falai_doutor_normalizacao.sinonimos sin
JOIN falai_doutor_normalizacao.sintomas s ON sin.sintoma_id = s.id
WHERE s.termo = 'Dor Torácica'
ORDER BY sin.aprovado DESC, sin.criado_em DESC;

-- Procurar sinonimos por padrão
SELECT DISTINCT
    sin.id,
    sin.termo,
    s.termo as sintoma_canonico,
    sin.aprovado
FROM falai_doutor_normalizacao.sinonimos sin
JOIN falai_doutor_normalizacao.sintomas s ON sin.sintoma_id = s.id
WHERE sin.termo ILIKE '%dor%'
LIMIT 20;


-- ================================================================
-- 3. GERENCIAR BASE_CANDIDATA
-- ================================================================

-- Ver candidatos pendentes
SELECT 
    id,
    input_original,
    normalizado_sugerido,
    score_e5,
    score_ollama_confianca,
    origem,
    criado_em
FROM falai_doutor_normalizacao.base_candidata
WHERE status = 'pendente'
ORDER BY criado_em DESC
LIMIT 20;

-- Contar pendentes por origem
SELECT 
    origem,
    status,
    COUNT(*) as quantidade
FROM falai_doutor_normalizacao.base_candidata
GROUP BY origem, status
ORDER BY quantidade DESC;

-- Candidatos com score E5 baixo (< 0.65)
SELECT 
    id,
    input_original,
    normalizado_sugerido,
    score_e5,
    status,
    criado_em
FROM falai_doutor_normalizacao.base_candidata
WHERE score_e5 IS NOT NULL AND score_e5 < 0.65
ORDER BY score_e5 ASC
LIMIT 20;


-- ================================================================
-- 4. GERENCIAR AUDITORIA
-- ================================================================

-- Ver decisões recentes
SELECT 
    a.id,
    bc.input_original,
    bc.normalizado_sugerido,
    a.decisao,
    a.auditado_por,
    a.criado_em
FROM falai_doutor_normalizacao.auditoria a
JOIN falai_doutor_normalizacao.base_candidata bc ON a.candidato_id = bc.id
ORDER BY a.criado_em DESC
LIMIT 20;

-- Taxa de aprovação
SELECT 
    decisao,
    COUNT(*) as quantidade,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentual
FROM falai_doutor_normalizacao.auditoria
GROUP BY decisao
ORDER BY quantidade DESC;

-- Por auditor
SELECT 
    auditado_por,
    decisao,
    COUNT(*) as quantidade
FROM falai_doutor_normalizacao.auditoria
GROUP BY auditado_por, decisao
ORDER BY auditado_por, quantidade DESC;


-- ================================================================
-- 5. ANÁLISE DE LOGS (INPUTS/OUTPUTS)
-- ================================================================

-- Ver classificações recentes
SELECT 
    i.id,
    i.texto_original,
    o.classificacao,
    o.confianca,
    o.tempo_processamento_ms,
    o.criado_em
FROM falai_doutor_normalizacao.inputs i
LEFT JOIN falai_doutor_normalizacao.outputs o ON i.id = o.input_id
ORDER BY o.criado_em DESC
LIMIT 20;

-- Taxa de classificação por tipo
SELECT 
    o.classificacao,
    o.confianca,
    COUNT(*) as quantidade,
    ROUND(AVG(o.tempo_processamento_ms), 2) as tempo_medio_ms
FROM falai_doutor_normalizacao.outputs o
GROUP BY o.classificacao, o.confianca
ORDER BY quantidade DESC;

-- Distribuição de confiança
SELECT 
    confianca,
    COUNT(*) as quantidade,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentual
FROM falai_doutor_normalizacao.outputs
GROUP BY confianca
ORDER BY quantidade DESC;


-- ================================================================
-- 6. MANUTENÇÃO
-- ================================================================

-- Deletar candidatos rejeitados há mais de 30 dias
-- (CUIDADO - comentado por segurança)
-- DELETE FROM falai_doutor_normalizacao.base_candidata 
-- WHERE status = 'rejeitado' 
-- AND criado_em < NOW() - INTERVAL '30 days';

-- Arquivar logs antigos
-- DELETE FROM falai_doutor_normalizacao.inputs 
-- WHERE criado_em < NOW() - INTERVAL '90 days';

-- Ver tamanho das tabelas
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as tamanho
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;


-- ================================================================
-- 7. VALIDAÇÃO DE INTEGRIDADE
-- ================================================================

-- Sinonimos órfãos (sintoma deletado)
SELECT 
    s.id,
    s.termo,
    s.sintoma_id,
    'ÓRFÃO' as status
FROM falai_doutor_normalizacao.sinonimos s
LEFT JOIN falai_doutor_normalizacao.sintomas sin ON s.sintoma_id = sin.id
WHERE sin.id IS NULL;

-- Sintomas sem sinonimos
SELECT 
    s.id,
    s.termo,
    COUNT(sin.id) as quantidade_sinonimos
FROM falai_doutor_normalizacao.sintomas s
LEFT JOIN falai_doutor_normalizacao.sinonimos sin ON s.id = sin.sintoma_id
WHERE s.ativo = TRUE
GROUP BY s.id, s.termo
HAVING COUNT(sin.id) = 0;

-- CID-10 não mapeadas para sintomas
SELECT 
    c.codigo,
    c.descricao,
    COUNT(sc.id) as quantidade_sintomas
FROM falai_doutor_normalizacao.cid10 c
LEFT JOIN falai_doutor_normalizacao.sintoma_cid10 sc ON c.codigo = sc.cid_codigo
GROUP BY c.codigo, c.descricao
HAVING COUNT(sc.id) = 0;


-- ================================================================
-- 8. RELATÓRIOS
-- ================================================================

-- Relatório diário de atividade
SELECT 
    DATE(o.criado_em) as data,
    COUNT(DISTINCT i.id) as total_requisicoes,
    COUNT(DISTINCT o.id) as total_classificacoes,
    COUNT(DISTINCT CASE WHEN o.confianca = 'alta' THEN o.id END) as alta_confianca,
    COUNT(DISTINCT CASE WHEN o.confianca = 'media' THEN o.id END) as media_confianca,
    COUNT(DISTINCT CASE WHEN o.confianca = 'baixa' THEN o.id END) as baixa_confianca,
    ROUND(AVG(o.tempo_processamento_ms), 2) as tempo_medio_ms
FROM falai_doutor_normalizacao.inputs i
LEFT JOIN falai_doutor_normalizacao.outputs o ON i.id = o.input_id
WHERE o.criado_em IS NOT NULL
GROUP BY DATE(o.criado_em)
ORDER BY data DESC
LIMIT 30;

-- Sintomas mais usados
SELECT 
    s.termo,
    s.categoria,
    COUNT(DISTINCT bc.id) as vezes_normalizado,
    ROUND(AVG(bc.score_e5), 3) as score_medio,
    COUNT(DISTINCT CASE WHEN bc.status = 'aprovado' THEN bc.id END) as aprovados
FROM falai_doutor_normalizacao.sintomas s
LEFT JOIN falai_doutor_normalizacao.base_candidata bc ON 
    (bc.normalizado_sugerido = s.termo OR bc.sintoma_id = s.id)
GROUP BY s.id, s.termo, s.categoria
ORDER BY vezes_normalizado DESC
LIMIT 30;
