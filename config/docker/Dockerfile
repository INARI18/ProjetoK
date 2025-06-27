# Multi-stage build para incluir Go e Python
FROM golang:1.21-alpine AS go-builder

WORKDIR /app
COPY src/cliente/cliente.go .
COPY src/cliente/go.mod .
RUN go mod tidy && go build -o cliente cliente.go

FROM python:3.11-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar requirements.txt
COPY requirements.txt /app/

# Copiar código fonte
COPY src/ /app/src/

# Copiar cliente Go compilado
COPY --from=go-builder /app/cliente /app/src/cliente/

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Criar estrutura de diretórios para resultados
RUN mkdir -p /app/resultados/csv /app/resultados/graficos /app/resultados/relatorios

# Comando padrão (pode ser sobrescrito)
CMD ["python", "src/servidor/servidor.py", "--porta", "8000"]
