# Dados Processados

Este diretório contém os dados processados e prontos para carga no banco de dados.

## Conteúdo

Após executar os scripts de processamento, você encontrará aqui:

- **GeoJSON**: Dados convertidos para EPSG:4326
- **Metadados**: Informações sobre o processamento
- **Logs**: Relatórios de validação

## Workflow

1. Dados brutos em `data/raw/`
2. Processamento via scripts em `scripts/`
3. Saída neste diretório
4. Carga no PostGIS
