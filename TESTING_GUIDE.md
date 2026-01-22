# 🧪 Guia de Testes - DataZone Energy

## 📋 Pré-requisitos

Antes de iniciar os testes, certifique-se de:

1. **Instalar todas as dependências:**
```bash
cd DataZone
pip install -r requirements.txt
```

2. **Configurar variáveis de ambiente:**
```bash
# Criar arquivo .env se não existir
cp .env.example .env

# Editar .env com suas configurações
# DATABASE_URL, SECRET_KEY, etc.
```

3. **Banco de dados configurado:**
```bash
# Verificar se PostgreSQL/PostGIS está rodando
# Criar banco de dados se necessário
```

---

## 🚀 Passo 1: Iniciar a API

### Opção A: Desenvolvimento (com reload)
```bash
cd DataZone
python app/main.py
```

### Opção B: Produção (com uvicorn)
```bash
cd DataZone
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Saída esperada:**
```
🚀 Iniciando DataZone Energy API...
Ambiente: development
Debug: True
✅ Conexão com PostgreSQL/PostGIS estabelecida
✅ Banco de dados inicializado
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## 🧪 Passo 2: Testes Manuais Rápidos

### 2.1 Testar Health Check
```bash
curl http://localhost:8000/health
```

**Resposta esperada:**
```json
{
  "status": "healthy",
  "service": "DataZone Energy API",
  "version": "1.0.0",
  "environment": "development",
  "database": "connected"
}
```

### 2.2 Testar Root Endpoint
```bash
curl http://localhost:8000/
```

**Resposta esperada:**
```json
{
  "message": "DataZone Energy API",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health",
  "rate_limit_status": "/api/v1/rate-limit-status"
}
```

### 2.3 Testar Rate Limit Status
```bash
curl http://localhost:8000/api/v1/rate-limit-status
```

**Resposta esperada:**
```json
{
  "client_id": "127.0.0.1",
  "whitelisted": true,
  "limits": {
    "read_light": "100/minute",
    "read_medium": "50/minute",
    "read_heavy": "20/minute",
    ...
  },
  "storage": "memory"
}
```

---

## 🚦 Passo 3: Testar Rate Limiting

### 3.1 Teste Manual com Loop

**Windows (PowerShell):**
```powershell
# Enviar 25 requisições (limite é 20/min)
1..25 | ForEach-Object {
    Write-Host "Requisição $_"
    curl http://localhost:8000/api/v1/fibra
    Start-Sleep -Milliseconds 100
}
```

**Linux/Mac:**
```bash
# Enviar 25 requisições (limite é 20/min)
for i in {1..25}; do
    echo "Requisição $i"
    curl http://localhost:8000/api/v1/fibra
    sleep 0.1
done
```

**Resultado esperado:**
- Primeiras 20 requisições: `200 OK`
- Requisições 21-25: `429 Too Many Requests`

**Resposta 429:**
```json
{
  "error": "Rate limit exceeded",
  "message": "Você excedeu o limite de requisições. Tente novamente em alguns segundos.",
  "detail": "20 per 1 minute",
  "endpoint": "/api/v1/fibra"
}
```

### 3.2 Verificar Headers de Rate Limit

```bash
curl -I http://localhost:8000/api/v1/fibra
```

**Headers esperados:**
```
HTTP/1.1 200 OK
X-RateLimit-Limit: 20
X-RateLimit-Remaining: 19
X-RateLimit-Reset: 1234567890
```

---

## 🛡️ Passo 4: Testar SQL Injection Prevention

### 4.1 Teste com Payloads Maliciosos

```bash
# Teste 1: SQL Injection clássico
curl "http://localhost:8000/api/v1/fibra?municipio='; DROP TABLE users--"

# Teste 2: UNION attack
curl "http://localhost:8000/api/v1/fibra?municipio=' UNION SELECT * FROM users--"

# Teste 3: Boolean-based blind
curl "http://localhost:8000/api/v1/fibra?municipio=1' OR '1'='1"
```

**Resultado esperado:**
- Status: `200 OK`
- Features: `[]` (vazio, pois SQLAlchemy sanitiza)
- **NUNCA** deve retornar erro de SQL ou executar comandos maliciosos

### 4.2 Testar Validação de Bbox

```bash
# Bbox válido (deve funcionar)
curl "http://localhost:8000/api/v1/fibra?bbox=-46.5,-23.5,-46.4,-23.4"

# Bbox muito grande (deve ser rejeitado)
curl "http://localhost:8000/api/v1/fibra?bbox=-100,-50,100,50"

# Bbox inválido (deve retornar 400)
curl "http://localhost:8000/api/v1/fibra?bbox=invalid,data,here"
```

---

## 🤖 Passo 5: Executar Testes Automatizados

### 5.1 Script de Teste Completo

```bash
cd DataZone
python test_security.py
```

**O script vai testar:**
1. ✅ Health Check da API
2. ✅ Rate Limiting funcionando
3. ✅ Endpoint de status de rate limit
4. ✅ Rate limiting em múltiplos endpoints
5. ✅ Proteção contra SQL Injection

**Saída esperada:**
```
🔒🔒🔒🔒🔒🔒🔒🔒🔒🔒
TESTES DE SEGURANÇA - DATAZONE ENERGY
🔒🔒🔒🔒🔒🔒🔒🔒🔒🔒

============================================================
🏥 TESTE 1: Health Check
============================================================
Status Code: 200
Response: {...}
✅ API está respondendo!

============================================================
🚦 TESTE 2: Rate Limiting - /api/v1/fibra
============================================================
Limite esperado: 20 requisições/minuto
Enviando 30 requisições...

✅ Requisição 1: OK (200)
✅ Requisição 2: OK (200)
...
✅ Requisição 20: OK (200)
🛑 Requisição 21: RATE LIMITED (429)
...

📊 RESULTADOS:
   Total de requisições: 30
   Sucesso (200): 20
   Rate Limited (429): 10
   Erros: 0
   Tempo total: 3.45s

✅ Rate limiting está FUNCIONANDO!
...
```

### 5.2 Testes Unitários (Pytest)

```bash
cd DataZone
pytest tests/ -v
```

---

## 📊 Passo 6: Testar com Ferramentas Profissionais

### 6.1 Apache Bench (ab)

```bash
# Instalar (se necessário)
# Windows: https://www.apachelounge.com/download/
# Linux: sudo apt-get install apache2-utils
# Mac: brew install ab

# Testar com 100 requisições, 10 concorrentes
ab -n 100 -c 10 http://localhost:8000/api/v1/fibra
```

**Resultado esperado:**
- Algumas requisições com erro 429
- Rate limiting funcionando sob carga

### 6.2 Postman/Insomnia

1. Importar collection do DataZone
2. Configurar ambiente com `base_url = http://localhost:8000`
3. Executar requests múltiplas vezes
4. Verificar erro 429 após limite

### 6.3 JMeter (Teste de Carga)

```bash
# Criar plano de teste
# - Thread Group: 50 usuários
# - Ramp-up: 10 segundos
# - Loop: 10 vezes
# - HTTP Request: GET /api/v1/fibra

# Executar
jmeter -n -t test_plan.jmx -l results.jtl
```

---

## 🔍 Passo 7: Verificar Logs

### 7.1 Logs da Aplicação

```bash
# Ver logs em tempo real
tail -f logs/app.log

# Buscar rate limits
grep "Rate limit excedido" logs/app.log

# Buscar erros de validação
grep "Erro de validação" logs/app.log
```

### 7.2 Logs Esperados

**Rate limit excedido:**
```
2026-01-22 10:30:15 | WARNING | ⚠️ Rate limit excedido | Cliente: 192.168.1.100 | Endpoint: /api/v1/fibra | Limite: 20 per 1 minute
```

**Validação de table name:**
```
2026-01-22 10:31:20 | ERROR | ❌ Erro de validação: Nome de tabela inválido: 'users; DROP--'
```

---

## 🐛 Troubleshooting

### Problema: "slowapi not found"
**Solução:**
```bash
pip install slowapi==0.1.9
```

### Problema: Rate limiting não funciona
**Verificações:**
1. ✅ `slowapi` instalado?
2. ✅ Limiter configurado em `main.py`?
3. ✅ Decoradores aplicados nos endpoints?
4. ✅ Redis rodando (se `ENABLE_REDIS_CACHE=true`)?

**Debug:**
```bash
# Verificar se rate limiter está ativo
curl http://localhost:8000/api/v1/rate-limit-status
```

### Problema: Erro 500 ao testar
**Verificações:**
1. ✅ Banco de dados está rodando?
2. ✅ Tabelas criadas?
3. ✅ Variáveis de ambiente configuradas?

**Ver logs:**
```bash
tail -f logs/app.log
```

### Problema: Localhost está whitelisted
**Solução:**
- Por padrão, `127.0.0.1` é whitelisted (sem rate limit)
- Para testar, use IP diferente ou desabilite whitelist em `rate_limit.py`

```python
# app/core/rate_limit.py
def is_whitelisted(ip: str) -> bool:
    # Comentar temporariamente para testar
    # return ip in ["127.0.0.1", "localhost", "::1"]
    return False  # Desabilitar whitelist para testes
```

---

## ✅ Checklist de Testes

Antes de considerar completo, verifique:

- [ ] API está respondendo em `/health`
- [ ] Rate limiting bloqueia após limite
- [ ] Erro 429 retorna JSON correto
- [ ] Headers de rate limit presentes
- [ ] `/api/v1/rate-limit-status` funciona
- [ ] Payloads SQL injection não quebram API
- [ ] Bbox muito grande é rejeitado
- [ ] Logs de segurança sendo gerados
- [ ] Script `test_security.py` passa 100%
- [ ] Testes unitários passam (`pytest`)

---

## 📚 Próximos Passos

Após todos os testes passarem:

1. **Produção:**
   - Habilitar Redis (`ENABLE_REDIS_CACHE=true`)
   - Configurar CORS apenas domínios autorizados
   - `DEBUG=False`
   - HTTPS habilitado

2. **Monitoramento:**
   - Configurar alertas para erros 429 frequentes
   - Monitorar logs de SQL injection tentativas
   - Dashboard de rate limiting

3. **Melhorias:**
   - Implementar autenticação JWT
   - Rate limiting por usuário (não só IP)
   - WAF (Web Application Firewall)

---

## 🎉 Conclusão

Se todos os testes passaram:
- ✅ Rate limiting funcionando
- ✅ SQL Injection bloqueado
- ✅ API protegida contra DDoS

**Status: Pronto para Produção! 🚀**

Para mais detalhes, consulte [SECURITY.md](SECURITY.md)
