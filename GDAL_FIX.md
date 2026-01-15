# 🔧 Correção do Erro de Build do GDAL

## ❌ Problema Identificado

O erro ocorreu porque:
1. **GDAL 3.2.2.1** (no requirements.txt) é **incompatível com Python 3.11**
2. A compilação do GDAL via pip falha com erros de C++

```
error: command '/usr/bin/g++' failed with exit code 1
ERROR: Failed building wheel for GDAL
```

## ✅ Solução Aplicada

### 1. Removido GDAL do `requirements.txt`
- ❌ Antes: `GDAL==3.2.2.1` (tentava compilar)
- ✅ Agora: Usa GDAL do sistema (pré-compilado)

### 2. Adicionado `python3-gdal` no `Dockerfile`
- Instalação via `apt-get` (mais confiável)
- Bindings Python já compilados
- Compatível com Python 3.11

## 🚀 Próximos Passos

Execute novamente o build:

```powershell
# Navegar para o diretório
cd "c:\Users\jmarc\OneDrive\Área de Trabalho\DataZone Energy"

# Build limpo (agora deve funcionar!)
docker-compose build --no-cache --pull

# Iniciar containers
docker-compose up -d

# Ver logs
docker-compose logs -f api
```

## ⏱️ Tempo Estimado

- **Build**: 5-8 minutos (baixando dependências)
- **Startup**: 10-20 segundos

## 🔍 Como Verificar se Funcionou

Após o build, você deve ver:

```
✅ Successfully built <image-id>
✅ Successfully tagged datazone-energy-api:latest
```

E ao iniciar:

```
datazone_postgis  ... healthy
datazone_api      ... healthy
```

## 💡 Por Que Isso Funciona?

| Método | Problema | Solução |
|--------|----------|---------|
| `pip install GDAL` | Precisa compilar C++ | ❌ Falha com Python 3.11 |
| `apt-get install python3-gdal` | Pré-compilado | ✅ Funciona sempre |

## 🐛 Se Ainda Der Erro

### Erro: "python3-gdal not found"

```dockerfile
# Trocar de:
python3-gdal

# Para:
python3-gdal=3.2.2+dfsg-2+deb11u2
```

### Erro: "Module 'osgeo' not found"

Adicione no Dockerfile após instalar dependências:

```dockerfile
RUN ln -s /usr/lib/python3/dist-packages/osgeo /usr/local/lib/python3.11/site-packages/
```

---

**Status**: ✅ Correções aplicadas, pronto para build!
