// Servidor Go para protocolo Ping-Pong com suporte a múltiplas threads (goroutines)
// Requisitos:
// - Cada conexão de cliente deve ser tratada em uma goroutine
// - Registrar requisições em CSV
// - Registrar logs de erro
// - Protocolo Ping-Pong: receber 'ping', responder 'pong'

package main

import (
	"bufio"
	"encoding/csv"
	"fmt"
	"log"
	"net"
	"os"
	"sync"
	"time"
)

func handleConnection(conn net.Conn, wg *sync.WaitGroup, csvWriter *csv.Writer, logFile *os.File, clientID int) {
	defer wg.Done()
	defer conn.Close()
	reader := bufio.NewReader(conn)
	for {
		msg, err := reader.ReadString('\n')
		if err != nil {
			logFile.WriteString(fmt.Sprintf("%s,ERRO_LEITURA,%v\n", time.Now().Format(time.RFC3339), err))
			return
		}
		msg = msg[:len(msg)-1] // remove '\n'
		if msg == "ping" {
			_, err := conn.Write([]byte("pong\n"))
			if err != nil {
				logFile.WriteString(fmt.Sprintf("%s,ERRO_RESPOSTA,%v\n", time.Now().Format(time.RFC3339), err))
				return
			}
			csvWriter.Write([]string{time.Now().Format(time.RFC3339), fmt.Sprint(clientID), "ping", "pong", "sucesso"})
			csvWriter.Flush()
		} else {
			logFile.WriteString(fmt.Sprintf("%s,MENSAGEM_INVALIDA,%s\n", time.Now().Format(time.RFC3339), msg))
		}
	}
}

func main() {
	// Garante que os diretórios existem
	os.MkdirAll("results/reports/error", 0755)
	os.MkdirAll("results/reports", 0755)

	csvFile, err := os.OpenFile("results/reports/server_result.csv", os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
	if err != nil {
		log.Fatalf("Erro ao abrir arquivo CSV: %v", err)
	}
	defer csvFile.Close()
	csvWriter := csv.NewWriter(csvFile)
	csvWriter.Write([]string{"timestamp", "client_id", "mensagem_recebida", "mensagem_enviada", "status"})
	csvWriter.Flush()

	logFile, err := os.OpenFile("results/reports/error/server_error.log", os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
	if err != nil {
		log.Fatalf("Erro ao abrir arquivo de log: %v", err)
	}
	defer logFile.Close()

	ln, err := net.Listen("tcp", ":9000")
	if err != nil {
		log.Fatalf("Erro ao iniciar servidor: %v", err)
	}
	defer ln.Close()
	fmt.Println("Servidor ouvindo na porta 9000...")

	var wg sync.WaitGroup
	clientID := 0
	for {
		conn, err := ln.Accept()
		if err != nil {
			logFile.WriteString(fmt.Sprintf("%s,ERRO_CONEXAO,%v\n", time.Now().Format(time.RFC3339), err))
			continue
		}
		clientID++
		wg.Add(1)
		go handleConnection(conn, &wg, csvWriter, logFile, clientID)
	}
	// wg.Wait() // Não é chamado pois o servidor é contínuo
}
