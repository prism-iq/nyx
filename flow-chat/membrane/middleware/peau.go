package main

import (
    "net"
    "net/http"
    "strings"
    "time"
    "sync"
)

// PEAU - Première barrière de défense
type Peau struct {
    AllowedIPs    []string
    BlockedIPs    map[string]time.Time
    RecentHits    map[string][]time.Time
    mutex         sync.RWMutex
}

// IPs autorisées (tes 2 ordis)
var peau = &Peau{
    AllowedIPs: []string{
        // À compléter avec tes vraies IPs
        "192.168.1.0/24",  // réseau local probable
        "127.0.0.1",       // localhost
        "::1",             // localhost IPv6
    },
    BlockedIPs: make(map[string]time.Time),
    RecentHits: make(map[string][]time.Time),
}

func (p *Peau) CheckAccess(r *http.Request) bool {
    clientIP := getClientIP(r)
    
    p.mutex.RLock()
    
    // Check si IP bloquée
    if blockTime, blocked := p.BlockedIPs[clientIP]; blocked {
        if time.Since(blockTime) < 24*time.Hour {
            p.mutex.RUnlock()
            return false // Encore bloqué
        }
        // Débloquer après 24h
        delete(p.BlockedIPs, clientIP)
    }
    
    p.mutex.RUnlock()
    
    // Check IP autorisée
    if !p.isIPAllowed(clientIP) {
        p.recordSuspiciousActivity(clientIP)
        return false
    }
    
    // Check rate limiting
    if p.isRateLimited(clientIP) {
        p.blockIP(clientIP)
        return false
    }
    
    p.recordHit(clientIP)
    return true
}

func (p *Peau) isIPAllowed(ip string) bool {
    clientIP := net.ParseIP(ip)
    if clientIP == nil {
        return false
    }
    
    for _, allowedCIDR := range p.AllowedIPs {
        if strings.Contains(allowedCIDR, "/") {
            _, network, err := net.ParseCIDR(allowedCIDR)
            if err == nil && network.Contains(clientIP) {
                return true
            }
        } else {
            if allowedCIDR == ip {
                return true
            }
        }
    }
    return false
}

func (p *Peau) recordHit(ip string) {
    p.mutex.Lock()
    defer p.mutex.Unlock()
    
    now := time.Now()
    if p.RecentHits[ip] == nil {
        p.RecentHits[ip] = []time.Time{}
    }
    p.RecentHits[ip] = append(p.RecentHits[ip], now)
    
    // Cleanup old hits (garder seulement dernière heure)
    cutoff := now.Add(-time.Hour)
    filtered := []time.Time{}
    for _, hit := range p.RecentHits[ip] {
        if hit.After(cutoff) {
            filtered = append(filtered, hit)
        }
    }
    p.RecentHits[ip] = filtered
}

func (p *Peau) isRateLimited(ip string) bool {
    p.mutex.RLock()
    defer p.mutex.RUnlock()
    
    hits, exists := p.RecentHits[ip]
    if !exists {
        return false
    }
    
    // Plus de 100 requêtes/heure = suspect
    return len(hits) > 100
}

func (p *Peau) blockIP(ip string) {
    p.mutex.Lock()
    defer p.mutex.Unlock()
    
    p.BlockedIPs[ip] = time.Now()
    
    // Notification aux anticorps
    go notifyAnticorps("IP_BLOCKED", map[string]interface{}{
        "ip": ip,
        "reason": "rate_limit_exceeded",
        "timestamp": time.Now(),
    })
}

func (p *Peau) recordSuspiciousActivity(ip string) {
    go notifyAnticorps("SUSPICIOUS_ACCESS", map[string]interface{}{
        "ip": ip,
        "reason": "ip_not_whitelisted",
        "timestamp": time.Now(),
    })
}

func getClientIP(r *http.Request) string {
    // Check X-Forwarded-For (si derrière proxy)
    forwarded := r.Header.Get("X-Forwarded-For")
    if forwarded != "" {
        return strings.Split(forwarded, ",")[0]
    }
    
    // Check X-Real-IP
    realIP := r.Header.Get("X-Real-IP")
    if realIP != "" {
        return realIP
    }
    
    // Fallback sur RemoteAddr
    ip, _, _ := net.SplitHostPort(r.RemoteAddr)
    return ip
}

// Middleware HTTP
func PeauMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        if !peau.CheckAccess(r) {
            // 404 pour masquer l'existence
            http.NotFound(w, r)
            return
        }
        next.ServeHTTP(w, r)
    })
}

func notifyAnticorps(eventType string, data map[string]interface{}) {
    // POST vers anticorps:8097
    // Implementation à compléter
}