# Script PowerShell para automatizar o teste de carga com clientes locais e servidores no Kubernetes
param(
    [int]$numHosts = 3
)
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
# --- GARANTE QUE A PORTA NÃO ESTÁ EM USO ANTES DE INICIAR O PORT-FORWARD ---
$portaOcupada = $false
try {
    $tcpListener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Parse($serverHost), $serverPort)
    $tcpListener.Start()
    $tcpListener.Stop()
} catch {
    $portaOcupada = $true
}
if ($portaOcupada) {
    Write-Host ("[INFO] Porta $serverPort já está em uso em $serverHost. Tentando liberar...") -ForegroundColor Yellow
    # Tenta matar processos que estejam usando a porta (Windows)
    $netstat = netstat -ano | Select-String ":$serverPort "
    foreach ($linha in $netstat) {
        if ($linha -match '\s+(\d+)$') {
            $pid = $matches[1]
            try {
                Stop-Process -Id $pid -Force -ErrorAction Stop
                Write-Host "[INFO] Processo $pid que usava a porta $serverPort foi finalizado." -ForegroundColor Yellow
            } catch {
                Write-Host "[WARN] Não foi possível finalizar o processo $pid usando a porta $serverPort." -ForegroundColor Yellow
            }
        }
    }
    # Aguarda a liberação
    Start-Sleep -Seconds 2
}
# --- FIM DA GARANTIA DE PORTA LIVRE ---

# Define o diretório base do projeto (um nível acima da pasta scripts)

# Corrige o path para garantir que tempGoDir sempre seja src/results/reports/temp-go relativo à raiz do projeto
$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Definition)
$resultsDir = Join-Path $projectRoot 'src/results/reports'
$tempGoDir = Join-Path $resultsDir 'temp-go'
$errorDir = Join-Path $resultsDir 'error'
$clientExe = Join-Path $projectRoot 'src/client/client-go.exe'

# Força o uso de barra normal para o tempGoDir (evita path estranho no WSL)

# Limpa resultados anteriores
$csvPath = Join-Path $resultsDir 'test-go.csv'
if (Test-Path $csvPath) { Remove-Item $csvPath -Force }

# Garante que os diretórios existem
if (!(Test-Path $resultsDir)) { New-Item -ItemType Directory -Path $resultsDir | Out-Null }

# Garante que o diretório temp-go existe e está limpo
if (Test-Path $tempGoDir) { Remove-Item $tempGoDir -Recurse -Force }
New-Item -ItemType Directory -Path $tempGoDir | Out-Null


# Usa apenas o binário Linux já pronto em src/client/client-go
$clientGoLinux = Join-Path $projectRoot 'src/client/client-go'
if (!(Test-Path $clientGoLinux)) {
    Write-Host "[ERRO] Binario Linux client-go nao encontrado em $clientGoLinux. Compile manualmente antes de rodar o script." -ForegroundColor Red
    exit 1
}

# Copia o binário para o home do usuário WSL2 antes dos testes, evitando /root

$wslUser = 'bia18'
Write-Host "[DEBUG] Usuario WSL2 detectado: '$wslUser'"
if (-not $wslUser) {
    Write-Host "[ERRO] Nao foi possível detectar o usuario do WSL2. Verifique se o WSL2 está instalado corretamente." -ForegroundColor Red
    exit 1
}
$wslHome = "/home/$wslUser"
Write-Host "[DEBUG] Listando arquivos em /mnt/c/Users/Bia/Desktop/ProjetoK/src/client dentro do WSL2:"
wsl -d Ubuntu -- sh -c "ls -l /mnt/c/Users/Bia/Desktop/ProjetoK/src/client/"
Write-Host "[INFO] Copiando binario client-go para $wslHome do WSL2..."
wsl -d Ubuntu -- sh -c "rm -f $wslHome/client-go && cp /mnt/c/Users/Bia/Desktop/ProjetoK/src/client/client-go $wslHome/client-go && chmod +x $wslHome/client-go"

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
    Write-Host "[INFO] Fazendo port-forward do pod $podName (via WSL2)..."
    $pf = Start-Process -FilePath "wsl" -ArgumentList @("-d", "Ubuntu", "--", "kubectl", "port-forward", $podName, "${serverPort}:${serverPort}", "-n", $namespace) -NoNewWindow -PassThru -RedirectStandardOutput "NUL"
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
        Write-Host ("[ERRO] Nao foi possível conectar ao servidor Go em {0}:{1} após várias tentativas. Verifique o pod e o serviço." -f $serverHost, $serverPort)
        if ($pf) { $pf.Kill() }
        exit 1
    }
    Write-Host "[INFO] Conexao com o servidor Go OK! Iniciando testes..."
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
                $cenarioId = "C$c"  # Agora passa C1, C2, ...
                for ($rep = 1; $rep -le $repeticoes; $rep++) {
                    Write-Host "[EXE] $execucaoAtual/$totalExecucoes | Servidores: $numServidores, Clientes: $numClientes, Mensagens: $numMensagens, Repeticao: $rep"
                    $logPath = Join-Path $resultsDir 'test-go-errors.log'
                    $procs = @()
                    # Divide os clientes entre os hosts
                    $clientesPorHost = [math]::Ceiling($numClientes / $numHosts)
                    for ($h = 1; $h -le $numHosts; $h++) {
                        $inicio = (($h - 1) * $clientesPorHost) + 1
                        $fim = [math]::Min($h * $clientesPorHost, $numClientes)
                        if ($inicio -gt $fim) { break }
                        $numClientesHost = $fim - $inicio + 1
                        # Define o caminho do CSV temporário para este processo
                        $csvTempName = "S${numServidores}_C${numClientes}_M${numMensagens}_R${rep}.csv"
                        $csvTempPath = Join-Path $tempGoDir $csvTempName
                        # Converte para path Linux (ex: /mnt/c/Users/Bia/Desktop/ProjetoK/src/results/reports/temp-go/S2_C10_M1_R1.csv)
                        $driveLetter = ($csvTempPath.Substring(0,1)).ToLower()
                        $csvTempPathLinux = "/mnt/$driveLetter" + ($csvTempPath.Substring(2) -replace "\\", "/")
                        $tempGoDirLinux = "/mnt/$driveLetter" + ($tempGoDir.Substring(2) -replace "\\", "/")
                        $env:GO_CSV_TEMP_DIR = $tempGoDirLinux
                        $env:GO_CSV_TEMP_FILE = $csvTempPathLinux
                        # Argumentos: host, porta, numMensagens, numClientesHost, clientIdxInicio, numServidores, numClientesTotal, cenarioId, repeticao
                        $args = @($serverHost, $serverPort, $numMensagens, $numClientesHost, $inicio, $numServidores, $numClientes, $cenarioId, $rep)
                        $clientGoLinuxWSL = "/home/$wslUser/client-go"
                        $cmdLine = "export GO_CSV_TEMP_DIR='$tempGoDirLinux'; export GO_CSV_TEMP_FILE='$csvTempPathLinux'; $clientGoLinuxWSL $($args -join ' ')"
                        $cmdLineQuoted = '"' + $cmdLine + '"'
                        try {
                            $allArgs = @("-d", "Ubuntu", "--", "sh", "-c", $cmdLineQuoted)
                            $proc = Start-Process -FilePath "wsl" -ArgumentList $allArgs -NoNewWindow -PassThru -WorkingDirectory $projectRoot -ErrorAction Stop
                            $procs += $proc
                        } catch {
                            $msg = "[ERRO] Falha ao iniciar client-go (Linux) via WSL | servidores=$numServidores | clientes=$numClientes | mensagens=$numMensagens | repeticao=$rep | host=$h | erro=$($_.Exception.Message)"
                            Write-Host $msg -ForegroundColor Red
                            Add-Content -Path $logPath -Value $msg
                        }
                    }
                    # Aguarda todos os hosts terminarem
                    $procs | ForEach-Object { $_.WaitForExit() }
                    $execucaoAtual++
                }
                $c++
            }
        }
    } finally {
        Stop-PortForward $pf
        Start-Sleep -Seconds 2 # Aguarda liberação da porta
    }
}

# 8. Instala dependências Python (requirements.txt)
if (Test-Path "requirements.txt") {
    Write-Host "[INFO] Instalando dependências Python..."
    pip install -r requirements.txt
}


# Faz merge dos resultados dos clientes Go

Write-Host "[INFO] Fazendo merge dos resultados dos clientes Go..."
$csvGo = Join-Path $resultsDir 'test-go.csv'
python src/tools/merge_csv_results.py $tempGoDir $csvGo

Write-Host "[INFO] Teste de carga finalizado! Veja os resultados em 'results/reports'."
# Só remove a pasta temp-go se o merge realmente criou o arquivo final
if (Test-Path $csvGo) {
    if (Test-Path $tempGoDir) { Remove-Item $tempGoDir -Recurse -Force }
} else {
    Write-Host "[WARN] test-go.csv não foi criado, mantendo a pasta temp-go para depuração." -ForegroundColor Yellow
}

# Salva tempo total Go ao final do teste Go
$csvGo = Join-Path $resultsDir 'test-go.csv'
$tempoFile = Join-Path $resultsDir 'tempo-total.txt'
function Get-Tempo-Total-Go {
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
$tempoGo = Get-Tempo-Total-Go $csvGo
if ($tempoGo) {
    Add-Content -Path $tempoFile -Value "Tempo Total Go:   $tempoGo"
}
