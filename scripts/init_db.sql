-- ============================================
-- DataZone Energy - Inicialização do Banco
-- ============================================

-- Habilitar extensões necessárias
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;

-- Verificar versão do PostGIS
SELECT PostGIS_Version();

-- ============================================
-- Schema para dados geográficos
-- ============================================
CREATE SCHEMA IF NOT EXISTS geo;

-- ============================================
-- Tabela: Subestações
-- ============================================
CREATE TABLE IF NOT EXISTS geo.subestacoes (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    codigo VARCHAR(100),
    tensao_kv NUMERIC,
    tipo VARCHAR(100),
    operador VARCHAR(255),
    municipio VARCHAR(255),
    uf CHAR(2),
    capacidade_mva NUMERIC,
    status VARCHAR(50),
    geometry GEOMETRY(Point, 4326) NOT NULL,
    
    -- Metadados
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_source VARCHAR(100) DEFAULT 'ANEEL'
);

-- Índices espaciais
CREATE INDEX IF NOT EXISTS idx_subestacoes_geom ON geo.subestacoes USING GIST (geometry);
CREATE INDEX IF NOT EXISTS idx_subestacoes_uf ON geo.subestacoes (uf);
CREATE INDEX IF NOT EXISTS idx_subestacoes_municipio ON geo.subestacoes (municipio);

-- ============================================
-- Tabela: Linhas de Transmissão
-- ============================================
CREATE TABLE IF NOT EXISTS geo.linhas_transmissao (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255),
    codigo VARCHAR(100),
    tensao_kv NUMERIC NOT NULL,
    extensao_km NUMERIC,
    operador VARCHAR(255),
    origem VARCHAR(255),
    destino VARCHAR(255),
    status VARCHAR(50),
    geometry GEOMETRY(LineString, 4326) NOT NULL,
    
    -- Metadados
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_source VARCHAR(100) DEFAULT 'ANEEL'
);

-- Índices espaciais
CREATE INDEX IF NOT EXISTS idx_linhas_geom ON geo.linhas_transmissao USING GIST (geometry);
CREATE INDEX IF NOT EXISTS idx_linhas_tensao ON geo.linhas_transmissao (tensao_kv);

-- ============================================
-- Tabela: Infraestrutura de Fibra Ótica
-- ============================================
CREATE TABLE IF NOT EXISTS geo.fibra_optica (
    id SERIAL PRIMARY KEY,
    operadora VARCHAR(255),
    tipo VARCHAR(100),
    tecnologia VARCHAR(100),
    municipio VARCHAR(255),
    uf CHAR(2),
    capacidade_gbps NUMERIC,
    status VARCHAR(50),
    geometry GEOMETRY(Point, 4326) NOT NULL,
    
    -- Metadados
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_source VARCHAR(100) DEFAULT 'ANATEL'
);

-- Índices espaciais
CREATE INDEX IF NOT EXISTS idx_fibra_geom ON geo.fibra_optica USING GIST (geometry);
CREATE INDEX IF NOT EXISTS idx_fibra_uf ON geo.fibra_optica (uf);
CREATE INDEX IF NOT EXISTS idx_fibra_operadora ON geo.fibra_optica (operadora);

-- ============================================
-- Tabelas BDGD (Enel SP)
-- ============================================

-- SUB: Subestações de distribuição
CREATE TABLE IF NOT EXISTS geo.bdgd_sub (
    id SERIAL PRIMARY KEY,
    cod_id VARCHAR(100),
    dist INTEGER,
    pos VARCHAR(10),
    nome VARCHAR(255),
    descr TEXT,
    geometry GEOMETRY(MultiPolygon, 4326) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_source VARCHAR(100) DEFAULT 'BDGD_ENEL_SP'
);

CREATE INDEX IF NOT EXISTS idx_bdgd_sub_geom ON geo.bdgd_sub USING GIST (geometry);
CREATE INDEX IF NOT EXISTS idx_bdgd_sub_cod_id ON geo.bdgd_sub (cod_id);

-- SSDAT: Segmentos de rede AT
CREATE TABLE IF NOT EXISTS geo.bdgd_ssdat (
    id SERIAL PRIMARY KEY,
    cod_id VARCHAR(100),
    pn_con_1 VARCHAR(50),
    pn_con_2 VARCHAR(50),
    ctat VARCHAR(100),
    ct_cod_op VARCHAR(100),
    conj VARCHAR(50),
    are_loc VARCHAR(10),
    dist INTEGER,
    pac_1 VARCHAR(50),
    pac_2 VARCHAR(50),
    fas_con VARCHAR(10),
    tip_inst VARCHAR(50),
    tip_cnd VARCHAR(50),
    pos VARCHAR(10),
    odi VARCHAR(20),
    ti VARCHAR(10),
    cm VARCHAR(10),
    sitcont VARCHAR(10),
    comp NUMERIC,
    descr TEXT,
    geometry GEOMETRY(MultiLineString, 4326) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_source VARCHAR(100) DEFAULT 'BDGD_ENEL_SP'
);

CREATE INDEX IF NOT EXISTS idx_bdgd_ssdat_geom ON geo.bdgd_ssdat USING GIST (geometry);
CREATE INDEX IF NOT EXISTS idx_bdgd_ssdat_cod_id ON geo.bdgd_ssdat (cod_id);
CREATE INDEX IF NOT EXISTS idx_bdgd_ssdat_ctat ON geo.bdgd_ssdat (ctat);

-- UNTRAT: Transformadores AT
CREATE TABLE IF NOT EXISTS geo.bdgd_untrat (
    id SERIAL PRIMARY KEY,
    cod_id VARCHAR(100),
    sub VARCHAR(50),
    barr_1 VARCHAR(50),
    barr_2 VARCHAR(50),
    barr_3 VARCHAR(50),
    pac_1 VARCHAR(50),
    pac_2 VARCHAR(50),
    pac_3 VARCHAR(50),
    dist INTEGER,
    fas_con_p VARCHAR(10),
    fas_con_s VARCHAR(10),
    fas_con_t VARCHAR(10),
    sit_ativ VARCHAR(10),
    tip_unid VARCHAR(10),
    pos VARCHAR(10),
    are_loc VARCHAR(10),
    pot_nom NUMERIC,
    pot_f01 NUMERIC,
    pot_f02 NUMERIC,
    per_fer NUMERIC,
    per_tot NUMERIC,
    banc VARCHAR(10),
    dat_con VARCHAR(20),
    conj VARCHAR(50),
    mun VARCHAR(50),
    tip_trafo VARCHAR(10),
    aloc_perd VARCHAR(10),
    descr TEXT,
    geometry GEOMETRY(Point, 4326) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_source VARCHAR(100) DEFAULT 'BDGD_ENEL_SP'
);

CREATE INDEX IF NOT EXISTS idx_bdgd_untrat_geom ON geo.bdgd_untrat USING GIST (geometry);
CREATE INDEX IF NOT EXISTS idx_bdgd_untrat_cod_id ON geo.bdgd_untrat (cod_id);
CREATE INDEX IF NOT EXISTS idx_bdgd_untrat_sub ON geo.bdgd_untrat (sub);

-- ARAT: Área de concessão
CREATE TABLE IF NOT EXISTS geo.bdgd_arat (
    id SERIAL PRIMARY KEY,
    cod_id VARCHAR(100),
    dist INTEGER,
    fun_pr NUMERIC,
    fun_te NUMERIC,
    descr TEXT,
    geometry GEOMETRY(MultiPolygon, 4326) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_source VARCHAR(100) DEFAULT 'BDGD_ENEL_SP'
);

CREATE INDEX IF NOT EXISTS idx_bdgd_arat_geom ON geo.bdgd_arat USING GIST (geometry);

-- CTAT: Circuitos AT (sem geometria)
CREATE TABLE IF NOT EXISTS geo.bdgd_ctat (
    id SERIAL PRIMARY KEY,
    cod_id VARCHAR(100),
    nome VARCHAR(255),
    ten_nom NUMERIC,
    pac_ini VARCHAR(100),
    dist INTEGER,
    descr TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_source VARCHAR(100) DEFAULT 'BDGD_ENEL_SP'
);

CREATE INDEX IF NOT EXISTS idx_bdgd_ctat_cod_id ON geo.bdgd_ctat (cod_id);

-- EQTRAT: Equipamentos transformadores AT (sem geometria)
CREATE TABLE IF NOT EXISTS geo.bdgd_eqtrat (
    id SERIAL PRIMARY KEY,
    cod_id VARCHAR(100),
    dist INTEGER,
    tip_inst VARCHAR(50),
    uni_tr_at VARCHAR(100),
    clas_ten VARCHAR(10),
    pot_nom NUMERIC,
    lig VARCHAR(10),
    fas_con VARCHAR(10),
    ten_pri NUMERIC,
    ten_sec NUMERIC,
    ten_ter NUMERIC,
    odi VARCHAR(20),
    ti VARCHAR(10),
    cm VARCHAR(10),
    tuc VARCHAR(10),
    a1 VARCHAR(10),
    a2 VARCHAR(10),
    a3 VARCHAR(10),
    a4 VARCHAR(10),
    a5 VARCHAR(10),
    a6 VARCHAR(10),
    uar VARCHAR(20),
    iduc VARCHAR(50),
    sitcont VARCHAR(10),
    dat_imo VARCHAR(20),
    per_fer NUMERIC,
    per_tot NUMERIC,
    pot_f01 NUMERIC,
    pot_f02 NUMERIC,
    descr TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_source VARCHAR(100) DEFAULT 'BDGD_ENEL_SP'
);

CREATE INDEX IF NOT EXISTS idx_bdgd_eqtrat_cod_id ON geo.bdgd_eqtrat (cod_id);
CREATE INDEX IF NOT EXISTS idx_bdgd_eqtrat_uni_tr_at ON geo.bdgd_eqtrat (uni_tr_at);

-- SEGCON: Segmentos condutores (sem geometria)
CREATE TABLE IF NOT EXISTS geo.bdgd_segcon (
    id SERIAL PRIMARY KEY,
    cod_id VARCHAR(100),
    dist INTEGER,
    geom_cab VARCHAR(10),
    form_cab VARCHAR(10),
    bit_fas_1 VARCHAR(10),
    bit_fas_2 VARCHAR(10),
    bit_fas_3 VARCHAR(10),
    bit_neu VARCHAR(10),
    mat_fas_1 VARCHAR(10),
    mat_fas_2 VARCHAR(10),
    mat_fas_3 VARCHAR(10),
    mat_neu VARCHAR(10),
    iso_fas_1 VARCHAR(10),
    iso_fas_2 VARCHAR(10),
    iso_fas_3 VARCHAR(10),
    iso_neu VARCHAR(10),
    cnd_fas VARCHAR(10),
    r1 NUMERIC,
    x1 NUMERIC,
    r_regul VARCHAR(50),
    ftrcnv NUMERIC,
    cnom NUMERIC,
    cap_max NUMERIC,
    tuc_fas VARCHAR(10),
    a1_fas VARCHAR(10),
    a2_fas VARCHAR(10),
    a3_fas VARCHAR(10),
    a4_fas VARCHAR(10),
    a5_fas VARCHAR(10),
    a6_fas VARCHAR(10),
    tuc_neu VARCHAR(10),
    a1_neu VARCHAR(10),
    a2_neu VARCHAR(10),
    a3_neu VARCHAR(10),
    a4_neu VARCHAR(10),
    a5_neu VARCHAR(10),
    a6_neu VARCHAR(10),
    uar VARCHAR(20),
    descr TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_source VARCHAR(100) DEFAULT 'BDGD_ENEL_SP'
);

CREATE INDEX IF NOT EXISTS idx_bdgd_segcon_cod_id ON geo.bdgd_segcon (cod_id);

-- Comentários nas tabelas BDGD
COMMENT ON TABLE geo.bdgd_sub IS 'Subestações de distribuição (fonte: BDGD Enel SP)';
COMMENT ON TABLE geo.bdgd_ssdat IS 'Segmentos de rede AT (fonte: BDGD Enel SP)';
COMMENT ON TABLE geo.bdgd_untrat IS 'Transformadores AT (fonte: BDGD Enel SP)';
COMMENT ON TABLE geo.bdgd_arat IS 'Área de concessão (fonte: BDGD Enel SP)';
COMMENT ON TABLE geo.bdgd_ctat IS 'Circuitos AT (fonte: BDGD Enel SP)';
COMMENT ON TABLE geo.bdgd_eqtrat IS 'Equipamentos transformadores AT (fonte: BDGD Enel SP)';
COMMENT ON TABLE geo.bdgd_segcon IS 'Segmentos condutores (fonte: BDGD Enel SP)';

-- ============================================
-- Funções auxiliares
-- ============================================

-- Função para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers para atualizar updated_at
CREATE TRIGGER update_subestacoes_updated_at BEFORE UPDATE ON geo.subestacoes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_linhas_updated_at BEFORE UPDATE ON geo.linhas_transmissao
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_fibra_updated_at BEFORE UPDATE ON geo.fibra_optica
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Comentários nas tabelas
-- ============================================
COMMENT ON TABLE geo.subestacoes IS 'Subestações de energia elétrica (fonte: ANEEL)';
COMMENT ON TABLE geo.linhas_transmissao IS 'Linhas de transmissão de alta tensão (fonte: ANEEL)';
COMMENT ON TABLE geo.fibra_optica IS 'Infraestrutura de fibra ótica (fonte: ANATEL)';

-- ============================================
-- Grants (ajustar conforme necessário)
-- ============================================
GRANT USAGE ON SCHEMA geo TO PUBLIC;
GRANT SELECT ON ALL TABLES IN SCHEMA geo TO PUBLIC;

-- Mensagem de sucesso
DO $$
BEGIN
    RAISE NOTICE 'DataZone Energy - Banco de dados inicializado com sucesso!';
END $$;
