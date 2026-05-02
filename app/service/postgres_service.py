"""
Serviço de integração com PostgreSQL para operações com sintomas e sinonimos.
Utiliza psycopg3 para conexões síncronas ao PostgreSQL.
"""

import logging
from typing import Dict, List, Optional, Any
import psycopg
from psycopg_pool import ConnectionPool
from datetime import datetime

from app.config.settings import (
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_DB,
    POSTGRES_USER,
    POSTGRES_PASSWORD,
    POSTGRES_POOL_SIZE,
)

logger = logging.getLogger(__name__)


class PostgresService:
    """
    Gerencia conexões e queries ao PostgreSQL.
    Usa connection pool para otimizar performance.
    """

    _instance = None
    _pool = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        try:
            logger.info(
                f"Inicializando PostgreSQL pool: {POSTGRES_USER}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
            )

            # Build connection string for psycopg3
            dsn = (
                f"dbname={POSTGRES_DB} "
                f"user={POSTGRES_USER} "
                f"password={POSTGRES_PASSWORD} "
                f"host={POSTGRES_HOST} "
                f"port={POSTGRES_PORT}"
            )

            self._pool = ConnectionPool(
                dsn,
                min_size=1,
                max_size=POSTGRES_POOL_SIZE,
            )

            self._initialized = True
            logger.info("PostgresService inicializado com sucesso")

        except Exception as e:
            logger.error(f"Erro ao inicializar PostgreSQL: {e}")
            raise

    def _get_connection(self):
        """Obtém conexão do pool."""
        try:
            return self._pool.getconn()
        except Exception as e:
            logger.error(f"Erro ao obter conexão do pool: {e}")
            raise

    def _return_connection(self, conn):
        """Devolve conexão ao pool."""
        if conn:
            self._pool.putconn(conn)

    def get_sinonimo_data(self, sinonimo_id: int) -> Optional[Dict[str, Any]]:
        """
        Busca um sinonimo e seus dados relacionados.

        Returns:
            {
                "id": int,
                "termo": str,
                "sintoma_id": int,
                "categoria": str (do sintoma),
                "aprovado": bool,
            }
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = """
                SELECT s.id, s.termo, s.sintoma_id, syn.termo as termo_sinonimo, syn.aprovado
                FROM falai_doutor_normalizacao.sinonimos s
                JOIN falai_doutor_normalizacao.sintomas syn ON s.sintoma_id = syn.id
                WHERE s.id = %s
            """

            cursor.execute(query, (sinonimo_id,))
            result = cursor.fetchone()
            cursor.close()

            if result:
                return {
                    "id": result[0],
                    "termo_sinonimo": result[1],
                    "sintoma_id": result[2],
                    "termo_canonico": result[3],
                    "aprovado": result[4],
                }
            return None

        except Exception as e:
            logger.error(f"Erro ao buscar sinonimo {sinonimo_id}: {e}")
            return None

        finally:
            self._return_connection(conn)

    def get_sintoma_canonico(self, sintoma_id: int) -> Optional[str]:
        """
        Retorna o termo canônico de um sintoma.
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = "SELECT termo FROM falai_doutor_normalizacao.sintomas WHERE id = %s"
            cursor.execute(query, (sintoma_id,))
            result = cursor.fetchone()
            cursor.close()

            return result[0] if result else None

        except Exception as e:
            logger.error(f"Erro ao buscar sintoma canônico {sintoma_id}: {e}")
            return None

        finally:
            self._return_connection(conn)

    def search_sinonimos(self, termo: str, limite: int = 10) -> List[Dict[str, Any]]:
        """
        Busca sinonimos por termo (para debug/admin).
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = """
                SELECT id, termo, sintoma_id, aprovado
                FROM falai_doutor_normalizacao.sinonimos
                WHERE termo ILIKE %s
                LIMIT %s
            """

            cursor.execute(query, (f"%{termo}%", limite))
            results = cursor.fetchall()
            cursor.close()

            return [
                {
                    "id": r[0],
                    "termo": r[1],
                    "sintoma_id": r[2],
                    "aprovado": r[3],
                }
                for r in results
            ]

        except Exception as e:
            logger.error(f"Erro ao buscar sinonimos: {e}")
            return []

        finally:
            self._return_connection(conn)

    def create_base_candidata(
        self,
        input_original: str,
        normalizado_sugerido: str,
        sintoma_id: Optional[int] = None,
        score_e5: Optional[float] = None,
        score_ollama_confianca: Optional[str] = None,
    ) -> Optional[int]:
        """
        Registra um termo na tabela base_candidata para auditoria/aprendizado.

        Returns:
            ID do registro criado, ou None se erro
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = """
                INSERT INTO falai_doutor_normalizacao.base_candidata (
                    input_original,
                    normalizado_sugerido,
                    sintoma_id,
                    score_e5,
                    score_ollama_confianca,
                    origem,
                    status,
                    criado_em
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """

            cursor.execute(
                query,
                (
                    input_original,
                    normalizado_sugerido,
                    sintoma_id,
                    score_e5,
                    score_ollama_confianca,
                    "ollama",  # origem
                    "pendente",  # status inicial
                    datetime.now(),
                ),
            )

            candidate_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()

            logger.info(f"Base candidata criada com ID {candidate_id}")
            return candidate_id

        except Exception as e:
            logger.error(f"Erro ao criar base_candidata: {e}")
            if conn:
                conn.rollback()
            return None

        finally:
            self._return_connection(conn)

    def get_base_candidata_pendentes(self, limite: int = 50) -> List[Dict[str, Any]]:
        """
        Busca candidatos pendentes de auditoria.
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = """
                SELECT id, input_original, normalizado_sugerido, sintoma_id, score_e5, score_ollama_confianca, criado_em
                FROM falai_doutor_normalizacao.base_candidata
                WHERE status = 'pendente'
                ORDER BY criado_em DESC
                LIMIT %s
            """

            cursor.execute(query, (limite,))
            results = cursor.fetchall()
            cursor.close()

            return [
                {
                    "id": r[0],
                    "input_original": r[1],
                    "normalizado_sugerido": r[2],
                    "sintoma_id": r[3],
                    "score_e5": r[4],
                    "score_ollama_confianca": r[5],
                    "criado_em": r[6],
                }
                for r in results
            ]

        except Exception as e:
            logger.error(f"Erro ao buscar base_candidata pendentes: {e}")
            return []

        finally:
            self._return_connection(conn)

    def approve_base_candidata(self, candidato_id: int) -> bool:
        """
        Aprova um candidato (move para sinonimos + marca como aprovado).
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Obter dados do candidato
            query = "SELECT input_original, normalizado_sugerido, sintoma_id FROM falai_doutor_normalizacao.base_candidata WHERE id = %s"
            cursor.execute(query, (candidato_id,))
            result = cursor.fetchone()

            if not result:
                logger.warning(f"Candidato {candidato_id} não encontrado")
                return False

            input_original, normalizado_sugerido, sintoma_id = result

            # Inserir em sinonimos
            if sintoma_id:
                insert_query = """
                    INSERT INTO falai_doutor_normalizacao.sinonimos (sintoma_id, termo, origem, aprovado, criado_em)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(
                    insert_query,
                    (sintoma_id, normalizado_sugerido, "ollama", True, datetime.now()),
                )

            # Marcar candidato como aprovado
            update_query = "UPDATE falai_doutor_normalizacao.base_candidata SET status = 'aprovado', revisado = TRUE WHERE id = %s"
            cursor.execute(update_query, (candidato_id,))

            conn.commit()
            cursor.close()

            logger.info(f"Candidato {candidato_id} aprovado")
            return True

        except Exception as e:
            logger.error(f"Erro ao aprovar candidato: {e}")
            if conn:
                conn.rollback()
            return False

        finally:
            self._return_connection(conn)

    def reject_base_candidata(self, candidato_id: int, motivo: str = "") -> bool:
        """
        Rejeita um candidato.
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = "UPDATE falai_doutor_normalizacao.base_candidata SET status = 'rejeitado', revisado = TRUE WHERE id = %s"
            cursor.execute(query, (candidato_id,))

            if motivo:
                query_audit = """
                    INSERT INTO falai_doutor_normalizacao.auditoria (candidato_id, decisao, justificativa, auditado_por, criado_em)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(
                    query_audit,
                    (candidato_id, "rejeitar", motivo, "humano", datetime.now()),
                )

            conn.commit()
            cursor.close()

            logger.info(f"Candidato {candidato_id} rejeitado")
            return True

        except Exception as e:
            logger.error(f"Erro ao rejeitar candidato: {e}")
            if conn:
                conn.rollback()
            return False

        finally:
            self._return_connection(conn)

    def get_all_sinonimos(self) -> List[Dict[str, Any]]:
        """
        Carrega todos os sinonimos aprovados para inicializar Qdrant.
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = """
                SELECT id, termo, sintoma_id
                FROM falai_doutor_normalizacao.sinonimos
                WHERE aprovado = TRUE
                ORDER BY id
            """

            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()

            return [
                {
                    "id": r[0],
                    "termo": r[1],
                    "sintoma_id": r[2],
                }
                for r in results
            ]

        except Exception as e:
            logger.error(f"Erro ao buscar sinonimos: {e}")
            return []

        finally:
            self._return_connection(conn)

    def get_all_sintomas(self) -> List[Dict[str, Any]]:
        """
        Carrega todos os sintomas canônicos para inicializar Qdrant.
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = """
                SELECT id, termo, categoria
                FROM falai_doutor_normalizacao.sintomas
                WHERE ativo = TRUE
                ORDER BY id
            """

            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()

            return [
                {
                    "id": r[0],
                    "termo": r[1],
                    "categoria": r[2],
                }
                for r in results
            ]

        except Exception as e:
            logger.error(f"Erro ao buscar sintomas: {e}")
            return []

        finally:
            self._return_connection(conn)

    def close_pool(self):
        """Fecha o pool de conexões."""
        if self._pool:
            self._pool.closeall()
            logger.info("PostgreSQL pool fechado")
