"""
Modelos SQLAlchemy para dados BDGD (Base de Dados Geográfica da Distribuidora)
Fonte: Enel SP
"""

from geoalchemy2 import Geometry
from sqlalchemy import Column, DateTime, Integer, Numeric, String, Text, func

from app.core.database import Base


# ============================================
# Camadas com geometria
# ============================================


class BdgdSub(Base):
    """Subestações de distribuição BDGD"""

    __tablename__ = "bdgd_sub"
    __table_args__ = {"schema": "geo"}

    id = Column(Integer, primary_key=True, index=True)
    cod_id = Column(String(100), index=True)
    dist = Column(Integer)
    pos = Column(String(10))
    nome = Column(String(255))
    descr = Column(Text)

    geometry = Column(Geometry(geometry_type="MULTIPOLYGON", srid=4326), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    data_source = Column(String(100), default="BDGD_ENEL_SP")

    def __repr__(self):
        return f"<BdgdSub(cod_id='{self.cod_id}', nome='{self.nome}')>"


class BdgdSsdat(Base):
    """Segmentos de rede de distribuição AT"""

    __tablename__ = "bdgd_ssdat"
    __table_args__ = {"schema": "geo"}

    id = Column(Integer, primary_key=True, index=True)
    cod_id = Column(String(100), index=True)
    pn_con_1 = Column(String(50))
    pn_con_2 = Column(String(50))
    ctat = Column(String(100), index=True)
    ct_cod_op = Column(String(100))
    conj = Column(String(50))
    are_loc = Column(String(10))
    dist = Column(Integer)
    pac_1 = Column(String(50))
    pac_2 = Column(String(50))
    fas_con = Column(String(10))
    tip_inst = Column(String(50))
    tip_cnd = Column(String(50))
    pos = Column(String(10))
    odi = Column(String(20))
    ti = Column(String(10))
    cm = Column(String(10))
    sitcont = Column(String(10))
    comp = Column(Numeric)
    descr = Column(Text)

    geometry = Column(
        Geometry(geometry_type="MULTILINESTRING", srid=4326), nullable=False
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    data_source = Column(String(100), default="BDGD_ENEL_SP")

    def __repr__(self):
        return f"<BdgdSsdat(cod_id='{self.cod_id}', ctat='{self.ctat}')>"


class BdgdUntrat(Base):
    """Transformadores AT (unidades transformadoras de alta tensão)"""

    __tablename__ = "bdgd_untrat"
    __table_args__ = {"schema": "geo"}

    id = Column(Integer, primary_key=True, index=True)
    cod_id = Column(String(100), index=True)
    sub = Column(String(50), index=True)
    barr_1 = Column(String(50))
    barr_2 = Column(String(50))
    barr_3 = Column(String(50))
    pac_1 = Column(String(50))
    pac_2 = Column(String(50))
    pac_3 = Column(String(50))
    dist = Column(Integer)
    fas_con_p = Column(String(10))
    fas_con_s = Column(String(10))
    fas_con_t = Column(String(10))
    sit_ativ = Column(String(10))
    tip_unid = Column(String(10))
    pos = Column(String(10))
    are_loc = Column(String(10))
    pot_nom = Column(Numeric)
    pot_f01 = Column(Numeric)
    pot_f02 = Column(Numeric)
    per_fer = Column(Numeric)
    per_tot = Column(Numeric)
    banc = Column(String(10))
    dat_con = Column(String(20))
    conj = Column(String(50))
    mun = Column(String(50))
    tip_trafo = Column(String(10))
    aloc_perd = Column(String(10))
    # Energia suprida mensal (kWh)
    enes_01 = Column(Numeric)
    enes_02 = Column(Numeric)
    enes_03 = Column(Numeric)
    enes_04 = Column(Numeric)
    enes_05 = Column(Numeric)
    enes_06 = Column(Numeric)
    enes_07 = Column(Numeric)
    enes_08 = Column(Numeric)
    enes_09 = Column(Numeric)
    enes_10 = Column(Numeric)
    enes_11 = Column(Numeric)
    enes_12 = Column(Numeric)
    # Energia total mensal (kWh)
    enet_01 = Column(Numeric)
    enet_02 = Column(Numeric)
    enet_03 = Column(Numeric)
    enet_04 = Column(Numeric)
    enet_05 = Column(Numeric)
    enet_06 = Column(Numeric)
    enet_07 = Column(Numeric)
    enet_08 = Column(Numeric)
    enet_09 = Column(Numeric)
    enet_10 = Column(Numeric)
    enet_11 = Column(Numeric)
    enet_12 = Column(Numeric)
    # Energia suprida injetada mensal
    enes_01_in = Column(Numeric)
    enes_02_in = Column(Numeric)
    enes_03_in = Column(Numeric)
    enes_04_in = Column(Numeric)
    enes_05_in = Column(Numeric)
    enes_06_in = Column(Numeric)
    enes_07_in = Column(Numeric)
    enes_08_in = Column(Numeric)
    enes_09_in = Column(Numeric)
    enes_10_in = Column(Numeric)
    enes_11_in = Column(Numeric)
    enes_12_in = Column(Numeric)
    # Energia total injetada mensal
    enet_01_in = Column(Numeric)
    enet_02_in = Column(Numeric)
    enet_03_in = Column(Numeric)
    enet_04_in = Column(Numeric)
    enet_05_in = Column(Numeric)
    enet_06_in = Column(Numeric)
    enet_07_in = Column(Numeric)
    enet_08_in = Column(Numeric)
    enet_09_in = Column(Numeric)
    enet_10_in = Column(Numeric)
    enet_11_in = Column(Numeric)
    enet_12_in = Column(Numeric)
    descr = Column(Text)

    geometry = Column(Geometry(geometry_type="POINT", srid=4326), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    data_source = Column(String(100), default="BDGD_ENEL_SP")

    def __repr__(self):
        return f"<BdgdUntrat(cod_id='{self.cod_id}', sub='{self.sub}', pot_nom={self.pot_nom})>"


class BdgdArat(Base):
    """Área de concessão da distribuidora"""

    __tablename__ = "bdgd_arat"
    __table_args__ = {"schema": "geo"}

    id = Column(Integer, primary_key=True, index=True)
    cod_id = Column(String(100), index=True)
    dist = Column(Integer)
    fun_pr = Column(Numeric)
    fun_te = Column(Numeric)
    descr = Column(Text)

    geometry = Column(Geometry(geometry_type="MULTIPOLYGON", srid=4326), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    data_source = Column(String(100), default="BDGD_ENEL_SP")

    def __repr__(self):
        return f"<BdgdArat(cod_id='{self.cod_id}')>"


# ============================================
# Tabelas sem geometria (auxiliares)
# ============================================


class BdgdCtat(Base):
    """Circuitos de alta tensão"""

    __tablename__ = "bdgd_ctat"
    __table_args__ = {"schema": "geo"}

    id = Column(Integer, primary_key=True, index=True)
    cod_id = Column(String(100), index=True)
    nome = Column(String(255))
    ten_nom = Column(Numeric)
    pac_ini = Column(String(100))
    dist = Column(Integer)
    descr = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    data_source = Column(String(100), default="BDGD_ENEL_SP")

    def __repr__(self):
        return f"<BdgdCtat(cod_id='{self.cod_id}', nome='{self.nome}')>"


class BdgdEqtrat(Base):
    """Equipamentos transformadores AT"""

    __tablename__ = "bdgd_eqtrat"
    __table_args__ = {"schema": "geo"}

    id = Column(Integer, primary_key=True, index=True)
    cod_id = Column(String(100), index=True)
    dist = Column(Integer)
    tip_inst = Column(String(50))
    uni_tr_at = Column(String(100), index=True)
    clas_ten = Column(String(10))
    pot_nom = Column(Numeric)
    lig = Column(String(10))
    fas_con = Column(String(10))
    ten_pri = Column(Numeric)
    ten_sec = Column(Numeric)
    ten_ter = Column(Numeric)
    odi = Column(String(20))
    ti = Column(String(10))
    cm = Column(String(10))
    tuc = Column(String(10))
    a1 = Column(String(10))
    a2 = Column(String(10))
    a3 = Column(String(10))
    a4 = Column(String(10))
    a5 = Column(String(10))
    a6 = Column(String(10))
    uar = Column(String(20))
    iduc = Column(String(50))
    sitcont = Column(String(10))
    dat_imo = Column(String(20))
    per_fer = Column(Numeric)
    per_tot = Column(Numeric)
    pot_f01 = Column(Numeric)
    pot_f02 = Column(Numeric)
    descr = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    data_source = Column(String(100), default="BDGD_ENEL_SP")

    def __repr__(self):
        return f"<BdgdEqtrat(cod_id='{self.cod_id}', uni_tr_at='{self.uni_tr_at}')>"


class BdgdSegcon(Base):
    """Segmentos condutores (tipos de cabos)"""

    __tablename__ = "bdgd_segcon"
    __table_args__ = {"schema": "geo"}

    id = Column(Integer, primary_key=True, index=True)
    cod_id = Column(String(100), index=True)
    dist = Column(Integer)
    geom_cab = Column(String(10))
    form_cab = Column(String(10))
    bit_fas_1 = Column(String(10))
    bit_fas_2 = Column(String(10))
    bit_fas_3 = Column(String(10))
    bit_neu = Column(String(10))
    mat_fas_1 = Column(String(10))
    mat_fas_2 = Column(String(10))
    mat_fas_3 = Column(String(10))
    mat_neu = Column(String(10))
    iso_fas_1 = Column(String(10))
    iso_fas_2 = Column(String(10))
    iso_fas_3 = Column(String(10))
    iso_neu = Column(String(10))
    cnd_fas = Column(String(10))
    r1 = Column(Numeric)
    x1 = Column(Numeric)
    r_regul = Column(String(50))
    ftrcnv = Column(Numeric)
    cnom = Column(Numeric)
    cap_max = Column(Numeric)
    tuc_fas = Column(String(10))
    a1_fas = Column(String(10))
    a2_fas = Column(String(10))
    a3_fas = Column(String(10))
    a4_fas = Column(String(10))
    a5_fas = Column(String(10))
    a6_fas = Column(String(10))
    tuc_neu = Column(String(10))
    a1_neu = Column(String(10))
    a2_neu = Column(String(10))
    a3_neu = Column(String(10))
    a4_neu = Column(String(10))
    a5_neu = Column(String(10))
    a6_neu = Column(String(10))
    uar = Column(String(20))
    descr = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    data_source = Column(String(100), default="BDGD_ENEL_SP")

    def __repr__(self):
        return f"<BdgdSegcon(cod_id='{self.cod_id}')>"
