# Configuração da normalização em nuvem

1. Aplique `scripts/01_schema.sql` no PostgreSQL/Supabase e carregue os dados
   necessários com os scripts de seed apropriados.
2. Execute o projeto independente `qdrant-job` para indexar sintomas e sinônimos
   no Qdrant Cloud. O backend não cria embeddings localmente.
3. Cadastre na Vercel as variáveis de `.env.example`.
4. Faça o deploy da branch `main` e valide `GET /health`.
5. Com `X-Application-Key`, valide `GET /debug/normalization-stats` e depois uma
   chamada real a `POST /triage`.

Para PostgreSQL em ambiente serverless, use preferencialmente o Session Pooler
do Supabase e mantenha `POSTGRES_POOL_SIZE` baixo.
