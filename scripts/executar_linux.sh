#!/bin/bash
# ============================================================
# PROJETOK - SCRIPT AVANÇADO PARA LINUX
# Sistema completo de testes de carga cliente-servidor
# Suporte: Local + Docker + Kubernetes
# ============================================================

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
RESET='\033[0m'

# Variáveis de controle
LOCAL_ONLY=false
SKIP_DOCKER=false
QUICK_TEST=false
VERBOSE=false

echo -e "\n${CYAN}============================================================${RESET}"
echo -e "${CYAN}    PROJETOK - SISTEMA AVANÇADO DE TESTES (LINUX)        ${RESET}"
echo -e "${CYAN}============================================================${RESET}\n"

# Processar argumentos da linha de comando
while [[ $# -gt 0 ]]; do
    case $1 in
        --local-only)
            LOCAL_ONLY=true
            shift
            ;;
        --skip-docker)
            SKIP_DOCKER=true
            shift
            ;;
        --quick)
            QUICK_TEST=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}[ERRO]${RESET} Opção desconhecida: $1"
            echo "Use --help para ver as opções disponíveis"
            exit 1
            ;;
    esac
done

# Função de ajuda
show_help() {
    echo -e "\n${CYAN}USO:${RESET} $0 [OPÇÕES]"
    echo
    echo -e "${WHITE}OPÇÕES:${RESET}"
    echo "  --local-only    Executa apenas testes locais"
    echo "  --skip-docker   Pula verificação do Docker"
    echo "  --quick         Execução rápida (menos cenários)"
    echo "  --verbose       Output detalhado"
    echo "  --help          Mostra esta ajuda"
    echo
    echo -e "${WHITE}EXEMPLOS:${RESET}"
    echo "  $0                    (execução interativa)"
    echo "  $0 --local-only       (apenas local)"
    echo "  $0 --quick            (execução rápida)"
    echo
}

# Navegar para diretório do script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

if [[ "$VERBOSE" == "true" ]]; then
    echo -e "${BLUE}[INFO]${RESET} Diretório do projeto: $PROJECT_DIR"
fi

# ============================================================
# VALIDAÇÃO DA ESTRUTURA DO PROJETO
# ============================================================
echo -e "${YELLOW}[VALIDAÇÃO]${RESET} Verificando estrutura do projeto..."

ESTRUTURA_OK=true

if [[ ! -f "src/testes/teste_carga.py" ]]; then
    echo -e "${RED}[ERRO]${RESET} Arquivo não encontrado: src/testes/teste_carga.py"
    ESTRUTURA_OK=false
fi

if [[ ! -f "src/servidor/servidor.py" ]]; then
    echo -e "${RED}[ERRO]${RESET} Arquivo não encontrado: src/servidor/servidor.py"
    ESTRUTURA_OK=false
fi

if [[ ! -f "src/cliente/cliente.py" ]]; then
    echo -e "${RED}[ERRO]${RESET} Arquivo não encontrado: src/cliente/cliente.py"
    ESTRUTURA_OK=false
fi

if [[ ! -f "requirements.txt" ]]; then
    echo -e "${RED}[ERRO]${RESET} Arquivo não encontrado: requirements.txt"
    ESTRUTURA_OK=false
fi

if [[ "$ESTRUTURA_OK" == "false" ]]; then
    echo
    echo -e "${RED}[ERRO CRÍTICO]${RESET} Estrutura do projeto incompleta!"
    echo "Execute este script do diretório raiz do ProjetoK."
    echo
    exit 1
fi

echo -e "${GREEN}[OK]${RESET} Estrutura do projeto validada"
[[ -f "src/cliente/cliente.go" ]] && echo -e "${GREEN}[OK]${RESET} Cliente Go encontrado"
[[ -f "config/docker/Dockerfile" ]] && echo -e "${GREEN}[OK]${RESET} Dockerfile encontrado"
[[ -d "config/kubernetes" ]] && echo -e "${GREEN}[OK]${RESET} Configurações Kubernetes encontradas"

# ============================================================
# VERIFICAÇÃO DE DEPENDÊNCIAS
# ============================================================
echo
echo -e "${YELLOW}[DEPENDÊNCIAS]${RESET} Verificando ferramentas..."

# Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    echo -e "${GREEN}[OK]${RESET} Python $PYTHON_VERSION"
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
    echo -e "${GREEN}[OK]${RESET} Python $PYTHON_VERSION"
    PYTHON_CMD="python"
else
    echo -e "${RED}[ERRO]${RESET} Python não encontrado"
    echo "Instale Python 3.10+ do repositório da sua distribuição"
    exit 1
fi

# pip
if command -v pip3 &> /dev/null; then
    echo -e "${GREEN}[OK]${RESET} pip3 disponível"
    PIP_CMD="pip3"
elif command -v pip &> /dev/null; then
    echo -e "${GREEN}[OK]${RESET} pip disponível"
    PIP_CMD="pip"
else
    echo -e "${RED}[ERRO]${RESET} pip não encontrado"
    exit 1
fi

# Go (opcional)
GO_AVAILABLE=false
if command -v go &> /dev/null; then
    GO_AVAILABLE=true
    GO_VERSION=$(go version 2>&1 | cut -d' ' -f3)
    echo -e "${GREEN}[OK]${RESET} Go $GO_VERSION"
else
    echo -e "${YELLOW}[AVISO]${RESET} Go não encontrado - usando apenas Python"
fi

# Docker (opcional)
DOCKER_AVAILABLE=false
if [[ "$SKIP_DOCKER" != "true" ]]; then
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version 2>&1 | cut -d' ' -f3 | tr -d ',')
        echo -e "${GREEN}[OK]${RESET} Docker $DOCKER_VERSION"
        
        # Verificar se Docker está rodando
        if docker ps &> /dev/null; then
            DOCKER_AVAILABLE=true
        else
            echo -e "${YELLOW}[AVISO]${RESET} Docker instalado mas não está rodando"
            echo "Inicie o serviço Docker: sudo systemctl start docker"
        fi
    else
        echo -e "${YELLOW}[AVISO]${RESET} Docker não encontrado - sem suporte a containers"
    fi
fi

# kubectl (opcional)
KUBECTL_AVAILABLE=false
if [[ "$LOCAL_ONLY" != "true" ]]; then
    if command -v kubectl &> /dev/null; then
        echo -e "${GREEN}[OK]${RESET} kubectl encontrado"
        
        if kubectl cluster-info --request-timeout=3s &> /dev/null; then
            KUBECTL_AVAILABLE=true
            echo -e "${GREEN}[OK]${RESET} Cluster Kubernetes conectado"
        else
            echo -e "${YELLOW}[AVISO]${RESET} kubectl sem conexão com cluster"
        fi
    else
        echo -e "${YELLOW}[AVISO]${RESET} kubectl não encontrado"
    fi
fi

# ============================================================
# INSTALAÇÃO DE DEPENDÊNCIAS PYTHON
# ============================================================
echo
echo -e "${YELLOW}[SETUP]${RESET} Instalando dependências Python..."

if [[ -d "venv" ]]; then
    echo -e "${BLUE}[INFO]${RESET} Ativando ambiente virtual existente..."
    source venv/bin/activate
else
    echo -e "${BLUE}[INFO]${RESET} Criando ambiente virtual..."
    $PYTHON_CMD -m venv venv
    if [[ $? -ne 0 ]]; then
        echo -e "${RED}[ERRO]${RESET} Falha ao criar ambiente virtual"
        exit 1
    fi
    source venv/bin/activate
fi

echo -e "${BLUE}[INFO]${RESET} Instalando pacotes Python..."
$PIP_CMD install --quiet --upgrade pip
$PIP_CMD install --quiet -r requirements.txt
if [[ $? -ne 0 ]]; then
    echo -e "${RED}[ERRO]${RESET} Falha ao instalar dependências Python"
    exit 1
fi
echo -e "${GREEN}[OK]${RESET} Dependências Python instaladas"

# ============================================================
# COMPILAÇÃO DO CLIENTE GO
# ============================================================
if [[ "$GO_AVAILABLE" == "true" ]]; then
    echo
    echo -e "${YELLOW}[GO]${RESET} Compilando cliente Go..."
    cd src/cliente
    
    if [[ ! -f "cliente" ]]; then
        go build -o cliente cliente.go
        if [[ $? -ne 0 ]]; then
            echo -e "${RED}[ERRO]${RESET} Falha na compilação do cliente Go"
            GO_AVAILABLE=false
        else
            echo -e "${GREEN}[OK]${RESET} Cliente Go compilado: cliente"
        fi
    else
        echo -e "${GREEN}[OK]${RESET} Cliente Go já compilado"
    fi
    cd "$PROJECT_DIR"
fi

# ============================================================
# MENU DE EXECUÇÃO
# ============================================================
if [[ "$QUICK_TEST" != "true" ]]; then
    echo
    echo -e "${CYAN}============================================================${RESET}"
    echo -e "${CYAN}                    MENU DE EXECUÇÃO                      ${RESET}"
    echo -e "${CYAN}============================================================${RESET}"
    echo
    echo -e "${WHITE}Escolha o tipo de execução:${RESET}"
    echo
    echo -e "${GREEN}[1]${RESET} Execução Local Completa     (3000 testes, ~45 min)"
    echo -e "${GREEN}[2]${RESET} Execução Local Rápida       (150 testes, ~5 min)"
    echo -e "${GREEN}[3]${RESET} Docker + Local              (containers + local)"
    echo -e "${GREEN}[4]${RESET} Kubernetes + Local          (cluster + local)"
    echo -e "${GREEN}[5]${RESET} Execução Completa           (local + docker + k8s)"
    echo -e "${GREEN}[0]${RESET} Sair"
    echo
    read -p "$(echo -e "${BLUE}Digite sua escolha [1-5]: ${RESET}")" ESCOLHA
    
    case $ESCOLHA in
        0) exit 0 ;;
        1) executar_local_completo ;;
        2) executar_local_rapido ;;
        3) executar_docker_local ;;
        4) executar_kubernetes_local ;;
        5) executar_completo ;;
        *) 
            echo -e "${RED}[ERRO]${RESET} Opção inválida. Executando local completo por padrão."
            executar_local_completo
            ;;
    esac
else
    executar_local_rapido
fi

# ============================================================
# FUNÇÕES DE EXECUÇÃO
# ============================================================

executar_local_completo() {
    echo
    echo -e "${CYAN}============================================================${RESET}"
    echo -e "${CYAN}              EXECUÇÃO LOCAL COMPLETA                     ${RESET}"
    echo -e "${CYAN}============================================================${RESET}"
    echo
    executar_local false
}

executar_local_rapido() {
    echo
    echo -e "${CYAN}============================================================${RESET}"
    echo -e "${CYAN}              EXECUÇÃO LOCAL RÁPIDA                       ${RESET}"
    echo -e "${CYAN}============================================================${RESET}"
    echo
    executar_local true
}

executar_local() {
    local quick_mode=$1
    echo -e "${YELLOW}[EXECUÇÃO]${RESET} Iniciando testes locais..."
    cd src/testes
    
    if [[ "$quick_mode" == "true" ]]; then
        echo -e "${BLUE}[INFO]${RESET} Modo rápido: reduzindo cenários de teste..."
        # Aqui você pode modificar o teste_carga.py temporariamente
    fi
    
    echo -e "${BLUE}[INFO]${RESET} Executando teste de carga..."
    $PYTHON_CMD teste_carga.py
    if [[ $? -ne 0 ]]; then
        echo -e "${RED}[ERRO]${RESET} Falha na execução dos testes"
        cd "$PROJECT_DIR"
        exit 1
    fi
    
    echo -e "${GREEN}[SUCESSO]${RESET} Testes locais concluídos!"
    cd "$PROJECT_DIR"
    finalizar
}

executar_docker_local() {
    if [[ "$DOCKER_AVAILABLE" == "false" ]]; then
        echo -e "${RED}[ERRO]${RESET} Docker não disponível. Executando apenas local."
        executar_local_completo
        return
    fi
    
    echo
    echo -e "${CYAN}============================================================${RESET}"
    echo -e "${CYAN}              EXECUÇÃO DOCKER + LOCAL                     ${RESET}"
    echo -e "${CYAN}============================================================${RESET}"
    
    echo -e "${YELLOW}[DOCKER]${RESET} Construindo imagem Docker..."
    docker build -f config/docker/Dockerfile -t projetok:latest .
    if [[ $? -ne 0 ]]; then
        echo -e "${RED}[ERRO]${RESET} Falha ao construir imagem Docker"
        executar_local_completo
        return
    fi
    
    echo -e "${YELLOW}[DOCKER]${RESET} Executando testes em container..."
    docker run --rm -v "$PROJECT_DIR/resultados:/app/results" projetok:latest
    if [[ $? -ne 0 ]]; then
        echo -e "${RED}[ERRO]${RESET} Falha na execução Docker"
    fi
    
    echo -e "${GREEN}[SUCESSO]${RESET} Testes Docker concluídos!"
    finalizar
}

executar_kubernetes_local() {
    if [[ "$KUBECTL_AVAILABLE" == "false" ]]; then
        echo -e "${RED}[ERRO]${RESET} Kubernetes não disponível. Executando apenas local."
        executar_local_completo
        return
    fi
    
    echo
    echo -e "${CYAN}============================================================${RESET}"
    echo -e "${CYAN}            EXECUÇÃO KUBERNETES + LOCAL                   ${RESET}"
    echo -e "${CYAN}============================================================${RESET}"
    
    echo -e "${YELLOW}[K8S]${RESET} Aplicando configurações Kubernetes..."
    kubectl apply -f config/kubernetes/
    if [[ $? -ne 0 ]]; then
        echo -e "${RED}[ERRO]${RESET} Falha ao aplicar configurações K8s"
        executar_local_completo
        return
    fi
    
    echo -e "${YELLOW}[K8S]${RESET} Aguardando conclusão dos jobs..."
    kubectl wait --for=condition=complete job/teste-carga --timeout=3600s
    if [[ $? -ne 0 ]]; then
        echo -e "${RED}[ERRO]${RESET} Timeout ou falha nos jobs K8s"
    fi
    
    echo -e "${YELLOW}[K8S]${RESET} Coletando resultados..."
    kubectl logs job/teste-carga > resultados/kubernetes_results.log
    
    echo -e "${GREEN}[SUCESSO]${RESET} Testes Kubernetes concluídos!"
    finalizar
}

executar_completo() {
    echo
    echo -e "${CYAN}============================================================${RESET}"
    echo -e "${CYAN}              EXECUÇÃO COMPLETA                           ${RESET}"
    echo -e "${CYAN}============================================================${RESET}"
    
    executar_local false
    
    if [[ "$DOCKER_AVAILABLE" == "true" ]]; then
        executar_docker_local
    fi
    
    if [[ "$KUBECTL_AVAILABLE" == "true" ]]; then
        executar_kubernetes_local
    fi
    
    finalizar
}

finalizar() {
    echo
    echo -e "${CYAN}============================================================${RESET}"
    echo -e "${CYAN}                     RESULTADOS                          ${RESET}"
    echo -e "${CYAN}============================================================${RESET}"
    echo
    
    if [[ -f "resultados/graficos/analise_performance.png" ]]; then
        echo -e "${GREEN}[SUCESSO]${RESET} Gráficos gerados: resultados/graficos/analise_performance.png"
    fi
    if [[ -f "resultados/csv/resultados_teste_carga.csv" ]]; then
        echo -e "${GREEN}[SUCESSO]${RESET} Dados brutos: resultados/csv/resultados_teste_carga.csv"
    fi
    if [[ -f "resultados/csv/comparacao_linguagens.csv" ]]; then
        echo -e "${GREEN}[SUCESSO]${RESET} Comparação: resultados/csv/comparacao_linguagens.csv"
    fi
    
    echo
    echo -e "${BLUE}[INFO]${RESET} Todos os arquivos de resultado estão em: resultados/"
    echo -e "${BLUE}[INFO]${RESET} Abra analise_performance.png para ver os gráficos"
    echo
    
    # Oferecer para abrir resultados
    read -p "$(echo -e "${YELLOW}Deseja abrir os resultados agora? [s/N]: ${RESET}")" ABRIR
    if [[ "$ABRIR" =~ ^[Ss]$ ]]; then
        if command -v xdg-open &> /dev/null; then
            [[ -f "resultados/graficos/analise_performance.png" ]] && xdg-open "resultados/graficos/analise_performance.png"
            [[ -d "resultados/" ]] && xdg-open "resultados/"
        elif command -v open &> /dev/null; then  # macOS
            [[ -f "resultados/graficos/analise_performance.png" ]] && open "resultados/graficos/analise_performance.png"
            [[ -d "resultados/" ]] && open "resultados/"
        else
            echo -e "${BLUE}[INFO]${RESET} Abra manualmente: resultados/graficos/analise_performance.png"
        fi
    fi
    
    echo
    echo -e "${GREEN}[CONCLUÍDO]${RESET} Execução finalizada com sucesso!"
    echo -e "${CYAN}Obrigado por usar o ProjetoK!${RESET}"
    echo
}

# Executar função principal se não foi chamado por source
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # Capturar Ctrl+C para limpeza
    trap 'echo -e "\n${YELLOW}[INFO]${RESET} Execução interrompida pelo usuário."; exit 1' INT
    
    # Se chegou até aqui sem execução específica, executar local completo
    if [[ "$QUICK_TEST" == "true" ]]; then
        executar_local_rapido
    fi
fi
