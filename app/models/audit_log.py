"""Modelo SQLAlchemy para auditoria de mapeamento CID-10."""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

from .base import Base


class CID10AuditLog(Base):
    """Modelo para registros de auditoria de mapeamento CID-10."""
    
    __tablename__ = "cid10_audit_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    data_hora = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    sintomas_entrada = Column(Text, nullable=False)
    sintomas_normalizados = Column(Text, nullable=False)  # JSON string ou array
    cids_sugeridos = Column(JSONB, nullable=False)
    numero_cids = Column(Integer, nullable=False)
    medico_id = Column(Integer, nullable=True, index=True)
    validado_medico = Column(Boolean, default=False, nullable=False, index=True)
    cid_final = Column(String(10), nullable=True, index=True)
    observacoes = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    __table_args__ = (
        CheckConstraint("numero_cids > 0", name="cid10_audit_log_not_null"),
        Index("idx_cid10_audit_data", "data_hora"),
        Index("idx_cid10_audit_medico", "medico_id"),
        Index("idx_cid10_audit_validacao", "validado_medico"),
        Index("idx_cid10_audit_cid_final", "cid_final"),
    )
    
    def to_dict(self):
        """Converte registro para dicionário."""
        return {
            "id": self.id,
            "data_hora": self.data_hora.isoformat() if self.data_hora else None,
            "sintomas_entrada": self.sintomas_entrada,
            "sintomas_normalizados": self.sintomas_normalizados,
            "cids_sugeridos": self.cids_sugeridos,
            "numero_cids": self.numero_cids,
            "medico_id": self.medico_id,
            "validado_medico": self.validado_medico,
            "cid_final": self.cid_final,
            "observacoes": self.observacoes,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
        }
