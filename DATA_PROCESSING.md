# 📊 Guia de Processamento de Dados

## Scripts Criados

Foram criados 3 scripts profissionais para processar dados:

### 1. `process_aneel_subestacoes.py`
- **Fonte**: Arquivos Geodatabase (.gdb) da ANEEL
- **Destino**: Tabela `geo.subestacoes`
- **Funcionalidades**:
  - Lê arquivos .gdb
  - Detecta automaticamente a camada de subestações
  - Valida e corrige geometrias inválidas
  - Converte CRS para EPSG:4326
  - Remove duplicatas
  - Gera estatísticas por UF e faixa de tensão

### 2. `process_aneel_linhas.py`
- **Fonte**: Arquivos Geodatabase (.gdb) da ANEEL
- **Destino**: Tabela `geo.linhas_transmissao`
- **Funcionalidades**:
  - Processa linhas de transmissão (LineString)
  - Calcula extensão em km automaticamente
  - Validação completa de geometrias
  - Estatísticas por tensão e extensão total

### 3. `process_anatel_fibra.py`
- **Fonte**: Arquivos CSV da ANATEL
- **Destino**: Tabela `geo.fibra_optica`
- **Funcionalidades**:
  - Lê CSV com múltiplos encodings
  - Cria geometrias Point a partir de lat/lon
  - Valida coordenadas
  - Estatísticas por UF e operadora

---

## 🚀 Como Usar

### Passo 1: Obter os Dados

#### ANEEL (Geodatabase)
1. Acesse: https://dadosabertos.aneel.gov.br/
2. Baixe os arquivos de:
   - Subestações
   - Linhas de Transmissão
3. Coloque os arquivos `.gdb` em `data/raw/`

#### ANATEL (CSV)
1. Acesse: https://www.anatel.gov.br/dados-abertos/
2. Baixe dados de infraestrutura de telecomunicações
3. Coloque os arquivos `.csv` em `data/raw/`

---

### Passo 2: Executar os Scripts

#### Dentro do Container Docker (Recomendado)

```powershell
# Processar subestações
docker-compose exec api python scripts/process_aneel_subestacoes.py

# Processar linhas de transmissão
docker-compose exec api python scripts/process_aneel_linhas.py

# Processar fibra ótica
docker-compose exec api python scripts/process_anatel_fibra.py
```

#### Localmente (se tiver Python instalado)

```powershell
# Ativar ambiente virtual (se tiver)
# .\.venv\Scripts\Activate.ps1

# Executar scripts
python scripts/process_aneel_subestacoes.py
python scripts/process_aneel_linhas.py
python scripts/process_anatel_fibra.py
```

---

### Passo 3: Ajustar os Scripts

**IMPORTANTE**: Você precisará ajustar os scripts conforme a estrutura real dos seus arquivos!

#### Ajustes Necessários:

1. **Caminho dos arquivos** (em cada script, função `main()`):
   ```python
   # AJUSTAR ESTES CAMINHOS:
   gdb_path = "data/raw/SEU_ARQUIVO.gdb"
   csv_path = "data/raw/SEU_ARQUIVO.csv"
   ```

2. **Nomes das colunas** (mapear colunas do arquivo para o banco):
   ```python
   column_mapping = {
       'NOME_COLUNA_ARQUIVO': 'nome_coluna_banco',
       # Exemplo:
       'NOM_SE': 'nome',
       'COD_SE': 'codigo',
       'TEN_NOM': 'tensao_kv',
   }
   ```

3. **Nome da camada** (para arquivos .gdb):
   ```python
   # Se a detecção automática não funcionar:
   layer_name = "nome_exato_da_camada"
   ```

---

## 🔍 Verificar Dados Processados

### Via psql

```powershell
# Conectar ao banco
docker-compose exec postgis psql -U datazone_user -d datazone_energy

# Dentro do psql:
# Contar registros
SELECT COUNT(*) FROM geo.subestacoes;
SELECT COUNT(*) FROM geo.linhas_transmissao;
SELECT COUNT(*) FROM geo.fibra_optica;

# Ver primeiros registros
SELECT * FROM geo.subestacoes LIMIT 5;

# Estatísticas por UF
SELECT uf, COUNT(*) as total 
FROM geo.subestacoes 
GROUP BY uf 
ORDER BY total DESC;

# Sair
\q
```

### Via API

```powershell
# Testar endpoints
curl http://localhost:8000/api/v1/subestacoes?limit=10
curl http://localhost:8000/api/v1/linhas?limit=10
curl http://localhost:8000/api/v1/fibra?limit=10
```

---

## 📝 Logs

Os scripts geram logs em:
- **Console**: Output colorido em tempo real
- **Arquivo**: `logs/process_*.log` (rotação diária, mantém 30 dias)

---

## 🐛 Troubleshooting

### Erro: "Arquivo não encontrado"
```
✅ Solução: Verificar caminho do arquivo no script
```

### Erro: "Camada não encontrada"
```
✅ Solução: Listar camadas disponíveis:
python -c "import fiona; print(fiona.listlayers('data/raw/arquivo.gdb'))"
```

### Erro: "Coluna não existe"
```
✅ Solução: Ver colunas disponíveis:
import geopandas as gpd
gdf = gpd.read_file('arquivo.gdb', layer='camada')
print(gdf.columns)
```

### Erro: "CRS inválido"
```
✅ Solução: O script converte automaticamente para EPSG:4326
Se persistir, verificar CRS original:
print(gdf.crs)
```

---

## 📊 Exemplo de Output

```
================================================================================
PROCESSAMENTO DE SUBESTAÇÕES - ANEEL
================================================================================
Arquivo GDB: data/raw/aneel_subestacoes.gdb
Camadas disponíveis: ['subestacoes', 'outras_camadas']
Usando camada: subestacoes
Lendo dados...
Colunas disponíveis: ['nome', 'codigo', 'tensao_kv', 'uf', 'geometry']
Tipo de geometria: ['Point']
Validando subestacoes...
Registros originais: 1500
Convertendo CRS de EPSG:31983 para EPSG:4326...
Registros após validação: 1498 (2 removidos)
Conectando ao banco de dados...
Inserindo dados no PostGIS...
✅ 1498 subestações inseridas com sucesso!

================================================================================
ESTATÍSTICAS
================================================================================

Distribuição por UF:
  SP: 450
  MG: 320
  RJ: 280
  ...

Distribuição por faixa de tensão:
  138-230kV: 600
  230-500kV: 450
  ...
```

---

## 🎯 Próximos Passos

1. ✅ Baixar dados da ANEEL e ANATEL
2. ✅ Colocar arquivos em `data/raw/`
3. ✅ Ajustar caminhos nos scripts
4. ✅ Executar scripts de processamento
5. ✅ Verificar dados no banco
6. ✅ Testar endpoints da API
7. ⏳ Criar GitHub Actions para CI/CD
8. ⏳ Deploy no Railway
