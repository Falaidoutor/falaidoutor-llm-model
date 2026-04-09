#!/usr/bin/env python
"""Scripts de inicialização e setup do banco de dados."""

import os
import subprocess
import sys
from app.database import test_connection, init_db

def criar_banco_dados():
    """Cria o banco de dados PostgreSQL se não existir."""
    print("📦 Criando banco de dados PostgreSQL...")
    
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "postgres")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "fala_doutor")
    
    try:
        # Usar psql para criar banco de dados
        create_cmd = (
            f'psql -U {db_user} -h {db_host} -p {db_port} '
            f'-c "CREATE DATABASE {db_name};"'
        )
        
        # No Windows, é melhor usar uma abordagem diferente
        if sys.platform == "win32":
            print(f"⚠️  Para Windows, execute manualmente no PostgreSQL:")
            print(f"   CREATE DATABASE {db_name};")
        else:
            os.environ["PGPASSWORD"] = db_password
            result = subprocess.run(create_cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Banco de dados '{db_name}' criado com sucesso")
            else:
                print(f"⚠️  {result.stderr}")
        
        return True
    except Exception as e:
        print(f"❌ Erro ao criar banco de dados: {e}")
        return False


def testar_conexao():
    """Testa a conexão com o banco de dados."""
    print("🔗 Testando conexão com banco de dados...")
    return test_connection()


def inicializar_schema():
    """Inicializa o schema do banco de dados."""
    print("📊 Inicializando schema...")
    try:
        init_db()
        print("✅ Schema inicializado com sucesso")
        return True
    except Exception as e:
        print(f"❌ Erro ao inicializar schema: {e}")
        return False


def setup_completo():
    """Executa o setup completo do banco de dados."""
    print("\n" + "="*60)
    print("🎯 SETUP COMPLETO DO BANCO DE DADOS")
    print("="*60 + "\n")
    
    # Passo 1: Criar banco de dados
    if not criar_banco_dados():
        print("⚠️  Pulando criação de banco de dados...")
    
    # Passo 2: Testar conexão
    if not testar_conexao():
        print("❌ Não foi possível conectar ao banco de dados")
        print("\nVerifique se:")
        print("1. PostgreSQL está instalado e rodando")
        print("2. As variáveis de ambiente estão corretas (.env)")
        print("3. O banco de dados foi criado manualmente se necessário")
        return False
    
    # Passo 3: Inicializar schema
    if not inicializar_schema():
        return False
    
    print("\n" + "="*60)
    print("✅ SETUP CONCLUÍDO COM SUCESSO!")
    print("="*60 + "\n")
    return True


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    import argparse
    parser = argparse.ArgumentParser(description="Setup do banco de dados")
    parser.add_argument(
        "command",
        choices=["setup", "test", "init"],
        help="Comando a executar"
    )
    
    args = parser.parse_args()
    
    if args.command == "setup":
        setup_completo()
    elif args.command == "test":
        testar_conexao()
    elif args.command == "init":
        inicializar_schema()
