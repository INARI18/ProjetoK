# Configurações - ProjetoK

Esta pasta contém todas as configurações para execução em diferentes ambientes.

## Subpastas

- **`docker/`** - Dockerfile para containerização
- **`kubernetes/`** - Manifests para deploy no K8s

## Docker

O Dockerfile usa multi-stage build:
1. **Stage 1**: Compila cliente Go
2. **Stage 2**: Configura ambiente Python e copia executáveis

### Build
```bash
docker build -f config/docker/Dockerfile -t projetok:latest .
```

## Kubernetes

Três recursos principais:
- **`deployment-servidor.yaml`** - Deploy dos servidores
- **`service-servidor.yaml`** - Serviço para load balancing
- **`job-teste-carga.yaml`** - Job para execução dos testes

### Deploy
```bash
kubectl apply -f config/kubernetes/
```

## Configurações

- **Servidores**: 2-10 instâncias configuráveis
- **Recursos**: CPU e memória limitados
- **Rede**: LoadBalancer interno para distribuição
