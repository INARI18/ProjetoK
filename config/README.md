# Configurações - ProjetoK

Esta pasta contém todas as configurações para execução em diferentes ambientes.

## Subpastas

- **`docker/`** - Dockerfiles para imagens customizadas dos servidores
- **`kubernetes/`** - Manifests para deploy no K8s

## 🐳 Docker Hub

As imagens estão hospedadas publicamente no Docker Hub:
- **bia18/projetok-servidor-go:latest** - Servidor Go
- **bia18/projetok-servidor-python:latest** - Servidor Python

### Scripts disponíveis
```bash
# Baixar imagens do Docker Hub (recomendado)
scripts\pull-imagens-dockerhub.bat

# Construir e enviar para Docker Hub (para desenvolvimento)
scripts\build-push-dockerhub.bat

# Construir localmente (para testes locais)
scripts\build-imagens.bat
```

### Build manual para Docker Hub
```bash
# Fazer login no Docker Hub
docker login

# Servidor Go
docker build -f config\docker\Dockerfile.servidor-go -t bia18/projetok-servidor-go:latest .
docker push bia18/projetok-servidor-go:latest

# Servidor Python  
docker build -f config\docker\Dockerfile.servidor-python -t bia18/projetok-servidor-python:latest .
docker push bia18/projetok-servidor-python:latest
```

## Kubernetes

Três recursos principais:
- **`deployment-servidor-go.yaml`** - Deploy do servidor Go
- **`deployment-servidor-python.yaml`** - Deploy do servidor Python  
- **`service-servidor.yaml`** - Serviços para load balancing

### Deploy
```bash
kubectl apply -f config/kubernetes/
```

### Imagens utilizadas
- **bia18/projetok-servidor-go:latest** - Imagem do Docker Hub para servidor Go
- **bia18/projetok-servidor-python:latest** - Imagem do Docker Hub para servidor Python
- **imagePullPolicy**: Always (sempre baixa a versão mais recente)

## Configurações

- **Servidores**: 2-10 instâncias configuráveis
- **Recursos**: CPU e memória limitados
- **Rede**: LoadBalancer interno para distribuição
