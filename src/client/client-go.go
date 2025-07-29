package main

import (
   "runtime"
   "bufio"
   "encoding/csv"
   "fmt"
   "net"
   "os"
   "strconv"
   "time"
   "sync"
)



func ensureCSVHeader(csvPath string, header []string) error {
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
   // Garante uso de todos os núcleos disponíveis
   runtime.GOMAXPROCS(runtime.NumCPU())
   // Garante que o diretório existe
   os.MkdirAll("src/results/reports", 0755)
   // Cria a pasta temp-go para os CSVs temporários
   tempGoDir := "src/results/reports/temp-go"
   os.MkdirAll(tempGoDir, 0755)

   // Parâmetros: endereço, porta, quantidade de mensagens
   serverHost := "127.0.0.1" // Força IPv4 para evitar problemas de conexão
   serverPort := 9000
   numMsgs := 10
   numClientes := 1
   numClientesTotal := 1
   numServidores := 2
   cenarioID := time.Now().Format("20060102T150405Z")
   clienteIdxInicio := 1
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
	   clienteIdxInicio, _ = strconv.Atoi(os.Args[5])
   }
   if len(os.Args) > 6 {
	   numServidores, _ = strconv.Atoi(os.Args[6])
   }
   if len(os.Args) > 7 {
	   numClientesTotal, _ = strconv.Atoi(os.Args[7])
   }
   if len(os.Args) > 8 {
	   cenarioID = os.Args[8]
	   if n, err := strconv.Atoi(cenarioID); err == nil {
		   cenarioID = fmt.Sprintf("C%d", n)
	   }
   }
   if len(os.Args) > 9 {
	   repeticao, _ = strconv.Atoi(os.Args[9])
   }



   // Usa o nome do arquivo temporário se passado pela variável de ambiente
   csvPath := os.Getenv("GO_CSV_TEMP_FILE")
   if csvPath == "" {
	   pid := os.Getpid()
	   csvDir := os.Getenv("GO_CSV_TEMP_DIR")
	   if csvDir == "" {
		   csvDir = tempGoDir
	   }
	   // Corrige path absoluto vindo do Windows (ex: C:\Users\Bia...) para sempre ser relativo ao projeto
	   if len(csvDir) > 1 && (csvDir[1] == ':' || csvDir[0] == '/' || csvDir[0] == '\\') {
		   csvDir = tempGoDir
	   }
	   os.MkdirAll(csvDir, 0755)
	   csvPath = fmt.Sprintf("%s/test-go-%d.csv", csvDir, pid)
   }

   // Captura qualquer panic e registra no CSV
   defer func() {
	   if r := recover(); r != nil {
		   // Em caso de panic, escreve diretamente no CSV (sem lock)
		   csvFile, err := os.OpenFile(csvPath, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
		   if err == nil {
			   defer csvFile.Close()
			   csvWriter := csv.NewWriter(csvFile)
			   csvWriter.Write([]string{
				   cenarioID,
				   strconv.Itoa(repeticao),
				   strconv.Itoa(clienteIdxInicio),
				   strconv.Itoa(numClientesTotal),
				   strconv.Itoa(numServidores),
				   strconv.Itoa(numMsgs),
				   time.Now().Format(time.RFC3339Nano),
				   time.Now().Format(time.RFC3339Nano),
				   "0",
				   "panic",
				   fmt.Sprintf("%v", r),
				   "",
				   "",
			   })
			   csvWriter.Flush()
		   }
	   }
   }()

   err := ensureCSVHeader(csvPath, []string{"cenario_id", "repeticao", "cliente_id", "num_clientes", "num_servidores", "num_mensagens", "tempo_inicio", "tempo_fim", "tempo_total_ms", "status", "erro", "mem_mb", "num_goroutine"})
   if err != nil {
	   fmt.Println("Erro ao garantir cabeçalho do CSV:", err)
   }

   if numMsgs <= 0 {
	  // Escreve erro no CSV e aborta
	  csvFile, err := os.OpenFile(csvPath, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
	  if err == nil {
		 defer csvFile.Close()
		 csvWriter := csv.NewWriter(csvFile)
		 csvWriter.Write([]string{
			cenarioID,
			strconv.Itoa(repeticao),
			strconv.Itoa(clienteIdxInicio),
			strconv.Itoa(numClientesTotal),
			strconv.Itoa(numServidores),
			strconv.Itoa(numMsgs),
			time.Now().Format(time.RFC3339Nano),
			time.Now().Format(time.RFC3339Nano),
			"0",
			"erro_param",
			"numMsgs deve ser > 0",
			"",
			"",
		 })
		 csvWriter.Flush()
	  }
	  fmt.Println("[ERRO] numMsgs deve ser > 0")
	  return
   }
   type resultado struct {
	  cenarioID, repeticao, clienteID, numClientes, numServidores, numMsgs, t0, t1, tempoTotal, status, erro, memMB, numGoroutine string
   }
   resultados := make([]resultado, numClientes)
   var wg sync.WaitGroup
   for i := 0; i < numClientes; i++ {
	  clienteIdx := clienteIdxInicio + i
	  wg.Add(1)
	  go func(clienteIdx int) {
		 defer wg.Done()
		 addr := fmt.Sprintf("%s:%d", serverHost, serverPort)
		 conn, err := net.Dial("tcp", addr)
		 t0Cliente := time.Now()
		 statusGeral := "sucesso"
		 erroGeral := ""
		 var memStats runtime.MemStats
		 runtime.ReadMemStats(&memStats)
		 memMB := float64(memStats.Alloc) / 1024.0 / 1024.0
		 t1Cliente := t0Cliente
		 tempoTotal := 0.0
		 if err != nil {
			statusGeral = "erro_conexao"
			erroGeral = err.Error()
		 } else {
			defer conn.Close()
			reader := bufio.NewReader(conn)
			for i := 1; i <= numMsgs; i++ {
			   _, err := conn.Write([]byte("ping\n"))
			   if err != nil {
				  statusGeral = "erro_envio"
				  erroGeral = err.Error()
				  break
			   }
			}
			for i := 1; i <= numMsgs; i++ {
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
			t1Cliente = time.Now()
			tempoTotal = t1Cliente.Sub(t0Cliente).Seconds() * 1000 // ms
		 }
		 resultados[clienteIdx-clienteIdxInicio] = resultado{
			cenarioID,
			strconv.Itoa(repeticao),
			strconv.Itoa(clienteIdx),
			strconv.Itoa(numClientesTotal),
			strconv.Itoa(numServidores),
			strconv.Itoa(numMsgs),
			t0Cliente.Format(time.RFC3339Nano),
			t1Cliente.Format(time.RFC3339Nano),
			fmt.Sprintf("%.2f", tempoTotal),
			statusGeral,
			erroGeral,
			fmt.Sprintf("%.2f", memMB),
			"", // numGoroutine preenchido depois
		 }
		 // Nenhum print dentro da goroutine
	  }(clienteIdx)
   }
   // Captura o número de goroutines logo após criar todas
   numGoroutineInit := runtime.NumGoroutine()
   wg.Wait()
   // Preenche o campo numGoroutine para todos os resultados
   for i := range resultados {
	  resultados[i].numGoroutine = strconv.Itoa(numGoroutineInit)
   }
   // Ordena por clienteID (já está em ordem, mas para garantir)
   // Escreve tudo no CSV de uma vez (sem lock)
   csvFile, err := os.OpenFile(csvPath, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
   if err == nil {
	  defer csvFile.Close()
	  csvWriter := csv.NewWriter(csvFile)
	  for _, r := range resultados {
		 csvWriter.Write([]string{
			r.cenarioID, r.repeticao, r.clienteID, r.numClientes, r.numServidores, r.numMsgs, r.t0, r.t1, r.tempoTotal, r.status, r.erro, r.memMB, r.numGoroutine,
		 })
	  }
	  csvWriter.Flush()
   }
}
