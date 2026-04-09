"""Testes de validação da conexão com banco de dados."""

import sys
import json
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def test_database_connection():
    """Testa a conexão básica com o banco de dados."""
    print("\n" + "="*60)
    print("🧪 TESTE DE CONEXÃO COM BANCO DE DADOS")
    print("="*60 + "\n")
    
    try:
        from app.config import test_connection, engine, init_db
        
        # Teste 1: Conexão básica
        print("✓ Teste 1: Conexão básica...")
        if not test_connection():
            print("❌ Falha na conexão com banco de dados")
            return False
        
        # Teste 2: Verificar se as tabelas existem
        print("✓ Teste 2: Verificando tabelas...")
        from sqlalchemy import inspect
        
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if "cid10_audit_log" in tables:
            print("  ✓ Tabela 'cid10_audit_log' existe")
        else:
            print("  ⚠️  Tabela 'cid10_audit_log' não encontrada (rodando init_db...)")
            try:
                init_db()
                print("  ✓ Schema inicializado com sucesso")
            except Exception as e:
                print(f"  ❌ Erro ao inicializar schema: {e}")
                return False
        
        # Teste 3: Operações básicas de CRUD
        print("✓ Teste 3: Testes de CRUD...")
        
        from app.repository.audit_repository import CID10AuditRepository
        
        repo = CID10AuditRepository()
        
        # Insert
        print("  - Inserindo registro de teste...")
        resultado = repo.registrar_mapeamento(
            sintomas_entrada="teste",
            sintomas_normalizados=["teste"],
            cid_sugeridos=[{"cid": "R51", "descricao": "Cefaleia"}],
            observacoes="Registro de teste"
        )
        
        if resultado["status"] == "registrado":
            print(f"  ✓ Registro inserido com ID: {resultado['id']}")
            registro_id = resultado["id"]
        else:
            print("  ❌ Falha ao inserir registro")
            return False
        
        # Select
        print("  - Lendo auditoria...")
        auditoria = repo.listar_auditoria(limite=1)
        if auditoria and len(auditoria) > 0:
            print(f"  ✓ {len(auditoria)} registro(s) lido(s)")
        else:
            print("  ❌ Falha ao ler registros")
            return False
        
        # Stats
        print("  - Obtendo estatísticas...")
        stats = repo.obter_estatisticas()
        print(f"  ✓ Total de mapeamentos: {stats['total_mapeamentos']}")
        print(f"  ✓ Taxa de validação: {stats['taxa_validacao']:.2f}%")
        
        # Update
        print("  - Atualizando validação...")
        if repo.atualizar_validacao(registro_id, True, medico_id=42, cid_final="R51"):
            print("  ✓ Validação atualizada com sucesso")
        else:
            print("  ❌ Falha ao atualizar validação")
            return False
        
        print("\n" + "="*60)
        print("✅ TODOS OS TESTES PASSARAM COM SUCESSO!")
        print("="*60 + "\n")
        return True
        
    except ImportError as e:
        print(f"❌ Erro ao importar: {e}")
        print("\nVerifique se todas as dependências estão instaladas:")
        print("  pip install -r requirements.txt")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ Erro durante testes: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_database_connection()
    sys.exit(0 if success else 1)
