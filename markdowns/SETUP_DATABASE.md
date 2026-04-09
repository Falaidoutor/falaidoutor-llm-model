# Database Integration - Quick Start Guide

## ✅ O que foi configurado

### 1. **Dependências Instaladas** ✓
- SQLAlchemy 2.0.25 (ORM Python)
- psycopg2-binary 2.9.9 (Driver PostgreSQL)
- python-dotenv 1.0.0 (Gerenciador de variáveis)

### 2. **Arquivos de Configuração** ✓
- `.env` - Variáveis de ambiente (local)
- `.env.example` - Template de referência

### 3. **Estrutura de Banco de Dados** ✓
- `app/config/database.py` - Engine e sessão SQLAlchemy
- `app/models.py` - Modelos ORM (CID10AuditLog)
- `app/schema_cid10_auditoria.sql` - Schema PostgreSQL

### 4. **Integração com FastAPI** ✓
- `main.py` - Startup hooks para inicializar BD
- `/health` endpoint - Verificar saúde da aplicação

### 5. **Repository Pattern** ✓
- `app/repository/audit_repository.py` - Acesso a dados refatorado para BD

### 6. **Utilitários** ✓
- `setup_db.py` - Script para configurar BD
- `test_database.py` - Testes de integração
- `DATABASE.md` - Documentação completa

---

## 🚀 Próximas Etapas

### PASSO 1: Verificar PostgreSQL

Certifique-se que PostgreSQL está instalado e rodando:

```bash
# Windows
psql --version
# psql (PostgreSQL) 12.x ou superior

# Testar conexão
psql -U postgres -h localhost
```

Se PostgreSQL não está rodando:
- **Windows**: Abrir "Services" → PostgreSQL → Start
- **Mac**: `brew services start postgresql`
- **Linux**: `sudo systemctl start postgresql`

### PASSO 2: Executar Setup

```bash
python setup_db.py setup
```

O script irá:
1. Criar banco de dados `fala_doutor`
2. Testar conexão
3. Inicializar schema (tabelas, índices)

**Saída esperada:**
```
📦 Criando banco de dados...
✅ Banco de dados 'fala_doutor' criado com sucesso

🧪 Testando conexão com banco de dados...
✅ Conexão com banco de dados estabelecida com sucesso

📋 Inicializando schema...
✅ Schema do banco de dados inicializado com sucesso

==================================================
✅ SETUP CONCLUÍDO COM SUCESSO!
==================================================
```

### PASSO 3: Executar Testes

```bash
python test_database.py
```

**Saída esperada:**
```
============================================================
TESTE DE CONEXÃO COM BANCO DE DADOS
============================================================

✓ Teste 1: Conexão básica...
✓ Teste 2: Verificando tabelas...
✓ Teste 3: Testes de CRUD...
  - Inserindo registro de teste...
  - Lendo auditoria...
  - Obtendo estatísticas...
  - Atualizando validação...

============================================================
✅ TODOS OS TESTES PASSARAM COM SUCESSO!
============================================================
```

### PASSO 4: Iniciar Aplicação

```bash
python main.py
```

**Saída esperada:**
```
🚀 Iniciando Fala Doutor...
✅ Conexão com banco de dados estabelecida com sucesso
✅ Schema do banco de dados inicializado com sucesso

INFO:     Uvicorn running on http://0.0.0.0:8000
```

### PASSO 5: Verificar Health

```bash
curl http://localhost:8000/health
```

**Resposta esperada:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

---

## 🔧 Configuração de Variáveis de Ambiente

Edite `.env` com seus valores:

```env
# Banco de Dados
DB_USER=seu_usuario_postgres
DB_PASSWORD=sua_senha
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fala_doutor

# Debug (colocar 'true' para ver SQL)
SQL_ECHO=false

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
MODEL_NAME=qwen2
```

---

## 📊 Arquitetura do BD

### Tabela Principal: cid10_audit_log

```
├── id (PK)
├── data_hora (TIMESTAMP)
├── sintomas_entrada (TEXT)
├── sintomas_normalizados (JSON)
├── cids_sugeridos (JSONB)
├── numero_cids (INTEGER)
├── medico_id (FK)
├── validado_medico (BOOLEAN)
├── cid_final (VARCHAR)
├── observacoes (TEXT)
├── ip_address (VARCHAR)
└── user_agent (TEXT)
```

### Índices para Performance

- `data_hora DESC` - Queries por período
- `medico_id` - Filtros por médico
- `validado_medico` - Filtros por validação
- `cid_final` - Buscas por CID
- `cids_sugeridos` (GIN) - Buscas em JSONB

---

## 💾 Modo Offline (Sem BD)

Se PostgreSQL não estiver disponível:

1. A aplicação iniciará e exibirá um aviso
2. As funções de auditoria podem retornar dados vazios
3. Sem persistência entre reinicializações

Para retomar com BD:
```bash
python setup_db.py setup
```

---

## 📁 Estrutura de Arquivos

```
py-back/
├── app/
│   ├── config/
│   │   ├── __init__.py
│   │   └── database.py          ← Engine e sessão
│   ├── models.py                 ← ORM models
│   ├── repository/
│   │   └── audit_repository.py   ← Acesso a dados
│   ├── service/                  ← Lógica de negócio
│   └── schema_cid10_auditoria.sql ← Schema
├── .env                          ← Variáveis (NÃO commitar!)
├── .env.example                  ← Template
├── main.py                        ← FastAPI app
├── setup_db.py                   ← Script setup
├── test_database.py              ← Testes
├── DATABASE.md                   ← Documentação
└── requirements.txt              ← Dependências
```

---

## ⚠️ Troubleshooting

### "Connection refused"
- [ ] PostgreSQL está rodando?
- [ ] Credenciais corretas no .env?
- [ ] Porta 5432 está aberta?

### "Database does not exist"
```bash
python setup_db.py setup
```

### "Module not found: sqlalchemy"
```bash
pip install -r requirements.txt
```

### Ver SQL sendo executado
```python
# Em .env
SQL_ECHO=true
```

---

## ✅ Checklist Rápido

- [ ] PostgreSQL instalado e rodando
- [ ] Python 3.9+
- [ ] `pip install -r requirements.txt`
- [ ] `.env` criado com credenciais
- [ ] `python setup_db.py setup` ✅
- [ ] `python test_database.py` ✅
- [ ] `python main.py` inicia sem erros
- [ ] `curl http://localhost:8000/health` → healthy

---

## 📞 Próxima Etapa

Após completar os passos acima, o banco está pronto para:

1. **Integração com Serviços** - Usar injeção de dependência:
   ```python
   @app.post("/triage")
   async def triage(request: SymptomsRequest, db_session: Session = Depends(get_db_session)):
       repo = CID10AuditRepository(db_session=db_session)
       # ... usar repo para auditoria
   ```

2. **Criar Endpoints de Admin**:
   - GET `/admin/audits` - Listar auditoria
   - GET `/admin/stats` - Estatísticas
   - GET `/admin/export?format=csv` - Exportar dados

3. **Setup em Produção**:
   - [ ] Usar PostgreSQL gerenciado (RDS, Railway, etc)
   - [ ] Configurar backup automático
   - [ ] Ativar SSL/TLS
   - [ ] Monitorar performance

Consulte `DATABASE.md` para mais detalhes!
