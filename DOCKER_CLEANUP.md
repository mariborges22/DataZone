# 🧹 Guia: Limpeza e Reinicialização do Docker (Memória Mínima)

## ✅ Otimizações Aplicadas

Reduzi o uso de memória:
- **PostgreSQL**: 512MB máximo (antes: sem limite)
- **API FastAPI**: 1GB máximo (antes: 2GB)
- **Total estimado**: ~1.5GB (antes: ~3GB+)

---

## 📋 Passo a Passo Completo

### 1️⃣ Parar Containers Atuais

```powershell
# Navegar para o diretório
cd "c:\Users\jmarc\OneDrive\Área de Trabalho\DataZone Energy"

# Parar todos os containers
docker-compose down
```

---

### 2️⃣ Limpar Cache e Volumes (Liberar Espaço)

```powershell
# Remover volumes (dados do banco)
docker-compose down -v

# Limpar TUDO: imagens, cache, volumes não utilizados
docker system prune -a --volumes

# Quando perguntar "Are you sure?", digite: y
```

⚠️ **Isso vai liberar MUITO espaço**, mas apaga:
- Imagens Docker antigas
- Cache de build
- Volumes não utilizados
- Containers parados

---

### 3️⃣ Verificar Espaço Liberado

```powershell
# Ver quanto espaço o Docker está usando
docker system df
```

---

### 4️⃣ Criar Arquivo .env (Se Ainda Não Existe)

```powershell
# Copiar template
Copy-Item .env.example .env
```

---

### 5️⃣ Build Limpo (Sem Cache)

```powershell
# Build sem usar cache (garante build limpo)
docker-compose build --no-cache --pull
```

⏱️ **Isso vai demorar ~5-10 minutos** porque vai baixar tudo do zero.

---

### 6️⃣ Iniciar Containers

```powershell
# Iniciar APENAS os serviços essenciais (sem PgAdmin)
docker-compose up -d

# Ver logs em tempo real
docker-compose logs -f
```

Para sair dos logs, pressione `Ctrl + C`.

---

### 7️⃣ Verificar Status

```powershell
# Ver status dos containers
docker-compose ps

# Verificar saúde da API
curl http://localhost:8000/health

# Ou abrir no navegador
start http://localhost:8000/docs
```

---

## 🔍 Troubleshooting

### ❌ Erro: "Port 5432 already in use"

```powershell
# Ver o que está usando a porta
netstat -ano | findstr :5432

# Parar PostgreSQL local (se tiver)
Stop-Service postgresql*
```

---

### ❌ Erro: "Cannot connect to Docker daemon"

1. Abrir Docker Desktop
2. Aguardar inicializar completamente
3. Tentar novamente

---

### ❌ Build parou em 10/12

Possíveis causas:
1. **Falta de memória**: Feche outros programas
2. **Internet lenta**: Aguarde, está baixando dependências
3. **Timeout**: Tente novamente

```powershell
# Se parou, tente com mais timeout
docker-compose build --no-cache --pull --build-arg BUILDKIT_INLINE_CACHE=1
```

---

### ❌ Container reiniciando constantemente

```powershell
# Ver logs de erro
docker-compose logs api
docker-compose logs postgis

# Ver últimas 50 linhas
docker-compose logs --tail=50 api
```

---

## 💡 Dicas para Economizar Memória

### Opção 1: Iniciar Apenas o Banco

```powershell
# Iniciar só o PostgreSQL
docker-compose up -d postgis

# Rodar a API localmente (sem Docker)
# Mas precisa instalar Python e dependências
```

### Opção 2: Desabilitar Hot Reload

Edite `docker-compose.yml`, linha do comando da API:

```yaml
# Trocar de:
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Para:
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Isso economiza ~100-200MB.

---

## 📊 Monitorar Uso de Recursos

```powershell
# Ver uso de CPU e memória em tempo real
docker stats

# Ver apenas containers do DataZone
docker stats datazone_api datazone_postgis
```

Para sair, pressione `Ctrl + C`.

---

## 🛑 Parar Tudo Quando Não Estiver Usando

```powershell
# Parar containers (mantém dados)
docker-compose stop

# Reiniciar depois
docker-compose start
```

---

## 🗑️ Limpar Tudo Novamente (Se Necessário)

```powershell
# Parar e remover tudo
docker-compose down -v

# Limpar sistema
docker system prune -a --volumes
```

---

## ✅ Checklist Final

- [ ] Executei `docker-compose down -v`
- [ ] Executei `docker system prune -a --volumes`
- [ ] Executei `docker-compose build --no-cache`
- [ ] Executei `docker-compose up -d`
- [ ] Containers estão rodando (`docker-compose ps`)
- [ ] API responde em http://localhost:8000/health
- [ ] Documentação acessível em http://localhost:8000/docs

---

**Uso de memória esperado:**
- PostgreSQL: ~300-400MB
- API: ~400-600MB
- **Total: ~1GB** (muito melhor que antes!)
