# Código Fonte - ProjetoK

Esta pasta contém todo o código fonte do sistema cliente-servidor.

## Estrutura

- **`cliente/`** - Implementações do cliente em Python e Go
- **`servidor/`** - Servidor Python com suporte a threading
- **`testes/`** - Scripts para execução e análise dos testes

## Protocolo Implementado

Todos os componentes implementam o protocolo PING/PONG:
- Cliente envia: `{"type": "PING", ...}`
- Servidor responde: `{"type": "PONG", ...}`

## Execução

Execute os testes a partir da raiz do projeto usando os scripts em `../scripts/`
