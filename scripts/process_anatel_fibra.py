"""
Script para processar dados de Fibra Ótica da ANATEL
Lê arquivos CSV e carrega no PostGIS
"""

import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd
from loguru import logger
from shapely.geometry import Point
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
        "logs/process_anatel_fibra_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="30 days",
        level="DEBUG",
    )


def create_geometry_from_coords(
    df: pd.DataFrame, lat_col: str = "latitude", lon_col: str = "longitude"
) -> gpd.GeoDataFrame:
    """
    Cria geometrias Point a partir de coordenadas

    Args:
        df: DataFrame com coordenadas
        lat_col: Nome da coluna de latitude
        lon_col: Nome da coluna de longitude

    Returns:
        GeoDataFrame com geometrias
    """
    logger.info("Criando geometrias a partir de coordenadas...")

    # Remover linhas sem coordenadas
    df = df.dropna(subset=[lat_col, lon_col])

    # Criar geometrias
    geometry = [Point(xy) for xy in zip(df[lon_col], df[lat_col])]

    # Criar GeoDataFrame
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")

    logger.info(f"Geometrias criadas: {len(gdf)}")

    return gdf


def process_fibra_optica(csv_path: str) -> None:
    """
    Processa dados de fibra ótica da ANATEL

    Args:
        csv_path: Caminho para o arquivo CSV
    """
    logger.info("=" * 80)
    logger.info("PROCESSAMENTO DE FIBRA ÓTICA - ANATEL")
    logger.info("=" * 80)

    csv_path = Path(csv_path)

    if not csv_path.exists():
        logger.error(f"Arquivo não encontrado: {csv_path}")
        return

    logger.info(f"Arquivo CSV: {csv_path}")

    try:
        # Ler CSV
        logger.info("Lendo arquivo CSV...")

        # Tentar diferentes encodings
        encodings = ["utf-8", "latin-1", "iso-8859-1", "cp1252"]
        df = None

        for encoding in encodings:
            try:
                df = pd.read_csv(
                    csv_path, encoding=encoding, sep=";"
                )  # Ajustar separador se necessário
                logger.info(f"Arquivo lido com encoding: {encoding}")
                break
            except UnicodeDecodeError:
                continue

        if df is None:
            logger.error("Não foi possível ler o arquivo com nenhum encoding testado")
            return

        logger.info(f"Registros lidos: {len(df)}")
        logger.info(f"Colunas disponíveis: {list(df.columns)}")

        # AJUSTAR NOMES DAS COLUNAS CONFORME ARQUIVO REAL
        # Exemplo de mapeamento (você precisará ajustar):
        column_mapping = {
            # 'Nome_Coluna_CSV': 'nome_coluna_banco',
            # Exemplo:
            # 'Operadora': 'operadora',
            # 'Municipio': 'municipio',
            # 'UF': 'uf',
            # 'Latitude': 'latitude',
            # 'Longitude': 'longitude',
        }

        # Renomear colunas se necessário
        # df = df.rename(columns=column_mapping)

        # Criar GeoDataFrame
        # AJUSTAR NOMES DAS COLUNAS DE LAT/LON
        gdf = create_geometry_from_coords(df, lat_col="latitude", lon_col="longitude")

        # Validar geometrias
        invalid_geoms = ~gdf.geometry.is_valid
        if invalid_geoms.any():
            logger.warning(f"Removendo {invalid_geoms.sum()} geometrias inválidas")
            gdf = gdf[~invalid_geoms]

        # Remover duplicatas
        gdf = gdf.drop_duplicates()

        # Adicionar metadados
        gdf["data_source"] = "ANATEL"

        # Conectar ao banco
        logger.info("Conectando ao banco de dados...")
        engine = create_engine(settings.DATABASE_URL)

        # Inserir
        logger.info("Inserindo dados no PostGIS...")
        gdf.to_postgis(
            name="fibra_optica",
            con=engine,
            schema="geo",
            if_exists="append",
            index=False,
        )

        logger.success(f"✅ {len(gdf)} pontos de fibra ótica inseridos com sucesso!")

        # Estatísticas
        logger.info("\n" + "=" * 80)
        logger.info("ESTATÍSTICAS")
        logger.info("=" * 80)

        if "uf" in gdf.columns:
            logger.info("\nDistribuição por UF:")
            uf_counts = gdf["uf"].value_counts()
            for uf, count in uf_counts.items():
                logger.info(f"  {uf}: {count}")

        if "operadora" in gdf.columns:
            logger.info("\nTop 10 operadoras:")
            op_counts = gdf["operadora"].value_counts().head(10)
            for op, count in op_counts.items():
                logger.info(f"  {op}: {count}")

        engine.dispose()

    except Exception as e:
        logger.error(f"Erro ao processar fibra ótica: {e}")
        logger.exception(e)
        raise


def main():
    """Função principal"""
    setup_logging()

    # AJUSTAR O CAMINHO
    csv_path = "data/raw/anatel_fibra_optica.csv"

    process_fibra_optica(csv_path)


if __name__ == "__main__":
    main()
