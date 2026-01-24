"""
Modelo SQLAlchemy para Linhas de Transmissão
"""

from geoalchemy2 import Geometry
from sqlalchemy import Column, DateTime, Integer, Numeric, String, func

from app.core.database import Base


class LinhaTransmissao(Base):
    """
    Modelo para linhas de transmissão de alta tensão (ANEEL)
    """

    __tablename__ = "linhas_transmissao"
    __table_args__ = {"schema": "geo"}

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255))
    codigo = Column(String(100), index=True)
    tensao_kv = Column(Numeric, nullable=False, index=True)
    extensao_km = Column(Numeric)
    operador = Column(String(255))
    origem = Column(String(255))
    destino = Column(String(255))
    status = Column(String(50))

    # Geometria (LineString em EPSG:4326)
    geometry = Column(Geometry(geometry_type="LINESTRING", srid=4326), nullable=False)

    # Metadados
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    data_source = Column(String(100), default="ANEEL")

    def __repr__(self):
        return f"<LinhaTransmissao(id={self.id}, nome='{self.nome}', tensao_kv={self.tensao_kv})>"
