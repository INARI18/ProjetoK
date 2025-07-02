@echo off
chcp 65001 >nul
REM Script para gerar graficos dos resultados
REM ProjetoK - Analise de performance

echo =========================================
echo GERAR GRAFICOS - PROJETO K
echo =========================================
echo.

REM Verificar se Python esta disponivel
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado. Instale Python 3.8+ primeiro.
    pause
    exit /b 1
)

REM Verificar se matplotlib esta instalado
python -c "import matplotlib" >nul 2>&1
if %errorlevel% neq 0 (
    echo [AVISO] Matplotlib nao encontrado. Instalando...
    pip install matplotlib pandas seaborn
    if %errorlevel% neq 0 (
        echo [ERRO] Erro ao instalar dependencias
        pause
        exit /b 1
    )
)

echo [OK] Dependencias verificadas
echo.

REM Navegar para a pasta do projeto
cd /d "%~dp0.."

echo [GRAFICOS] Gerando graficos dos resultados...
echo [INFO] Diretorio de trabalho: %CD%
echo.

REM Executar o script Python de geracao de graficos
python src\testes\graficos.py

echo.
echo [OK] Geracao concluida!
echo [INFO] Verifique os graficos na pasta 'resultados\graficos'
echo.
pause
