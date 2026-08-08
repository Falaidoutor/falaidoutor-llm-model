-- ================================================================
-- SEED DATA: Dados iniciais de sintomas e sinonimos
-- Database: falai
-- Description: Carrega dados de exemplo para começar
-- ================================================================
-- Execute APÓS 01_schema.sql

BEGIN;

-- ================================================================
-- INSERIR CATEGORIAS DE SINTOMAS
-- ================================================================

INSERT INTO falai_doutor_normalizacao.categorias_sintomas (codigo, nome) VALUES
('cardiovascular', 'Cardiovascular'),
('respiratorio', 'Respiratório'),
('neurologico', 'Neurológico'),
('gastrointestinal', 'Gastrointestinal'),
('geral', 'Geral')
ON CONFLICT (codigo) DO UPDATE SET nome = EXCLUDED.nome;


-- ================================================================
-- INSERIR SINTOMAS CANÔNICOS
-- ================================================================

INSERT INTO falai_doutor_normalizacao.sintomas (termo, categoria_id, descricao, ativo) VALUES
('Dor Torácica', (SELECT id FROM falai_doutor_normalizacao.categorias_sintomas WHERE codigo = 'cardiovascular'), 'Dor no peito, pode irradiar para braço ou mandíbula', TRUE),
('Dispneia', (SELECT id FROM falai_doutor_normalizacao.categorias_sintomas WHERE codigo = 'respiratorio'), 'Falta de ar ou dificuldade para respirar', TRUE),
('Palpitações', (SELECT id FROM falai_doutor_normalizacao.categorias_sintomas WHERE codigo = 'cardiovascular'), 'Sensação de batidas do coração irregulares ou aceleradas', TRUE),
('Febre', (SELECT id FROM falai_doutor_normalizacao.categorias_sintomas WHERE codigo = 'geral'), 'Elevação da temperatura corporal acima de 37.5°C', TRUE),
('Taquicardia', (SELECT id FROM falai_doutor_normalizacao.categorias_sintomas WHERE codigo = 'cardiovascular'), 'Aceleração do ritmo cardíaco (FC > 100 bpm)', TRUE),
('Mal-estar Geral', (SELECT id FROM falai_doutor_normalizacao.categorias_sintomas WHERE codigo = 'geral'), 'Sensação vaga de indisposição ou desconforto', TRUE),
('Tonturas', (SELECT id FROM falai_doutor_normalizacao.categorias_sintomas WHERE codigo = 'neurologico'), 'Sensação de vertigem ou desequilíbrio', TRUE),
('Sudorese', (SELECT id FROM falai_doutor_normalizacao.categorias_sintomas WHERE codigo = 'geral'), 'Suor excessivo', TRUE),
('Náusea', (SELECT id FROM falai_doutor_normalizacao.categorias_sintomas WHERE codigo = 'gastrointestinal'), 'Sensação de enjôo', TRUE),
('Tosse', (SELECT id FROM falai_doutor_normalizacao.categorias_sintomas WHERE codigo = 'respiratorio'), 'Expulsão abrupta de ar dos pulmões', TRUE)
ON CONFLICT (termo) DO NOTHING;


-- ================================================================
-- INSERIR SINONIMOS (como os usuários falam)
-- ================================================================

WITH dados_sinonimos (sintoma_id, termo, origem, aprovado) AS (
VALUES
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
)
INSERT INTO falai_doutor_normalizacao.sinonimos (sintoma_id, termo, origem, status)
SELECT
    sintoma_id,
    termo,
    origem,
    CASE WHEN aprovado THEN 'aprovado' ELSE 'pendente' END
FROM dados_sinonimos
ON CONFLICT (termo_busca, sintoma_id) DO NOTHING;


-- ================================================================
-- INSERIR CID-10 (exemplos principais)
-- ================================================================

INSERT INTO falai_doutor_normalizacao.cid10 (codigo, descricao, subcategorias) VALUES
('R07', 'Dor em tórax', 'R07.0, R07.1, R07.2, R07.9'),
('R06', 'Anormalidades da respiração', 'R06.0, R06.1, R06.2'),
('R07.3', 'Dor em região da mama', NULL),
('I49', 'Arritmias cardíacas, não especificadas', NULL),
('R50', 'Febre de origem desconhecida e de outras origens', 'R50.2, R50.8, R50.9'),
('R53', 'Mal-estar e fadiga', 'R53.0, R53.1, R53.8, R53.9'),
('R42', 'Tonturas e vertigem', NULL),
('R61', 'Hiperhidrose (sudorese excessiva)', NULL),
('R11', 'Náuseas e vômitos', 'R11.0, R11.1, R11.2'),
('R05', 'Tosse', NULL)
ON CONFLICT (codigo) DO UPDATE SET
    descricao = EXCLUDED.descricao,
    subcategorias = EXCLUDED.subcategorias;


-- ================================================================
-- ASSOCIAR SINTOMAS ↔ CID-10
-- ================================================================

-- Corrigir associações presentes em versões anteriores do seed.
DELETE FROM falai_doutor_normalizacao.sintoma_cid10 sc
USING falai_doutor_normalizacao.sintomas s
WHERE sc.sintoma_id = s.id
  AND (
      (s.termo = 'Febre' AND sc.cid_codigo = 'R05')
      OR (s.termo = 'Tosse' AND sc.cid_codigo = 'R05.9')
  );

-- A versão anterior cadastrava R05.9 incorretamente como febre.
DELETE FROM falai_doutor_normalizacao.cid10 c
WHERE c.codigo = 'R05.9'
  AND c.descricao = 'Febre, não especificada'
  AND NOT EXISTS (
      SELECT 1
      FROM falai_doutor_normalizacao.sintoma_cid10 sc
      WHERE sc.cid_codigo = c.codigo
  );

INSERT INTO falai_doutor_normalizacao.sintoma_cid10 (sintoma_id, cid_codigo, confianca) VALUES
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Dor Torácica'), 'R07', 0.95),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Dor Torácica'), 'R07.3', 0.7),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Dispneia'), 'R06', 0.9),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Palpitações'), 'I49', 0.85),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Febre'), 'R50', 0.98),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Mal-estar Geral'), 'R53', 0.8),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Tonturas'), 'R42', 0.9),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Sudorese'), 'R61', 0.75),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Náusea'), 'R11', 0.85),
((SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Tosse'), 'R05', 0.95)
ON CONFLICT (sintoma_id, cid_codigo) DO UPDATE SET
    confianca = EXCLUDED.confianca;


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
