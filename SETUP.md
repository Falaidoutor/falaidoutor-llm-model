# Normalização Semântica com Qdrant + E5 + NER (v2.0.0)

## Setup Rápido

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
python -m spacy download pt_core_news_md
```

### 2. Configurar Variáveis de Ambiente

```bash
cp .env.example .env
# Editar .env com suas configurações (PostgreSQL, Qdrant, etc)
```

### 3. Iniciar Serviços Externos

#### Qdrant (Docker)
```bash
docker run -p 6333:6333 qdrant/qdrant
```

#### Ollama (Local)
```bash
ollama serve
ollama pull qwen3  # ou seu modelo preferido
```

#### PostgreSQL
```bash
# Criar database e executar script SQL
psql -U postgres -c "CREATE DATABASE falai;"
psql -U postgres -d falai -f seu_script.sql
```

### 4. Carregar Dados no Qdrant

```bash
python -m app.scripts.init_qdrant
```

Exemplo de saída esperada:
```
======================================================================
Iniciando carregamento de dados: PostgreSQL → Qdrant
======================================================================

[1/6] Validando conexões...
✓ Conexão com PostgreSQL validada
✓ Conexão com Qdrant validada
✓ Modelo E5 carregado (dimensão: 1024)

[2/6] Inicializando collection no Qdrant...
✓ Collection 'sintomas_embeddings' criada com sucesso (dimensão: 1024, similaridade: Cosine)

[3/6] Carregando dados de PostgreSQL...
✓ Carregados 150 sinonimos de PostgreSQL
✓ Carregados 50 sintomas canônicos de PostgreSQL

[4/6] Gerando dados de embedding...
✓ Gerados 200 embeddings

[5/6] Fazendo upsert ao Qdrant...
✓ 200 vetores inseridos ao Qdrant

[6/6] Verificando resultado...
✓ Collection info: {'name': 'sintomas_embeddings', 'points_count': 200, ...}

======================================================================
✓ Inicialização concluída com sucesso!
======================================================================
```

### 5. Iniciar a API

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

A API estará disponível em: `http://localhost:8000`

---

## Pipeline de Normalização Semântica

### Fluxo Completo

```
Texto do Usuário
    ↓
[NER] Extração de Sintomas (spaCy)
    ↓
Para cada Sintoma:
    ├─ [E5] Gerar Embedding
    ├─ [Qdrant] Buscar Similar
    └─ [PostgreSQL] Recuperar Dados
    ↓
Classificação:
├─ Score ≥ 0.65 → Sintoma Normalizado ✓
└─ Score < 0.65 → Sintoma Não Normalizado ⚠️
    ↓
Dois Arrays → Ollama/Manchester
    ├─ sintomas_normalizados
    └─ sintomas_nao_normalizados (Ollama normaliza)
    ↓
TriageResponse com:
├─ Classificação de Risco (Vermelho|Laranja|Amarelo|Verde|Azul)
├─ Normalizacao Resultado
└─ Normalizacao Ollama
    ↓
Registrar em base_candidata (Auditoria)
```

---

## Endpoints da API

### 1. Triage (Principal)

**POST** `/triage`

Exemplo de requisição:
```json
{
  "symptoms": "Tenho aperto no coração e estou com febre alta",
  "debug_mode": false
}
```

Exemplo de resposta:
```json
{
  "classificacao": "Laranja",
  "prioridade": "Muito urgente",
  "tempo_atendimento_minutos": 10,
  "fluxograma_utilizado": "Dor Torácica",
  "discriminadores_gerais_avaliados": [...],
  "discriminadores_especificos_ativados": [...],
  "populacao_especial": null,
  "over_triage_aplicado": false,
  "confianca": "alta",
  "justificativa": "...",
  "alertas": [],
  
  "normalizacao_resultado": {
    "sintomas_normalizados": [
      {
        "original": "aperto no coração",
        "normalizado": "dor torácica",
        "sintoma_id": 1,
        "sinonimo_id": 10,
        "score": 0.92,
        "tipo": "normalizado"
      }
    ],
    "sintomas_nao_normalizados": [
      {
        "original": "estou com febre alta",
        "score": 0.58,
        "tipo": "nao_normalizado",
        "motivo": "score_baixo"
      }
    ],
    "total_extraidos": 2,
    "taxa_normalizacao": 0.5
  },
  
  "normalizacao_ollama": [
    {
      "original": "estou com febre alta",
      "normalizado": "febre alta",
      "confianca": "media"
    }
  ]
}
```

### 2. Health Check

**GET** `/health`

Response:
```json
{
  "status": "ok",
  "version": "2.0.0"
}
```

### 3. Normalization Stats (Debug)

**GET** `/debug/normalization-stats`

Response:
```json
{
  "similarity_threshold": 0.65,
  "modelo_e5": "intfloat/multilingual-e5-large-instruct",
  "embedding_dimension": 1024,
  "qdrant_info": {
    "name": "sintomas_embeddings",
    "points_count": 200
  }
}
```

---

## Estrutura de Arquivos

```
backend-ai-normalizacao/
├── main.py                          # FastAPI app principal
├── requirements.txt                 # Dependências
├── .env.example                     # Template de configuração
│
├── app/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py              # Configurações centralizadas
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py               # Pydantic Models (Request/Response)
│   ├── prompt/
│   │   └── prompt.py                # System Prompt + build_user_prompt
│   ├── service/
│   │   ├── __init__.py
│   │   ├── ner_service.py           # NER com spaCy
│   │   ├── embedding.py             # E5 Embedding Service
│   │   ├── qdrant_service.py        # Qdrant Operations
│   │   ├── postgres_service.py      # PostgreSQL Queries
│   │   ├── normalization.py         # Orquestrador Principal
│   │   ├── ollama_service.py        # Integração com Ollama
│   │   └── validator.py             # Validação de respostas MTS
│   └── scripts/
│       ├── __init__.py
│       └── init_qdrant.py           # Script de inicialização
│
└── tests/
    ├── __init__.py
    ├── test_validator.py
    ├── test_ner.py                  # [TODO] Testes NER
    ├── test_embedding.py            # [TODO] Testes Embedding
    ├── test_normalization.py        # [TODO] Testes Normalização
    └── test_integration.py          # [TODO] Testes E2E
```

---

## Fluxo de Retroalimentação (Learning Loop)

### Como Funciona

1. **Normalização não encontrada** (score < 0.65):
   - Sintoma é sinalizado como "não normalizado"
   - Ollama tenta normalizar
   - Normalização do Ollama é registrada em `base_candidata`

2. **Auditoria Humana**:
   - Usuários revisam candidatos pendentes
   - Aprovam/rejeitam normalizações

3. **Atualização do Qdrant**:
   - Sinonimos aprovados são adicionados ao Qdrant
   - Re-indexação periódica

### Próximas Requisições:
- Sintomas similares agora encontram match no Qdrant ✓
- Score melhora incrementalmente
- Taxa de normalização aumenta

---

## Troubleshooting

### Erro: "Modelo spaCy não encontrado"

```bash
python -m spacy download pt_core_news_md
```

### Erro: "Conexão com PostgreSQL recusada"

- Verificar se PostgreSQL está rodando: `psql --version`
- Verificar credenciais em `.env`
- Executar script SQL com os dados de seed

### Erro: "Collection Qdrant está vazia"

- Executar `python -m app.scripts.init_qdrant`
- Verificar se PostgreSQL tem dados em `sinonimos` e `sintomas`

### Erro: "Ollama retorna JSON inválido"

- Verificar se o modelo suporta formato JSON: `ollama list`
- Certificar que modelo está rodando: `curl http://localhost:11434/api/tags`
- Considerar usar modelo que garante JSON: `mistral-large`, `qwen3`, etc

---

## Limites de Conhecimento Atual

1. **NER**: Usando modelo genérico `pt_core_news_md`. Idealmente seria fine-tuned para sintomas médicos.
2. **E5 Model**: Carregado uma vez no startup. Para aplicações com pouco traffic, considear lazy load.
3. **Qdrant**: Sem replication/backup nativo. Para produção, usar Qdrant Cloud.
4. **PostgreSQL**: Connection pool simples. Para escala, considerar asyncpg + Alembic para migrations.

---

## Próximos Passos

- [ ] Fine-tuning de modelo NER para sintomas médicos
- [ ] Testes unitários e de integração
- [ ] Caching de embeddings
- [ ] Dashboard de monitoramento (base_candidata)
- [ ] API de auditoria (approve/reject candidatos)
- [ ] Documentação Swagger automática
- [ ] Deploy com Docker Compose

---

## Contato / Issues

Para problemas, ver: [GitHub Issues](https://github.com/)
