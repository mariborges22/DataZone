"""
Schemas para Subestações
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SubestacaoBase(BaseModel):
    """Schema base para Subestação"""

    nome: str
    codigo: Optional[str] = None
    tensao_kv: Optional[float] = None
    tipo: Optional[str] = None
    operador: Optional[str] = None
    municipio: Optional[str] = None
    uf: Optional[str] = None
    capacidade_mva: Optional[float] = None
    status: Optional[str] = None


class SubestacaoProperties(SubestacaoBase):
    """Propriedades de Subestação para GeoJSON"""

    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    data_source: Optional[str] = "ANEEL"

    class Config:
        from_attributes = True


class SubestacaoFilter(BaseModel):
    """Filtros para busca de subestações"""

    uf: Optional[str] = Field(None, max_length=2, description="Unidade Federativa")
    municipio: Optional[str] = Field(None, description="Nome do município")
    tensao_min: Optional[float] = Field(None, ge=0, description="Tensão mínima (kV)")
    tensao_max: Optional[float] = Field(None, ge=0, description="Tensão máxima (kV)")
    operador: Optional[str] = Field(None, description="Nome do operador")
    tipo: Optional[str] = Field(None, description="Tipo de subestação")
