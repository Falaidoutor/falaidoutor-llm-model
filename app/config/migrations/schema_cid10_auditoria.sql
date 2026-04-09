-- Schema de Auditoria para CID-10
-- Fala Doutor - Triagem Médica Inteligente

-- Tabela de auditoria de mapeamentos CID-10
CREATE TABLE IF NOT EXISTS cid10_audit_log (
    id SERIAL PRIMARY KEY,
    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sintomas_entrada TEXT NOT NULL,
    sintomas_normalizados TEXT[] NOT NULL,
    cids_sugeridos JSONB NOT NULL,
    numero_cids INTEGER NOT NULL,
    medico_id INTEGER,
    validado_medico BOOLEAN DEFAULT FALSE,
    cid_final VARCHAR(10),
    observacoes TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    
    -- Índices para busca rápida
    CONSTRAINT cid10_audit_log_not_null CHECK (numero_cids > 0)
);

-- Índices para melhor performance
CREATE INDEX idx_cid10_audit_data ON cid10_audit_log(data_hora DESC);
CREATE INDEX idx_cid10_audit_medico ON cid10_audit_log(medico_id);
CREATE INDEX idx_cid10_audit_validacao ON cid10_audit_log(validado_medico);
CREATE INDEX idx_cid10_audit_cid_final ON cid10_audit_log(cid_final);

-- View para estatísticas
CREATE OR REPLACE VIEW v_cid10_audit_stats AS
SELECT
    DATE(data_hora) as data,
    COUNT(*) as total_mapeamentos,
    SUM(CASE WHEN validado_medico THEN 1 ELSE 0 END) as validados_medico,
    ROUND(
        SUM(CASE WHEN validado_medico THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC * 100,
        2
    ) as taxa_validacao_perc,
    SUM(numero_cids) as total_cids_mapeados,
    ROUND(AVG(numero_cids)::NUMERIC, 2) as media_cids_por_mapeamento
FROM cid10_audit_log
GROUP BY DATE(data_hora)
ORDER BY data DESC;

-- View dos CIDs mais mapeados
CREATE OR REPLACE VIEW v_cid10_audit_top_cids AS
WITH cid_exploded AS (
    SELECT
        (elem->>'cid') as cid_codigo,
        (elem->>'descricao') as descricao
    FROM cid10_audit_log,
    LATERAL jsonb_array_elements(cids_sugeridos) as elem
)
SELECT
    cid_codigo,
    descricao,
    COUNT(*) as frequencia,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM cid10_audit_log), 2) as percentual
FROM cid_exploded
GROUP BY cid_codigo, descricao
ORDER BY frequencia DESC
LIMIT 20;

-- View de taxas de validação por médico
CREATE OR REPLACE VIEW v_cid10_audit_medicos AS
SELECT
    medico_id,
    COUNT(*) as mapeamentos_analisados,
    SUM(CASE WHEN validado_medico THEN 1 ELSE 0 END) as aprovados,
    SUM(CASE WHEN validado_medico THEN 0 ELSE 1 END) as rejeitados,
    ROUND(
        SUM(CASE WHEN validado_medico THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC * 100,
        2
    ) as taxa_aprovacao
FROM cid10_audit_log
WHERE medico_id IS NOT NULL
GROUP BY medico_id
ORDER BY mapeamentos_analisados DESC;

-- Tabela de histórico de erros (para aprendizado)
CREATE TABLE IF NOT EXISTS cid10_erro_log (
    id SERIAL PRIMARY KEY,
    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    audit_id INTEGER REFERENCES cid10_audit_log(id),
    cid_sugerido VARCHAR(10) NOT NULL,
    cid_correto VARCHAR(10),
    tipo_erro VARCHAR(50),
    descricao_erro TEXT,
    
    FOREIGN KEY (audit_id) REFERENCES cid10_audit_log(id) ON DELETE CASCADE
);

CREATE INDEX idx_cid10_erro_tipo ON cid10_erro_log(tipo_erro);
CREATE INDEX idx_cid10_erro_data ON cid10_erro_log(data_hora DESC);

-- Procedure para limpar auditoria antiga (manutenção)
CREATE OR REPLACE FUNCTION limpar_auditoria_antiga(dias INT DEFAULT 365)
RETURNS TABLE(registros_removidos INT, data_limite DATE) AS $$
DECLARE
    v_registros_removidos INT;
    v_data_limite DATE;
BEGIN
    v_data_limite := CURRENT_DATE - dias;
    
    DELETE FROM cid10_audit_log
    WHERE DATE(data_hora) < v_data_limite;
    
    GET DIAGNOSTICS v_registros_removidos = ROW_COUNT;
    
    RETURN QUERY SELECT v_registros_removidos, v_data_limite;
END;
$$ LANGUAGE plpgsql;

-- Comentários para documentação
COMMENT ON TABLE cid10_audit_log IS 'Registra todos os mapeamentos CID-10 para auditoria clínica e rastreabilidade';
COMMENT ON COLUMN cid10_audit_log.cids_sugeridos IS 'JSONB contendo array de CIDs com campos: cid, descricao, sintoma_detectado';
COMMENT ON COLUMN cid10_audit_log.validado_medico IS 'TRUE se médico aprovou o mapeamento sugerido';
