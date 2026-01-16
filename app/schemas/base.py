"""
Schemas base para GeoJSON
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class GeometryBase(BaseModel):
    """Schema base para geometrias GeoJSON"""

    type: str
    coordinates: List[Any]


class PropertiesBase(BaseModel):
    """Schema base para propriedades de features"""

    id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    data_source: Optional[str] = None


class FeatureBase(BaseModel):
    """Schema base para Feature GeoJSON"""

    type: str = "Feature"
    geometry: GeometryBase
    properties: Dict[str, Any]


class FeatureCollectionBase(BaseModel):
    """Schema base para FeatureCollection GeoJSON"""

    type: str = "FeatureCollection"
    features: List[FeatureBase]

    class Config:
        json_schema_extra = {
            "example": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [-46.6333, -23.5505],
                        },
                        "properties": {"id": 1, "nome": "Exemplo"},
                    }
                ],
            }
        }


class BBoxFilter(BaseModel):
    """Schema para filtro de bounding box"""

    min_lon: float = Field(..., ge=-180, le=180, description="Longitude mínima")
    min_lat: float = Field(..., ge=-90, le=90, description="Latitude mínima")
    max_lon: float = Field(..., ge=-180, le=180, description="Longitude máxima")
    max_lat: float = Field(..., ge=-90, le=90, description="Latitude máxima")

    class Config:
        json_schema_extra = {
            "example": {
                "min_lon": -46.8,
                "min_lat": -23.7,
                "max_lon": -46.4,
                "max_lat": -23.4,
            }
        }


class PaginationParams(BaseModel):
    """Schema para parâmetros de paginação"""

    skip: int = Field(0, ge=0, description="Número de registros para pular")
    limit: int = Field(100, ge=1, le=1000, description="Número máximo de registros")
