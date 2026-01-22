-- ============================================
-- DataZone Energy - Schema para Cobertura de Fibra
-- ============================================
-- Tabela para armazenar dados agregados de cobertura
-- de fibra óptica (FTTH/FTTB) extraídos do BigQuery

-- Criar tabela se não existir
CREATE TABLE IF NOT EXISTS geo.cobertura_fibra (
    id SERIAL PRIMARY KEY,
    
    -- Identificação geográfica
    id_municipio VARCHAR(7) NOT NULL,  -- Código IBGE 7 dígitos
    municipio VARCHAR(255) NOT NULL,
    uf CHAR(2) NOT NULL,
    
    -- Tecnologia
    tecnologia VARCHAR(50) NOT NULL,  -- FTTH ou FTTB
    
    -- Métricas agregadas
    total_acessos INTEGER DEFAULT 0,
    total_operadoras INTEGER DEFAULT 0,
    
    -- Velocidades (Mbps)
    velocidade_media_mbps NUMERIC(10, 2),
    velocidade_maxima_mbps NUMERIC(10, 2),
    
    -- Período de referência
    ano_referencia INTEGER,
    mes_referencia INTEGER,
    
    -- Metadados
    data_source VARCHAR(100) DEFAULT 'ANATEL_BIGQUERY',
    data_extracao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_uf CHECK (LENGTH(uf) = 2),
    CONSTRAINT chk_tecnologia CHECK (tecnologia IN ('FTTH', 'FTTB')),
    CONSTRAINT chk_velocidades CHECK (
        velocidade_media_mbps >= 0 AND 
        velocidade_maxima_mbps >= 0
    )
);

-- Índices para otimização de queries
CREATE INDEX IF NOT EXISTS idx_cobertura_fibra_uf 
    ON geo.cobertura_fibra (uf);

CREATE INDEX IF NOT EXISTS idx_cobertura_fibra_municipio 
    ON geo.cobertura_fibra (id_municipio);

CREATE INDEX IF NOT EXISTS idx_cobertura_fibra_tecnologia 
    ON geo.cobertura_fibra (tecnologia);

CREATE INDEX IF NOT EXISTS idx_cobertura_fibra_uf_tecnologia 
    ON geo.cobertura_fibra (uf, tecnologia);

-- Índice composto para queries comuns
CREATE INDEX IF NOT EXISTS idx_cobertura_fibra_lookup 
    ON geo.cobertura_fibra (id_municipio, tecnologia, ano_referencia);

-- Trigger para atualizar updated_at automaticamente
CREATE TRIGGER update_cobertura_fibra_updated_at 
    BEFORE UPDATE ON geo.cobertura_fibra
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Comentários
COMMENT ON TABLE geo.cobertura_fibra IS 
    'Cobertura de fibra óptica (FTTH/FTTB) agregada por município - Fonte: Anatel via BigQuery';

COMMENT ON COLUMN geo.cobertura_fibra.id_municipio IS 
    'Código IBGE do município (7 dígitos)';

COMMENT ON COLUMN geo.cobertura_fibra.tecnologia IS 
    'Tecnologia de fibra: FTTH (Fiber to the Home) ou FTTB (Fiber to the Building)';

COMMENT ON COLUMN geo.cobertura_fibra.total_acessos IS 
    'Total de acessos de banda larga fixa nesta tecnologia';

COMMENT ON COLUMN geo.cobertura_fibra.total_operadoras IS 
    'Número de operadoras distintas atuando no município';

-- Mensagem de sucesso
DO $$
BEGIN
    RAISE NOTICE 'Tabela geo.cobertura_fibra criada/atualizada com sucesso!';
END $$;
