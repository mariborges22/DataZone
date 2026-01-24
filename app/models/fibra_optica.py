"""
Modelo SQLAlchemy para Infraestrutura de Fibra Ótica
"""

from geoalchemy2 import Geometry
from sqlalchemy import Column, DateTime, Integer, Numeric, String, func

from app.core.database import Base


class FibraOptica(Base):
    """
    Modelo para infraestrutura de fibra ótica (ANATEL)
    """

    __tablename__ = "fibra_optica"
    __table_args__ = {"schema": "geo"}

    id = Column(Integer, primary_key=True, index=True)
    operadora = Column(String(255), index=True)
    tipo = Column(String(100))
    tecnologia = Column(String(100))
    municipio = Column(String(255), index=True)
    uf = Column(String(2), index=True)
    capacidade_gbps = Column(Numeric)
    status = Column(String(50))

    # Geometria (Point em EPSG:4326)
    geometry = Column(Geometry(geometry_type="POINT", srid=4326), nullable=False)

    # Metadados
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    data_source = Column(String(100), default="ANATEL")

    def __repr__(self):
        return f"<FibraOptica(id={self.id}, operadora='{self.operadora}', municipio='{self.municipio}')>"
