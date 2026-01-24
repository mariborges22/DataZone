"""
Modelo SQLAlchemy para Subestações
"""

from geoalchemy2 import Geometry
from sqlalchemy import Column, DateTime, Integer, Numeric, String, func

from app.core.database import Base


class Subestacao(Base):
    """
    Modelo para subestações de energia elétrica (ANEEL)
    """

    __tablename__ = "subestacoes"
    __table_args__ = {"schema": "geo"}

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    codigo = Column(String(100), index=True)
    tensao_kv = Column(Numeric)
    tipo = Column(String(100))
    operador = Column(String(255))
    municipio = Column(String(255), index=True)
    uf = Column(String(2), index=True)
    capacidade_mva = Column(Numeric)
    status = Column(String(50))

    # Geometria (Point em EPSG:4326)
    geometry = Column(Geometry(geometry_type="POINT", srid=4326), nullable=False)

    # Metadados
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    data_source = Column(String(100), default="ANEEL")

    def __repr__(self):
        return f"<Subestacao(id={self.id}, nome='{self.nome}', tensao_kv={self.tensao_kv})>"
