"""Configuração de conexão com banco de dados PostgreSQL."""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do banco de dados
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "fala_doutor")

# Construir connection string (usando psycopg3)
DatabaseURL = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Criar engine
engine = create_engine(
    DatabaseURL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    pool_pre_ping=True,  # Verifica se a conexão ainda está válida antes de usar
    pool_size=5,
    max_overflow=10,
)

# Criar session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session() -> Session:
    """Dependency injection para FastAPI - fornece session de BD."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db():
    """Inicializa o banco de dados executando o schema."""
    try:
        # Ler e executar arquivo de schema
        schema_path = os.path.join(
            os.path.dirname(__file__), "..", "database", "migrations", "001_initial_schema.sql"
        )
        
        if os.path.exists(schema_path):
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_sql = f.read()
            
            with engine.connect() as connection:
                # Executar schema em blocos (PostgreSQL não permite múltiplos comandos de uma vez)
                for statement in schema_sql.split(";"):
                    statement = statement.strip()
                    if statement:
                        connection.execute(text(statement))
                connection.commit()
            
            print("Schema do banco de dados inicializado com sucesso")
        else:
            print(f"Arquivo de schema não encontrado: {schema_path}")
    except Exception as e:
        print(f"Erro ao inicializar schema: {e}")


def test_connection():
    """Testa se a conexão com o banco de dados está funcionando."""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            result.close()
        print("Conexão com banco de dados estabelecida com sucesso")
        return True
    except Exception as e:
        print(f"Erro na conexão com banco de dados: {e}")
        return False
