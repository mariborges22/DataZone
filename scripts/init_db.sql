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
