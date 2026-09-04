# Fala Doutor LLM

Este repositório contém o serviço de inteligência artificial do **Falaidoutor**, uma plataforma de apoio à triagem clínica. Ele recebe informações clínicas estruturadas e produz uma sugestão de classificação de risco, justificativa, resumo e ação recomendada. Não fornece diagnóstico: o resultado deve ser validado e confirmado por um profissional de saúde.

## Papel deste componente

É a camada de inferência e normalização da IA. O backend API coordena a triagem e se comunica com este serviço; o frontend exibe o resultado e o fluxo de revisão. Este componente não é a interface nem o banco de dados do sistema.

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
