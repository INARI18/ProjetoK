# Script PowerShell para rodar clientes Python em paralelo, igual ao Go
param(
    [int]$numHosts = 3
)

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
$tempPyDir = Join-Path $resultsDir 'temp-py'

# Garante que o diretório temp-py existe e está limpo
if (Test-Path $tempPyDir) { Remove-Item $tempPyDir -Recurse -Force }
New-Item -ItemType Directory -Path $tempPyDir | Out-Null

# Limpa resultados anteriores
if (Test-Path (Join-Path $resultsDir 'test-python.csv')) { Remove-Item (Join-Path $resultsDir 'test-python.csv') -Force }

# Garante que o diretório existe
if (!(Test-Path $resultsDir)) { New-Item -ItemType Directory -Path $resultsDir | Out-Null }

# --- SETUP PORT-FORWARD E VALIDAÇÃO DO SERVIDOR ---
Write-Host "[INFO] Procurando pod do servidor Python no cluster..."
$podName = kubectl get pods -l app=server-python -o jsonpath='{.items[0].metadata.name}'
if (-not $podName) {
    Write-Host "[ERRO] Nao foi encontrado pod com label app=server-python. Ajuste o label ou namespace."
    exit 1
}
Write-Host "[INFO] Encontrado pod: $podName"


Write-Host "[INFO] Iniciando port-forward para o pod do servidor Python na porta $serverPort (via WSL2)..."
$pfJob = Start-Process -FilePath "wsl" -ArgumentList @("-d", "Ubuntu", "--", "kubectl", "port-forward", $podName, "${serverPort}:${serverPort}") -NoNewWindow -PassThru -RedirectStandardOutput "NUL"

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
    Write-Host ("[ERRO] Nao foi possível conectar ao servidor Python em {0}:{1} após várias tentativas. Verifique o pod e o serviço." -f $serverHost, $serverPort)
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
                Write-Host "[EXE] $execucaoAtual/$totalExecucoes | Servidores: $numServidores, Clientes: $numClientes, Mensagens: $numMensagens, Repeticao: $rep"
                $procs = @()
                $clientesPorHost = [math]::Ceiling($numClientes / $numHosts)
                for ($h = 1; $h -le $numHosts; $h++) {
                    $inicio = (($h - 1) * $clientesPorHost) + 1
                    $fim = [math]::Min($h * $clientesPorHost, $numClientes)
                    if ($inicio -gt $fim) { break }
                    $numClientesHost = $fim - $inicio + 1
                    $driveLetter = ($clientPy.Substring(0,1)).ToLower()
                    $wslClientPy = "/mnt/$driveLetter" + ($clientPy.Substring(2) -replace "\\", "/")
                    $csvTempName = "S${numServidores}_C${numClientes}_M${numMensagens}_R${rep}.csv"
                    $csvTemp = Join-Path $tempPyDir $csvTempName
                    # Corrige o prefixo para /mnt/c/Users/... no WSL
                    if ($csvTemp -match "^([A-Za-z]):") {
                        $wslCsvTemp = $csvTemp -replace "^([A-Za-z]):", "/mnt/$($matches[1].ToLower())" -replace "\\", "/"
                    } else {
                        $wslCsvTemp = $csvTemp -replace "\\", "/"
                    }
                    $wslTempPyDir = $tempPyDir -replace "\\", "/"
                    $env:PYTHON_CSV_TEMP_FILE = $wslCsvTemp
                    $wslArgs = @($wslClientPy, $serverHost, $serverPort, $numMensagens, $numClientesHost, $inicio, $numServidores, $numClientes, $cenarioId, $rep, $wslCsvTemp)
                    $allArgs = @("python3") + $wslArgs
                    try {
                        $proc = Start-Process -FilePath "wsl" -ArgumentList $allArgs -NoNewWindow -PassThru -WorkingDirectory $projectRoot -ErrorAction Stop
                        $procs += $proc
                    } catch {
                        $msg = "[ERRO] Falha ao iniciar client-python.py via WSL | servidores=$numServidores | clientes=$numClientes | mensagens=$numMensagens | repeticao=$rep | host=$h | erro=$($_.Exception.Message)"
                        Write-Host $msg -ForegroundColor Red
                        Add-Content -Path (Join-Path $resultsDir 'test-python-errors.log') -Value $msg
                    }
                }
                $procs | ForEach-Object { $_.WaitForExit() }
                $execucaoAtual++
            }
            $cenarioId++
        }
    }
}

Write-Host "[INFO] Teste de carga Python finalizado! Veja os resultados em 'results/reports'."
# Remove a pasta temp-py ao final somente se o merge criou o arquivo final
$csvPython = Join-Path $resultsDir 'test-python.csv'
if (Test-Path $csvPython) {
    if (Test-Path $tempPyDir) { Remove-Item $tempPyDir -Recurse -Force }
} else {
    Write-Host "[WARN] test-python.csv não foi criado, mantendo a pasta temp-py para depuração." -ForegroundColor Yellow
}

# Salva tempo total Python ao final do teste Python
$csvPython = Join-Path $resultsDir 'test-python.csv'
$tempoFile = Join-Path $resultsDir 'tempo-total.txt'
function Get-Tempo-Total-Py {
    param($csvPath)
    if (Test-Path $csvPath) {
        $df = Import-Csv $csvPath
        if ($df.Count -eq 0) { return $null }
        $tempos = $df | Where-Object { $_.tempo_inicio -and $_.tempo_fim } |
            Select-Object -Property tempo_inicio, tempo_fim
        if ($tempos.Count -eq 0) { return $null }
        $inicio = ($tempos | Sort-Object tempo_inicio | Select-Object -First 1).tempo_inicio
        $fim = ($tempos | Sort-Object tempo_fim -Descending | Select-Object -First 1).tempo_fim
        try {
            $dtInicio = [datetime]::Parse($inicio)
            $dtFim = [datetime]::Parse($fim)
            $duracao = $dtFim - $dtInicio
            return $duracao
        } catch { return $null }
    }
    return $null
}
$tempoPy = Get-Tempo-Total-Py $csvPython
if ($tempoPy) {
    Add-Content -Path $tempoFile -Value "Tempo Total Python: $tempoPy"
}

# Finaliza o port-forward
if ($pfJob) {
    Write-Host "[INFO] Encerrando port-forward..."
    $pfJob.Kill()
    if (Test-Path $nullFile) { Remove-Item $nullFile -Force }
}
