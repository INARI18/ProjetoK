# Script PowerShell para rodar clientes Python em paralelo, igual ao Go

$ErrorActionPreference = 'Stop'

# Parâmetros de teste
$servidoresList = 2,4,6,8,10
$clientesList = 10,20,30,40,50,60,70,80,90,100
$mensagensList = 1,10,100,500,1000,10000
$serverPort = 9000
$serverHost = "127.0.0.1"
$pythonExe = "python"  # ou caminho completo do python, se necessário
$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Definition)
$clientPy = Join-Path $projectRoot 'src/client/client-python.py'
$resultsDir = Join-Path $projectRoot 'src/results/reports'

# Limpa resultados anteriores
if (Test-Path (Join-Path $resultsDir 'test-python.csv')) { Remove-Item (Join-Path $resultsDir 'test-python.csv') -Force }

# Garante que o diretório existe
if (!(Test-Path $resultsDir)) { New-Item -ItemType Directory -Path $resultsDir | Out-Null }

# --- SETUP PORT-FORWARD E VALIDAÇÃO DO SERVIDOR ---
Write-Host "[INFO] Procurando pod do servidor Python no cluster..."
$podName = kubectl get pods -l app=server-python -o jsonpath='{.items[0].metadata.name}'
if (-not $podName) {
    Write-Host "[ERRO] Não foi encontrado pod com label app=server-python. Ajuste o label ou namespace."
    exit 1
}
Write-Host "[INFO] Encontrado pod: $podName"

Write-Host "[INFO] Iniciando port-forward para o pod do servidor Python na porta $serverPort..."
$nullFile = [System.IO.Path]::GetTempFileName()
$pfJob = Start-Process -FilePath "kubectl" -ArgumentList @("port-forward", $podName, ("{0}:{0}" -f $serverPort)) -NoNewWindow -PassThru -RedirectStandardOutput "NUL" -RedirectStandardError $nullFile

# Aguarda o servidor realmente aceitar conexões múltiplas
$maxTentativas = 20
$conexoesOk = $false
for ($tentativa = 1; $tentativa -le $maxTentativas; $tentativa++) {
    $ok = $true
    for ($i = 1; $i -le 3; $i++) {
        try {
            $tcp = New-Object System.Net.Sockets.TcpClient
            $tcp.Connect($serverHost, $serverPort)
            if ($tcp.Connected) {
                $tcp.Close()
            } else {
                $ok = $false
                break
            }
        } catch {
            $ok = $false
            break
        }
    }
    if ($ok) { $conexoesOk = $true; break }
    Start-Sleep -Milliseconds 500
}
if (-not $conexoesOk) {
    Write-Host ("[ERRO] Não foi possível conectar ao servidor Python em {0}:{1} após várias tentativas. Verifique o pod e o serviço." -f $serverHost, $serverPort)
    if ($pfJob) { $pfJob.Kill() }
    exit 1
}
Write-Host "[INFO] Conexao com o servidor Python OK! Iniciando testes..."

# Calcula o total de execuções
$repeticoes = 10
$totalExecucoes = $servidoresList.Count * $clientesList.Count * $mensagensList.Count * $repeticoes
$execucaoAtual = 1
$cenarioId = 1

foreach ($numServidores in $servidoresList) {
    foreach ($numClientes in $clientesList) {
        foreach ($numMensagens in $mensagensList) {
            for ($rep = 1; $rep -le $repeticoes; $rep++) {
                Write-Host "[EXE] $execucaoAtual/$totalExecucoes"
                Write-Host "Servidores: $numServidores, Clientes: $numClientes, Mensagens: $numMensagens, Repeticao: $rep"
                $jobs = @()
                for ($i = 1; $i -le $numClientes; $i++) {
                    $args = @($clientPy, $serverHost, $serverPort, $numMensagens, $numClientes, $i, $numServidores, $cenarioId, $rep)
                    $jobs += Start-Process -FilePath $pythonExe -ArgumentList $args -NoNewWindow -PassThru -WorkingDirectory $projectRoot
                }
                $jobs | ForEach-Object { $_.WaitForExit() }
                $execucaoAtual++
            }
            $cenarioId++
        }
    }
}

Write-Host "[INFO] Teste de carga Python finalizado! Veja os resultados em 'results/reports'."

# Finaliza o port-forward
if ($pfJob) {
    Write-Host "[INFO] Encerrando port-forward..."
    $pfJob.Kill()
    if (Test-Path $nullFile) { Remove-Item $nullFile -Force }
}
