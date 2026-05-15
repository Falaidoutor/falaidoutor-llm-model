"""
Script para corrigir dados no PostgreSQL e reinicializar Qdrant.
"""

from app.service.postgres_service import PostgresService
from app.service.qdrant_service import QdrantService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

postgres_svc = PostgresService()

# 1. Delete old unapproved synonym
try:
    conn = postgres_svc._get_connection()
    cursor = conn.cursor()
    
    # Delete 'sensação de queda' with aprovado=FALSE
    cursor.execute("""
        DELETE FROM falai_doutor_normalizacao.sinonimos 
        WHERE termo = 'sensação de queda' AND aprovado = FALSE
    """)
    
    rows_deleted = cursor.rowcount
    print(f"✓ Deletados {rows_deleted} sinonimos 'sensação de queda' com aprovado=FALSE")
    
    conn.commit()
    cursor.close()
    postgres_svc._return_connection(conn)
except Exception as e:
    print(f"✗ Erro ao deletar: {e}")
    import traceback
    traceback.print_exc()

# 2. Insert the corrected approved version
try:
    conn = postgres_svc._get_connection()
    cursor = conn.cursor()
    
    # Get Tonturas id
    cursor.execute("SELECT id FROM falai_doutor_normalizacao.sintomas WHERE termo = 'Tonturas'")
    tonturas_id = cursor.fetchone()[0]
    print(f"Tonturas ID: {tonturas_id}")
    
    # Insert approved version
    cursor.execute("""
        INSERT INTO falai_doutor_normalizacao.sinonimos (sintoma_id, termo, origem, aprovado)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (termo, sintoma_id) DO NOTHING
    """, (tonturas_id, 'sensação de queda', 'usuario', True))
    
    rows_inserted = cursor.rowcount
    print(f"✓ Inseridos {rows_inserted} sinonimos 'sensação de queda' com aprovado=TRUE")
    
    conn.commit()
    cursor.close()
    postgres_svc._return_connection(conn)
except Exception as e:
    print(f"✗ Erro ao inserir: {e}")
    import traceback
    traceback.print_exc()

# 3. Verify data was inserted
try:
    conn = postgres_svc._get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, termo, sintoma_id, aprovado 
        FROM falai_doutor_normalizacao.sinonimos 
        WHERE termo = 'sensação de queda'
    """)
    
    results = cursor.fetchall()
    print(f"\n✓ Sinonimos 'sensação de queda' no banco:")
    for r in results:
        print(f"  - ID: {r[0]}, termo: {r[1]}, sintoma_id: {r[2]}, aprovado: {r[3]}")
    
    cursor.close()
    postgres_svc._return_connection(conn)
except Exception as e:
    print(f"✗ Erro ao verificar: {e}")

print("\n" + "="*60)
print("Agora execute: python -m app.scripts.init_qdrant")
print("="*60)
