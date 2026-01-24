"""
Script helper para explorar arquivos GDB e CSV
Use este script para descobrir a estrutura dos seus arquivos antes de processar
"""

import sys
from pathlib import Path

import fiona
import geopandas as gpd
import pandas as pd

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))


def explore_gdb(gdb_path: str):
    """
    Explora estrutura de arquivo Geodatabase

    Args:
        gdb_path: Caminho para o arquivo .gdb
    """
    print("=" * 80)
    print(f"EXPLORANDO GEODATABASE: {gdb_path}")
    print("=" * 80)

    gdb_path = Path(gdb_path)

    if not gdb_path.exists():
        print(f"❌ Arquivo não encontrado: {gdb_path}")
        return

    try:
        # Listar camadas
        layers = fiona.listlayers(str(gdb_path))
        print(f"\n📁 Camadas disponíveis ({len(layers)}):")
        for i, layer in enumerate(layers, 1):
            print(f"  {i}. {layer}")

        # Explorar cada camada
        for layer in layers:
            print(f"\n{'=' * 80}")
            print(f"CAMADA: {layer}")
            print("=" * 80)

            try:
                gdf = gpd.read_file(gdb_path, layer=layer, rows=5)

                print(f"\n📊 Informações:")
                print(f"  - Total de registros: {len(gpd.read_file(gdb_path, layer=layer))}")
                print(f"  - Tipo de geometria: {gdf.geometry.type.unique().tolist()}")
                print(f"  - CRS: {gdf.crs}")

                print(f"\n📋 Colunas ({len(gdf.columns)}):")
                for col in gdf.columns:
                    dtype = gdf[col].dtype
                    non_null = gdf[col].notna().sum()
                    print(f"  - {col:30} | Tipo: {dtype:15} | Não-nulos: {non_null}/5")

                print(f"\n🔍 Primeiros 3 registros:")
                print(gdf.head(3).to_string())

            except Exception as e:
                print(f"❌ Erro ao ler camada {layer}: {e}")

    except Exception as e:
        print(f"❌ Erro ao explorar GDB: {e}")


def explore_csv(csv_path: str):
    """
    Explora estrutura de arquivo CSV

    Args:
        csv_path: Caminho para o arquivo CSV
    """
    print("=" * 80)
    print(f"EXPLORANDO CSV: {csv_path}")
    print("=" * 80)

    csv_path = Path(csv_path)

    if not csv_path.exists():
        print(f"❌ Arquivo não encontrado: {csv_path}")
        return

    try:
        # Tentar diferentes encodings e separadores
        encodings = ["utf-8", "latin-1", "iso-8859-1", "cp1252"]
        separators = [",", ";", "\t", "|"]

        df = None
        used_encoding = None
        used_separator = None

        for encoding in encodings:
            for sep in separators:
                try:
                    df = pd.read_csv(csv_path, encoding=encoding, sep=sep, nrows=5)
                    if len(df.columns) > 1:  # Verificar se separador está correto
                        used_encoding = encoding
                        used_separator = sep
                        break
                except:
                    continue
            if df is not None:
                break

        if df is None:
            print("❌ Não foi possível ler o arquivo")
            return

        print(f"\n✅ Arquivo lido com:")
        print(f"  - Encoding: {used_encoding}")
        print(f"  - Separador: '{used_separator}'")

        # Ler arquivo completo para estatísticas
        df_full = pd.read_csv(csv_path, encoding=used_encoding, sep=used_separator)

        print(f"\n📊 Informações:")
        print(f"  - Total de registros: {len(df_full)}")
        print(f"  - Total de colunas: {len(df_full.columns)}")

        print(f"\n📋 Colunas:")
        for col in df_full.columns:
            dtype = df_full[col].dtype
            non_null = df_full[col].notna().sum()
            null_pct = (1 - non_null / len(df_full)) * 100
            unique = df_full[col].nunique()
            print(
                f"  - {col:30} | Tipo: {dtype:15} | Não-nulos: {non_null:6} ({100-null_pct:.1f}%) | Únicos: {unique}"
            )

        print(f"\n🔍 Primeiros 3 registros:")
        print(df.head(3).to_string())

        # Verificar se tem coordenadas
        possible_lat_cols = ["latitude", "lat", "y", "coord_y"]
        possible_lon_cols = ["longitude", "lon", "long", "x", "coord_x"]

        lat_col = next((col for col in df_full.columns if col.lower() in possible_lat_cols), None)
        lon_col = next((col for col in df_full.columns if col.lower() in possible_lon_cols), None)

        if lat_col and lon_col:
            print(f"\n📍 Coordenadas encontradas:")
            print(f"  - Latitude: {lat_col}")
            print(f"  - Longitude: {lon_col}")
            print(
                f"  - Registros com coordenadas: {df_full[[lat_col, lon_col]].notna().all(axis=1).sum()}"
            )
        else:
            print(f"\n⚠️  Colunas de coordenadas não encontradas automaticamente")
            print(f"  Procure por colunas que contenham lat/lon nos dados acima")

    except Exception as e:
        print(f"❌ Erro ao explorar CSV: {e}")
        import traceback

        traceback.print_exc()


def main():
    """Função principal"""
    print("\n🔍 EXPLORADOR DE DADOS - DataZone Energy\n")

    # AJUSTAR OS CAMINHOS AQUI
    print("📁 Explorando arquivos GDB...")
    explore_gdb("data/raw/aneel_subestacoes.gdb")
    explore_gdb("data/raw/aneel_linhas_transmissao.gdb")

    print("\n📁 Explorando arquivos CSV...")
    explore_csv("data/raw/anatel_fibra_optica.csv")

    print("\n" + "=" * 80)
    print("✅ Exploração concluída!")
    print("=" * 80)


if __name__ == "__main__":
    main()
