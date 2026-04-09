# 🗄️ Conexão com Banco de Dados

## Visão Geral

A aplicação Fala Doutor está integrada com **PostgreSQL** para persistência de auditoria de mapeamentos CID-10. 

## Configuração Rápida

### Pré-requisitos

- PostgreSQL 12+ instalado
- Python 3.10+
- pip

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente

Edite o arquivo `.env` na raiz do projeto:

```env
# Configuração de Banco de Dados
DB_USER=postgres
DB_PASSWORD=sua_senha_aqui
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fala_doutor

# Flags de Debug
SQL_ECHO=false
```

### 3. Criar banco de dados (opcional)

Se estiver usando PostgreSQL localmente, crie o banco manualmente:

```sql
CREATE DATABASE fala_doutor;
```

Ou use o script de setup:

```bash
python setup_db.py setup
```

### 4. Inicializar schema

```bash
python setup_db.py init
```

Ou se estiver usando a aplicação, o schema será criado automaticamente no startup.

## Arquitetura do Banco de Dados

### Tabela Principal: `cid10_audit_log`

```sql
CREATE TABLE cid10_audit_log (
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
    user_agent TEXT
);
```

### Índices

- `idx_cid10_audit_data`: Otimiza queries por data
- `idx_cid10_audit_medico`: Otimiza queries por médico
- `idx_cid10_audit_validacao`: Otimiza queries por validação
- `idx_cid10_audit_cid_final`: Otimiza queries por CID final

### Views

**v_cid10_audit_stats**: Estatísticas diárias
- Total de mapeamentos
- Validações completadas
- Taxa de validação
- Média de CIDs por mapeamento

**v_cid10_audit_top_cids**: Top 20 CIDs mais mapeados

## Integração com FastAPI

### Injeção de Dependência

Use a função `get_db_session` para obter uma sessão SQLAlchemy:

```python
from fastapi import Depends
from app.database import get_db_session
from sqlalchemy.orm import Session

@app.get("/audit")
async def get_audit(db: Session = Depends(get_db_session)):
    # Usar db aqui
    pass
```

### Uso no NormalizacaoSemantica

```python
from app.repository import CID10AuditRepository
from sqlalchemy.orm import Session

# Com injeção de dependência
audit_repo = CID10AuditRepository(db_session=session)

# Ou usar a sessão padrão (SessionLocal)
audit_repo = CID10AuditRepository()
```

## Operações Comuns

### Listar auditoria

```python
audit_repo = CID10AuditRepository()
registros = audit_repo.listar_auditoria(limite=10)
```

### Obter estatísticas

```python
stats = audit_repo.obter_estatisticas()
print(f"Total de mapeamentos: {stats['total_mapeamentos']}")
print(f"Taxa de validação: {stats['taxa_validacao']:.2f}%")
```

### Buscar por período

```python
registros = audit_repo.buscar_por_periodo(
    data_inicio="2026-04-01",
    data_fim="2026-04-08"
)
```

### Exportar CSV

```python
arquivo = audit_repo.exportar_csv("relatorio.csv")
```

### Atualizar validação

```python
audit_repo.atualizar_validacao(
    registro_id=1,
    validado_medico=True,
    medico_id=42,
    cid_final="R51"
)
```

## Troubleshooting

### Erro: "connection refused"

- Verifique se PostgreSQL está rodando
- Confirme as configurações de host e porta no `.env`

### Erro: "database does not exist"

- Crie o banco manualmente com `CREATE DATABASE fala_doutor;`
- Ou execute `python setup_db.py setup`

### Erro: "permission denied"

- Verifique as credenciais de acesso no `.env`
- Certifique-se que o usuário PostgreSQL tem permissões

### Schema não é criado automaticamente

- Execute manualmente: `python setup_db.py init`
- Ou rode o arquivo SQL diretamente: `psql -U postgres -d fala_doutor -f schema_cid10_auditoria.sql`

## Backup e Manutenção

### Fazer backup

```bash
pg_dump -U postgres fala_doutor > backup.sql
```

### Restaurar backup

```bash
psql -U postgres fala_doutor < backup.sql
```

### Limpar dados antigos (>90 dias)

```python
audit_repo = CID10AuditRepository()
removidos = audit_repo.limpar_auditoria_antiga(dias=90)
print(f"Removidos {removidos} registros antigos")
```

## Variáveis de Ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `DB_USER` | postgres | Usuário PostgreSQL |
| `DB_PASSWORD` | postgres | Senha PostgreSQL |
| `DB_HOST` | localhost | Host PostgreSQL |
| `DB_PORT` | 5432 | Porta PostgreSQL |
| `DB_NAME` | fala_doutor | Nome do banco |
| `SQL_ECHO` | false | Debug SQL (true/false) |

## Segurança

⚠️ **IMPORTANTE**: 

- ✅ Nunca commitar o `.env` com credenciais reais
- ✅ Usar `.env.example` para documentar variáveis
- ✅ Em produção, usar variáveis de ambiente do sistema operacional
- ✅ Usar senhas fortes para PostgreSQL
- ✅ Limitar acesso de rede ao PostgreSQL
- ✅ Fazer backups regulares
