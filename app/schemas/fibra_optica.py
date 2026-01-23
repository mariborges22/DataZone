"""
Schemas para Fibra Ótica
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class FibraOpticaBase(BaseModel):
    """Schema base para Fibra Ótica"""

    operadora: Optional[str] = None
    tipo: Optional[str] = None
    tecnologia: Optional[str] = None
    municipio: Optional[str] = None
    uf: Optional[str] = None
    capacidade_gbps: Optional[float] = None
    status: Optional[str] = None


class FibraOpticaProperties(FibraOpticaBase):
    """Propriedades de Fibra Ótica para GeoJSON"""

    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    data_source: Optional[str] = "ANATEL"

    class Config:
        from_attributes = True


class FibraOpticaFilter(BaseModel):
    """Filtros para busca de infraestrutura de fibra"""

    uf: Optional[str] = Field(None, max_length=2, description="Unidade Federativa")
    municipio: Optional[str] = Field(None, description="Nome do município")
    operadora: Optional[str] = Field(None, description="Nome da operadora")
    tecnologia: Optional[str] = Field(None, description="Tipo de tecnologia")
    capacidade_min: Optional[float] = Field(None, ge=0, description="Capacidade mínima (Gbps)")
