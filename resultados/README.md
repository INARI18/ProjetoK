# Resultados - ProjetoK

Esta pasta organiza todos os outputs gerados pelos testes de carga.

## Subpastas

- **`graficos/`** - Visualizações em PNG (gráficos por cenário e comparativos)
- **`relatorios/`** - Relatórios estatísticos, comparativos e dados CSV

## Arquivos Principais

### Dados JSON (gerados pelos testes otimizados)
- `resultados_python_YYYYMMDD_HHMMSS.json` - Dados completos dos testes Python
- `resultados_go_YYYYMMDD_HHMMSS.json` - Dados completos dos testes Go

### Gráficos
- `analise_performance_1_mensagens.png` - Análise para 1 mensagem por cliente
- `analise_performance_10_mensagens.png` - Análise para 10 mensagens por cliente
- `analise_performance_100_mensagens.png` - Análise para 100 mensagens por cliente
- `analise_performance_500_mensagens.png` - Análise para 500 mensagens por cliente
- `analise_performance_1000_mensagens.png` - Análise para 1000 mensagens por cliente
- `analise_performance_10000_mensagens.png` - Análise para 10000 mensagens por cliente
- `comparacao_linguagens.png` - Comparativo Python vs Go

### Relatórios CSV (gerados pela análise de gráficos)
- `relatorio_por_linguagem_YYYYMMDD_HHMMSS.csv` - Estatísticas por linguagem
- `relatorio_detalhado_YYYYMMDD_HHMMSS.csv` - Análise detalhada por configuração

### Relatórios
- `relatorio_detalhado.csv` - Estatísticas por cenário
- `resumo_executivo.csv` - Resumo geral
- `estatisticas_avancadas.csv` - Métricas aprofundadas

## Regeneração

Os arquivos são sobrescritos a cada execução dos testes. Para preservar resultados específicos, renomeie os arquivos antes de uma nova execução.
