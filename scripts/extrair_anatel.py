"""
DataZone Energy - Extração Anatel (BigQuery → PostGIS)
========================================================
Pipeline ETL para extrair dados de fibra óptica do BigQuery (basedosdados)
e carregar no PostGIS de forma otimizada.

Autor: DataZone Energy Team
Data: 2026-01-20
"""

import os
import re
import sys
import time
from pathlib import Path
from typing import Optional

import pandas as pd
from google.api_core import retry
from google.cloud import bigquery
from loguru import logger
from sqlalchemy import create_engine, text

# Configurar credenciais:
# Removemos a definição explícita de GOOGLE_APPLICATION_CREDENTIALS para arquivo local.
# O script agora usará ADC (Application Default Credentials), que funciona automaticamente
# com Workload Identity Federation (no GitHub) e gcloud auth application-default login (local).

# Configurar logging
logger.remove()  # Remove handler padrão
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=os.getenv("LOG_LEVEL", "INFO"),
)
logger.add(
    "logs/etl_anatel_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="30 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
)


class AnatelBigQueryETL:
    """Pipeline ETL para extração de dados Anatel do BigQuery."""

    def __init__(
        self,
        project_id: str,
        database_url: str,
        query_path: str = "queries/extrair_fibra.sql",
        chunk_size: int = 10000,
        max_retries: int = 3,
        retry_delay: int = 5,
    ):
        """
        Inicializa a pipeline ETL.

        Args:
            project_id: ID do projeto GCP (ex: 'basedosdados')
            database_url: URL de conexão PostgreSQL
            query_path: Caminho para arquivo .sql com query BigQuery
            chunk_size: Tamanho dos chunks para processamento
            max_retries: Número máximo de tentativas em caso de falha
            retry_delay: Delay entre tentativas (segundos)
        """
        self.project_id = project_id
        self.database_url = database_url
        self.query_path = Path(query_path)
        self.chunk_size = chunk_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self.bq_client: Optional[bigquery.Client] = None
        self.pg_engine = None

        logger.info(f"Pipeline ETL inicializada | Projeto: {project_id} | Chunk Size: {chunk_size}")

    def _validate_credentials(self) -> bool:
        """Valida credenciais do Google Cloud (ADC)."""
        # Com ADC, não verificamos mais um arquivo estático específico.
        # A própria biblioteca google-auth gerencia isso.
        # Podemos verificar se o projeto padrão está acessível.
        try:
            import google.auth

            credentials, project = google.auth.default()
            if not credentials:
                logger.error("Credenciais ADC não encontradas!")
                return False
            logger.success(f"Credenciais GCP (ADC) detectadas. Projeto quota/billing: {project}")
            return True
        except Exception as e:
            logger.error(f"Erro ao validar credenciais ADC: {e}")
            return False

    def _connect_bigquery(self) -> bool:
        """Estabelece conexão com BigQuery."""
        try:
            # IMPORTANTE: Usar projeto faturador explicitamente
            # Jobs criados em: causal-tracker-484821-f1
            # Query acessa: basedosdados.br_anatel_banda_larga_fixa.microdados (público)
            self.bq_client = bigquery.Client(project="causal-tracker-484821-f1")

            # Teste de conexão (job criado no projeto faturador)
            query_test = "SELECT 1 as test"
            job_config = bigquery.QueryJobConfig(
                use_query_cache=False,  # Desabilitar cache para monitoramento preciso no MVP
                use_legacy_sql=False,
            )
            result = self.bq_client.query(query_test, job_config=job_config).result()

            logger.success(
                f"✅ Conectado ao BigQuery | Projeto faturador: causal-tracker-484821-f1"
            )
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao conectar BigQuery: {e}")
            logger.error(
                f"Verifique se a autenticação via ADC ou WIF está configurada corretamente."
            )
            return False

    def _connect_postgres(self) -> bool:
        """Estabelece conexão com PostgreSQL/PostGIS."""
        try:
            self.pg_engine = create_engine(self.database_url)

            # Teste de conexão
            with self.pg_engine.connect() as conn:
                result = conn.execute(text("SELECT PostGIS_Version()"))
                version = result.fetchone()[0]
                logger.success(f"✅ Conectado ao PostGIS | Versão: {version}")

            return True

        except Exception as e:
            logger.error(f"❌ Erro ao conectar PostgreSQL: {e}")
            return False

    def _load_query(self) -> Optional[str]:
        """Carrega query SQL do arquivo."""
        try:
            if not self.query_path.exists():
                logger.error(f"Arquivo de query não encontrado: {self.query_path}")
                return None

            query = self.query_path.read_text(encoding="utf-8")
            logger.info(f"Query carregada: {self.query_path} ({len(query)} caracteres)")
            return query

        except Exception as e:
            logger.error(f"Erro ao carregar query: {e}")
            return None

    def _execute_bigquery(self, query: str) -> Optional[pd.DataFrame]:
        """
        Executa query no BigQuery e retorna DataFrame.

        Args:
            query: Query SQL para executar

        Returns:
            DataFrame com resultados ou None em caso de erro
        """
        try:
            logger.info("Executando query no BigQuery...")
            start_time = time.time()

            # Configurar job (criado no projeto faturador, mas query acessa dados públicos)
            job_config = bigquery.QueryJobConfig(
                use_query_cache=False,  # Desabilitar cache para monitoramento preciso no MVP
                use_legacy_sql=False,
            )

            # Executar query
            # Job criado em: causal-tracker-484821-f1 (projeto faturador)
            # Query acessa: basedosdados.br_anatel_banda_larga_fixa.microdados (público)
            query_job = self.bq_client.query(query, job_config=job_config)

            # Aguardar conclusão
            df = query_job.to_dataframe()

            elapsed_time = time.time() - start_time

            # Log de performance e custos
            bytes_processed = (
                query_job.total_bytes_processed
                if query_job.total_bytes_processed is not None
                else 0
            )
            print(f"Bytes processados: {bytes_processed:,}")

            logger.success(
                f"✅ Query executada com sucesso | "
                f"Linhas: {len(df):,} | "
                f"Tempo: {elapsed_time:.2f}s | "
                f"Bytes processados: {bytes_processed:,}"
            )

            return df

        except Exception as e:
            logger.error(f"❌ Erro ao executar query BigQuery: {e}")
            return None

    def _prepare_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepara DataFrame para inserção no PostGIS.

        Args:
            df: DataFrame bruto do BigQuery

        Returns:
            DataFrame preparado
        """
        logger.info("Preparando dados para inserção...")

        # Colunas da query otimizada: ano, mes, id_municipio, tecnologia, empresa, acessos
        # Manter nomes originais (já estão em snake_case)

        # Adicionar metadados
        df["data_source"] = "ANATEL_BIGQUERY"
        df["data_extracao"] = pd.Timestamp.now()

        # Limpeza de dados
        df = df.fillna({"acessos": 0, "empresa": "Não informado"})

        # Garantir tipos corretos
        df["ano"] = df["ano"].astype(int)
        df["mes"] = df["mes"].astype(int)
        df["acessos"] = pd.to_numeric(df["acessos"], errors="coerce").fillna(0).astype(int)

        logger.info(f"Dados preparados | Linhas: {len(df):,} | Colunas: {list(df.columns)}")
        return df

    def _insert_to_postgres(self, df: pd.DataFrame, table_name: str = "cobertura_fibra") -> bool:
        """
        Insere dados no PostgreSQL em chunks.

        Args:
            df: DataFrame para inserir
            table_name: Nome da tabela destino

        Returns:
            True se sucesso, False caso contrário
        """
        try:
            # Validar table_name para prevenir SQL Injection
            validated_table_name = self._validate_table_name(table_name)

            logger.info(f"Iniciando inserção no PostgreSQL | Tabela: geo.{validated_table_name}")
            start_time = time.time()

            # Inserir em chunks para melhor performance
            total_chunks = (len(df) // self.chunk_size) + 1

            for i, chunk_start in enumerate(range(0, len(df), self.chunk_size)):
                chunk_end = min(chunk_start + self.chunk_size, len(df))
                chunk = df.iloc[chunk_start:chunk_end]

                # Primeira iteração: replace (limpa tabela)
                # Demais: append
                if_exists_mode = "replace" if i == 0 else "append"

                chunk.to_sql(
                    validated_table_name,
                    self.pg_engine,
                    schema="geo",
                    if_exists=if_exists_mode,
                    index=False,
                    method="multi",  # Inserção batch otimizada
                    chunksize=1000,
                )

                logger.info(
                    f"Chunk {i+1}/{total_chunks} inserido | "
                    f"Linhas: {len(chunk)} | "
                    f"Progresso: {(chunk_end/len(df)*100):.1f}%"
                )

            elapsed_time = time.time() - start_time
            logger.success(
                f"✅ Inserção concluída | "
                f"Total de linhas: {len(df):,} | "
                f"Tempo: {elapsed_time:.2f}s | "
                f"Taxa: {len(df)/elapsed_time:.0f} linhas/s"
            )

            return True

        except ValueError as e:
            logger.error(f"❌ Erro de validação: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Erro ao inserir dados no PostgreSQL: {e}")
            return False

    @staticmethod
    def _validate_table_name(table_name: str) -> str:
        """
        Valida e sanitiza nome da tabela para prevenir SQL Injection.

        Args:
            table_name: Nome da tabela a validar

        Returns:
            Nome da tabela validado

        Raises:
            ValueError: Se o nome da tabela for inválido
        """
        # Permitir apenas letras, números e underscores
        if not re.match(r"^[a-zA-Z0-9_]+$", table_name):
            raise ValueError(
                f"Nome de tabela inválido: '{table_name}'. "
                "Apenas letras, números e underscores são permitidos."
            )

        # Limitar tamanho máximo
        if len(table_name) > 63:  # Limite do PostgreSQL
            raise ValueError(f"Nome de tabela muito longo: '{table_name}' (máximo 63 caracteres)")

        return table_name

    def _create_indexes(self, table_name: str = "cobertura_fibra") -> bool:
        """Cria índices na tabela para otimizar consultas."""
        try:
            logger.info("Criando índices...")

            # Validar table_name para prevenir SQL Injection
            validated_table_name = self._validate_table_name(table_name)

            with self.pg_engine.connect() as conn:
                # Índice por município (id_municipio)
                # SEGURANÇA: table_name validado acima
                conn.execute(text(f"""
                    CREATE INDEX IF NOT EXISTS idx_{validated_table_name}_municipio
                    ON geo.{validated_table_name} (id_municipio)
                """))

                # Índice por tecnologia
                conn.execute(text(f"""
                    CREATE INDEX IF NOT EXISTS idx_{validated_table_name}_tecnologia
                    ON geo.{validated_table_name} (tecnologia)
                """))

                conn.commit()

            logger.success("✅ Índices criados com sucesso")
            return True

        except ValueError as e:
            logger.error(f"❌ Erro de validação: {e}")
            return False
        except Exception as e:
            logger.warning(f"⚠️ Erro ao criar índices (não crítico): {e}")
            return False

    def run(self) -> bool:
        """
        Executa a pipeline ETL completa.

        Returns:
            True se sucesso, False caso contrário
        """
        logger.info("=" * 80)
        logger.info("🚀 INICIANDO PIPELINE ETL ANATEL (BigQuery → PostGIS)")
        logger.info("=" * 80)

        pipeline_start = time.time()

        try:
            # 1. Validar credenciais
            if not self._validate_credentials():
                return False

            # 2. Conectar BigQuery
            if not self._connect_bigquery():
                return False

            # 3. Conectar PostgreSQL
            if not self._connect_postgres():
                return False

            # 4. Carregar query
            query = self._load_query()
            if not query:
                return False

            # 5. Executar query BigQuery
            df = self._execute_bigquery(query)
            if df is None or df.empty:
                logger.warning("⚠️ Nenhum dado retornado do BigQuery")
                return False

            # 6. Preparar dados
            df_prepared = self._prepare_dataframe(df)

            # 7. Inserir no PostgreSQL
            if not self._insert_to_postgres(df_prepared):
                return False

            # 8. Criar índices
            self._create_indexes()

            # Sucesso!
            total_time = time.time() - pipeline_start
            logger.success("=" * 80)
            logger.success(f"✅ PIPELINE CONCLUÍDA COM SUCESSO | Tempo total: {total_time:.2f}s")
            logger.success("=" * 80)

            return True

        except Exception as e:
            logger.critical(f"❌ ERRO CRÍTICO NA PIPELINE: {e}", exc_info=True)
            return False


def main():
    """Função principal."""
    # Carregar variáveis de ambiente
    # IMPORTANTE: Usar projeto faturador (billing project) para criar jobs
    # A query pode acessar datasets públicos (basedosdados.*)
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv(
        "GCP_PROJECT_ID", "causal-tracker-484821-f1"
    )
    database_url = os.getenv("DATABASE_URL")
    chunk_size = int(os.getenv("ETL_CHUNK_SIZE", "10000"))

    # Validações
    if not database_url:
        logger.error("DATABASE_URL não configurada!")
        sys.exit(1)

    logger.info(f"Usando projeto faturador: {project_id}")

    # Criar e executar pipeline
    pipeline = AnatelBigQueryETL(
        project_id=project_id, database_url=database_url, chunk_size=chunk_size
    )

    success = pipeline.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
