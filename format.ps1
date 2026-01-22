Write-Host "🎨 Iniciando formatação de código..." -ForegroundColor Cyan

# Função para verificar se o comando existe
function Test-Command ($command) {
    if (Get-Command $command -ErrorAction SilentlyContinue) {
        return $true
    }
    return $false
}

# Verificar ferramentas
if (-not (Test-Command "black") -or -not (Test-Command "isort")) {
    Write-Host "⚠️  Black ou Isort não encontrados. Instalando..." -ForegroundColor Yellow
    pip install black isort
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Falha ao instalar dependências." -ForegroundColor Red
        exit 1
    }
}

# Definir pastas alvo (apenas se existirem)
$targets = @()
if (Test-Path "scripts") { $targets += "scripts" }
if (Test-Path "tests") { $targets += "tests" }

if ($targets.Count -eq 0) {
    Write-Host "⚠️  Nenhuma pasta alvo encontrada (scripts/ ou tests/)." -ForegroundColor Yellow
    exit 0
}

# 1. Executar Isort
Write-Host "`n📦 Organizando imports com isort..." -ForegroundColor Green
isort $targets --profile black --line-length 100
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Falha no isort." -ForegroundColor Red
    exit 1
}

# 2. Executar Black
Write-Host "`n⚫ Formatando código com black..." -ForegroundColor Green
black $targets --line-length 100 --target-version py311
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Falha no black." -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ Formatação concluída com sucesso!" -ForegroundColor Cyan
