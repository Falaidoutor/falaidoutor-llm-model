-- Schema para auditoria de mapeamento CID10
-- Criado com suporte a PostgreSQL 12+
-- Migração: 001_initial_schema

-- Criar tabela se não existir
CREATE TABLE IF NOT EXISTS cid10_audit_log (
    id SERIAL PRIMARY KEY,
    data_hora TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sintomas_entrada TEXT NOT NULL,
    sintomas_normalizados TEXT,
    cids_sugeridos JSONB,
    numero_cids INTEGER NOT NULL DEFAULT 0 CHECK (numero_cids >= 0),
    medico_id INTEGER,
    validado_medico BOOLEAN DEFAULT FALSE,
    cid_final VARCHAR(10),
    observacoes TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    CONSTRAINT cids_sugeridos_not_empty CHECK (numero_cids > 0 OR cids_sugeridos IS NULL)
);

-- Criar índices para melhorar performance
CREATE INDEX IF NOT EXISTS idx_cid10_audit_data_hora 
ON cid10_audit_log (data_hora DESC);

CREATE INDEX IF NOT EXISTS idx_cid10_audit_medico_id 
ON cid10_audit_log (medico_id);

CREATE INDEX IF NOT EXISTS idx_cid10_audit_validado 
ON cid10_audit_log (validado_medico);

CREATE INDEX IF NOT EXISTS idx_cid10_audit_cid_final 
ON cid10_audit_log (cid_final);

-- Criar índice JSONB para melhor performance em buscas nos CIDs sugeridos
CREATE INDEX IF NOT EXISTS idx_cid10_audit_cids_sugeridos 
ON cid10_audit_log USING GIN (cids_sugeridos);

-- Criar view para estatísticas
CREATE OR REPLACE VIEW cid10_audit_stats AS
SELECT 
    COUNT(*) as total_registros,
    COUNT(DISTINCT medico_id) as total_medicos,
    COUNT(CASE WHEN validado_medico = TRUE THEN 1 END) as registros_validados,
    COUNT(CASE WHEN validado_medico = FALSE THEN 1 END) as registros_nao_validados,
    AVG(numero_cids) as media_cids_sugeridos,
    MAX(numero_cids) as max_cids_sugeridos
FROM cid10_audit_log;

-- Criar função para atualizar data_hora
CREATE OR REPLACE FUNCTION update_cid10_audit_datetime()
RETURNS TRIGGER AS $$
BEGIN
    NEW.data_hora = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Criar trigger para atualizar data_hora
DROP TRIGGER IF EXISTS trigger_update_cid10_audit_datetime ON cid10_audit_log;
CREATE TRIGGER trigger_update_cid10_audit_datetime
BEFORE UPDATE ON cid10_audit_log
FOR EACH ROW
EXECUTE FUNCTION update_cid10_audit_datetime();
