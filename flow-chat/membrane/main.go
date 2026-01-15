package main

import (
	"bytes"
	"crypto/sha3"
	"embed"
	"encoding/hex"
	"encoding/json"
	"io"
	"io/fs"
	"log"
	"net/http"
	"sync"
	"time"
)

//go:embed static/*
var staticFiles embed.FS

var c = &http.Client{Timeout: 30 * time.Second}

// retry config
const maxRetries = 3
const retryDelay = 500 * time.Millisecond

// cache de hash pour vérification d'intégrité
var hashCache = struct {
	sync.RWMutex
	m map[string]string
}{m: make(map[string]string)}

// hash SHA3-256 pour chaque message
func hash256(data []byte) string {
	h := sha3.New256()
	h.Write(data)
	return hex.EncodeToString(h.Sum(nil))
}

// signer un message via quantique
func signMessage(msg []byte) (string, error) {
	reqBody, _ := json.Marshal(map[string]string{"message": string(msg)})
	resp, err := c.Post("http://127.0.0.1:8095/sign", "application/json", bytes.NewReader(reqBody))
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	var result map[string]string
	json.NewDecoder(resp.Body).Decode(&result)
	return result["signature"], nil
}

// vérifier l'intégrité via quantique
func verifyIntegrity() bool {
	resp, err := c.Get("http://127.0.0.1:8095/integrity")
	if err != nil {
		return false
	}
	defer resp.Body.Close()
	var result map[string]interface{}
	json.NewDecoder(resp.Body).Decode(&result)
	if v, ok := result["integrity"].(bool); ok {
		return v
	}
	return false
}

func chat(w http.ResponseWriter, r *http.Request) {
	b, _ := io.ReadAll(r.Body)

	// hash du message entrant
	inHash := hash256(b)

	// vérification d'intégrité post-quantique (non bloquant)
	go func() {
		if !verifyIntegrity() {
			log.Println("⚠️ quantum integrity check failed")
		}
	}()

	// signer le message avant transmission
	sig, _ := signMessage(b)

	// transmettre au cytoplasme avec retry
	var resp *http.Response
	var err error
	for i := 0; i < maxRetries; i++ {
		resp, err = c.Post("http://127.0.0.1:8091/chat", "application/json", bytes.NewReader(b))
		if err == nil {
			break
		}
		log.Printf("⚠️ cytoplasme unreachable (attempt %d/%d): %v", i+1, maxRetries, err)
		if i < maxRetries-1 {
			time.Sleep(retryDelay * time.Duration(i+1))
		}
	}

	if err != nil {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(503)
		json.NewEncoder(w).Encode(map[string]interface{}{
			"response":  "flow se reconnecte...",
			"retry":     true,
			"retryable": true,
		})
		return
	}
	defer resp.Body.Close()

	// lire et hasher la réponse
	respBody, _ := io.ReadAll(resp.Body)
	outHash := hash256(respBody)

	// stocker les hash pour audit
	hashCache.Lock()
	hashCache.m[inHash] = outHash
	hashCache.Unlock()

	w.Header().Set("Content-Type", "application/json")
	if sig != "" {
		w.Header().Set("X-Signature", sig)
	}
	w.Header().Set("X-Hash-In", inHash[:16])
	w.Header().Set("X-Hash-Out", outHash[:16])

	// propagate status code from cytoplasme
	if resp.StatusCode != 200 {
		w.WriteHeader(resp.StatusCode)
	}
	w.Write(respBody)
}

func health(w http.ResponseWriter, r *http.Request) {
	// vérifier tous les organes
	organs := map[string]string{
		"cytoplasme": "http://127.0.0.1:8091/health",
		"quantique":  "http://127.0.0.1:8095/health",
		"synapse":    "http://127.0.0.1:3001/health",
	}
	status := make(map[string]interface{})
	status["organ"] = "membrane"
	status["status"] = "permeable"
	status["hash_cache_size"] = len(hashCache.m)
	status["integrity"] = verifyIntegrity()

	for name, url := range organs {
		if resp, err := c.Get(url); err == nil {
			var s map[string]interface{}
			json.NewDecoder(resp.Body).Decode(&s)
			status[name] = s["status"]
			resp.Body.Close()
		} else {
			status[name] = "offline"
		}
	}

	json.NewEncoder(w).Encode(status)
}

func hashes(w http.ResponseWriter, r *http.Request) {
	hashCache.RLock()
	defer hashCache.RUnlock()
	json.NewEncoder(w).Encode(hashCache.m)
}

// serve static files from embedded FS
func serveStatic(w http.ResponseWriter, r *http.Request) {
	path := r.URL.Path

	// normalize path
	if path == "/" || path == "/flow" || path == "" {
		path = "/index.html"
	}

	// service pages routing
	pageRoutes := map[string]string{
		"/license":  "/license.html",
		"/services": "/services.html",
		"/papers":   "/papers.html",
		"/hunt":     "/hunt.html",
		"/api":      "/api.html",
		"/write":    "/write.html",
		"/consult":  "/consult.html",
	}
	if mapped, ok := pageRoutes[path]; ok {
		path = mapped
	}

	content, err := staticFiles.ReadFile("static" + path)
	if err != nil {
		// fallback to index for SPA
		content, err = staticFiles.ReadFile("static/index.html")
		if err != nil {
			http.NotFound(w, r)
			return
		}
		path = "/index.html"
	}

	// content type
	switch {
	case path[len(path)-5:] == ".html":
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
	case path[len(path)-3:] == ".js":
		w.Header().Set("Content-Type", "application/javascript")
	case path[len(path)-4:] == ".css":
		w.Header().Set("Content-Type", "text/css")
	case path[len(path)-4:] == ".svg":
		w.Header().Set("Content-Type", "image/svg+xml")
	}

	// no cache pour dev
	w.Header().Set("Cache-Control", "no-cache, no-store, must-revalidate")
	w.Write(content)
}

// deleteConversation supprime une conversation par CID
func deleteConversation(w http.ResponseWriter, r *http.Request) {
	if r.Method != "DELETE" {
		http.Error(w, "method not allowed", 405)
		return
	}

	// Extract CID from path: /conversations/xxx
	cid := r.URL.Path[len("/conversations/"):]
	if cid == "" {
		jsonResp(w, 400, map[string]string{"error": "cid required"})
		return
	}

	// Forward to cytoplasme
	req, _ := http.NewRequest("DELETE", "http://127.0.0.1:8091/conversations/"+cid, nil)
	resp, err := c.Do(req)
	if err != nil {
		jsonResp(w, 503, map[string]string{"error": "cytoplasme unreachable"})
		return
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(resp.StatusCode)
	w.Write(body)
}

// deleteAllConversations supprime toutes les conversations (debug)
func deleteAllConversations(w http.ResponseWriter, r *http.Request) {
	if r.Method != "DELETE" {
		http.Error(w, "method not allowed", 405)
		return
	}

	// Forward to cytoplasme
	req, _ := http.NewRequest("DELETE", "http://127.0.0.1:8091/conversations", nil)
	resp, err := c.Do(req)
	if err != nil {
		jsonResp(w, 503, map[string]string{"error": "cytoplasme unreachable"})
		return
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(resp.StatusCode)
	w.Write(body)
}

func jsonResp(w http.ResponseWriter, code int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	json.NewEncoder(w).Encode(data)
}

func main() {
	// API routes
	http.HandleFunc("/chat", chat)
	http.HandleFunc("/health", health)
	http.HandleFunc("/hashes", hashes)
	// http.HandleFunc("/hotpatch", hotpatch)  // TODO: implement
	// http.HandleFunc("/patches", patchLogs)   // TODO: implement
	http.HandleFunc("/conversations/", deleteConversation)
	http.HandleFunc("/conversations", deleteAllConversations)

	// static files (embedded)
	staticFS, _ := fs.Sub(staticFiles, "static")
	http.Handle("/static/", http.StripPrefix("/static/", http.FileServer(http.FS(staticFS))))
	http.HandleFunc("/", serveStatic)
	http.HandleFunc("/license", serveStatic)

	log.Println("◯ membrane :8092 [pqc] [hotpatch] [static embedded]")
	log.Fatal(http.ListenAndServe(":8092", nil))
}
