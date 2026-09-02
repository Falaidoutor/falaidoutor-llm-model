# Fala Doutor LLM

Backend FastAPI de triagem ESI via Groq, com autenticação, payload HTTP
opcionalmente criptografado e normalização semântica de sintomas.

O pipeline de normalização foi preparado para execução serverless:

- extração leve dos sintomas, sem modelo spaCy local;
- embeddings E5 executados pelo Qdrant Cloud Inference;
- busca vetorial no Qdrant Cloud;
- vocabulário e base candidata no Supabase/PostgreSQL;
- fallback para o texto original quando a normalização estiver indisponível.

## Execução local

```powershell
python -m pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

O endpoint `GET /health` não consulta dependências externas. O endpoint
`GET /debug/normalization-stats` exige `X-Application-Key`.

## Vercel

Configure na Vercel todas as variáveis obrigatórias descritas em `.env.example`,
principalmente `APPLICATION_KEY`, `GROQ_API_KEY`, `POSTGRES_DSN`, `QDRANT_URL` e
`QDRANT_API_KEY`. O `server.py` continua exportando `main:app`, preservando o
entrypoint que já opera na branch `main`.

O carregamento da coleção vetorial permanece fora do backend. Execute o projeto
irmão `qdrant-job` quando for necessário sincronizar dados do PostgreSQL para o
Qdrant Cloud.
