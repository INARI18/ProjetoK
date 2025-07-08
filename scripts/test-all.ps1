# Script unificado para rodar testes de carga Go e Python

param(
    [switch]$onlyPython,
    [switch]$onlyGo
)

# Verifica se o kind está instalado
if (-not (Get-Command kind -ErrorAction SilentlyContinue)) {
    Write-Host "[ERRO] O 'kind' nao esta instalado ou nao esta no PATH. Instale o kind antes de rodar este script." -ForegroundColor Red
    exit 1
}

Write-Host "[INFO] Configurando cluster Kubernetes com kind..." -ForegroundColor Cyan

# 1. Usa o cluster project-k se existir, senão cria
$clusterName = "project-k"
$kindGetClusters = & kind get clusters
if ($kindGetClusters -notcontains $clusterName) {
    Write-Host "[INFO] Criando cluster $clusterName..." -ForegroundColor Cyan
    kind create cluster --name $clusterName
} else {
    Write-Host "[INFO] Cluster $clusterName ja existe." -ForegroundColor Green
}

# 2. Aplica os YAMLs de deployment dos servidores Go e Python
$projectRoot = Split-Path $PSScriptRoot -Parent  # Agora pega a raiz do projeto
$kubeDir = Join-Path $projectRoot 'kubernetes'
$yamlGo = Join-Path $kubeDir 'server-go-deployment.yaml'
$yamlPython = Join-Path $kubeDir 'server-python-deployment.yaml'

if (Test-Path $yamlGo) {
    Write-Host "[INFO] Aplicando deployment do servidor Go..." -ForegroundColor Cyan
    kubectl apply -f $yamlGo
} else {
    Write-Host "[ERRO] Nao encontrou $yamlGo" -ForegroundColor Red
    exit 1
}
if (Test-Path $yamlPython) {
    Write-Host "[INFO] Aplicando deployment do servidor Python..." -ForegroundColor Cyan
    kubectl apply -f $yamlPython
} else {
    Write-Host "[ERRO] Nao encontrou $yamlPython" -ForegroundColor Red
    exit 1
}

# Aguarda pods ficarem prontos
Write-Host "[INFO] Aguardando pods dos servidores ficarem prontos..." -ForegroundColor Cyan
$maxTentativas = 30
for ($tentativa = 1; $tentativa -le $maxTentativas; $tentativa++) {
    $pods = kubectl get pods -o json | ConvertFrom-Json
    $allReady = $true
    foreach ($pod in $pods.items) {
        if ($pod.status.phase -ne "Running") { $allReady = $false }
    }
    if ($allReady -and $pods.items.Count -ge 2) { break }
    Start-Sleep -Seconds 5
}

Write-Host "[INFO] Cluster e deployments prontos! Iniciando testes..." -ForegroundColor Green

Write-Host "[INFO] Iniciando testes de carga com clientes Go..." -ForegroundColor Cyan

if (-not $onlyPython) {
    # Executa o script de testes Go
    $goScript = Join-Path $projectRoot 'scripts\test-go.ps1'
    if (Test-Path $goScript) {
        & $goScript
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERRO] Testes Go falharam ou foram interrompidos." -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "[ERRO] test-go.ps1 nao encontrado em $goScript" -ForegroundColor Red
        exit 1
    }
    if (-not $onlyGo) {
        Write-Host "[INFO] Testes Go finalizados. Iniciando testes de carga com clientes Python..." -ForegroundColor Cyan
    }
} else {
    Write-Host "[INFO] Pulando testes Go. Executando apenas testes Python..." -ForegroundColor Yellow
}

if (-not $onlyGo) {
    # Executa o script de testes Python
    $pythonScript = Join-Path $projectRoot 'scripts\test-python.ps1'
    if (Test-Path $pythonScript) {
        & $pythonScript
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERRO] Testes Python falharam ou foram interrompidos." -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "[ERRO] test-python.ps1 nao encontrado em $pythonScript" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[INFO] Pulando testes Python. Executando apenas testes Go..." -ForegroundColor Yellow
}

Write-Host "[INFO] Ambos os testes concluidos. Iniciando analise dos resultados..." -ForegroundColor Cyan

# Caminhos dos CSVs e do script de análise
$toolsPath = Join-Path $projectRoot 'src\tools'
$analyzeScript = Join-Path $toolsPath 'analyze_results.py'
$csvGo = Join-Path $projectRoot 'src\results\reports\test-go.csv'
$csvPython = Join-Path $projectRoot 'src\results\reports\test-python.csv'

# Analisa resultados Go
if (Test-Path $analyzeScript -and Test-Path $csvGo) {
    Write-Host "[INFO] Analisando resultados do Go..." -ForegroundColor Yellow
    python $analyzeScript $csvGo go
} else {
    Write-Host "[WARN] Nao foi possivel encontrar o script de análise ou o CSV do Go." -ForegroundColor DarkYellow
}

# Analisa resultados Python
if (Test-Path $analyzeScript -and Test-Path $csvPython) {
    Write-Host "[INFO] Analisando resultados do Python..." -ForegroundColor Yellow
    python $analyzeScript $csvPython python
} else {
    Write-Host "[WARN] Nao foi possivel encontrar o script de analise ou o CSV do Python." -ForegroundColor DarkYellow
}

Write-Host "[OK] Teste de carga finalizado! Veja os resultados em 'results/reports'." -ForegroundColor Green

# Geração dos gráficos comparativos
$generateChartsScript = Join-Path $toolsPath 'generate_charts.py'
if (Test-Path $generateChartsScript) {
    Write-Host "[INFO] Gerando gráficos comparativos..." -ForegroundColor Cyan
    python $generateChartsScript
    Write-Host "[OK] Gráficos gerados em 'results/charts'." -ForegroundColor Green
} else {
    Write-Host "[WARN] Script de geração de gráficos não encontrado em $generateChartsScript" -ForegroundColor DarkYellow
}
