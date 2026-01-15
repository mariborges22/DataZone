# Dados Brutos

Este diretório contém os dados brutos obtidos das fontes oficiais.

## Fontes de Dados

### ANEEL (Agência Nacional de Energia Elétrica)
- **Subestações**: Arquivos .gdb com localização e características técnicas
- **Linhas de Transmissão**: Arquivos .gdb com traçado e especificações

### ANATEL (Agência Nacional de Telecomunicações)
- **Infraestrutura de Fibra Ótica**: Arquivos CSV com dados de cobertura

## Instruções

1. Baixar dados das fontes oficiais
2. Colocar arquivos neste diretório
3. Executar scripts de processamento em `scripts/`

## Formato Esperado

- `.gdb/` - Geodatabase da ANEEL
- `.csv` - Dados tabulares da ANATEL
- `.shp` - Shapefiles (se disponível)
