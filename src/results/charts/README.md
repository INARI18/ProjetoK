# Explicação das Métricas Avançadas de Desempenho

Este documento detalha como cada métrica utilizada na análise comparativa dos servidores Go e Python foi calculada, o que ela representa e qual a unidade de medida utilizada. As métricas são apresentadas nos gráficos radar e na tabela comparativa.

## O que significa "adimensional"?
Adimensional significa que a métrica não possui unidade de medida física associada (como segundos, bytes, etc). Ou seja, é um valor puro, resultado de uma razão ou comparação, e serve apenas para indicar desempenho relativo entre sistemas.

## 1. Escalabilidade
**Fórmula:**
```
Escalabilidade = (Throughput com máximo de clientes) / (Throughput com mínimo de clientes)
```
- **Unidade:** Adimensional
- **Como foi calculada:** Considera o throughput médio (mensagens por segundo) quando o número de clientes é mínimo e quando é máximo, mantendo fixos o número de servidores e de mensagens. Mede o quanto o sistema consegue crescer em desempenho ao aumentar a carga de clientes.

## 2. Eficiência Relativa
**Fórmula:**
```
Eficiência Relativa = (Throughput com máximo de clientes) / (Máx. clientes × Throughput com mínimo de clientes)
```
- **Unidade:** Adimensional
- **Como foi calculada:** Compara o throughput obtido com muitos clientes com o throughput "ideal" (caso cada cliente adicional trouxesse ganho linear). Mede o quanto o sistema se aproxima de uma escalabilidade perfeita.

## 3. Consistência (DPR)
**Fórmula:**
```
Consistência = 1 / (1 + (desvio padrão do tempo de resposta / média do tempo de resposta))
```
- **Unidade:** Adimensional
- **Como foi calculada:** Mede a estabilidade do tempo de resposta. Quanto menor a variação em relação à média, mais consistente é o desempenho. Valores próximos de 1 indicam alta consistência.

## 4. Tempo de Resposta por Mensagem
**Fórmula:**
```
Tempo de Resposta por Mensagem = Média do tempo de resposta global / Média do número de mensagens
```
- **Unidade:** ms/msg (milissegundos por mensagem)
- **Como foi calculada:** Indica o tempo médio para processar cada mensagem, considerando todos os experimentos. Quanto menor, melhor.

## 5. Speedup
**Fórmula:**
```
Speedup = (Tempo com mínimo de servidores) / (Tempo com máximo de servidores)
```
- **Unidade:** Adimensional
- **Como foi calculada:** Compara o tempo de execução com poucos servidores versus muitos servidores, mantendo fixos clientes e mensagens. Mede o ganho de desempenho ao paralelizar.

## 6. Overhead
**Fórmula:**
```
Overhead = (Tempo com máximo de clientes - Tempo com mínimo de clientes) / (Máx. clientes - Mín. clientes)
```
- **Unidade:** ms/cli (milissegundos por cliente)
- **Como foi calculada:** Mede o quanto o tempo de resposta aumenta para cada cliente adicional, mantendo fixos servidores e mensagens. Quanto menor, melhor.

---

Essas métricas foram escolhidas para fornecer uma visão abrangente sobre escalabilidade, eficiência, estabilidade e custo de paralelismo dos servidores testados. Em caso de dúvidas, consulte o código-fonte `generate_charts.py`.
