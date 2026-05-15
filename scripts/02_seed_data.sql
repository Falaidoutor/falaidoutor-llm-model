-- ================================================================
-- SEED DATA: Dados iniciais de sintomas e sinonimos
-- Database: falai
-- Description: Carrega dados de exemplo para começar
-- ================================================================
-- Execute APÓS 01_schema.sql

BEGIN;

-- ================================================================
-- INSERIR SINTOMAS CANÔNICOS (cardiologia)
-- ================================================================

INSERT INTO falai_doutor_normalizacao.sintomas (termo, categoria, descricao, ativo) VALUES
('Dor Torácica', 'cardiovascular', 'Dor no peito, pode irradiar para braço ou mandíbula', TRUE),
('Dispneia', 'respiratório', 'Falta de ar ou dificuldade para respirar', TRUE),
('Palpitações', 'cardiovascular', 'Sensação de batidas do coração irregulares ou aceleradas', TRUE),
('Febre', 'geral', 'Elevação da temperatura corporal acima de 37.5°C', TRUE),
('Taquicardia', 'cardiovascular', 'Aceleração do ritmo cardíaco (FC > 100 bpm)', TRUE),
('Mal-estar Geral', 'geral', 'Sensação vaga de indisposição ou desconforto', TRUE),
('Tonturas', 'neurológico', 'Sensação de vertigem ou desequilíbrio', TRUE),
('Sudorese', 'geral', 'Suor excessivo', TRUE),
('Náusea', 'gastrointestinal', 'Sensação de enjôo', TRUE),
('Tosse', 'respiratório', 'Expulsão abrupta de ar dos pulmões', TRUE)
ON CONFLICT (termo) DO NOTHING;


-- ================================================================
-- INSERIR SINONIMOS (como os usuários falam)
-- ================================================================

INSERT INTO falai_doutor_normalizacao.sinonimos (sintoma_id, termo, origem, aprovado) VALUES
-- Para "Dor Torácica"
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Dor Torácica'), 'aperto no coração', 'manual', TRUE),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Dor Torácica'), 'dor no peito', 'manual', TRUE),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Dor Torácica'), 'dor na região do coração', 'manual', TRUE),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Dor Torácica'), 'queimação no peito', 'llm', TRUE),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Dor Torácica'), 'peitada', 'usuario', FALSE),

-- Para "Dispneia"
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Dispneia'), 'falta de ar', 'manual', TRUE),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Dispneia'), 'dificuldade para respirar', 'manual', TRUE),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Dispneia'), 'não consigo respirar', 'manual', TRUE),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Dispneia'), 'respiração curta', 'llm', TRUE),

-- Para "Palpitações"
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Palpitações'), 'batidas do coração', 'manual', TRUE),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Palpitações'), 'coração acelerado', 'manual', TRUE),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Palpitações'), 'taquicardia', 'llm', TRUE),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Palpitações'), 'batidas irregulares', 'manual', TRUE),

-- Para "Febre"
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Febre'), 'temperatura alta', 'manual', TRUE),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Febre'), 'estou quente', 'usuario', FALSE),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Febre'), 'queimação corporal', 'llm', TRUE),

-- Para "Mal-estar Geral"
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Mal-estar Geral'), 'mal estar', 'manual', TRUE),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Mal-estar Geral'), 'me sinto mal', 'usuario', FALSE),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Mal-estar Geral'), 'indisposição', 'llm', TRUE),

-- Para "Tonturas"
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Tonturas'), 'tontura', 'manual', TRUE),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Tonturas'), 'vertigem', 'llm', TRUE),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Tonturas'), 'desequilíbrio', 'manual', TRUE),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Tonturas'), 'sensação de queda', 'usuario', TRUE),

-- Para "Sudorese"
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Sudorese'), 'suor', 'manual', TRUE),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Sudorese'), 'suor frio', 'manual', TRUE),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Sudorese'), 'transpiração', 'llm', TRUE),

-- Para "Náusea"
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Náusea'), 'enjoo', 'manual', TRUE),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Náusea'), 'vontade de vomitar', 'manual', TRUE),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Náusea'), 'enjôo', 'usuario', FALSE),

-- Para "Tosse"
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Tosse'), 'tosse seca', 'manual', TRUE),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Tosse'), 'tosse com catarro', 'manual', TRUE),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Tosse'), 'pigarro', 'llm', TRUE)
ON CONFLICT (termo, sintoma_id) DO NOTHING;


-- ================================================================
-- INSERIR CID-10 (exemplos principais)
-- ================================================================

INSERT INTO falai_doutor_normalizacao.cid10 (codigo, descricao, subcategorias) VALUES
('R07', 'Dor em tórax', 'R07.0, R07.1, R07.2, R07.9'),
('R06', 'Anormalidades da respiração', 'R06.0, R06.1, R06.2'),
('R07.3', 'Dor em região da mama', NULL),
('I49', 'Arritmias cardíacas, não especificadas', NULL),
('R05', 'Febre de origem desconhecida', 'R05.0, R05.1, R05.9'),
('R53', 'Mal-estar e fadiga', 'R53.0, R53.1, R53.8, R53.9'),
('R42', 'Tonturas e vertigem', NULL),
('R61', 'Hiperhidrose (sudorese excessiva)', NULL),
('R11', 'Náuseas e vômitos', 'R11.0, R11.1, R11.2'),
('R05.9', 'Febre, não especificada', NULL)
ON CONFLICT (codigo) DO NOTHING;


-- ================================================================
-- ASSOCIAR SINTOMAS ↔ CID-10
-- ================================================================

INSERT INTO falai_doutor_normalizacao.sintoma_cid10 (sintoma_id, cid_codigo, confianca) VALUES
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Dor Torácica'), 'R07', 0.95),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Dor Torácica'), 'R07.3', 0.7),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Dispneia'), 'R06', 0.9),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Palpitações'), 'I49', 0.85),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Febre'), 'R05', 0.98),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Mal-estar Geral'), 'R53', 0.8),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Tonturas'), 'R42', 0.9),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Sudorese'), 'R61', 0.75),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Náusea'), 'R11', 0.85),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Tosse'), 'R05.9', 0.6)
ON CONFLICT (sintoma_id, cid_codigo) DO NOTHING;


-- ================================================================
-- VERIFICAR DADOS CARREGADOS
-- ================================================================

SELECT 'Sintomas Carregados:' as log, COUNT(*) FROM falai_doutor_normalizacao.sintomas;
SELECT 'Sinonimos Carregados:' as log, COUNT(*) FROM falai_doutor_normalizacao.sinonimos;
SELECT 'CID-10 Carregadas:' as log, COUNT(*) FROM falai_doutor_normalizacao.cid10;
SELECT 'Associações SintomaxCID-10:' as log, COUNT(*) FROM falai_doutor_normalizacao.sintoma_cid10;

-- Vista para verificar dados
SELECT * FROM falai_doutor_normalizacao.vw_sinonimos_normalizacao LIMIT 5;


COMMIT;
