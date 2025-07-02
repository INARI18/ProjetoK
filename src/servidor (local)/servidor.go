package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net"
	"strconv"
	"time"
)

type Message struct {
	Type      string `json:"type"`
	ClientID  string `json:"client_id"`
	Timestamp int64  `json:"timestamp"`
	Sequence  int    `json:"sequence"`
	Data      string `json:"data"`
}

type Response struct {
	Type             string `json:"type"`
	Status           string `json:"status"`
	Timestamp        int64  `json:"timestamp"`
	OriginalTimestamp int64 `json:"original_timestamp,omitempty"`
	ClientID         string `json:"client_id,omitempty"`
	Sequence         int    `json:"sequence,omitempty"`
	Message          string `json:"message"`
}

func lidarComCliente(conn net.Conn, portaServidor int) {
	defer conn.Close()

	for {
		// Ler tamanho da mensagem (protocolo)
		sizeBuffer := make([]byte, 8)
		n, err := io.ReadFull(conn, sizeBuffer)
		if err != nil || n < 8 {
			break
		}

		msgSize, err := strconv.Atoi(string(sizeBuffer))
		if err != nil {
			break
		}

		// Ler a mensagem completa
		msgBuffer := make([]byte, msgSize)
		n, err = io.ReadFull(conn, msgBuffer)
		if err != nil || n < msgSize {
			break
		}

		var message Message
		err = json.Unmarshal(msgBuffer, &message)
		if err != nil {
			// Erro de decodificação
			response := Response{
				Type:      "response",
				Status:    "error",
				Timestamp: time.Now().UnixNano() / int64(time.Millisecond),
				Message:   "Erro ao decodificar mensagem",
			}

			enviarResposta(conn, response)
			continue
		}

		var response Response

		// Implementar protocolo PING
		if message.Type == "PING" {
			response = Response{
				Type:              "PONG",
				Status:            "success",
				Timestamp:         time.Now().UnixNano() / int64(time.Millisecond),
				OriginalTimestamp: message.Timestamp,
				ClientID:          message.ClientID,
				Sequence:          message.Sequence,
				Message:           fmt.Sprintf("PONG para %s", message.ClientID),
			}
		} else {
			// Protocolo genérico para outras mensagens
			response = Response{
				Type:      "response",
				Status:    "success",
				Timestamp: time.Now().UnixNano() / int64(time.Millisecond),
				Message:   fmt.Sprintf("Processado: %s", message.Data),
			}
		}

		enviarResposta(conn, response)
	}
}

func enviarResposta(conn net.Conn, response Response) {
	responseBytes, err := json.Marshal(response)
	if err != nil {
		return
	}

	responseSize := fmt.Sprintf("%08d", len(responseBytes))
	conn.Write([]byte(responseSize))
	conn.Write(responseBytes)
}

func iniciarServidor(porta int) {
	listener, err := net.Listen("tcp", fmt.Sprintf(":%d", porta))
	if err != nil {
		fmt.Printf("Erro ao iniciar servidor: %v\n", err)
		return
	}
	defer listener.Close()

	fmt.Printf("[SERVIDOR GO] Escutando na porta %d\n", porta)

	for {
		conn, err := listener.Accept()
		if err != nil {
			continue
		}

		// Uma goroutine por cliente
		go lidarComCliente(conn, porta)
	}
}

func main() {
	porta := flag.Int("porta", 8001, "Porta do servidor")
	flag.Parse()

	iniciarServidor(*porta)
}
