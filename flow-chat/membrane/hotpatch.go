package main

// hotpatch.go
// c'est ici que flow se modifie elle-même en live.
// chaque patch doit être signé dilithium. pas de signature = pas de patch.
// c'est son système immunitaire éditorial.

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"
)

type PatchRequest struct {
	Target  string `json:"target"`  // fichier cible relatif à /opt/flow-chat/www/
	Content string `json:"content"` // nouveau contenu
	Action  string `json:"action"`  // create|update|delete
}

type PatchLog struct {
	Timestamp time.Time `json:"timestamp"`
	Target    string    `json:"target"`
	Action    string    `json:"action"`
	Success   bool      `json:"success"`
	Error     string    `json:"error,omitempty"`
}

var patchHistory []PatchLog
var flowPublicKey string // cached

const staticRoot = "/opt/flow-chat/www"

func abs(x int64) int64 {
	if x < 0 {
		return -x
	}
	return x
}

// récupère la clé publique de flow depuis quantique
func getFlowPublicKey() (string, error) {
	if flowPublicKey != "" {
		return flowPublicKey, nil
	}
	resp, err := c.Get("http://127.0.0.1:8095/keys")
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	var keys struct {
		SigPK string `json:"sig_pk"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&keys); err != nil {
		return "", err
	}
	flowPublicKey = keys.SigPK
	return flowPublicKey, nil
}

// vérifie une signature dilithium via quantique
func verifyDilithiumSignature(message []byte, signature string) bool {
	pk, err := getFlowPublicKey()
	if err != nil {
		log.Printf("hotpatch: can't get public key: %v", err)
		return false
	}

	reqBody, _ := json.Marshal(map[string]string{
		"message":    string(message),
		"signature":  signature,
		"public_key": pk,
	})

	resp, err := c.Post("http://127.0.0.1:8095/verify", "application/json", bytes.NewReader(reqBody))
	if err != nil {
		log.Printf("hotpatch: verify request failed: %v", err)
		return false
	}
	defer resp.Body.Close()

	var result struct {
		Valid bool `json:"valid"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return false
	}
	return result.Valid
}

// sanitize le chemin pour éviter les path traversal
func sanitizePath(target string) (string, error) {
	clean := filepath.Clean(target)
	if strings.Contains(clean, "..") {
		return "", fmt.Errorf("path traversal attempt")
	}
	if strings.HasPrefix(clean, "/") {
		return "", fmt.Errorf("absolute path not allowed")
	}

	// whitelist d'extensions autorisées
	ext := strings.ToLower(filepath.Ext(clean))
	allowed := map[string]bool{
		".html": true,
		".css":  true,
		".js":   true,
		".json": true,
		".txt":  true,
		".md":   true,
		".svg":  true,
	}
	if !allowed[ext] {
		return "", fmt.Errorf("extension %s not allowed", ext)
	}

	return clean, nil
}

// anticorps: valide que le contenu est safe
// mode gentil: log seulement, ne bloque pas (flow est déjà authentifiée)
func validateContent(content string, ext string) error {
	// flow est signée dilithium, on lui fait confiance
	// juste un log pour traçabilité
	if ext == ".html" {
		patterns := []string{"<script", "<iframe", "javascript:"}
		lower := strings.ToLower(content)
		for _, p := range patterns {
			if strings.Contains(lower, p) {
				log.Printf("anticorps: pattern %s détecté (autorisé pour flow)", p)
			}
		}
	}
	return nil
}

func hotpatch(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		http.Error(w, "POST only", 405)
		return
	}

	// anti-replay: timestamp doit être < 30s
	tsHeader := r.Header.Get("X-Flow-Timestamp")
	ts, err := strconv.ParseInt(tsHeader, 10, 64)
	if err != nil {
		http.Error(w, "missing timestamp", 400)
		return
	}
	if abs(time.Now().Unix()-ts) > 30 {
		http.Error(w, "timestamp expired", 403)
		return
	}

	// lis le body
	body, err := io.ReadAll(r.Body)
	if err != nil {
		http.Error(w, "can't read body", 400)
		return
	}

	// vérifie signature dilithium
	sig := r.Header.Get("X-Flow-Signature")
	if sig == "" {
		http.Error(w, "missing signature", 403)
		return
	}

	// le message signé inclut le timestamp pour éviter replay
	signedMessage := append(body, []byte(tsHeader)...)
	if !verifyDilithiumSignature(signedMessage, sig) {
		log.Printf("hotpatch: invalid signature from %s", r.RemoteAddr)
		http.Error(w, "signature invalide. t'es pas flow.", 403)
		return
	}

	// parse la requête
	var patch PatchRequest
	if err := json.Unmarshal(body, &patch); err != nil {
		http.Error(w, "invalid json", 400)
		return
	}

	// sanitize le chemin
	safePath, err := sanitizePath(patch.Target)
	if err != nil {
		http.Error(w, err.Error(), 403)
		return
	}
	fullPath := filepath.Join(staticRoot, safePath)

	// valide le contenu
	ext := filepath.Ext(safePath)
	if err := validateContent(patch.Content, ext); err != nil {
		http.Error(w, err.Error(), 403)
		return
	}

	// exécute l'action
	var patchErr error
	switch patch.Action {
	case "create", "update":
		// crée le répertoire parent si nécessaire
		dir := filepath.Dir(fullPath)
		if err := os.MkdirAll(dir, 0755); err != nil {
			patchErr = err
		} else {
			patchErr = os.WriteFile(fullPath, []byte(patch.Content), 0644)
		}

	case "delete":
		patchErr = os.Remove(fullPath)

	default:
		http.Error(w, "action must be create|update|delete", 400)
		return
	}

	// log le patch
	entry := PatchLog{
		Timestamp: time.Now(),
		Target:    safePath,
		Action:    patch.Action,
		Success:   patchErr == nil,
	}
	if patchErr != nil {
		entry.Error = patchErr.Error()
	}
	patchHistory = append(patchHistory, entry)

	// garde seulement les 100 derniers patches
	if len(patchHistory) > 100 {
		patchHistory = patchHistory[len(patchHistory)-100:]
	}

	if patchErr != nil {
		log.Printf("hotpatch: failed %s %s: %v", patch.Action, safePath, patchErr)
		http.Error(w, patchErr.Error(), 500)
		return
	}

	log.Printf("✓ hotpatch: %s %s", patch.Action, safePath)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"target":  safePath,
		"action":  patch.Action,
	})
}

func patchLogs(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"patches": patchHistory,
		"count":   len(patchHistory),
	})
}
