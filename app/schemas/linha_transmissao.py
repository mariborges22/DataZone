"""
Schemas para Linhas de Transmissão
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class LinhaTransmissaoBase(BaseModel):
    """Schema base para Linha de Transmissão"""

    nome: Optional[str] = None
    codigo: Optional[str] = None
    tensao_kv: float
    extensao_km: Optional[float] = None
    operador: Optional[str] = None
    origem: Optional[str] = None
    destino: Optional[str] = None
    status: Optional[str] = None


class LinhaTransmissaoProperties(LinhaTransmissaoBase):
    """Propriedades de Linha de Transmissão para GeoJSON"""

    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    data_source: Optional[str] = "ANEEL"

    class Config:
        from_attributes = True


class LinhaTransmissaoFilter(BaseModel):
    """Filtros para busca de linhas de transmissão"""

    tensao_min: Optional[float] = Field(None, ge=0, description="Tensão mínima (kV)")
    tensao_max: Optional[float] = Field(None, ge=0, description="Tensão máxima (kV)")
    operador: Optional[str] = Field(None, description="Nome do operador")
    origem: Optional[str] = Field(None, description="Subestação de origem")
    destino: Optional[str] = Field(None, description="Subestação de destino")
