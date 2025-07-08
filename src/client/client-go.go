package main

import (
	"bufio"
	"encoding/csv"
	"fmt"
	"github.com/gofrs/flock"
	"net"
	"os"
	"strconv"
	"time"
)

func writeCSVWithLock(csvPath string, record []string) error {
	lock := flock.New(csvPath + ".lock")
	locked, err := lock.TryLock()
	if err != nil || !locked {
		return fmt.Errorf("erro ao obter lock do CSV: %v", err)
	}
	defer lock.Unlock()

	csvFile, err := os.OpenFile(csvPath, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
	if err != nil {
		return err
	}
	defer csvFile.Close()
	csvWriter := csv.NewWriter(csvFile)
	csvWriter.Write(record)
	csvWriter.Flush()
	return nil
}

func ensureCSVHeaderWithLock(csvPath string, header []string) error {
	lock := flock.New(csvPath + ".lock")
	locked, err := lock.TryLock()
	if err != nil || !locked {
		return fmt.Errorf("erro ao obter lock do CSV para cabeçalho: %v", err)
	}
	defer lock.Unlock()

	// Abre ou cria o arquivo
	csvFile, err := os.OpenFile(csvPath, os.O_CREATE|os.O_RDWR, 0644)
	if err != nil {
		return err
	}
	defer csvFile.Close()

	// Verifica se está vazio
	fileInfo, err := csvFile.Stat()
	if err != nil {
		return err
	}
	if fileInfo.Size() == 0 {
		csvWriter := csv.NewWriter(csvFile)
		csvWriter.Write(header)
		csvWriter.Flush()
	}
	return nil
}

func main() {
	// Garante que o diretório existe
	os.MkdirAll("src/results/reports", 0755)

	// Parâmetros: endereço, porta, quantidade de mensagens
	serverHost := "127.0.0.1" // Força IPv4 para evitar problemas de conexão
	serverPort := 9000
	numMsgs := 10
	numClientes := 1
	numServidores := 2
	rodadaID := time.Now().Format("20060102T150405Z")
	clienteIdx := 1
	repeticao := 1
	if len(os.Args) > 1 {
		serverHost = os.Args[1]
	}
	if len(os.Args) > 2 {
		serverPort, _ = strconv.Atoi(os.Args[2])
	}
	if len(os.Args) > 3 {
		numMsgs, _ = strconv.Atoi(os.Args[3])
	}
	if len(os.Args) > 4 {
		numClientes, _ = strconv.Atoi(os.Args[4])
	}
	if len(os.Args) > 5 {
		clienteIdx, _ = strconv.Atoi(os.Args[5])
	}
	if len(os.Args) > 6 {
		numServidores, _ = strconv.Atoi(os.Args[6])
	}
	if len(os.Args) > 7 {
		rodadaNum, err := strconv.Atoi(os.Args[7])
		if err == nil {
			rodadaID = fmt.Sprintf("R%d", rodadaNum)
		}
	}
	if len(os.Args) > 8 {
		repeticao, _ = strconv.Atoi(os.Args[8])
	}

	csvPath := "src/results/reports/test-go.csv"

	err := ensureCSVHeaderWithLock(csvPath, []string{"rodada_id", "repeticao", "cliente_id", "num_clientes", "num_servidores", "num_mensagens", "tempo_inicio", "tempo_fim", "tempo_total_ms", "status", "erro"})
	if err != nil && err.Error() != "erro ao obter lock do CSV para cabeçalho: <nil>" {
		fmt.Println("Erro ao garantir cabeçalho do CSV:", err)
	}

	addr := fmt.Sprintf("%s:%d", serverHost, serverPort)
	conn, err := net.Dial("tcp", addr)
	if err != nil {
		_ = writeCSVWithLock(csvPath, []string{rodadaID, strconv.Itoa(repeticao), strconv.Itoa(clienteIdx), strconv.Itoa(numClientes), strconv.Itoa(numServidores), strconv.Itoa(numMsgs), "", "", "", "erro_conexao", err.Error()})
		return
	}
	defer conn.Close()
	reader := bufio.NewReader(conn)

	t0Cliente := time.Now()
	statusGeral := "sucesso"
	erroGeral := ""

	for i := 1; i <= numMsgs; i++ {
		_, err := conn.Write([]byte("ping\n"))
		if err != nil {
			statusGeral = "erro_envio"
			erroGeral = err.Error()
			break
		}
		resp, err := reader.ReadString('\n')
		if err != nil {
			statusGeral = "erro_resposta"
			erroGeral = err.Error()
			break
		}
		resp = resp[:len(resp)-1] // remove '\n'
		if resp != "pong" {
			statusGeral = "falha"
			erroGeral = resp
			break
		}
	}
	t1Cliente := time.Now()
	tempoTotal := t1Cliente.Sub(t0Cliente).Seconds() * 1000 // ms
	_ = writeCSVWithLock(csvPath, []string{
		rodadaID,
		strconv.Itoa(repeticao),
		strconv.Itoa(clienteIdx),
		strconv.Itoa(numClientes),
		strconv.Itoa(numServidores),
		strconv.Itoa(numMsgs),
		t0Cliente.Format(time.RFC3339Nano),
		t1Cliente.Format(time.RFC3339Nano),
		fmt.Sprintf("%.2f", tempoTotal),
		statusGeral,
		erroGeral,
	})
}
