@echo off
chcp 65001 >nul
REM script com o teste completo, contendo todos os passos necessários para configurar o ambiente, 
REM executar os testes e limpar o ambiente.
REM ProjetoK - Execucao completa de testes e analise de resultados

echo =========================================
echo TESTE COMPLETO - GO vs PYTHON
echo =========================================
echo.
echo Este script executara:
echo 1. Testes de performance em Go (3.000 testes)
echo 2. Testes de performance em Python (3.000 testes)
echo 3. Geracao de graficos comparativos
echo.
echo [AVISO] O processo executa Kubernetes e Docker em background.
echo         Caso o computador entre em modo de suspensao, os conteineres 
echo         e o cluster Kubernetes serao interrompidos, causando falha nos testes.
echo         Desative o modo de suspensao nas configuracoes de energia.
echo.
echo Pressione CTRL+C para cancelar ou
pause

REM Registrar horário de início
set START_TIME=%TIME%
echo [INFO] Iniciando teste completo em: %DATE% %TIME%

REM Verificar se Python esta disponivel
echo [CHECK] Verificando pre-requisitos...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado. Instale Python 3.8+ primeiro.
    pause
    exit /b 1
)

REM Verificar se Docker esta disponivel
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Docker nao encontrado. Instale Docker Desktop primeiro.
    pause
    exit /b 1
)

REM Verificar bibliotecas Python necessarias
python -c "import matplotlib, pandas, seaborn" 2>nul
if %errorlevel% neq 0 (
    echo [AVISO] Bibliotecas Python necessarias nao encontradas. Instalando...
    pip install matplotlib pandas seaborn
    if %errorlevel% neq 0 (
        echo [ERRO] Erro ao instalar dependencias
        pause
        exit /b 1
    )
)

echo [OK] Pre-requisitos verificados
echo.

REM Navegar para a pasta do projeto
cd /d "%~dp0"

echo [INFO] Diretorio de trabalho: %CD%
echo.

REM ==================================================
REM PARTE 1: EXECUTAR TESTES GO
REM ==================================================
echo =========================================
echo PARTE 1/3: EXECUTAR TESTES GO
echo =========================================
echo.

REM Verificar se kind esta disponivel
kind --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] kind nao encontrado. Baixando kind...
    curl -Lo kind.exe https://github.com/kubernetes-sigs/kind/releases/latest/download/kind-windows-amd64
    if %errorlevel% neq 0 (
        echo [ERRO] Falha ao baixar kind
        pause
        exit /b 1
    )
    move kind.exe %SYSTEMROOT%\system32\
    if %errorlevel% neq 0 (
        echo [AVISO] Nao foi possivel mover kind.exe para %SYSTEMROOT%\system32\
        echo [AVISO] kind.exe esta disponivel no diretorio atual
    )
)

REM Verificar se kubectl esta disponivel
kubectl version --client >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] kubectl nao encontrado. Baixando kubectl...
    curl -Lo kubectl.exe https://dl.k8s.io/release/v1.29.0/bin/windows/amd64/kubectl.exe
    if %errorlevel% neq 0 (
        echo [ERRO] Falha ao baixar kubectl
        pause
        exit /b 1
    )
    move kubectl.exe %SYSTEMROOT%\system32\
    if %errorlevel% neq 0 (
        echo [AVISO] Nao foi possivel mover kubectl.exe para %SYSTEMROOT%\system32\
        echo [AVISO] kubectl.exe esta disponivel no diretorio atual
    )
)

echo [AMBIENTE] Verificando e preparando cluster Kubernetes...
kind get clusters | findstr projeto-k >nul
if %errorlevel% equ 0 (
    echo [INFO] Removendo cluster existente para garantir ambiente limpo...
    kind delete cluster --name projeto-k
    echo [INFO] Criando novo cluster Kubernetes...
    kind create cluster --name projeto-k --wait 30s
    if %errorlevel% neq 0 (
        echo [ERRO] Falha ao criar cluster Kubernetes
        pause
        exit /b 1
    )
) else (
    echo [INFO] Criando novo cluster Kubernetes com kind...
    kind create cluster --name projeto-k --wait 30s
    if %errorlevel% neq 0 (
        echo [ERRO] Falha ao criar cluster Kubernetes
        pause
        exit /b 1
    )
)

echo [COMPILANDO] Construindo imagens Docker para os testes Go...
cd "src\servidor (local)"
docker build -t servidor-go:latest -f "..\..\config\docker\Dockerfile" .
cd ..\..

echo [KUBERNETES] Aplicando configuracoes ao cluster...
kubectl apply -f "config/kubernetes/deployment-servidor-go.yaml"
kubectl apply -f "config/kubernetes/service-servidor.yaml"

echo [KUBERNETES] Aguardando pods ficarem prontos...
kubectl wait --for=condition=Ready pods --all --timeout=60s
if %errorlevel% neq 0 (
    echo [AVISO] Timeout ao aguardar pods. Continuando mesmo assim...
)

REM Calcular número total de execuções
set total_execucoes=3000
echo [INFO] Total de execucoes por linguagem: %total_execucoes%
echo [AVISO] Lembre-se de desativar o modo de suspensao do Windows manualmente
echo         para evitar que o computador entre em suspensao durante os testes.

echo.

echo [TESTE] Executando testes de performance para Go (%total_execucoes% testes)...
python "src\testes\executor_unificado.py" --linguagem go
if %errorlevel% neq 0 (
    echo [ERRO] Falha na execucao dos testes Go
    echo [AMBIENTE] Removendo cluster Kubernetes...
    kind delete cluster --name projeto-k
    pause
    exit /b 1
)

echo [OK] Testes Go concluidos com sucesso!
echo.

echo [PROGRESSO] Aproximadamente 33%% concluido.
echo.

REM ==================================================
REM PARTE 2: EXECUTAR TESTES PYTHON
REM ==================================================
echo =========================================
echo PARTE 2/3: EXECUTAR TESTES PYTHON
echo =========================================
echo.

echo [KUBERNETES] Removendo deployments Go anteriores...
kubectl delete deployment servidor-go-deployment --ignore-not-found

echo [COMPILANDO] Construindo imagens Docker para os testes Python...
cd "src\servidor (local)"
docker build -t servidor-python:latest -f "..\..\config\docker\Dockerfile.python" .
cd ..\..

echo [KUBERNETES] Aplicando configuracoes ao cluster...
kubectl apply -f "config/kubernetes/deployment-servidor-python.yaml"
kubectl apply -f "config/kubernetes/service-servidor.yaml"

echo [KUBERNETES] Aguardando pods ficarem prontos...
kubectl wait --for=condition=Ready pods --all --timeout=60s
if %errorlevel% neq 0 (
    echo [AVISO] Timeout ao aguardar pods. Continuando mesmo assim...
)

set total_execucoes=3000
echo [TESTE] Executando testes de performance para Python (%total_execucoes% testes)...
python "src\testes\executor_unificado.py" --linguagem python
if %errorlevel% neq 0 (
    echo [ERRO] Falha na execucao dos testes Python
    echo [AMBIENTE] Removendo cluster Kubernetes...
    kind delete cluster --name projeto-k
    pause
    exit /b 1
)

echo [OK] Testes Python concluidos com sucesso!
echo.

echo [PROGRESSO] Aproximadamente 66%% concluido.
echo.

REM ==================================================
REM PARTE 3: GERAR GRAFICOS
REM ==================================================
echo =========================================
echo PARTE 3/3: GERANDO GRAFICOS COMPARATIVOS
echo =========================================
echo.

echo [AMBIENTE] Limpando cluster Kubernetes...
kind delete cluster --name projeto-k

echo [GRAFICOS] Gerando graficos comparativos...
python "src\testes\graficos.py"
if %errorlevel% neq 0 (
    echo [ERRO] Falha ao gerar graficos
    pause
    exit /b 1
)

REM Calcular o tempo total de execução
echo.
echo [INFO] Horario de inicio: %START_TIME%
echo [INFO] Horario de termino: %TIME%

REM Calcular tempo aproximado (simplificado)
for /F "tokens=1-4 delims=:.," %%a in ("%START_TIME%") do (
   set /A start_total_mins="(1%%a-100)*60+(1%%b-100)"
)
for /F "tokens=1-4 delims=:.," %%a in ("%TIME%") do (
   set /A end_total_mins="(1%%a-100)*60+(1%%b-100)"
)
set /A elapsed_mins=end_total_mins-start_total_mins
if %elapsed_mins% LSS 0 set /A elapsed_mins+=24*60

set /A elapsed_hours=%elapsed_mins% / 60
set /A elapsed_mins_remainder=%elapsed_mins% %% 60

if %elapsed_hours% GTR 0 (
    echo [INFO] Tempo total de execucao: %elapsed_hours% hora(s) e %elapsed_mins_remainder% minuto(s)
) else (
    echo [INFO] Tempo total de execucao: %elapsed_mins% minuto(s)
)

echo.
echo =========================================
echo PROCESSO COMPLETO FINALIZADO COM SUCESSO!
echo =========================================
echo.
echo [RESUMO] Todos os testes foram executados e os graficos foram gerados.
echo [INFO] Verifique os resultados na pasta 'resultados\graficos'
echo [INFO] O arquivo principal e: relatorio_final_completo.png

echo.
echo Pressione qualquer tecla para abrir a pasta de resultados...
pause >nul

start explorer "%CD%\resultados\graficos"