-- ================================================================
-- SCHEMA: Normalização Semântica com Qdrant + E5 + NER
-- Database: falai
-- Description: Estrutura completa para geração de embeddings e sintomas
-- ================================================================

BEGIN;

-- ================================================================
-- CRIAR SCHEMA
-- ================================================================

CREATE SCHEMA IF NOT EXISTS falai_doutor_normalizacao;


-- ================================================================
-- EXTENSÕES (opcional)
-- ================================================================

-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


-- ================================================================
-- TABELA: SINTOMAS (conceitos canônicos)
-- ================================================================
-- Termos médicos canônicos/normalizados que serão indexados no Qdrant

CREATE TABLE IF NOT EXISTS falai_doutor_normalizacao.sintomas (
    id SERIAL PRIMARY KEY,
    termo TEXT NOT NULL UNIQUE,
    categoria TEXT,                       -- ex: "cardiovascular", "respiratório"
    descricao TEXT,                       -- descrição adicional
    ativo BOOLEAN DEFAULT TRUE,
    criado_em TIMESTAMP DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sintomas_termo ON falai_doutor_normalizacao.sintomas(termo);
CREATE INDEX IF NOT EXISTS idx_sintomas_categoria ON falai_doutor_normalizacao.sintomas(categoria);
CREATE INDEX IF NOT EXISTS idx_sintomas_ativo ON falai_doutor_normalizacao.sintomas(ativo);


-- ================================================================
-- TABELA: SINONIMOS (linguagem do usuário)
-- ================================================================
-- Variações de termos que o usuário pode usar; apontam para sintomas canônicos

CREATE TABLE IF NOT EXISTS falai_doutor_normalizacao.sinonimos (
    id SERIAL PRIMARY KEY,
    sintoma_id INTEGER NOT NULL REFERENCES falai_doutor_normalizacao.sintomas(id) ON DELETE CASCADE,
    termo TEXT NOT NULL,                  -- ex: "aperto no coração"
    origem TEXT,                          -- "manual", "llm", "usuario"
    aprovado BOOLEAN DEFAULT FALSE,       -- controle de qualidade
    criado_em TIMESTAMP DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_sinonimos_termo_sintoma_id 
    ON falai_doutor_normalizacao.sinonimos(termo, sintoma_id);
CREATE INDEX IF NOT EXISTS idx_sinonimos_termo ON falai_doutor_normalizacao.sinonimos(termo);
CREATE INDEX IF NOT EXISTS idx_sinonimos_sintoma_id ON falai_doutor_normalizacao.sinonimos(sintoma_id);
CREATE INDEX IF NOT EXISTS idx_sinonimos_aprovado ON falai_doutor_normalizacao.sinonimos(aprovado);


-- ================================================================
-- TABELA: CID-10
-- ================================================================
-- Classificação Internacional de Doenças (CID-10)

CREATE TABLE IF NOT EXISTS falai_doutor_normalizacao.cid10 (
    codigo TEXT PRIMARY KEY,              -- ex: "R07" (dor torácica)
    descricao TEXT NOT NULL,
    subcategorias TEXT,                   -- ex: "R07.1, R07.2, R07.9"
    criado_em TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cid10_descricao ON falai_doutor_normalizacao.cid10(descricao);


-- ================================================================
-- TABELA: RELAÇÃO SINTOMA ↔ CID-10
-- ================================================================
-- Many-to-many: um sintoma pode mapear para múltiplos códigos CID-10

CREATE TABLE IF NOT EXISTS falai_doutor_normalizacao.sintoma_cid10 (
    id SERIAL PRIMARY KEY,
    sintoma_id INTEGER NOT NULL REFERENCES falai_doutor_normalizacao.sintomas(id) ON DELETE CASCADE,
    cid_codigo TEXT NOT NULL REFERENCES falai_doutor_normalizacao.cid10(codigo) ON DELETE RESTRICT,
    confianca FLOAT DEFAULT 1.0,          -- 0.0-1.0, quanto confiável é o mapeamento
    criado_em TIMESTAMP DEFAULT NOW(),
    UNIQUE(sintoma_id, cid_codigo)
);

CREATE INDEX IF NOT EXISTS idx_sintoma_cid10_sintoma_id ON falai_doutor_normalizacao.sintoma_cid10(sintoma_id);
CREATE INDEX IF NOT EXISTS idx_sintoma_cid10_cid_codigo ON falai_doutor_normalizacao.sintoma_cid10(cid_codigo);


-- ================================================================
-- TABELA: INPUTS (logs do sistema)
-- ================================================================
-- Registro de todas as entradas/requisições processadas

CREATE TABLE IF NOT EXISTS falai_doutor_normalizacao.inputs (
    id SERIAL PRIMARY KEY,
    texto_original TEXT NOT NULL,         -- texto bruto do usuário
    hash_input TEXT,                      -- SHA256 para deduplicação
    modelo TEXT DEFAULT 'qwen3',          -- modelo LLM usado
    versao_prompt TEXT,                   -- versão do prompt MTS
    versao_vocabulario TEXT,              -- versão do vocabulário de sintomas
    ip_origem TEXT,                       -- IP do cliente (se aplicável)
    criado_em TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_inputs_hash ON falai_doutor_normalizacao.inputs(hash_input);
CREATE INDEX IF NOT EXISTS idx_inputs_criado_em ON falai_doutor_normalizacao.inputs(criado_em);


-- ================================================================
-- TABELA: OUTPUTS (resultado da classificação)
-- ================================================================
-- Saída completa estruturada do classificador MTS

CREATE TABLE IF NOT EXISTS falai_doutor_normalizacao.outputs (
    id SERIAL PRIMARY KEY,
    input_id INTEGER NOT NULL REFERENCES falai_doutor_normalizacao.inputs(id) ON DELETE CASCADE,
    json_resultado JSONB NOT NULL,        -- resposta TriageResponse completa
    classificacao TEXT,                   -- para busca rápida: Vermelho|Laranja|Amarelo|Verde|Azul
    tempo_processamento_ms INTEGER,       -- latência em ms
    confianca TEXT,                       -- alta|media|baixa
    criado_em TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_outputs_input_id ON falai_doutor_normalizacao.outputs(input_id);
CREATE INDEX IF NOT EXISTS idx_outputs_classificacao ON falai_doutor_normalizacao.outputs(classificacao);
CREATE INDEX IF NOT EXISTS idx_outputs_confianca ON falai_doutor_normalizacao.outputs(confianca);
CREATE INDEX IF NOT EXISTS idx_outputs_criado_em ON falai_doutor_normalizacao.outputs(criado_em);


-- ================================================================
-- TABELA: BASE_CANDIDATA (aprendizado)
-- ================================================================
-- Termos normalizados pelo LLM que aguardam auditoria
-- Retroalimentação para melhorar o vocabulário

CREATE TABLE IF NOT EXISTS falai_doutor_normalizacao.base_candidata (
    id SERIAL PRIMARY KEY,
    input_original TEXT NOT NULL,         -- termo original do usuário
    normalizado_sugerido TEXT NOT NULL,   -- normalização sugerida
    sintoma_id INTEGER,                   -- preenchido após validação
    score_e5 FLOAT,                       -- score de similaridade E5
    score_ollama_confianca TEXT,          -- confiança do Ollama
    origem TEXT DEFAULT 'llm',            -- "llm", "usuario", "admin"
    status TEXT DEFAULT 'pendente',       -- pendente, aprovado, rejeitado
    revisado BOOLEAN DEFAULT FALSE,       -- marcado como review?
    criado_em TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (sintoma_id) REFERENCES falai_doutor_normalizacao.sintomas(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_base_candidata_status ON falai_doutor_normalizacao.base_candidata(status);
CREATE INDEX IF NOT EXISTS idx_base_candidata_sintoma_id ON falai_doutor_normalizacao.base_candidata(sintoma_id);
CREATE INDEX IF NOT EXISTS idx_base_candidata_criado_em ON falai_doutor_normalizacao.base_candidata(criado_em);
CREATE INDEX IF NOT EXISTS idx_base_candidata_score_e5 ON falai_doutor_normalizacao.base_candidata(score_e5);


-- ================================================================
-- TABELA: AUDITORIA (rastreamento de decisões)
-- ================================================================
-- Registro de aprovações, rejeições e correções

CREATE TABLE IF NOT EXISTS falai_doutor_normalizacao.auditoria (
    id SERIAL PRIMARY KEY,
    candidato_id INTEGER NOT NULL REFERENCES falai_doutor_normalizacao.base_candidata(id) ON DELETE CASCADE,
    decisao TEXT NOT NULL,                -- "aprovar", "rejeitar", "corrigir"
    correcao TEXT,                        -- se "corrigir", qual foi a correção?
    justificativa TEXT,                   -- motivo da decisão
    auditado_por TEXT,                    -- "llm", "humano", "admin"
    ip_auditoria TEXT,                    -- IP de quem fez auditoria
    criado_em TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_auditoria_candidato_id ON falai_doutor_normalizacao.auditoria(candidato_id);
CREATE INDEX IF NOT EXISTS idx_auditoria_decisao ON falai_doutor_normalizacao.auditoria(decisao);
CREATE INDEX IF NOT EXISTS idx_auditoria_auditado_por ON falai_doutor_normalizacao.auditoria(auditado_por);
CREATE INDEX IF NOT EXISTS idx_auditoria_criado_em ON falai_doutor_normalizacao.auditoria(criado_em);


-- ================================================================
-- TRIGGERS (opcional)
-- ================================================================
-- Auto-atualizar timestamps

CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_sintomas_timestamp
BEFORE UPDATE ON falai_doutor_normalizacao.sintomas
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trigger_sinonimos_timestamp
BEFORE UPDATE ON falai_doutor_normalizacao.sinonimos
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();


-- ================================================================
-- VIEWS (opcional)
-- ================================================================
-- Vista para facilitar queries comuns

CREATE OR REPLACE VIEW falai_doutor_normalizacao.vw_sinonimos_normalizacao AS
SELECT 
    s.id as sinonimo_id,
    s.termo as termo_sinonimo,
    s.sintoma_id,
    sin.termo as termo_canonico,
    sin.categoria,
    s.aprovado,
    s.origem,
    s.criado_em
FROM falai_doutor_normalizacao.sinonimos s
JOIN falai_doutor_normalizacao.sintomas sin ON s.sintoma_id = sin.id
WHERE sin.ativo = TRUE AND s.aprovado = TRUE;


CREATE OR REPLACE VIEW falai_doutor_normalizacao.vw_base_candidata_pendentes AS
SELECT 
    bc.id,
    bc.input_original,
    bc.normalizado_sugerido,
    bc.score_e5,
    bc.score_ollama_confianca,
    bc.origem,
    COUNT(a.id) as auditoria_count
FROM falai_doutor_normalizacao.base_candidata bc
LEFT JOIN falai_doutor_normalizacao.auditoria a ON bc.id = a.candidato_id
WHERE bc.status = 'pendente'
GROUP BY bc.id
ORDER BY bc.criado_em DESC;


-- ================================================================
-- COMENTÁRIOS
-- ================================================================
-- Documentar estrutura

COMMENT ON TABLE falai_doutor_normalizacao.sintomas IS 'Termos médicos canônicos que serão indexados no Qdrant com embeddings E5';
COMMENT ON TABLE falai_doutor_normalizacao.sinonimos IS 'Variações de termos (como usuários falam) que apontam a sintomas canônicos';
COMMENT ON TABLE falai_doutor_normalizacao.base_candidata IS 'Candidatos aguardando auditoria para melhoria contínua do vocabulário';
COMMENT ON TABLE falai_doutor_normalizacao.auditoria IS 'Rastreamento completo de aprovações/rejeições de normalizações';


-- ================================================================
-- PERMISSÕES (opcional - se usar usuários diferentes)
-- ================================================================
-- GRANT SELECT ON ALL TABLES IN SCHEMA falai_doutor_normalizacao TO api_user;
-- GRANT INSERT, UPDATE, DELETE ON falai_doutor_normalizacao.sintomas, falai_doutor_normalizacao.sinonimos TO api_user;
-- GRANT INSERT ON falai_doutor_normalizacao.inputs, falai_doutor_normalizacao.outputs, falai_doutor_normalizacao.base_candidata, falai_doutor_normalizacao.auditoria TO api_user;


COMMIT;
