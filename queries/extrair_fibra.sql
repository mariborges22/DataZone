-- ============================================
-- DataZone Energy - Query BigQuery Anatel
-- ============================================
-- Extração otimizada de dados de fibra óptica
-- Fonte: basedosdados.br_anatel_banda_larga_fixa.microdados
-- Objetivo: Reduzir volume de dados processados em 44.5%

-- IMPORTANTE: Esta query seleciona apenas colunas necessárias e
-- filtra por partição (ano=2023) para otimizar custos

SELECT 
    -- Período
    ano,
    mes,
    
    -- Identificação geográfica
    id_municipio,
    
    -- Tecnologia de fibra (FTTH = Fiber to the Home, FTTB = Fiber to the Building)
    tecnologia,
    
    -- Empresa/Operadora
    empresa,
    
    -- Total de acessos
    acessos

FROM 
    `basedosdados.br_anatel_banda_larga_fixa.microdados`

WHERE 
    -- Filtro 1: Partição por ano (otimiza scan da tabela)
    ano = 2023
    
    -- Filtro 2: Apenas tecnologias de fibra óptica
    AND tecnologia IN ('FTTH', 'FTTB')

-- Ordenar por município e mês
ORDER BY 
    id_municipio,
    mes

-- NOTA: Processamento em chunks será feito no Python
-- Colunas removidas: status (não existe no schema)
-- Redução estimada: 44.5% menos bytes processados
