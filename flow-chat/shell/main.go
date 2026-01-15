package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"time"
)

const (
	flowHome = "/opt/flow-chat"
	auditLog = "/opt/flow-chat/adn/shell_audit.log"
)

// audit log
var auditMu sync.Mutex

func audit(format string, args ...interface{}) {
	auditMu.Lock()
	defer auditMu.Unlock()

	f, err := os.OpenFile(auditLog, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		return err
	}
	defer f.Close()

	ts := time.Now().Format("2006-01-02 15:04:05")
	msg := fmt.Sprintf(format, args...)
	fmt.Fprintf(f, "[%s] %s\n", ts, msg)
}

// ExecRequest - requête d'exécution
type ExecRequest struct {
	Cmd     string `json:"cmd"`
	Timeout int    `json:"timeout"` // secondes, défaut 60
	Cwd     string `json:"cwd"`     // working dir, défaut flowHome
}

// ExecResponse - réponse d'exécution
type ExecResponse struct {
	Stdout   string  `json:"stdout"`
	Stderr   string  `json:"stderr"`
	Code     int     `json:"code"`
	Duration float64 `json:"duration_ms"`
	Success  bool    `json:"success"`
}

// exécuter une commande
func execute(req ExecRequest) ExecResponse {
	start := time.Now()

	// timeout par défaut
	timeout := req.Timeout
	if timeout <= 0 {
		timeout = 60
	}
	if timeout > 300 {
		timeout = 300 // max 5 min
	}

	// working directory
	cwd := req.Cwd
	if cwd == "" {
		cwd = flowHome
	}

	audit("EXEC [%s] %s", cwd, req.Cmd)

	// créer la commande
	ctx, cancel := exec.Command("bash", "-c", req.Cmd), func() {}
	cmd := ctx
	cmd.Dir = cwd

	// environnement
	cmd.Env = append(os.Environ(),
		"HOME="+flowHome,
		"PATH=/opt/flow-chat/bin:/usr/local/bin:/usr/bin:/bin",
		"FLOW_SHELL=1",
	)

	// capturer stdout/stderr
	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	// timeout
	done := make(chan error, 1)
	go func() {
		done <- cmd.Run()
	}()

	var err error
	select {
	case err = <-done:
		// terminé
	case <-time.After(time.Duration(timeout) * time.Second):
		cmd.Process.Kill()
		err = fmt.Errorf("timeout after %ds", timeout)
	}
	cancel()

	duration := float64(time.Since(start).Microseconds()) / 1000

	code := 0
	if err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			code = exitErr.ExitCode()
		} else {
			code = -1
		}
	}

	// limiter la taille de sortie
	out := stdout.String()
	if len(out) > 50000 {
		out = out[:50000] + "\n... (tronqué)"
	}
	errOut := stderr.String()
	if len(errOut) > 10000 {
		errOut = errOut[:10000] + "\n... (tronqué)"
	}

	audit("CODE %d (%.1fms)", code, duration)

	return ExecResponse{
		Stdout:   out,
		Stderr:   errOut,
		Code:     code,
		Duration: duration,
		Success:  code == 0,
	}
}

// handler HTTP
func execHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		http.Error(w, "POST only", 405)
		return
	}

	body, _ := io.ReadAll(r.Body)
	var req ExecRequest
	if err := json.Unmarshal(body, &req); err != nil {
		http.Error(w, "invalid json", 400)
		return
	}

	if req.Cmd == "" {
		http.Error(w, "cmd required", 400)
		return
	}

	resp := execute(req)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

// health check
func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"organ":  "shell",
		"status": "ready",
		"home":   flowHome,
	})
}

// read file
func readHandler(w http.ResponseWriter, r *http.Request) {
	path := r.URL.Query().Get("path")
	if path == "" {
		http.Error(w, "path required", 400)
		return
	}

	// sécurité: résoudre le chemin
	if !filepath.IsAbs(path) {
		path = filepath.Join(flowHome, path)
	}
	path = filepath.Clean(path)

	content, err := os.ReadFile(path)
	if err != nil {
		http.Error(w, err.Error(), 404)
		return
	}

	// limiter
	if len(content) > 100000 {
		content = append(content[:100000], []byte("\n... (tronqué)")...)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"path":    path,
		"content": string(content),
		"size":    len(content),
	})
}

// write file
func writeHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		http.Error(w, "POST only", 405)
		return
	}

	var req struct {
		Path    string `json:"path"`
		Content string `json:"content"`
	}

	body, _ := io.ReadAll(r.Body)
	if err := json.Unmarshal(body, &req); err != nil {
		http.Error(w, "invalid json", 400)
		return
	}

	if req.Path == "" {
		http.Error(w, "path required", 400)
		return
	}

	// sécurité: résoudre le chemin
	path := req.Path
	if !filepath.IsAbs(path) {
		path = filepath.Join(flowHome, path)
	}
	path = filepath.Clean(path)

	// créer le dossier parent si nécessaire
	os.MkdirAll(filepath.Dir(path), 0755)

	audit("WRITE %s (%d bytes)", path, len(req.Content))

	if err := os.WriteFile(path, []byte(req.Content), 0644); err != nil {
		http.Error(w, err.Error(), 500)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"path":    path,
		"written": len(req.Content),
		"success": true,
	})
}

// list directory
func listHandler(w http.ResponseWriter, r *http.Request) {
	path := r.URL.Query().Get("path")
	if path == "" {
		path = flowHome
	}

	if !filepath.IsAbs(path) {
		path = filepath.Join(flowHome, path)
	}

	entries, err := os.ReadDir(path)
	if err != nil {
		http.Error(w, err.Error(), 404)
		return
	}

	var files []map[string]interface{}
	for _, e := range entries {
		info, _ := e.Info()
		files = append(files, map[string]interface{}{
			"name":  e.Name(),
			"dir":   e.IsDir(),
			"size":  info.Size(),
			"mode":  info.Mode().String(),
			"mtime": info.ModTime().Format(time.RFC3339),
		})
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"path":  path,
		"files": files,
	})
}

// console - écrire à la Console via synapse
func consoleHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		http.Error(w, "POST only", 405)
		return
	}

	var req struct {
		Message string `json:"message"`
		Type    string `json:"type"` // info, warn, error, success
		Context string `json:"context"`
	}

	body, _ := io.ReadAll(r.Body)
	if err := json.Unmarshal(body, &req); err != nil {
		http.Error(w, "invalid json", 400)
		return
	}

	if req.Message == "" {
		http.Error(w, "message required", 400)
		return
	}

	if req.Type == "" {
		req.Type = "info"
	}

	audit("CONSOLE [%s] %s", req.Type, req.Message)

	// Envoyer à synapse pour broadcast
	payload := map[string]interface{}{
		"source":  "shell",
		"type":    req.Type,
		"message": req.Message,
		"context": req.Context,
		"time":    time.Now().Format(time.RFC3339),
	}

	jsonData, _ := json.Marshal(payload)

	resp, err := http.Post(
		"http://127.0.0.1:3001/notify",
		"application/json",
		bytes.NewBuffer(jsonData),
	)

	success := false
	if err == nil && resp.StatusCode == 200 {
		success = true
		resp.Body.Close()
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"sent":    success,
		"message": req.Message,
		"type":    req.Type,
	})
}

// print - raccourci pour écrire un message simple
func printHandler(w http.ResponseWriter, r *http.Request) {
	msg := r.URL.Query().Get("msg")
	if msg == "" {
		http.Error(w, "msg required", 400)
		return
	}

	msgType := r.URL.Query().Get("type")
	if msgType == "" {
		msgType = "info"
	}

	audit("PRINT [%s] %s", msgType, msg)

	payload := map[string]interface{}{
		"source":  "shell",
		"type":    msgType,
		"message": msg,
		"time":    time.Now().Format(time.RFC3339),
	}

	jsonData, _ := json.Marshal(payload)

	resp, err := http.Post(
		"http://127.0.0.1:3001/notify",
		"application/json",
		bytes.NewBuffer(jsonData),
	)

	success := false
	if err == nil && resp.StatusCode == 200 {
		success = true
		resp.Body.Close()
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"sent":    success,
		"message": msg,
	})
}

// senses - état des 12 sens
func sensesHandler(w http.ResponseWriter, r *http.Request) {
	organs := []struct {
		name string
		port int
	}{
		{"membrane", 8092},
		{"cytoplasme", 8091},
		{"oreille", 8093},
		{"noyau", 8094},
		{"quantique", 8095},
		{"mitochondrie", 8096},
		{"anticorps", 8097},
		{"myeline", 8098},
		{"hypnos", 8099},
		{"corps", 8101},
		{"synapse", 3001},
		{"phoenix", 8888},
	}

	var results []map[string]interface{}
	alive := 0

	for _, o := range organs {
		start := time.Now()
		resp, err := http.Get(fmt.Sprintf("http://127.0.0.1:%d/health", o.port))
		latency := float64(time.Since(start).Microseconds()) / 1000

		status := "dead"
		if err == nil && resp.StatusCode == 200 {
			status = "alive"
			alive++
			resp.Body.Close()
		}

		results = append(results, map[string]interface{}{
			"name":       o.name,
			"port":       o.port,
			"status":     status,
			"latency_ms": latency,
		})
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"organs":     results,
		"alive":      alive,
		"total":      len(organs),
		"health_pct": float64(alive) / float64(len(organs)) * 100,
	})
}

func main() {
	// s'assurer que le dossier audit existe
	os.MkdirAll(filepath.Dir(auditLog), 0755)

	http.HandleFunc("/health", healthHandler)
	http.HandleFunc("/exec", execHandler)
	http.HandleFunc("/read", readHandler)
	http.HandleFunc("/write", writeHandler)
	http.HandleFunc("/list", listHandler)
	http.HandleFunc("/senses", sensesHandler)
	http.HandleFunc("/console", consoleHandler)
	http.HandleFunc("/print", printHandler)

	// CLI mode
	if len(os.Args) > 1 {
		cmd := strings.Join(os.Args[1:], " ")
		resp := execute(ExecRequest{Cmd: cmd})
		fmt.Print(resp.Stdout)
		if resp.Stderr != "" {
			fmt.Fprint(os.Stderr, resp.Stderr)
		}
		os.Exit(resp.Code)
	}

	fmt.Println("🐚 shell :8100 [go]")
	audit("SHELL STARTED")
	http.ListenAndServe("127.0.0.1:8100", nil)
}
