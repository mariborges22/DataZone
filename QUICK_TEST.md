# ⚡ Teste Rápido - 5 Minutos

## 🚀 Passo 1: Instalar Dependências (1 min)

```bash
cd DataZone
pip install -r requirements.txt
```

## 🏃 Passo 2: Iniciar API (1 min)

```bash
python app/main.py
```

**Aguarde ver:** `✅ Banco de dados inicializado`

## 🧪 Passo 3: Teste Automatizado (3 min)

### Opção A: Script Python (Completo)

```bash
# Em outro terminal
cd DataZone
python test_security.py
```

### Opção B: Script PowerShell (Windows - Rápido)

```powershell
# Em outro terminal PowerShell
cd DataZone
.\test_rate_limit.ps1
```

### Opção C: Teste Manual (cURL)

```bash
# Teste 1: Health Check
curl http://localhost:8000/health

# Teste 2: Rate Limiting (enviar 25 requisições)
# Windows PowerShell:
1..25 | ForEach-Object { curl http://localhost:8000/api/v1/fibra }

# Linux/Mac:
for i in {1..25}; do curl http://localhost:8000/api/v1/fibra; done
```

## ✅ Resultado Esperado

### API Rodando:
```
✅ Conexão com PostgreSQL/PostGIS estabelecida
✅ Banco de dados inicializado
INFO: Uvicorn running on http://0.0.0.0:8000
```

### Rate Limiting:
```
✅ Requisição 1-20: OK (200)
🛑 Requisição 21-25: RATE LIMITED (429)
```

### Resposta 429:
```json
{
  "error": "Rate limit exceeded",
  "message": "Você excedeu o limite de requisições...",
  "detail": "20 per 1 minute"
}
```

## 🐛 Problemas?

### API não inicia:
```bash
# Verificar se porta 8000 está livre
netstat -ano | findstr :8000

# Verificar se banco está rodando
psql -U postgres -c "SELECT version();"
```

### slowapi não encontrado:
```bash
pip install slowapi==0.1.9
```

### Rate limiting não funciona:
- Localhost (`127.0.0.1`) é whitelisted por padrão
- Para testar, use IP diferente ou desabilite whitelist temporariamente

## 📚 Mais Detalhes

- **Testes Completos:** [TESTING_GUIDE.md](TESTING_GUIDE.md)
- **Segurança:** [SECURITY.md](SECURITY.md)
- **Scripts:**
  - [test_security.py](test_security.py) - Testes completos
  - [test_rate_limit.ps1](test_rate_limit.ps1) - Teste rápido Windows

## 🎉 Próximo Passo

Se tudo funcionou:
1. ✅ Rate limiting implementado
2. ✅ SQL Injection bloqueado
3. ✅ API protegida

**Deploy para produção!** 🚀
