"""
Schemas Pydantic para Zoneamento Urbano de São Paulo
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ZoneamentoSPBase(BaseModel):
    """Schema base para Zoneamento de São Paulo"""

    cd_tipo_legislacao_zoneamento: Optional[str] = None
    cd_numero_legislacao_zoneamento: Optional[str] = None
    an_legislacao_zoneamento: Optional[int] = None
    cd_zoneamento_perimetro: Optional[str] = None
    tx_zoneamento_perimetro: Optional[str] = None
    cd_identificador: Optional[str] = None
    tx_observacao_perimetro: Optional[str] = None
    dt_atualizacao: Optional[datetime] = None
    cd_usuario_atualizacao: Optional[str] = None


class ZoneamentoSPProperties(ZoneamentoSPBase):
    """Propriedades de Zoneamento SP para GeoJSON"""

    id: int
    id_original: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    data_source: Optional[str] = "BIGQUERY_SP_ZONEAMENTO"

    class Config:
        from_attributes = True


class ZoneamentoSPFilter(BaseModel):
    """Filtros para busca de zoneamento"""

    cd_zoneamento_perimetro: Optional[str] = Field(
        None, description="Código do zoneamento (ex: ZEPAM, ZC, ZEIS-1, ZM, ZER-1)"
    )
    an_legislacao_zoneamento: Optional[int] = Field(
        None, ge=1900, le=2100, description="Ano da legislação"
    )
    cd_tipo_legislacao_zoneamento: Optional[str] = Field(
        None, description="Tipo da legislação (lei, decreto, etc.)"
    )
    bbox: Optional[str] = Field(
        None,
        description="Bounding box (min_lon,min_lat,max_lon,max_lat)",
        pattern=r"^-?\d+\.?\d*,-?\d+\.?\d*,-?\d+\.?\d*,-?\d+\.?\d*$",
    )


class ZoneamentoSPResponse(BaseModel):
    """Resposta da API com estatísticas"""

    total: int = Field(..., description="Total de registros encontrados")
    returned: int = Field(..., description="Número de registros retornados")
    features: list = Field(..., description="Features GeoJSON")

    class Config:
        from_attributes = True
