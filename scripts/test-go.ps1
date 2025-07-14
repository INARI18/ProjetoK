# Script PowerShell para automatizar o teste de carga com clientes locais e servidores no Kubernetes
# Requisitos: kind, kubectl, docker, python (para análise)

$ErrorActionPreference = 'Stop'

# Parâmetros de teste
$servidoresList = 2,4,6,8,10
$clientesList = 10,20,30,40,50,60,70,80,90,100
$mensagensList = 1,10,100,500,1000,10000
$serverDeployment = "kubernetes/server-go-deployment.yaml"
$deploymentName = "server-go"
$namespace = "default"
$clientExe = "src/client/client-go.exe"
$serverPort = 9000
$serverHost = "127.0.0.1"

# Define o diretório base do projeto (um nível acima da pasta scripts)
$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Definition)
$resultsDir = Join-Path $projectRoot 'src/results/reports'
$errorDir = Join-Path $resultsDir 'error'
$clientExe = Join-Path $projectRoot 'src/client/client-go.exe'

# Limpa resultados anteriores
$csvPath = Join-Path $resultsDir 'test-go.csv'
if (Test-Path $csvPath) { Remove-Item $csvPath -Force }

# Garante que os diretórios existem
if (!(Test-Path $resultsDir)) { New-Item -ItemType Directory -Path $resultsDir | Out-Null }

# Compila o client-go se não existir ou se o fonte for mais novo
$clientGoSrc = Join-Path $projectRoot 'src/client/client-go.go'
if (!(Test-Path $clientExe) -or ((Get-Item $clientGoSrc).LastWriteTime -gt (Get-Item $clientExe).LastWriteTime)) {
    Write-Host "[INFO] Compilando client-go.exe..."
    go build -o $clientExe $clientGoSrc
}

# Função para escalar o deployment
function Scale-Deployment($replicas) {
    kubectl scale deployment $deploymentName --replicas=$replicas -n $namespace
    Write-Host "[INFO] Aguardando pods ficarem prontos..."
    do {
        Start-Sleep -Seconds 5
        $ready = kubectl get pods -l app=server-go -o json | ConvertFrom-Json
        $allReady = $true
        foreach ($pod in $ready.items) {
            if ($pod.status.phase -ne "Running") { $allReady = $false }
        }
    } while (-not $allReady)
}

# Função para iniciar port-forward
function Start-PortForward {
    $podName = kubectl get pods -l app=server-go -o jsonpath='{.items[0].metadata.name}'
    Write-Host "[INFO] Fazendo port-forward do pod $podName..."
    $pf = Start-Process -FilePath "kubectl" -ArgumentList @("port-forward", $podName, "${serverPort}:${serverPort}", "-n", $namespace) -NoNewWindow -PassThru -RedirectStandardOutput "NUL"
    Start-Sleep -Seconds 2 # tempo para estabilizar
    return $pf
}

# Função para parar port-forward
function Stop-PortForward($pf) {
    if ($pf) { Stop-Process -Id $pf.Id -Force }
}

# Limpa resultados anteriores
if (Test-Path "results/reports/test-go.csv") { Remove-Item "results/reports/test-go.csv" -Force }

# Calcula o total de execuções
$repeticoes = 10
$totalExecucoes = $servidoresList.Count * $clientesList.Count * $mensagensList.Count * $repeticoes
$execucaoAtual = 1
$c = 1
foreach ($numServidores in $servidoresList) {
    Write-Host "[INFO] Escalando deployment para $numServidores servidores..."
    Scale-Deployment $numServidores
    $pf = Start-PortForward
    try {
        foreach ($numClientes in $clientesList) {
            foreach ($numMensagens in $mensagensList) {
                $cenarioId = $c  # Agora passa só o número
                for ($rep = 1; $rep -le $repeticoes; $rep++) {
                    Write-Host "[EXE] $execucaoAtual/$totalExecucoes"
                    Write-Host "Servidores: $numServidores, Clientes: $numClientes, Mensagens: $numMensagens, Repeticao: $rep"
                    $jobs = @()
                    $logPath = Join-Path $resultsDir 'test-go-errors.log'
                    for ($i = 1; $i -le $numClientes; $i++) {
                        $args = @($serverHost, $serverPort, $numMensagens, $numClientes, $i, $numServidores, $cenarioId, $rep)
                        try {
                            $proc = Start-Process -FilePath $clientExe -ArgumentList $args -NoNewWindow -PassThru -WorkingDirectory $projectRoot -ErrorAction Stop
                            $jobs += $proc
                        } catch {
                            $msg = "[ERRO] Falha ao iniciar cliente_id=$i | servidores=$numServidores | clientes=$numClientes | mensagens=$numMensagens | repeticao=$rep | erro=$($_.Exception.Message)"
                            Write-Host $msg -ForegroundColor Red
                            Add-Content -Path $logPath -Value $msg
                        }
                    }
                    $jobs | ForEach-Object { $_.WaitForExit() }
                    $execucaoAtual++
                }
                $c++
            }
        }
    } finally {
        Stop-PortForward $pf
    }
}

# 8. Instala dependências Python (requirements.txt)
if (Test-Path "requirements.txt") {
    Write-Host "[INFO] Instalando dependências Python..."
    pip install -r requirements.txt
}

Write-Host "[INFO] Teste de carga finalizado! Veja os resultados em 'results/reports'."
