"""
Script para processar dados de Linhas de Transmissão da ANEEL
Lê arquivos Geodatabase (.gdb) e carrega no PostGIS
"""

import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd
from loguru import logger
from sqlalchemy import create_engine

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings


def setup_logging():
    """Configurar logging para o script"""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO",
    )
    logger.add(
        "logs/process_aneel_linhas_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="30 days",
        level="DEBUG",
    )


def validate_gdf(gdf: gpd.GeoDataFrame, layer_name: str) -> gpd.GeoDataFrame:
    """Valida e limpa GeoDataFrame"""
    logger.info(f"Validando {layer_name}...")

    original_count = len(gdf)
    logger.info(f"Registros originais: {original_count}")

    # Remover geometrias inválidas
    invalid_geoms = ~gdf.geometry.is_valid
    if invalid_geoms.any():
        logger.warning(
            f"Encontradas {invalid_geoms.sum()} geometrias inválidas. Tentando corrigir..."
        )
        gdf.loc[invalid_geoms, "geometry"] = gdf.loc[invalid_geoms, "geometry"].buffer(0)

    # Remover geometrias vazias
    gdf = gdf[~gdf.geometry.is_empty].copy()

    # Remover duplicatas
    gdf = gdf.drop_duplicates()

    # Converter para EPSG:4326
    if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
        logger.info(f"Convertendo CRS de {gdf.crs} para EPSG:4326...")
        gdf = gdf.to_crs(epsg=4326)
    elif gdf.crs is None:
        logger.warning("CRS não definido. Assumindo EPSG:4326")
        gdf.set_crs(epsg=4326, inplace=True)

    final_count = len(gdf)
    logger.info(
        f"Registros após validação: {final_count} ({original_count - final_count} removidos)"
    )

    return gdf


def process_linhas_transmissao(gdb_path: str, layer_name: str = None) -> None:
    """
    Processa linhas de transmissão de arquivo GDB da ANEEL

    Args:
        gdb_path: Caminho para o arquivo .gdb
        layer_name: Nome da camada (opcional)
    """
    logger.info("=" * 80)
    logger.info("PROCESSAMENTO DE LINHAS DE TRANSMISSÃO - ANEEL")
    logger.info("=" * 80)

    gdb_path = Path(gdb_path)

    if not gdb_path.exists():
        logger.error(f"Arquivo não encontrado: {gdb_path}")
        return

    logger.info(f"Arquivo GDB: {gdb_path}")

    try:
        # Listar camadas
        import fiona

        layers = fiona.listlayers(str(gdb_path))
        logger.info(f"Camadas disponíveis: {layers}")

        # Detectar camada de linhas
        if layer_name is None:
            possible_names = ["linha", "linhas", "transmissao", "transmission", "lt"]
            layer_name = next(
                (l for l in layers if any(name in l.lower() for name in possible_names)),
                layers[0] if layers else None,
            )

        if layer_name is None:
            logger.error("Nenhuma camada encontrada")
            return

        logger.info(f"Usando camada: {layer_name}")

        # Ler dados
        logger.info("Lendo dados...")
        gdf = gpd.read_file(gdb_path, layer=layer_name)

        logger.info(f"Colunas disponíveis: {list(gdf.columns)}")
        logger.info(f"Tipo de geometria: {gdf.geometry.type.unique()}")

        # Validar
        gdf = validate_gdf(gdf, layer_name)

        # Calcular extensão se não existir
        if "extensao_km" not in gdf.columns:
            logger.info("Calculando extensão das linhas...")
            # Converter para projeção métrica para cálculo preciso
            gdf_metric = gdf.to_crs(epsg=3857)  # Web Mercator
            gdf["extensao_km"] = gdf_metric.geometry.length / 1000

        # Preparar para inserção
        df_to_insert = gdf.copy()
        df_to_insert["data_source"] = "ANEEL"

        # Conectar ao banco
        logger.info("Conectando ao banco de dados...")
        engine = create_engine(settings.DATABASE_URL)

        # Inserir
        logger.info("Inserindo dados no PostGIS...")
        df_to_insert.to_postgis(
            name="linhas_transmissao",
            con=engine,
            schema="geo",
            if_exists="append",
            index=False,
        )

        logger.success(f"✅ {len(df_to_insert)} linhas de transmissão inseridas com sucesso!")

        # Estatísticas
        logger.info("\n" + "=" * 80)
        logger.info("ESTATÍSTICAS")
        logger.info("=" * 80)

        if "tensao_kv" in df_to_insert.columns:
            logger.info("\nDistribuição por tensão:")
            tensao_counts = df_to_insert["tensao_kv"].value_counts().sort_index()
            for tensao, count in tensao_counts.items():
                logger.info(f"  {tensao} kV: {count} linhas")

        if "extensao_km" in df_to_insert.columns:
            total_km = df_to_insert["extensao_km"].sum()
            media_km = df_to_insert["extensao_km"].mean()
            logger.info(f"\nExtensão total: {total_km:,.2f} km")
            logger.info(f"Extensão média: {media_km:,.2f} km")

        engine.dispose()

    except Exception as e:
        logger.error(f"Erro ao processar linhas: {e}")
        logger.exception(e)
        raise


def main():
    """Função principal"""
    setup_logging()

    # AJUSTAR O CAMINHO
    gdb_path = "data/raw/aneel_linhas_transmissao.gdb"

    process_linhas_transmissao(gdb_path)


if __name__ == "__main__":
    main()
