"""Repository para auditoria de mapeamentos CID-10."""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from ..config.database import SessionLocal
from ..models.audit_log import CID10AuditLog

logger = logging.getLogger(__name__)


class CID10AuditRepository:
    """Gerencia registros de auditoria de mapeamentos CID-10 em banco de dados."""

    def __init__(self, db_session: Optional[Session] = None):
        """
        Args:
            db_session: Sessão SQLAlchemy (opcional, usa SessionLocal por padrão)
        """
        self.db_session = db_session

    def _get_session(self) -> Session:
        """Retorna uma sessão de banco de dados."""
        if self.db_session:
            return self.db_session
        return SessionLocal()

    def registrar_mapeamento(
        self,
        sintomas_entrada: str,
        sintomas_normalizados: list[str],
        cid_sugeridos: list[dict],
        medico_id: Optional[str] = None,
        validado_medico: bool = False,
        observacoes: str = "",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> dict:
        """Registra um mapeamento CID-10 para auditoria.

        Args:
            sintomas_entrada: Texto original do paciente
            sintomas_normalizados: Sintomas após normalização
            cid_sugeridos: Lista de CIDs mapeados
            medico_id: ID do médico que validou (opcional)
            validado_medico: Se médico aprovou o mapeamento
            observacoes: Notas adicionais
            ip_address: IP do cliente
            user_agent: User agent do cliente

        Returns:
            dict com ID do registro e timestamp
        """
        session = self._get_session()
        try:
            # Preparar dados
            sintomas_json = json.dumps(sintomas_normalizados)
            cids_json = cid_sugeridos  # Já será armazenado como JSONB

            # Criar registro
            registro = CID10AuditLog(
                sintomas_entrada=sintomas_entrada,
                sintomas_normalizados=sintomas_json,
                cids_sugeridos=cids_json,
                numero_cids=len(cid_sugeridos),
                medico_id=int(medico_id) if medico_id else None,
                validado_medico=validado_medico,
                observacoes=observacoes,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            session.add(registro)
            session.commit()

            logger.info(f"Auditoria registrada: {registro.id} - {len(cid_sugeridos)} CIDs mapeados")

            return {
                "id": registro.id,
                "timestamp": registro.data_hora.isoformat(),
                "status": "registrado"
            }

        except Exception as e:
            session.rollback()
            logger.error(f"Erro ao registrar auditoria: {str(e)}")
            raise
        finally:
            if not self.db_session:  # Fechar apenas se não foi fornecida uma sessão
                session.close()

    def listar_auditoria(self, limite: int = 100, offset: int = 0) -> list[dict]:
        """Lista registros de auditoria com paginação.

        Args:
            limite: Número máximo de registros
            offset: Número de registros a pular

        Returns:
            Lista de registros de auditoria
        """
        session = self._get_session()
        try:
            registros = session.query(CID10AuditLog) \
                .order_by(desc(CID10AuditLog.data_hora)) \
                .limit(limite) \
                .offset(offset) \
                .all()

            return [r.to_dict() for r in registros]

        finally:
            if not self.db_session:
                session.close()

    def obter_estatisticas(self) -> dict:
        """Calcula estatísticas de auditoria.

        Returns:
            Dict com métricas
        """
        session = self._get_session()
        try:
            total = session.query(func.count(CID10AuditLog.id)).scalar() or 0
            validados = session.query(func.count(CID10AuditLog.id)) \
                .filter(CID10AuditLog.validado_medico == True) \
                .scalar() or 0
            total_cids = session.query(func.sum(CID10AuditLog.numero_cids)).scalar() or 0

            return {
                "total_mapeamentos": total,
                "validados_medico": validados,
                "taxa_validacao": (validados / total * 100) if total > 0 else 0.0,
                "total_cids_mapeados": total_cids,
                "media_cids_por_mapeamento": total_cids / total if total > 0 else 0.0
            }

        finally:
            if not self.db_session:
                session.close()

    def listar_cids_mais_mapeados(self, limite: int = 10) -> list[dict]:
        """Retorna CIDs mais frequentemente mapeados.

        Args:
            limite: Top N

        Returns:
            Lista com CID, descrição e contagem
        """
        session = self._get_session()
        try:
            registros = session.query(CID10AuditLog) \
                .order_by(desc(CID10AuditLog.data_hora)) \
                .all()

            cid_count = {}

            for registro in registros:
                try:
                    cids = registro.cids_sugeridos if isinstance(registro.cids_sugeridos, list) else []
                    for cid in cids:
                        cid_codigo = cid.get("cid", "")
                        if cid_codigo not in cid_count:
                            cid_count[cid_codigo] = {
                                "cid": cid_codigo,
                                "descricao": cid.get("descricao", ""),
                                "contagem": 0
                            }
                        cid_count[cid_codigo]["contagem"] += 1
                except Exception as e:
                    logger.warning(f"Erro ao processar CIDs do registro {registro.id}: {e}")

            # Ordenar por frequência
            ordenados = sorted(
                cid_count.values(),
                key=lambda x: x["contagem"],
                reverse=True
            )

            return ordenados[:limite]

        finally:
            if not self.db_session:
                session.close()

    def buscar_por_periodo(self, data_inicio: str, data_fim: str) -> list[dict]:
        """Busca mapeamentos em um período.

        Args:
            data_inicio: ISO format (2026-04-08)
            data_fim: ISO format (2026-04-08)

        Returns:
            Lista de registros no período
        """
        session = self._get_session()
        try:
            from datetime import datetime
            inicio = datetime.fromisoformat(data_inicio)
            fim = datetime.fromisoformat(data_fim) + timedelta(days=1)

            registros = session.query(CID10AuditLog) \
                .filter(CID10AuditLog.data_hora >= inicio) \
                .filter(CID10AuditLog.data_hora < fim) \
                .order_by(desc(CID10AuditLog.data_hora)) \
                .all()

            return [r.to_dict() for r in registros]

        finally:
            if not self.db_session:
                session.close()

    def exportar_csv(self, arquivo_saida: str = "auditoria_cid10.csv") -> str:
        """Exporta auditoria como CSV para relatório.

        Args:
            arquivo_saida: Caminho do arquivo

        Returns:
            Caminho do arquivo gerado
        """
        import csv

        session = self._get_session()
        try:
            registros = session.query(CID10AuditLog) \
                .order_by(desc(CID10AuditLog.data_hora)) \
                .all()

            if not registros:
                logger.warning("Nenhum registro para exportar")
                return ""

            with open(arquivo_saida, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "id",
                        "data_hora",
                        "sintomas_entrada",
                        "numero_cids",
                        "cids_mapeados",
                        "validado_medico",
                        "observacoes"
                    ]
                )

                writer.writeheader()

                for registro in registros:
                    try:
                        cids = registro.cids_sugeridos if isinstance(registro.cids_sugeridos, list) else []
                        cids_str = ", ".join(
                            f"{cid.get('cid', '')} ({cid.get('descricao', '')})"
                            for cid in cids
                        )

                        writer.writerow({
                            "id": registro.id,
                            "data_hora": registro.data_hora.isoformat(),
                            "sintomas_entrada": registro.sintomas_entrada,
                            "numero_cids": registro.numero_cids,
                            "cids_mapeados": cids_str,
                            "validado_medico": "SIM" if registro.validado_medico else "NÃO",
                            "observacoes": registro.observacoes or ""
                        })
                    except Exception as e:
                        logger.error(f"Erro ao exportar registro {registro.id}: {e}")

            logger.info(f"Auditoria exportada: {arquivo_saida}")
            return arquivo_saida

        except Exception as e:
            logger.error(f"Erro ao exportar auditoria: {str(e)}")
            return ""
        finally:
            if not self.db_session:
                session.close()

    def limpar_auditoria_antiga(self, dias: int = 90) -> int:
        """Limpa registros de auditoria mais antigos que N dias.

        Args:
            dias: Número de dias

        Returns:
            Número de registros removidos
        """
        session = self._get_session()
        try:
            data_limite = datetime.utcnow() - timedelta(days=dias)

            resultado = session.query(CID10AuditLog) \
                .filter(CID10AuditLog.data_hora < data_limite) \
                .delete()

            session.commit()
            logger.warning(f"Auditoria limpa: {resultado} registros antigos removidos")
            return resultado

        except Exception as e:
            session.rollback()
            logger.error(f"Erro ao limpar auditoria: {str(e)}")
            raise
        finally:
            if not self.db_session:
                session.close()

    def atualizar_validacao(self, registro_id: int, validado_medico: bool, medico_id: Optional[int] = None, cid_final: Optional[str] = None) -> bool:
        """Atualiza validação de um mapeamento por médico.

        Args:
            registro_id: ID do registro
            validado_medico: Se foi validado
            medico_id: ID do médico
            cid_final: CID final escolhido

        Returns:
            True se atualizado com sucesso
        """
        session = self._get_session()
        try:
            registro = session.query(CID10AuditLog).filter(
                CID10AuditLog.id == registro_id
            ).first()

            if not registro:
                logger.warning(f"Registro {registro_id} não encontrado")
                return False

            registro.validado_medico = validado_medico
            if medico_id:
                registro.medico_id = medico_id
            if cid_final:
                registro.cid_final = cid_final

            session.commit()
            logger.info(f"Validação do registro {registro_id} atualizada")
            return True

        except Exception as e:
            session.rollback()
            logger.error(f"Erro ao atualizar validação: {str(e)}")
            raise
        finally:
            if not self.db_session:
                session.close()

