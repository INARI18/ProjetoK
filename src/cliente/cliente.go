package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"net"
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
	Type      string `json:"type"`
	Status    string `json:"status"`
	Timestamp int64  `json:"timestamp"`
	Message   string `json:"message"`
}

func conectar(host string, porta int, numMensagens int, clienteID string) error {
	address := fmt.Sprintf("%s:%d", host, porta)
	
	conn, err := net.Dial("tcp", address)
	if err != nil {
		return err
	}
	defer conn.Close()

	// Enviar múltiplas mensagens conforme configurado
	for i := 1; i <= numMensagens; i++ {
		msg := Message{
			Type:      "PING",
			ClientID:  clienteID,
			Timestamp: time.Now().UnixNano() / int64(time.Millisecond),
			Sequence:  i,
			Data:      fmt.Sprintf("PING %d do cliente %s", i, clienteID),
		}

		msgBytes, err := json.Marshal(msg)
		if err != nil {
			return err
		}

		// Enviar tamanho da mensagem primeiro (protocolo)
		msgSize := fmt.Sprintf("%08d", len(msgBytes))
		_, err = conn.Write([]byte(msgSize))
		if err != nil {
			return err
		}

		// Enviar a mensagem
		_, err = conn.Write(msgBytes)
		if err != nil {
			return err
		}

		// Ler resposta
		sizeBuffer := make([]byte, 8)
		_, err = conn.Read(sizeBuffer)
		if err != nil {
			return err
		}

		var responseSize int
		fmt.Sscanf(string(sizeBuffer), "%d", &responseSize)

		responseBuffer := make([]byte, responseSize)
		_, err = conn.Read(responseBuffer)
		if err != nil {
			return err
		}

		var response Response
		err = json.Unmarshal(responseBuffer, &response)
		if err != nil {
			return err
		}

		// Pequena pausa entre mensagens para evitar sobrecarga
		if i < numMensagens {
			time.Sleep(10 * time.Millisecond)
		}
	}

	return nil
}

func main() {
	host := flag.String("host", "127.0.0.1", "Host do servidor")
	porta := flag.Int("porta", 8000, "Porta do servidor")
	numMensagens := flag.Int("mensagens", 1, "Número de mensagens a enviar")
	clienteID := flag.String("cliente-id", "", "ID único do cliente")
	flag.Parse()

	if *clienteID == "" {
		*clienteID = fmt.Sprintf("cliente_%d", time.Now().UnixNano())
	}

	err := conectar(*host, *porta, *numMensagens, *clienteID)
	if err != nil {
		// Falha silenciosa para não poluir os logs de teste
		return
	}
}
