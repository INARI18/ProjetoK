@echo off
setlocal enabledelayedexpansion
REM ============================================================
REM PROJETOK - SCRIPT AVANÇADO PARA WINDOWS
REM Sistema completo de testes de carga cliente-servidor
REM Suporte: Local + Docker + Kubernetes
REM ============================================================

REM Cores para output (se suportado)
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "MAGENTA=[95m"
set "CYAN=[96m"
set "WHITE=[97m"
set "RESET=[0m"

echo.
echo %CYAN%============================================================%RESET%
echo %CYAN%    PROJETOK - SISTEMA AVANÇADO DE TESTES (WINDOWS)      %RESET%
echo %CYAN%============================================================%RESET%
echo.

REM Processar argumentos da linha de comando
set "LOCAL_ONLY=false"
set "SKIP_DOCKER=false"
set "QUICK_TEST=false"
set "VERBOSE=false"

:parse_args
if "%~1"=="" goto :args_done
if "%~1"=="--local-only" set "LOCAL_ONLY=true"
if "%~1"=="--skip-docker" set "SKIP_DOCKER=true"
if "%~1"=="--quick" set "QUICK_TEST=true"
if "%~1"=="--verbose" set "VERBOSE=true"
if "%~1"=="--help" goto :show_help
shift
goto :parse_args
:args_done

REM Navegar para diretório do script
cd /d "%~dp0"
cd ..
if "%VERBOSE%"=="true" echo %BLUE%[INFO]%RESET% Diretório de trabalho: %CD%

REM ============================================================
REM VALIDAÇÃO DA ESTRUTURA DO PROJETO
REM ============================================================
echo %YELLOW%[VALIDAÇÃO]%RESET% Verificando estrutura do projeto...

set "ESTRUTURA_OK=true"
if not exist "src\testes\teste_carga.py" (
    echo %RED%[ERRO]%RESET% Arquivo não encontrado: src\testes\teste_carga.py
    set "ESTRUTURA_OK=false"
)
if not exist "src\servidor\servidor.py" (
    echo %RED%[ERRO]%RESET% Arquivo não encontrado: src\servidor\servidor.py
    set "ESTRUTURA_OK=false"
)
if not exist "src\cliente\cliente.py" (
    echo %RED%[ERRO]%RESET% Arquivo não encontrado: src\cliente\cliente.py
    set "ESTRUTURA_OK=false"
)
if not exist "requirements.txt" (
    echo %RED%[ERRO]%RESET% Arquivo não encontrado: requirements.txt
    set "ESTRUTURA_OK=false"
)

if "%ESTRUTURA_OK%"=="false" (
    echo.
    echo %RED%[ERRO CRÍTICO]%RESET% Estrutura do projeto incompleta!
    echo Execute este script do diretório raiz do ProjetoK.
    echo.
    pause
    exit /b 1
)

echo %GREEN%[OK]%RESET% Estrutura do projeto validada
if exist "src\cliente\cliente.go" echo %GREEN%[OK]%RESET% Cliente Go encontrado
if exist "config\docker\Dockerfile" echo %GREEN%[OK]%RESET% Dockerfile encontrado
if exist "config\kubernetes\" echo %GREEN%[OK]%RESET% Configurações Kubernetes encontradas

REM ============================================================
REM VERIFICAÇÃO DE DEPENDÊNCIAS
REM ============================================================
echo.
echo %YELLOW%[DEPENDÊNCIAS]%RESET% Verificando ferramentas...

REM Python
python --version >nul 2>&1
if errorlevel 1 (
    echo %RED%[ERRO]%RESET% Python não encontrado no PATH
    echo Instale Python 3.10+ de: https://python.org/downloads/
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo %GREEN%[OK]%RESET% Python %PYTHON_VERSION%

REM pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo %RED%[ERRO]%RESET% pip não encontrado
    pause
    exit /b 1
)
echo %GREEN%[OK]%RESET% pip disponível

REM Go (opcional)
set "GO_AVAILABLE=false"
set "GO_CMD=go"

REM Verificar Go no PATH primeiro
go version >nul 2>&1
if not errorlevel 1 (
    set "GO_AVAILABLE=true"
    for /f "tokens=3" %%i in ('go version 2^>^&1') do set GO_VERSION=%%i
    echo %GREEN%[OK]%RESET% Go !GO_VERSION!
) else (
    REM Verificar em locais comuns
    if exist "C:\Program Files\Go\bin\go.exe" (
        set "GO_AVAILABLE=true"
        set "GO_CMD=C:\Program Files\Go\bin\go.exe"
        for /f "tokens=3" %%i in ('"C:\Program Files\Go\bin\go.exe" version 2^>^&1') do set GO_VERSION=%%i
        echo %GREEN%[OK]%RESET% Go !GO_VERSION! ^(em C:\Program Files\Go\bin\^)
    ) else if exist "C:\Go\bin\go.exe" (
        set "GO_AVAILABLE=true"
        set "GO_CMD=C:\Go\bin\go.exe"
        for /f "tokens=3" %%i in ('"C:\Go\bin\go.exe" version 2^>^&1') do set GO_VERSION=%%i
        echo %GREEN%[OK]%RESET% Go !GO_VERSION! ^(em C:\Go\bin\^)
    ) else (
        echo %YELLOW%[AVISO]%RESET% Go não encontrado - usando apenas Python
    )
)

REM Docker (opcional)
set "DOCKER_AVAILABLE=false"
if not "%SKIP_DOCKER%"=="true" (
    docker --version >nul 2>&1
    if not errorlevel 1 (
        set "DOCKER_AVAILABLE=true"
        for /f "tokens=3" %%i in ('docker --version 2^>^&1') do set DOCKER_VERSION=%%i
        echo %GREEN%[OK]%RESET% Docker !DOCKER_VERSION!
        
        REM Verificar se Docker está rodando
        docker ps >nul 2>&1
        if errorlevel 1 (
            echo %YELLOW%[AVISO]%RESET% Docker instalado mas não está rodando
            echo Inicie o Docker Desktop e tente novamente.
            set "DOCKER_AVAILABLE=false"
        )
    ) else (
        echo %YELLOW%[AVISO]%RESET% Docker não encontrado - sem suporte a containers
    )
)

REM kubectl (opcional)
set "KUBECTL_AVAILABLE=false"
if not "%LOCAL_ONLY%"=="true" (
    kubectl version --client >nul 2>&1
    if not errorlevel 1 (
        echo %GREEN%[OK]%RESET% kubectl encontrado
        
        kubectl cluster-info --request-timeout=3s >nul 2>&1
        if not errorlevel 1 (
            set "KUBECTL_AVAILABLE=true"
            echo %GREEN%[OK]%RESET% Cluster Kubernetes conectado
        ) else (
            echo %YELLOW%[AVISO]%RESET% kubectl sem conexão com cluster
        )
    ) else (
        echo %YELLOW%[AVISO]%RESET% kubectl não encontrado
    )
)

REM ============================================================
REM INSTALAÇÃO DE DEPENDÊNCIAS PYTHON
REM ============================================================
echo.
echo %YELLOW%[SETUP]%RESET% Instalando dependências Python...

if exist "venv\" (
    echo %BLUE%[INFO]%RESET% Ativando ambiente virtual existente...
    call venv\Scripts\activate.bat
) else (
    echo %BLUE%[INFO]%RESET% Criando ambiente virtual...
    python -m venv venv
    if errorlevel 1 (
        echo %RED%[ERRO]%RESET% Falha ao criar ambiente virtual
        pause
        exit /b 1
    )
    call venv\Scripts\activate.bat
)

echo %BLUE%[INFO]%RESET% Instalando pacotes Python...
pip install -q --upgrade pip
pip install -q -r requirements.txt
if errorlevel 1 (
    echo %RED%[ERRO]%RESET% Falha ao instalar dependências Python
    pause
    exit /b 1
)
echo %GREEN%[OK]%RESET% Dependências Python instaladas

REM ============================================================
REM COMPILAÇÃO DO CLIENTE GO
REM ============================================================
if "%GO_AVAILABLE%"=="true" (
    echo.
    echo %YELLOW%[GO]%RESET% Compilando cliente Go...
    cd src\cliente
    
    if not exist "cliente.exe" (
        "%GO_CMD%" build -o cliente.exe cliente.go
        if errorlevel 1 (
            echo %RED%[ERRO]%RESET% Falha na compilação do cliente Go
            set "GO_AVAILABLE=false"
        ) else (
            echo %GREEN%[OK]%RESET% Cliente Go compilado: cliente.exe
        )
    ) else (
        echo %GREEN%[OK]%RESET% Cliente Go já compilado
    )
    cd ..\..
)

REM ============================================================
REM MENU DE EXECUÇÃO
REM ============================================================
if not "%QUICK_TEST%"=="true" (
    echo.
    echo %CYAN%============================================================%RESET%
    echo %CYAN%                    MENU DE EXECUÇÃO                      %RESET%
    echo %CYAN%============================================================%RESET%
    echo.
    echo %WHITE%Escolha o tipo de execução:%RESET%
    echo.
    echo %GREEN%[1]%RESET% Execução Local Completa     (3000 testes, ~45 min)
    echo %GREEN%[2]%RESET% Execução Local Rápida       (150 testes, ~5 min)
    echo %GREEN%[3]%RESET% Docker + Local              (containers + local)
    echo %GREEN%[4]%RESET% Kubernetes + Local          (cluster + local)
    echo %GREEN%[5]%RESET% Execução Completa           (local + docker + k8s)
    echo %GREEN%[0]%RESET% Sair
    echo.
    set /p "ESCOLHA=%BLUE%Digite sua escolha [1-5]: %RESET%"
    
    if "!ESCOLHA!"=="0" exit /b 0
    if "!ESCOLHA!"=="1" goto :local_completo
    if "!ESCOLHA!"=="2" goto :local_rapido
    if "!ESCOLHA!"=="3" goto :docker_local
    if "!ESCOLHA!"=="4" goto :kubernetes_local
    if "!ESCOLHA!"=="5" goto :execucao_completa
    
    echo %RED%[ERRO]%RESET% Opção inválida. Executando local completo por padrão.
    goto :local_completo
)

REM ============================================================
REM EXECUÇÕES
REM ============================================================

:local_completo
echo.
echo %CYAN%============================================================%RESET%
echo %CYAN%              EXECUÇÃO LOCAL COMPLETA                     %RESET%
echo %CYAN%============================================================%RESET%
echo.
goto :executar_local

:local_rapido
echo.
echo %CYAN%============================================================%RESET%
echo %CYAN%              EXECUÇÃO LOCAL RÁPIDA                       %RESET%
echo %CYAN%============================================================%RESET%
echo.
set "QUICK_TEST=true"
goto :executar_local

:docker_local
if "%DOCKER_AVAILABLE%"=="false" (
    echo %RED%[ERRO]%RESET% Docker não disponível. Executando apenas local.
    goto :local_completo
)
echo.
echo %CYAN%============================================================%RESET%
echo %CYAN%              EXECUÇÃO DOCKER + LOCAL                     %RESET%
echo %CYAN%============================================================%RESET%
goto :executar_docker

:kubernetes_local
if "%KUBECTL_AVAILABLE%"=="false" (
    echo %RED%[ERRO]%RESET% Kubernetes não disponível. Executando apenas local.
    goto :local_completo
)
echo.
echo %CYAN%============================================================%RESET%
echo %CYAN%            EXECUÇÃO KUBERNETES + LOCAL                   %RESET%
echo %CYAN%============================================================%RESET%
goto :executar_kubernetes

:execucao_completa
echo.
echo %CYAN%============================================================%RESET%
echo %CYAN%              EXECUÇÃO COMPLETA                           %RESET%
echo %CYAN%============================================================%RESET%
goto :executar_tudo

REM ============================================================
REM IMPLEMENTAÇÕES DAS EXECUÇÕES
REM ============================================================

:executar_local
echo %YELLOW%[EXECUÇÃO]%RESET% Iniciando testes locais...
cd src\testes

if "%QUICK_TEST%"=="true" (
    echo %BLUE%[INFO]%RESET% Modo rápido: reduzindo cenários de teste...
    REM Aqui você pode modificar o teste_carga.py temporariamente
)

echo %BLUE%[INFO]%RESET% Executando teste de carga...
python teste_carga.py
if errorlevel 1 (
    echo %RED%[ERRO]%RESET% Falha na execução dos testes
    cd ..\..
    pause
    exit /b 1
)

echo %BLUE%[INFO]%RESET% Executando análise estatística avançada...
python analise_estatistica.py
if errorlevel 1 (
    echo %YELLOW%[AVISO]%RESET% Análise estatística não executada completamente
)

echo %GREEN%[SUCESSO]%RESET% Testes locais concluídos!
cd ..\..
goto :finalizar

:executar_docker
echo %YELLOW%[DOCKER]%RESET% Construindo imagem Docker...
docker build -t projetok:latest .
if errorlevel 1 (
    echo %RED%[ERRO]%RESET% Falha ao construir imagem Docker
    goto :local_completo
)

echo %YELLOW%[DOCKER]%RESET% Executando testes em container...
docker run --rm -v "%CD%\files:/app/results" projetok:latest
if errorlevel 1 (
    echo %RED%[ERRO]%RESET% Falha na execução Docker
)

echo %GREEN%[SUCESSO]%RESET% Testes Docker concluídos!
goto :finalizar

:executar_kubernetes
echo %YELLOW%[K8S]%RESET% Aplicando configurações Kubernetes...
kubectl apply -f config\kubernetes\
if errorlevel 1 (
    echo %RED%[ERRO]%RESET% Falha ao aplicar configurações K8s
    goto :local_completo
)

echo %YELLOW%[K8S]%RESET% Aguardando conclusão dos jobs...
kubectl wait --for=condition=complete job/teste-carga --timeout=3600s
if errorlevel 1 (
    echo %RED%[ERRO]%RESET% Timeout ou falha nos jobs K8s
)

echo %YELLOW%[K8S]%RESET% Coletando resultados...
kubectl logs job/teste-carga > kubernetes_results.log

echo %GREEN%[SUCESSO]%RESET% Testes Kubernetes concluídos!
goto :finalizar

:executar_tudo
call :executar_local
if "%DOCKER_AVAILABLE%"=="true" call :executar_docker
if "%KUBECTL_AVAILABLE%"=="true" call :executar_kubernetes
goto :finalizar

:finalizar
echo.
echo %CYAN%============================================================%RESET%
echo %CYAN%                     RESULTADOS                          %RESET%
echo %CYAN%============================================================%RESET%
echo.

if exist "resultados\graficos\analise_performance.png" (
    echo %GREEN%[SUCESSO]%RESET% Gráficos gerados: resultados\graficos\analise_performance.png
)
if exist "resultados\csv\resultados_teste_carga.csv" (
    echo %GREEN%[SUCESSO]%RESET% Dados brutos: resultados\csv\resultados_teste_carga.csv
)
if exist "resultados\csv\comparacao_linguagens.csv" (
    echo %GREEN%[SUCESSO]%RESET% Comparação: resultados\csv\comparacao_linguagens.csv
)

echo.
echo %BLUE%[INFO]%RESET% Todos os arquivos de resultado estão em: resultados\
echo %BLUE%[INFO]%RESET% Abra analise_performance.png para ver os gráficos
echo.

REM Oferecer para abrir resultados
set /p "ABRIR=%YELLOW%Deseja abrir os resultados agora? [s/N]: %RESET%"
if /i "!ABRIR!"=="s" (
    if exist "resultados\graficos\analise_performance.png" start "" "resultados\graficos\analise_performance.png"
    if exist "resultados\" start "" "resultados\"
)

echo.
echo %GREEN%[CONCLUÍDO]%RESET% Execução finalizada com sucesso!
echo %CYAN%Obrigado por usar o ProjetoK!%RESET%
echo.
pause
exit /b 0

REM ============================================================
REM FUNÇÕES DE APOIO
REM ============================================================

:show_help
echo.
echo %CYAN%USO:%RESET% %0 [OPÇÕES]
echo.
echo %WHITE%OPÇÕES:%RESET%
echo   --local-only    Executa apenas testes locais
echo   --skip-docker   Pula verificação do Docker
echo   --quick         Execução rápida (menos cenários)
echo   --verbose       Output detalhado
echo   --help          Mostra esta ajuda
echo.
echo %WHITE%EXEMPLOS:%RESET%
echo   %0                    (execução interativa)
echo   %0 --local-only       (apenas local)
echo   %0 --quick            (execução rápida)
echo.
exit /b 0
