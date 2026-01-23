import os
import sys

import geopandas as gpd
from shapely.geometry import LineString, MultiLineString
from sqlalchemy import create_engine

from app.config import settings
from app.core.logging import app_logger as logger

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


def extrair_linhas_at(gdb_path: str):
    """
    Lê o .gdb da ANEEL, filtra Linhas de Transmissão de Alta Tensão (AT),
    converte CRS e salva como MultiLineString no PostGIS.
    """
    logger.info(f"Iniciando extração de linhas de transmissão: {gdb_path}")

    if not os.path.exists(gdb_path):
        logger.error(f"Arquivo não encontrado: {gdb_path}")
        return

    try:
        # Camada de Segmentos de Rede ou Linhas de Transmissão
        # Geralmente 'SSD' (Segmento de Rede de Distribuição) ou 'SLT' (Segmento de Linha de Transmissão)
        layer_name = "SLT"  # Ajustar conforme nome real da camada no GDB

        logger.info(f"Lendo camada '{layer_name}'...")
        gdf = gpd.read_file(gdb_path, layer=layer_name)

        logger.info(f"Total de segmentos encontrados: {len(gdf)}")

        # Filtrar Alta Tensão (ex: > 69kV)
        if "TEN_NOM" in gdf.columns:
            gdf_at = gdf[gdf["TEN_NOM"].astype(float) >= 69]
            logger.info(f"Linhas AT filtradas: {len(gdf_at)}")
        else:
            logger.warning("Coluna de tensão não encontrada. Processando todas as linhas.")
            gdf_at = gdf

        # Converter CRS
        if gdf_at.crs != "EPSG:4326":
            logger.info("Convertendo CRS para EPSG:4326...")
            gdf_at = gdf_at.to_crs("EPSG:4326")

        # Garantir geometria MultiLineString
        # O PostGIS pode reclamar se misturar LineString e MultiLineString na mesma coluna geometry(MultiLineString)
        def force_multilinestring(geom):
            if isinstance(geom, LineString):
                return MultiLineString([geom])
            return geom

        gdf_at["geometry"] = gdf_at["geometry"].apply(force_multilinestring)

        # Mapeamento de colunas
        columns_map = {
            "NOME": "nome",
            "COD_ID": "codigo",
            "TEN_NOM": "tensao_kv",
            "COMP": "comprimento_km",
        }
        valid_columns = {k: v for k, v in columns_map.items() if k in gdf_at.columns}
        gdf_final = gdf_at.rename(columns=valid_columns)

        # Salvar no Banco
        engine = create_engine(settings.DATABASE_URL)
        table_name = "linhas_transmissao"

        logger.info(f"Salvando {len(gdf_final)} linhas na tabela '{table_name}'...")
        gdf_final.to_postgis(
            table_name,
            engine,
            if_exists="replace",
            index=False,
            dtype={"geometry": "MultiLineString"},
        )
        logger.info("Extração de linhas concluída!")

    except Exception as e:
        logger.critical(f"Erro na extração de linhas: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    gdb_path = os.getenv("ANEEL_GDB_PATH", "data/raw/BDGD_ANEEL.gdb")
    extrair_linhas_at(gdb_path)
