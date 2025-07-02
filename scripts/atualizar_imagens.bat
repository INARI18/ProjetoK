@echo off
chcp 65001 >nul
REM Script para buildar e fazer push das imagens Docker para o Docker Hub
REM ProjetoK - Build e Push para Docker Hub (bia18)

echo =========================================
echo BUILD E PUSH PARA DOCKER HUB - PROJETOK
echo =========================================
echo.

REM Verificar se Docker esta disponivel
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Docker nao encontrado. Instale Docker Desktop primeiro.
    pause
    exit /b 1
)

echo [OK] Docker encontrado
echo.

REM Verificar se esta logado no Docker Hub
echo [INFO] Verificando login no Docker Hub...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Docker nao esta funcionando!
    pause
    exit /b 1
)

REM Tentar fazer um comando que requer autenticacao
docker system df >nul 2>&1
if %errorlevel% neq 0 (
    echo [AVISO] Problemas com Docker. Tentando login...
    docker login
    if %errorlevel% neq 0 (
        echo [ERRO] Erro no login!
        pause
        exit /b 1
    )
) else (
    echo [OK] Docker funcionando, assumindo que esta logado
)

echo [OK] Login verificado
echo.

REM Navegar para a raiz do projeto
cd /d "%~dp0.."
echo [INFO] Diretorio de trabalho: %CD%
echo.

REM Definir variaveis
set DOCKER_USERNAME=bia18
set GO_IMAGE_NAME=%DOCKER_USERNAME%/projetok-servidor-go
set PYTHON_IMAGE_NAME=%DOCKER_USERNAME%/projetok-servidor-python
set TAG=latest

echo [BUILD] Buildando imagem do servidor Go...
docker build -f config\docker\Dockerfile.servidor-go -t %GO_IMAGE_NAME%:%TAG% .
if %errorlevel% neq 0 (
    echo [ERRO] Erro ao buildar imagem Go!
    pause
    exit /b 1
)

echo [OK] Imagem Go criada: %GO_IMAGE_NAME%:%TAG%
echo.

echo [BUILD] Buildando imagem do servidor Python...
docker build -f config\docker\Dockerfile.servidor-python -t %PYTHON_IMAGE_NAME%:%TAG% .
if %errorlevel% neq 0 (
    echo [ERRO] Erro ao buildar imagem Python!
    pause
    exit /b 1
)

echo [OK] Imagem Python criada: %PYTHON_IMAGE_NAME%:%TAG%
echo.

echo [PUSH] Fazendo push da imagem Go para Docker Hub...
docker push %GO_IMAGE_NAME%:%TAG%
if %errorlevel% neq 0 (
    echo [ERRO] Erro ao fazer push da imagem Go!
    pause
    exit /b 1
)

echo [OK] Push da imagem Go concluido!
echo.

echo [PUSH] Fazendo push da imagem Python para Docker Hub...
docker push %PYTHON_IMAGE_NAME%:%TAG%
if %errorlevel% neq 0 (
    echo [ERRO] Erro ao fazer push da imagem Python!
    pause
    exit /b 1
)

echo [OK] Push da imagem Python concluido!
echo.

echo [INFO] Imagens disponiveis no Docker Hub:
echo    - %GO_IMAGE_NAME%:%TAG%
echo    - %PYTHON_IMAGE_NAME%:%TAG%
echo.

echo [SUCESSO] IMAGENS ENVIADAS PARA DOCKER HUB COM SUCESSO!
echo.
echo [PROXIMOS PASSOS]
echo    1. As imagens agora estao disponiveis publicamente no Docker Hub
echo    2. Execute os testes com: scripts\executar_testes_go.bat ou scripts\executar_testes_python.bat
echo    3. Os deployments do Kubernetes ja estao configurados para usar as imagens do Docker Hub
echo.

pause
