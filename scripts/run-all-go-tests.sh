#!/bin/sh
set -e

REPLICAS_LIST="2 4 6 8 10"
CLIENTES_LIST="10 20 30 40 50 60 70 80 90 100"
MENSAGENS_LIST="1 10 100 500 1000 10000"

TOTAL_EXEC=0
for REPLICAS in $REPLICAS_LIST; do
  echo "Ajustando servidores para $REPLICAS replicas..."
  kubectl scale deployment/server-go --replicas=$REPLICAS
  # Aguarda os pods ficarem prontos
  while true; do
    RUNNING=$(kubectl get pods | grep server-go | grep Running | wc -l)
    if [ "$RUNNING" -ge "$REPLICAS" ]; then break; fi
    sleep 2
  done
  echo "Testando com $REPLICAS servidores."
  for NCLIENTES in $CLIENTES_LIST; do
    for NMENSAGENS in $MENSAGENS_LIST; do
      TOTAL_EXEC=$((TOTAL_EXEC+1))
      i=1
      while [ $i -le $NCLIENTES ]; do
        if [ $i -eq $NCLIENTES ]; then
          # Só o último cliente printa o resumo
          /app/client-go server-go 9000 $NMENSAGENS $REPLICAS $NCLIENTES $NMENSAGENS $TOTAL_EXEC $i $REPLICAS
          echo "------------------------------------------"
        else
          /app/client-go server-go 9000 $NMENSAGENS $REPLICAS $NCLIENTES $NMENSAGENS $TOTAL_EXEC $i $REPLICAS > /dev/null 2>&1 &
        fi
        i=$((i+1))
      done
      wait
      sleep 5
    done
  done

done

echo "Todos os testes concluídos!"
