"""
Modelo SQLAlchemy para Zoneamento Urbano de São Paulo
Dados extraídos do BigQuery - Lei 18.177/2024
"""

from geoalchemy2 import Geometry
from sqlalchemy import Column, DateTime, Integer, String

from app.core.database import Base


class ZoneamentoSP(Base):
    """
    Modelo para perímetros de zoneamento urbano do município de São Paulo

    Representa as zonas de uso do solo definidas pela legislação municipal,
    incluindo ZEPAM, ZC, ZEIS-1, ZM, ZER-1, entre outras.
    """

    __tablename__ = "zoneamento_sp"
    __table_args__ = {"schema": "geo"}

    # Identificador original do BigQuery (chave primária)
    id_original = Column(String(255), primary_key=True, index=True)

    # Identificação legal
    cd_tipo_legislacao_zoneamento = Column(
        String(50), comment="Tipo da legislação (lei, decreto, etc.)"
    )
    cd_numero_legislacao_zoneamento = Column(String(50), comment="Número da lei/decreto")
    an_legislacao_zoneamento = Column(Integer, comment="Ano da legislação", index=True)

    # Identificação do zoneamento
    cd_zoneamento_perimetro = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Código do zoneamento (ex: ZEU, ZM-3, ZEIS-1)",
    )
    tx_zoneamento_perimetro = Column(String(500), comment="Descrição/nome textual do zoneamento")

    # Metadados administrativos
    cd_identificador = Column(String(100), comment="Identificador interno")
    tx_observacao_perimetro = Column(String(1000), comment="Observações sobre o perímetro")

    # Auditoria
    dt_atualizacao = Column(
        DateTime(timezone=True), comment="Data de atualização no sistema origem"
    )
    cd_usuario_atualizacao = Column(String(100), comment="Usuário que realizou atualização")

    # Geometria (MULTIPOLYGON em EPSG:4326 / WGS84)
    geometry = Column(
        Geometry(geometry_type="MULTIPOLYGON", srid=4326),
        nullable=False,
        comment="Polígono do perímetro de zoneamento",
    )

    # Metadados de carga
    data_source = Column(String(100), default="BIGQUERY_SP_ZONEAMENTO")

    def __repr__(self):
        return (
            f"<ZoneamentoSP("
            f"id_original='{self.id_original}', "
            f"codigo='{self.cd_zoneamento_perimetro}', "
            f"descricao='{self.tx_zoneamento_perimetro}'"
            f")>"
        )
