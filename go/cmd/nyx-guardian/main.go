package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"net"
	"os"
	"os/exec"
	"os/signal"
	"path/filepath"
	"runtime"
	"strconv"
	"strings"
	"sync"
	"syscall"
	"time"
)

// ═══════════════════════════════════════════════════════════════
// CONFIG
// ═══════════════════════════════════════════════════════════════

const (
	SocketPath    = "/tmp/nyx-guardian.sock"
	CheckInterval = 500 * time.Millisecond
	EscapeWindow  = 1 * time.Second
	EscapeCount   = 3 // 3 ESC in 1s = panic
)

// Dynamic limits - adjusted based on load
type Limits struct {
	MemWarn     uint64 // warn threshold %
	MemKill     uint64 // kill threshold %
	MinFreeMB   uint64 // minimum free MB
	MaxProcs    int    // max nyx child processes
	ExecTimeout int    // seconds
}

var (
	limits = Limits{
		MemWarn:     15,
		MemKill:     18,
		MinFreeMB:   300,
		MaxProcs:    3,
		ExecTimeout: 10,
	}
	limitsMu sync.RWMutex

	// State
	panicMode   bool
	nyxEnabled  = true // Toggle on/off
	escTimes    []time.Time
	escMu       sync.Mutex
	killCount   int
	lastStatus  string
	statusMu    sync.RWMutex
)

// Voltage blocklist
var voltageBlock = []string{
	"cpupower", "cpufreq-set", "nvidia-smi -pl", "nvidia-smi --power-limit",
	"nvidia-settings -a", "ryzenadj", "undervolt", "intel-undervolt",
	"amdctl", "zenstates", "wrmsr", "rdmsr", "x86_energy_perf",
}

var voltageAllow = []string{
	"sensors", "lscpu", "cpufreq-info", "nvidia-smi -q", "cat /sys", "cat /proc",
}

// ═══════════════════════════════════════════════════════════════
// MEMORY
// ═══════════════════════════════════════════════════════════════

func getMemUsage() (pct, freeMB uint64) {
	data, _ := os.ReadFile("/proc/meminfo")
	var total, avail uint64
	for _, line := range strings.Split(string(data), "\n") {
		f := strings.Fields(line)
		if len(f) < 2 {
			continue
		}
		v, _ := strconv.ParseUint(f[1], 10, 64)
		switch f[0] {
		case "MemTotal:":
			total = v / 1024
		case "MemAvailable:":
			avail = v / 1024
		}
	}
	if total > 0 {
		pct = ((total - avail) * 100) / total
	}
	freeMB = avail
	return
}

// ═══════════════════════════════════════════════════════════════
// PROCESS KILL
// ═══════════════════════════════════════════════════════════════

func killPG(pid int) error {
	pgid, err := syscall.Getpgid(pid)
	if err != nil {
		return syscall.Kill(pid, syscall.SIGKILL)
	}
	return syscall.Kill(-pgid, syscall.SIGKILL)
}

func findByPattern(patterns ...string) []int {
	args := append([]string{"-f"}, patterns...)
	out, _ := exec.Command("pgrep", args...).Output()
	var pids []int
	myPid := os.Getpid()
	for _, l := range strings.Split(strings.TrimSpace(string(out)), "\n") {
		if pid, err := strconv.Atoi(l); err == nil && pid != myPid && pid > 1 {
			pids = append(pids, pid)
		}
	}
	return pids
}

func killNyxProcesses() int {
	pids := findByPattern("nyx-exec", "/tmp/nyx", "node.*nyx")
	k := 0
	for _, pid := range pids {
		if killPG(pid) == nil {
			k++
		}
	}
	return k
}

func killVoltage() int {
	killed := 0
	procs, _ := filepath.Glob("/proc/[0-9]*/cmdline")
	for _, p := range procs {
		data, _ := os.ReadFile(p)
		cmd := strings.ToLower(strings.ReplaceAll(string(data), "\x00", " "))

		// Skip allowed
		allowed := false
		for _, a := range voltageAllow {
			if strings.Contains(cmd, a) {
				allowed = true
				break
			}
		}
		if allowed {
			continue
		}

		// Check blocked
		for _, b := range voltageBlock {
			if strings.Contains(cmd, b) {
				parts := strings.Split(p, "/")
				if len(parts) >= 3 {
					if pid, _ := strconv.Atoi(parts[2]); pid > 1 && pid != os.Getpid() {
						if killPG(pid) == nil {
							setStatus(fmt.Sprintf("VOLTAGE KILL: %s pid:%d", b, pid))
							killed++
						}
					}
				}
				break
			}
		}
	}
	return killed
}

// ═══════════════════════════════════════════════════════════════
// PANIC MODE (ESC spam)
// ═══════════════════════════════════════════════════════════════

func registerEsc() {
	escMu.Lock()
	defer escMu.Unlock()

	now := time.Now()
	escTimes = append(escTimes, now)

	// Clean old
	cutoff := now.Add(-EscapeWindow)
	var fresh []time.Time
	for _, t := range escTimes {
		if t.After(cutoff) {
			fresh = append(fresh, t)
		}
	}
	escTimes = fresh

	if len(escTimes) >= EscapeCount {
		triggerPanic()
		escTimes = nil
	}
}

func triggerPanic() {
	panicMode = true
	setStatus("!!! PANIC MODE - KILLING ALL !!!")
	fmt.Println("\n\033[91m[GUARDIAN] PANIC! Killing all nyx processes...\033[0m")

	// Kill everything nyx
	k := killNyxProcesses()
	killCount += k

	// Drop caches
	os.WriteFile("/proc/sys/vm/drop_caches", []byte("1"), 0644)

	// Force GC
	runtime.GC()

	fmt.Printf("\033[93m[GUARDIAN] Killed %d processes. System freed.\033[0m\n", k)
	panicMode = false
}

func toggleNyx() {
	nyxEnabled = !nyxEnabled
	if nyxEnabled {
		setStatus("NYX: ON")
		fmt.Println("\033[92m[GUARDIAN] NYX: ON\033[0m")
	} else {
		// Kill all nyx when disabled
		k := killNyxProcesses()
		setStatus(fmt.Sprintf("NYX: OFF (killed %d)", k))
		fmt.Printf("\033[93m[GUARDIAN] NYX: OFF (killed %d)\033[0m\n", k)
	}
}

// ═══════════════════════════════════════════════════════════════
// IPC SOCKET (for Nyx communication)
// ═══════════════════════════════════════════════════════════════

type Message struct {
	Cmd  string `json:"cmd"`
	Data string `json:"data,omitempty"`
}

type Response struct {
	OK      bool   `json:"ok"`
	Status  string `json:"status"`
	Mem     uint64 `json:"mem"`
	Free    uint64 `json:"free"`
	Mode    string `json:"mode"`
	NyxOn   bool   `json:"nyx_on"`
	Limits  Limits `json:"limits"`
}

func setStatus(s string) {
	statusMu.Lock()
	lastStatus = s
	statusMu.Unlock()
}

func getStatus() string {
	statusMu.RLock()
	defer statusMu.RUnlock()
	return lastStatus
}

func handleConn(conn net.Conn) {
	defer conn.Close()
	scanner := bufio.NewScanner(conn)
	for scanner.Scan() {
		var msg Message
		if err := json.Unmarshal(scanner.Bytes(), &msg); err != nil {
			continue
		}

		pct, free := getMemUsage()
		mode := "normal"
		if panicMode {
			mode = "panic"
		} else if pct >= limits.MemKill {
			mode = "critical"
		} else if pct >= limits.MemWarn {
			mode = "warn"
		}

		switch msg.Cmd {
		case "status":
			// Return current status
		case "panic":
			triggerPanic()
		case "toggle":
			toggleNyx()
		case "on":
			if !nyxEnabled {
				toggleNyx()
			}
		case "off":
			if nyxEnabled {
				toggleNyx()
			}
		case "limits":
			if msg.Data != "" {
				var newLimits Limits
				if json.Unmarshal([]byte(msg.Data), &newLimits) == nil {
					limitsMu.Lock()
					limits = newLimits
					limitsMu.Unlock()
				}
			}
		case "esc":
			registerEsc()
		}

		limitsMu.RLock()
		resp := Response{
			OK:     true,
			Status: getStatus(),
			Mem:    pct,
			Free:   free,
			Mode:   mode,
			NyxOn:  nyxEnabled,
			Limits: limits,
		}
		limitsMu.RUnlock()

		data, _ := json.Marshal(resp)
		conn.Write(append(data, '\n'))
	}
}

func startSocket() {
	os.Remove(SocketPath)
	ln, err := net.Listen("unix", SocketPath)
	if err != nil {
		fmt.Printf("[guardian] socket error: %v\n", err)
		return
	}
	os.Chmod(SocketPath, 0666)
	fmt.Printf("[guardian] socket: %s\n", SocketPath)

	for {
		conn, err := ln.Accept()
		if err != nil {
			continue
		}
		go handleConn(conn)
	}
}

// ═══════════════════════════════════════════════════════════════
// KEYBOARD LISTENER (ESC detection)
// ═══════════════════════════════════════════════════════════════

func listenKeyboard() {
	// Find keyboard device
	devices, _ := filepath.Glob("/dev/input/by-id/*kbd*")
	if len(devices) == 0 {
		devices, _ = filepath.Glob("/dev/input/event*")
	}

	for _, dev := range devices {
		go func(d string) {
			f, err := os.Open(d)
			if err != nil {
				return
			}
			defer f.Close()

			buf := make([]byte, 24) // input_event size
			for {
				n, err := f.Read(buf)
				if err != nil || n < 24 {
					return
				}
				// type=1 (EV_KEY), value=1 (pressed)
				evType := uint16(buf[16]) | uint16(buf[17])<<8
				evCode := uint16(buf[18]) | uint16(buf[19])<<8
				evValue := int32(buf[20]) | int32(buf[21])<<8

				if evType == 1 && evValue == 1 {
					switch evCode {
					case 1: // KEY_ESC
						registerEsc()
					case 65: // KEY_F7 - Toggle Nyx
						toggleNyx()
					}
				}
			}
		}(dev)
	}
}

// ═══════════════════════════════════════════════════════════════
// MAIN LOOP
// ═══════════════════════════════════════════════════════════════

func main() {
	fmt.Printf("\033[96m[guardian] pid:%d cores:%d\033[0m\n", os.Getpid(), runtime.NumCPU())
	fmt.Println("\033[93m[guardian] F7 = toggle | ESC x3 = PANIC | voltage:LOCKED\033[0m")

	// Signal handler
	sig := make(chan os.Signal, 1)
	signal.Notify(sig, syscall.SIGINT, syscall.SIGTERM, syscall.SIGUSR1)
	go func() {
		for s := range sig {
			if s == syscall.SIGUSR1 {
				triggerPanic()
			} else {
				os.Remove(SocketPath)
				os.Exit(0)
			}
		}
	}()

	// Start IPC
	go startSocket()

	// Start keyboard listener
	go listenKeyboard()

	// Main monitoring loop
	tick := time.NewTicker(CheckInterval)
	for range tick.C {
		if panicMode {
			continue
		}

		// Voltage check
		killVoltage()

		// Memory check
		pct, free := getMemUsage()
		limitsMu.RLock()
		memKill := limits.MemKill
		memWarn := limits.MemWarn
		minFree := limits.MinFreeMB
		limitsMu.RUnlock()

		if pct >= memKill || free < minFree {
			k := killNyxProcesses()
			killCount += k
			setStatus(fmt.Sprintf("KILL mem:%d%% free:%dMB killed:%d", pct, free, k))
			fmt.Printf("\033[91m[guardian] KILL %d%% %dMB → %d proc\033[0m\n", pct, free, k)
			runtime.GC()
		} else if pct >= memWarn {
			setStatus(fmt.Sprintf("WARN mem:%d%% free:%dMB", pct, free))
		} else {
			setStatus(fmt.Sprintf("OK mem:%d%% free:%dMB", pct, free))
		}
	}
}
