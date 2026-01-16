"""
Utilitários GIS para conversão de geometrias
"""

import json
from typing import Any, Dict, List

from geoalchemy2.shape import to_shape
from shapely.geometry import mapping
from sqlalchemy.engine import Row


def geometry_to_geojson(geometry) -> Dict[str, Any]:
    """
    Converte geometria GeoAlchemy2 para dict GeoJSON

    Args:
        geometry: Objeto GeoAlchemy2 Geometry

    Returns:
        Dict com type e coordinates
    """
    if geometry is None:
        return None

    # Converter para Shapely geometry
    shape = to_shape(geometry)

    # Converter para GeoJSON dict
    return mapping(shape)


def row_to_feature(row: Row, geometry_column: str = "geometry") -> Dict[str, Any]:
    """
    Converte uma linha do banco em Feature GeoJSON

    Args:
        row: Linha do resultado da query
        geometry_column: Nome da coluna de geometria

    Returns:
        Dict Feature GeoJSON
    """
    # Converter row para dict
    row_dict = dict(row._mapping)

    # Extrair geometria
    geometry = row_dict.pop(geometry_column, None)
    geojson_geometry = geometry_to_geojson(geometry)

    # Converter datetime para string ISO
    properties = {}
    for key, value in row_dict.items():
        if hasattr(value, "isoformat"):
            properties[key] = value.isoformat()
        else:
            properties[key] = value

    return {"type": "Feature", "geometry": geojson_geometry, "properties": properties}


def rows_to_feature_collection(
    rows: List[Row], geometry_column: str = "geometry"
) -> Dict[str, Any]:
    """
    Converte lista de linhas em FeatureCollection GeoJSON

    Args:
        rows: Lista de linhas do resultado da query
        geometry_column: Nome da coluna de geometria

    Returns:
        Dict FeatureCollection GeoJSON
    """
    features = [row_to_feature(row, geometry_column) for row in rows]

    return {"type": "FeatureCollection", "features": features}


def simplify_geometry_query(tolerance: float = 0.001) -> str:
    """
    Retorna SQL para simplificar geometrias usando ST_Simplify

    Args:
        tolerance: Tolerância para simplificação (graus em EPSG:4326)

    Returns:
        String SQL para usar em queries
    """
    return f"ST_Simplify(geometry, {tolerance})"
