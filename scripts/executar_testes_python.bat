@echo off
chcp 65001 >nul
REM Script para executar testes Python usando Kubernetes
REM ProjetoK - Configuracao automatica e execucao de testes

echo =========================================
echo EXECUTAR TESTES PYTHON - KUBERNETES
echo =========================================
echo.

REM Verificar se Python esta disponivel
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

echo [OK] Pre-requisitos verificados
echo.

REM Verificar bibliotecas Python necessarias
python -c "import matplotlib, pandas, seaborn" 2>nul
if %errorlevel% neq 0 (
    echo [ERRO] Bibliotecas Python necessarias nao encontradas!
    echo Execute: pip install matplotlib pandas seaborn
    pause
    exit /b 1
)

REM Navegar para a pasta do projeto
cd /d "%~dp0.."

echo [INICIO] Configurando ambiente Kubernetes e executando testes Python...
echo [INFO] Diretorio de trabalho: %CD%
echo.

REM Verificar se kind esta disponivel
kind --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] kind nao encontrado. Baixando kind...
    curl -Lo kind.exe https://github.com/kubernetes-sigs/kind/releases/latest/download/kind-windows-amd64
    if %errorlevel% neq 0 (
        echo [ERRO] Erro ao baixar kind!
        pause
        exit /b 1
    )
    echo [OK] kind baixado com sucesso
)

echo [INFO] Configurando cluster Kubernetes...
REM Verificar se cluster ja existe
kind get clusters | findstr "projetok" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Criando cluster Kubernetes com NodePort...
    kind create cluster --config config\kind-config.yaml
    if %errorlevel% neq 0 (
        echo [ERRO] Erro ao criar cluster!
        pause
        exit /b 1
    )
    echo [OK] Cluster criado com sucesso
) else (
    echo [INFO] Usando cluster existente 'projetok'
    kubectl config use-context kind-projetok
)

echo.
echo [DEPLOY] Aplicando manifests Kubernetes...
kubectl apply -f config\kubernetes\deployment-servidor-python.yaml
kubectl apply -f config\kubernetes\service-servidor.yaml
kubectl apply -f config\kubernetes\deployment-servidor-go.yaml
kubectl apply -f config\kubernetes\deployment-servidor-python.yaml
kubectl apply -f config\kubernetes\service-servidor.yaml
if %errorlevel% neq 0 (
    echo [ERRO] Erro ao aplicar manifests Kubernetes!
    pause
    exit /b 1
)

echo.
echo [AVISO] ATENCAO: Este processo pode levar VARIAS HORAS!
echo Estimativa: 2-4 horas dependendo do hardware
echo.
set /p continuar="Deseja continuar? (S/N): "
if /i not "%continuar%"=="S" (
    echo Operacao cancelada.
    pause
    exit /b 0
)

echo.
echo [TESTE] Iniciando testes...
echo [INFO] Data/Hora inicio: %date% %time%
echo.

REM Executar o script Python de testes Python
python src\testes\executar_testes_python.py

REM Verificar se o teste foi bem-sucedido
if %errorlevel% neq 0 (
    echo.
    echo [ERRO] Os testes falharam!
    echo Verifique os logs acima para mais detalhes.
    pause
    exit /b 1
)

echo.
echo ========================================
echo TESTES PYTHON CONCLUIDOS COM SUCESSO!
echo ========================================
echo.
echo [INFO] Data/Hora fim: %date% %time%
echo.

REM Verificar se os resultados foram gerados
if exist "resultados\resultados_python_*.json" (
    echo [OK] Arquivo de resultados gerado na pasta resultados/
    echo.
    echo [PROXIMOS PASSOS]
    echo 1. Para gerar graficos: scripts\gerar_graficos.bat
    echo 2. Para comparar com Go: scripts\executar_testes_go.bat
) else (
    echo [AVISO] Arquivo de resultados nao encontrado!
)

echo.
echo [CONCLUIDO] Execucao concluida!
echo Verifique os resultados na pasta 'resultados'
echo.
pause
