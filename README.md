# falaidoutor-llm-model

Para iniciar com todas as depêndencias:

pip install -r requirements.txt
python -m spacy download pt_core_news_md
cp .env.example .env  # editar com credenciais

docker run -p 6333:6333 qdrant/qdrant  # Qdrant
ollama serve & ollama pull qwen3:8b     # Ollama

python -m app.scripts.init_qdrant

uvicorn main:app --reload --reload-delay 1.0 --host 0.0.0.0 --port 8000