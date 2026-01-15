package main

import (
	"bytes"
	"embed"
	"encoding/json"
	"fmt"
	"io"
	"io/fs"
	"log"
	"mime/multipart"
	"net/http"
	"os"
	"os/exec"
	"sync"
	"time"

	"github.com/gorilla/websocket"
)

//go:embed static
var staticFiles embed.FS

var (
	httpClient = &http.Client{Timeout: 120 * time.Second}
	upgrader   = websocket.Upgrader{CheckOrigin: func(r *http.Request) bool { return true }}
)

// Config
var cfg = struct {
	Port       string
	MembraneURL string // pour crypto + forward
	IPFSURL    string
	XMRWallet  string
}{
	Port:        getEnv("PORT", "8200"),
	MembraneURL: getEnv("MEMBRANE_URL", "http://127.0.0.1:8092"),
	IPFSURL:     getEnv("IPFS_URL", "http://127.0.0.1:5001"),
	XMRWallet:   getEnv("XMR_RPC", "http://127.0.0.1:18083/json_rpc"),
}

// Jobs storage
var jobs = struct {
	sync.RWMutex
	m map[string]*Job
}{m: make(map[string]*Job)}

// WebSocket clients
var wsClients = struct {
	sync.RWMutex
	m map[string]*websocket.Conn
}{m: make(map[string]*websocket.Conn)}

// Job represents an analysis job
type Job struct {
	ID            string    `json:"id"`
	Status        string    `json:"status"`
	PDFCID        string    `json:"pdf_cid"`
	ResultCID     string    `json:"result_cid,omitempty"`
	XMRAddress    string    `json:"xmr_address"`
	AmountXMR     float64   `json:"amount_xmr"`
	AmountEUR     float64   `json:"amount_eur"`
	Confirmations int       `json:"confirmations"`
	Insights      int       `json:"insights,omitempty"`
	Error         string    `json:"error,omitempty"`
	CreatedAt     time.Time `json:"created_at"`
}

func main() {
	// API endpoints
	http.HandleFunc("/health", healthHandler)
	http.HandleFunc("/api/submit", submitHandler)
	http.HandleFunc("/api/result/", resultHandler)
	http.HandleFunc("/api/pubkey", pubkeyHandler)
	http.HandleFunc("/api/status", statusWSHandler)

	// Static files
	staticFS, err := fs.Sub(staticFiles, "web/static")
	if err != nil {
		http.Handle("/", http.FileServer(http.Dir("web/static")))
	} else {
		http.Handle("/", http.FileServer(http.FS(staticFS)))
	}

	log.Printf("◯ papers-service :%s → membrane:%s ipfs:%s", cfg.Port, cfg.MembraneURL, cfg.IPFSURL)
	log.Fatal(http.ListenAndServe(":"+cfg.Port, nil))
}

// healthHandler GET /health
func healthHandler(w http.ResponseWriter, r *http.Request) {
	jobs.RLock()
	count := len(jobs.m)
	jobs.RUnlock()

	json.NewEncoder(w).Encode(map[string]interface{}{
		"service":  "papers-service",
		"status":   "healthy",
		"jobs":     count,
		"membrane": cfg.MembraneURL,
	})
}

// pubkeyHandler GET /api/pubkey - forward to quantique
func pubkeyHandler(w http.ResponseWriter, r *http.Request) {
	// Forward to quantique:8095/pubkey
	resp, err := httpClient.Get("http://127.0.0.1:8095/pubkey")
	if err != nil {
		jsonError(w, "quantique unavailable", 503)
		return
	}
	defer resp.Body.Close()
	w.Header().Set("Content-Type", "application/json")
	io.Copy(w, resp.Body)
}

// submitHandler POST /api/submit
func submitHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		http.Error(w, "method not allowed", 405)
		return
	}

	var req struct {
		CID  string `json:"cid"`  // IPFS CID of encrypted PDF
		Tier int    `json:"tier"` // 50, 200, 500
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		jsonError(w, "invalid json", 400)
		return
	}

	if req.CID == "" {
		jsonError(w, "cid required", 400)
		return
	}

	// Generate job ID
	jobID := fmt.Sprintf("%x", time.Now().UnixNano())[:12]

	// Determine tier
	tier := req.Tier
	if tier != 50 && tier != 200 && tier != 500 {
		tier = 50
	}

	// Get XMR address for payment
	xmrAddr, amountXMR := createXMRPayment(jobID, float64(tier))

	job := &Job{
		ID:         jobID,
		Status:     "pending_payment",
		PDFCID:     req.CID,
		XMRAddress: xmrAddr,
		AmountXMR:  amountXMR,
		AmountEUR:  float64(tier),
		CreatedAt:  time.Now(),
	}

	jobs.Lock()
	jobs.m[jobID] = job
	jobs.Unlock()

	// Start watching payment
	go watchPayment(jobID)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"job_id":      jobID,
		"status":      job.Status,
		"xmr_address": xmrAddr,
		"amount_xmr":  amountXMR,
		"amount_eur":  tier,
		"result_url":  fmt.Sprintf("/api/result/%s", jobID),
	})
}

// createXMRPayment creates a payment request
func createXMRPayment(jobID string, amountEUR float64) (string, float64) {
	// Call monero-wallet-rpc to create subaddress
	payload := map[string]interface{}{
		"jsonrpc": "2.0",
		"id":      "0",
		"method":  "create_address",
		"params":  map[string]interface{}{"account_index": 0, "label": jobID},
	}
	body, _ := json.Marshal(payload)

	resp, err := httpClient.Post(cfg.XMRWallet, "application/json", bytes.NewReader(body))
	if err != nil {
		log.Printf("xmr rpc failed: %v", err)
		return "XMR_WALLET_OFFLINE", amountEUR / 150.0
	}
	defer resp.Body.Close()

	var result struct {
		Result struct {
			Address string `json:"address"`
		} `json:"result"`
	}
	json.NewDecoder(resp.Body).Decode(&result)

	// Get current XMR/EUR rate
	xmrRate := getXMRRate()
	amountXMR := amountEUR / xmrRate

	if result.Result.Address != "" {
		return result.Result.Address, amountXMR
	}
	return "XMR_ADDR_ERROR", amountXMR
}

// getXMRRate fetches current XMR/EUR rate
func getXMRRate() float64 {
	resp, err := httpClient.Get("https://api.coingecko.com/api/v3/simple/price?ids=monero&vs_currencies=eur")
	if err != nil {
		return 150.0
	}
	defer resp.Body.Close()

	var rate struct {
		Monero struct {
			EUR float64 `json:"eur"`
		} `json:"monero"`
	}
	json.NewDecoder(resp.Body).Decode(&rate)
	if rate.Monero.EUR > 0 {
		return rate.Monero.EUR
	}
	return 150.0
}

// watchPayment monitors XMR confirmations
func watchPayment(jobID string) {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		jobs.RLock()
		job, ok := jobs.m[jobID]
		jobs.RUnlock()

		if !ok || job.Status == "done" || job.Status == "error" {
			return
		}

		// Check for incoming payments
		confirmations := checkXMRPayment(job.XMRAddress, job.AmountXMR)
		if confirmations > 0 {
			jobs.Lock()
			job.Confirmations = confirmations
			jobs.Unlock()

			notifyWS(jobID, map[string]interface{}{
				"status":        "confirming",
				"confirmations": confirmations,
			})

			// 10 confirmations required
			if confirmations >= 10 {
				jobs.Lock()
				job.Status = "paid"
				jobs.Unlock()

				notifyWS(jobID, map[string]interface{}{"status": "paid"})
				go processJob(jobID)
				return
			}
		}
	}
}

// checkXMRPayment checks for payment at address
func checkXMRPayment(address string, amount float64) int {
	payload := map[string]interface{}{
		"jsonrpc": "2.0",
		"id":      "0",
		"method":  "get_transfers",
		"params":  map[string]interface{}{"in": true, "pending": true},
	}
	body, _ := json.Marshal(payload)

	resp, err := httpClient.Post(cfg.XMRWallet, "application/json", bytes.NewReader(body))
	if err != nil {
		return 0
	}
	defer resp.Body.Close()

	var result struct {
		Result struct {
			In      []struct{ Address string; Amount uint64; Confirmations int } `json:"in"`
			Pending []struct{ Address string; Amount uint64 }                    `json:"pending"`
		} `json:"result"`
	}
	json.NewDecoder(resp.Body).Decode(&result)

	amountAtomic := uint64(amount * 1e12)
	for _, tx := range result.Result.In {
		if tx.Address == address && tx.Amount >= amountAtomic {
			return tx.Confirmations
		}
	}
	for _, tx := range result.Result.Pending {
		if tx.Address == address && tx.Amount >= amountAtomic {
			return 1 // pending = 1 confirmation
		}
	}
	return 0
}

// processJob downloads, extracts, analyzes, uploads
func processJob(jobID string) {
	jobs.Lock()
	job := jobs.m[jobID]
	job.Status = "processing"
	jobs.Unlock()

	notifyWS(jobID, map[string]interface{}{"status": "processing"})

	// 1. Download from IPFS
	pdfData, err := ipfsDownload(job.PDFCID)
	if err != nil {
		setJobError(jobID, "ipfs download: "+err.Error())
		return
	}
	notifyWS(jobID, map[string]interface{}{"status": "downloaded", "size": len(pdfData)})

	// 2. Extract text with pdftotext
	text, err := extractText(pdfData)
	if err != nil {
		text = string(pdfData) // fallback
	}
	notifyWS(jobID, map[string]interface{}{"status": "extracted", "chars": len(text)})

	// 3. Send to membrane (which handles crypto + forward to cytoplasme)
	result, err := sendToMembrane(text)
	if err != nil {
		setJobError(jobID, "analysis: "+err.Error())
		return
	}
	notifyWS(jobID, map[string]interface{}{"status": "analyzed"})

	// 4. Upload result to IPFS
	resultCID, err := ipfsUpload(result, jobID+"_result.json")
	if err != nil {
		setJobError(jobID, "upload result: "+err.Error())
		return
	}

	// 5. Update job
	jobs.Lock()
	job.Status = "done"
	job.ResultCID = resultCID
	// Count insights from result
	var parsed struct{ Insights []interface{} }
	json.Unmarshal(result, &parsed)
	job.Insights = len(parsed.Insights)
	jobs.Unlock()

	notifyWS(jobID, map[string]interface{}{
		"status":     "done",
		"result_cid": resultCID,
		"insights":   job.Insights,
	})
}

// ipfsDownload downloads from IPFS
func ipfsDownload(cid string) ([]byte, error) {
	resp, err := httpClient.Post(cfg.IPFSURL+"/api/v0/cat?arg="+cid, "application/json", nil)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	return io.ReadAll(resp.Body)
}

// ipfsUpload uploads to IPFS
func ipfsUpload(data []byte, filename string) (string, error) {
	var body bytes.Buffer
	writer := multipart.NewWriter(&body)
	part, _ := writer.CreateFormFile("file", filename)
	part.Write(data)
	writer.Close()

	req, _ := http.NewRequest("POST", cfg.IPFSURL+"/api/v0/add", &body)
	req.Header.Set("Content-Type", writer.FormDataContentType())

	resp, err := httpClient.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	var result struct{ Hash string }
	json.NewDecoder(resp.Body).Decode(&result)
	return result.Hash, nil
}

// extractText extracts text from PDF using pdftotext
func extractText(pdfData []byte) (string, error) {
	cmd := exec.Command("pdftotext", "-", "-")
	cmd.Stdin = bytes.NewReader(pdfData)
	output, err := cmd.Output()
	return string(output), err
}

// sendToMembrane sends text to membrane for analysis
func sendToMembrane(text string) ([]byte, error) {
	payload := map[string]interface{}{
		"message": fmt.Sprintf("Analyse ce paper scientifique et trouve les insights:\n\n%s", text),
		"mode":    "analyze",
	}
	body, _ := json.Marshal(payload)

	resp, err := httpClient.Post(cfg.MembraneURL+"/chat", "application/json", bytes.NewReader(body))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	return io.ReadAll(resp.Body)
}

// resultHandler GET /api/result/:id
func resultHandler(w http.ResponseWriter, r *http.Request) {
	jobID := r.URL.Path[len("/api/result/"):]

	jobs.RLock()
	job, ok := jobs.m[jobID]
	jobs.RUnlock()

	if !ok {
		jsonError(w, "job not found", 404)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(job)
}

// statusWSHandler WebSocket for status updates
func statusWSHandler(w http.ResponseWriter, r *http.Request) {
	jobID := r.URL.Query().Get("job")
	if jobID == "" {
		http.Error(w, "job required", 400)
		return
	}

	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		return
	}

	wsClients.Lock()
	wsClients.m[jobID] = conn
	wsClients.Unlock()

	// Keep alive
	for {
		if _, _, err := conn.ReadMessage(); err != nil {
			break
		}
	}

	wsClients.Lock()
	delete(wsClients.m, jobID)
	wsClients.Unlock()
	conn.Close()
}

// notifyWS sends WebSocket notification
func notifyWS(jobID string, data map[string]interface{}) {
	wsClients.RLock()
	conn, ok := wsClients.m[jobID]
	wsClients.RUnlock()
	if ok {
		data["timestamp"] = time.Now().Unix()
		conn.WriteJSON(data)
	}
}

func setJobError(jobID, errMsg string) {
	jobs.Lock()
	if job, ok := jobs.m[jobID]; ok {
		job.Status = "error"
		job.Error = errMsg
	}
	jobs.Unlock()
	notifyWS(jobID, map[string]interface{}{"status": "error", "error": errMsg})
}

func jsonError(w http.ResponseWriter, msg string, code int) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	json.NewEncoder(w).Encode(map[string]string{"error": msg})
}

func getEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}
