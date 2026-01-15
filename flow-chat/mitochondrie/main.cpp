// mitochondrie.cpp - énergie, métriques système real-time, C++20
// CPU / RAM / Network / Disk monitoring pour Flow

#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <atomic>
#include <chrono>
#include <thread>
#include <mutex>
#include <vector>
#include <sys/socket.h>
#include <sys/sysinfo.h>
#include <sys/statvfs.h>
#include <netinet/in.h>
#include <unistd.h>
#include <cstring>
#include <dirent.h>

// === ENERGY METRICS (API usage) ===
struct EnergyMetrics {
    std::atomic<uint64_t> requests{0};
    std::atomic<uint64_t> cache_hits{0};
    std::atomic<uint64_t> llm_calls{0};
    std::atomic<double> total_latency{0.0};

    void record(bool cache_hit, double latency_ms) {
        requests++;
        if (cache_hit) cache_hits++;
        else llm_calls++;
        // atomic double workaround
        double old_val = total_latency.load();
        while (!total_latency.compare_exchange_weak(old_val, old_val + latency_ms));
    }

    double efficiency() const {
        auto r = requests.load();
        return r == 0 ? 0.0 : static_cast<double>(cache_hits.load()) / r;
    }

    double avg_latency() const {
        auto r = requests.load();
        return r == 0 ? 0.0 : total_latency.load() / r;
    }
};

// === SYSTEM METRICS ===
struct CpuInfo {
    unsigned long long user, nice, system, idle, iowait, irq, softirq;
};

struct SystemMetrics {
    std::mutex mtx;

    // CPU
    CpuInfo prev_cpu{};
    double cpu_percent{0.0};
    int cpu_cores{0};
    double load_avg[3]{0.0, 0.0, 0.0};

    // Memory
    unsigned long total_ram{0};
    unsigned long free_ram{0};
    unsigned long used_ram{0};
    double ram_percent{0.0};
    unsigned long total_swap{0};
    unsigned long free_swap{0};

    // Network
    unsigned long long rx_bytes{0};
    unsigned long long tx_bytes{0};
    unsigned long long prev_rx{0};
    unsigned long long prev_tx{0};
    double rx_rate{0.0};  // bytes/sec
    double tx_rate{0.0};

    // Disk
    unsigned long disk_total{0};
    unsigned long disk_free{0};
    double disk_percent{0.0};

    // Processes
    int process_count{0};
    int thread_count{0};

    SystemMetrics() {
        cpu_cores = sysconf(_SC_NPROCESSORS_ONLN);
        update();
    }

    void update() {
        std::lock_guard<std::mutex> lock(mtx);
        update_cpu();
        update_memory();
        update_network();
        update_disk();
        update_processes();
    }

    void update_cpu() {
        std::ifstream stat("/proc/stat");
        std::string line;
        if (std::getline(stat, line) && line.substr(0, 3) == "cpu") {
            CpuInfo curr{};
            sscanf(line.c_str(), "cpu %llu %llu %llu %llu %llu %llu %llu",
                   &curr.user, &curr.nice, &curr.system, &curr.idle,
                   &curr.iowait, &curr.irq, &curr.softirq);

            auto prev_total = prev_cpu.user + prev_cpu.nice + prev_cpu.system +
                              prev_cpu.idle + prev_cpu.iowait + prev_cpu.irq + prev_cpu.softirq;
            auto curr_total = curr.user + curr.nice + curr.system +
                              curr.idle + curr.iowait + curr.irq + curr.softirq;
            auto total_diff = curr_total - prev_total;
            auto idle_diff = (curr.idle + curr.iowait) - (prev_cpu.idle + prev_cpu.iowait);

            if (total_diff > 0) {
                cpu_percent = 100.0 * (1.0 - static_cast<double>(idle_diff) / total_diff);
            }
            prev_cpu = curr;
        }

        // Load average
        std::ifstream loadavg("/proc/loadavg");
        if (loadavg) {
            loadavg >> load_avg[0] >> load_avg[1] >> load_avg[2];
        }
    }

    void update_memory() {
        struct sysinfo si;
        if (sysinfo(&si) == 0) {
            total_ram = si.totalram * si.mem_unit / (1024 * 1024);  // MB
            free_ram = si.freeram * si.mem_unit / (1024 * 1024);

            // Get actual available memory from /proc/meminfo
            std::ifstream meminfo("/proc/meminfo");
            std::string line;
            unsigned long available = 0, buffers = 0, cached = 0;
            while (std::getline(meminfo, line)) {
                if (line.find("MemAvailable:") == 0) {
                    sscanf(line.c_str(), "MemAvailable: %lu", &available);
                    available /= 1024;  // KB to MB
                } else if (line.find("Buffers:") == 0) {
                    sscanf(line.c_str(), "Buffers: %lu", &buffers);
                } else if (line.find("Cached:") == 0 && line.find("SwapCached") == std::string::npos) {
                    sscanf(line.c_str(), "Cached: %lu", &cached);
                }
            }

            if (available > 0) {
                used_ram = total_ram - available;
            } else {
                used_ram = total_ram - free_ram - (buffers + cached) / 1024;
            }
            ram_percent = total_ram > 0 ? 100.0 * used_ram / total_ram : 0.0;

            total_swap = si.totalswap * si.mem_unit / (1024 * 1024);
            free_swap = si.freeswap * si.mem_unit / (1024 * 1024);
        }
    }

    void update_network() {
        std::ifstream net("/proc/net/dev");
        std::string line;
        unsigned long long total_rx = 0, total_tx = 0;

        while (std::getline(net, line)) {
            // Skip header lines
            if (line.find(':') == std::string::npos) continue;
            if (line.find("lo:") != std::string::npos) continue;  // Skip loopback

            unsigned long long rx, tx;
            char iface[32];
            if (sscanf(line.c_str(), " %31[^:]: %llu %*u %*u %*u %*u %*u %*u %*u %llu",
                       iface, &rx, &tx) >= 3) {
                total_rx += rx;
                total_tx += tx;
            }
        }

        // Calculate rate (assuming ~1 second between updates)
        if (prev_rx > 0) {
            rx_rate = (total_rx > prev_rx) ? (total_rx - prev_rx) : 0;
            tx_rate = (total_tx > prev_tx) ? (total_tx - prev_tx) : 0;
        }
        prev_rx = rx_bytes = total_rx;
        prev_tx = tx_bytes = total_tx;
    }

    void update_disk() {
        struct statvfs stat;
        if (statvfs("/", &stat) == 0) {
            disk_total = (stat.f_blocks * stat.f_frsize) / (1024ULL * 1024 * 1024);  // GB
            disk_free = (stat.f_bavail * stat.f_frsize) / (1024ULL * 1024 * 1024);
            disk_percent = disk_total > 0 ? 100.0 * (disk_total - disk_free) / disk_total : 0.0;
        }
    }

    void update_processes() {
        process_count = 0;
        thread_count = 0;

        DIR* proc = opendir("/proc");
        if (proc) {
            struct dirent* entry;
            while ((entry = readdir(proc))) {
                // Only count numeric directories (PIDs)
                if (entry->d_type == DT_DIR && isdigit(entry->d_name[0])) {
                    process_count++;

                    // Count threads from /proc/[pid]/task
                    std::string task_path = std::string("/proc/") + entry->d_name + "/task";
                    DIR* task = opendir(task_path.c_str());
                    if (task) {
                        struct dirent* t;
                        while ((t = readdir(task))) {
                            if (t->d_name[0] != '.') thread_count++;
                        }
                        closedir(task);
                    }
                }
            }
            closedir(proc);
        }
    }

    std::string to_json() const {
        std::ostringstream ss;
        ss << std::fixed;
        ss.precision(2);
        ss << R"({"cpu":{"percent":)" << cpu_percent
           << R"(,"cores":)" << cpu_cores
           << R"(,"load":[)" << load_avg[0] << "," << load_avg[1] << "," << load_avg[2] << "]}";
        ss << R"(,"memory":{"total_mb":)" << total_ram
           << R"(,"used_mb":)" << used_ram
           << R"(,"percent":)" << ram_percent
           << R"(,"swap_total_mb":)" << total_swap
           << R"(,"swap_free_mb":)" << free_swap << "}";
        ss << R"(,"network":{"rx_bytes":)" << rx_bytes
           << R"(,"tx_bytes":)" << tx_bytes
           << R"(,"rx_rate":)" << rx_rate
           << R"(,"tx_rate":)" << tx_rate << "}";
        ss << R"(,"disk":{"total_gb":)" << disk_total
           << R"(,"free_gb":)" << disk_free
           << R"(,"percent":)" << disk_percent << "}";
        ss << R"(,"processes":{"count":)" << process_count
           << R"(,"threads":)" << thread_count << "}}";
        return ss.str();
    }
};

// === GLOBALS ===
static EnergyMetrics energy;
static SystemMetrics sys_metrics;
static std::atomic<bool> running{true};

// === BACKGROUND UPDATER ===
void metrics_updater() {
    while (running) {
        sys_metrics.update();
        std::this_thread::sleep_for(std::chrono::seconds(1));
    }
}

// === HTTP HANDLER ===
void handle_request(int client) {
    char buf[8192];
    memset(buf, 0, sizeof(buf));
    read(client, buf, sizeof(buf) - 1);

    std::string req(buf);
    std::string response;
    std::string body;
    int status = 200;

    // CORS preflight
    if (req.find("OPTIONS") == 0) {
        response = "HTTP/1.1 200 OK\r\n"
                   "Access-Control-Allow-Origin: *\r\n"
                   "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
                   "Access-Control-Allow-Headers: Content-Type\r\n"
                   "Content-Length: 0\r\n\r\n";
        write(client, response.c_str(), response.size());
        close(client);
        return;
    }

    // Route: POST /record
    if (req.find("POST") == 0 && req.find("/record") != std::string::npos) {
        bool cache_hit = req.find("\"cache_hit\":true") != std::string::npos;
        double latency = 50.0;
        auto pos = req.find("\"latency\":");
        if (pos != std::string::npos) {
            try { latency = std::stod(req.substr(pos + 10)); } catch (...) {}
        }
        energy.record(cache_hit, latency);
        body = R"({"recorded":true})";
    }
    // Route: GET /system
    else if (req.find("GET /system") != std::string::npos) {
        body = sys_metrics.to_json();
    }
    // Route: GET /energy
    else if (req.find("GET /energy") != std::string::npos) {
        std::ostringstream ss;
        ss << R"({"requests":)" << energy.requests.load()
           << R"(,"cache_hits":)" << energy.cache_hits.load()
           << R"(,"llm_calls":)" << energy.llm_calls.load()
           << R"(,"efficiency":)" << energy.efficiency()
           << R"(,"avg_latency_ms":)" << energy.avg_latency() << "}";
        body = ss.str();
    }
    // Route: GET /health or GET /
    else if (req.find("GET /health") != std::string::npos ||
             (req.find("GET /") != std::string::npos && req.find("GET / ") != std::string::npos)) {
        std::ostringstream ss;
        ss << R"({"organ":"mitochondrie","status":"powered")"
           << R"(,"requests":)" << energy.requests.load()
           << R"(,"cache_hits":)" << energy.cache_hits.load()
           << R"(,"llm_calls":)" << energy.llm_calls.load()
           << R"(,"efficiency":)" << energy.efficiency()
           << R"(,"avg_latency_ms":)" << energy.avg_latency()
           << R"(,"cpu_percent":)" << sys_metrics.cpu_percent
           << R"(,"ram_percent":)" << sys_metrics.ram_percent << "}";
        body = ss.str();
    }
    // Route: GET /metrics (Prometheus-style)
    else if (req.find("GET /metrics") != std::string::npos) {
        std::ostringstream ss;
        ss << "# HELP flow_requests_total Total requests processed\n";
        ss << "# TYPE flow_requests_total counter\n";
        ss << "flow_requests_total " << energy.requests.load() << "\n";
        ss << "# HELP flow_cache_hits_total Cache hits\n";
        ss << "flow_cache_hits_total " << energy.cache_hits.load() << "\n";
        ss << "# HELP flow_llm_calls_total LLM API calls\n";
        ss << "flow_llm_calls_total " << energy.llm_calls.load() << "\n";
        ss << "# HELP flow_cpu_percent CPU usage\n";
        ss << "flow_cpu_percent " << sys_metrics.cpu_percent << "\n";
        ss << "# HELP flow_ram_percent RAM usage\n";
        ss << "flow_ram_percent " << sys_metrics.ram_percent << "\n";
        ss << "# HELP flow_disk_percent Disk usage\n";
        ss << "flow_disk_percent " << sys_metrics.disk_percent << "\n";
        body = ss.str();
    }
    // Route: GET /full - Everything
    else if (req.find("GET /full") != std::string::npos) {
        std::ostringstream ss;
        ss << R"({"organ":"mitochondrie","energy":)"
           << R"({"requests":)" << energy.requests.load()
           << R"(,"cache_hits":)" << energy.cache_hits.load()
           << R"(,"llm_calls":)" << energy.llm_calls.load()
           << R"(,"efficiency":)" << energy.efficiency()
           << R"(,"avg_latency_ms":)" << energy.avg_latency() << "}"
           << R"(,"system":)" << sys_metrics.to_json() << "}";
        body = ss.str();
    }
    // Default: combined health
    else {
        std::ostringstream ss;
        ss << R"({"organ":"mitochondrie","status":"powered")"
           << R"(,"requests":)" << energy.requests.load()
           << R"(,"cache_hits":)" << energy.cache_hits.load()
           << R"(,"llm_calls":)" << energy.llm_calls.load()
           << R"(,"efficiency":)" << energy.efficiency()
           << R"(,"avg_latency_ms":)" << energy.avg_latency() << "}";
        body = ss.str();
    }

    response = "HTTP/1.1 " + std::to_string(status) + " OK\r\n"
               "Content-Type: application/json\r\n"
               "Access-Control-Allow-Origin: *\r\n"
               "Content-Length: " + std::to_string(body.size()) + "\r\n\r\n" + body;
    write(client, response.c_str(), response.size());
    close(client);
}

int main() {
    int server = socket(AF_INET, SOCK_STREAM, 0);
    if (server < 0) {
        std::cerr << "Error creating socket\n";
        return 1;
    }

    int opt = 1;
    setsockopt(server, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons(8096);

    if (bind(server, (sockaddr*)&addr, sizeof(addr)) < 0) {
        std::cerr << "Error binding to port 8096\n";
        return 1;
    }

    listen(server, 10);

    std::cout << "⚡ mitochondrie :8096 - système énergétique\n";
    std::cout << "  GET /health   - état général\n";
    std::cout << "  GET /system   - métriques système\n";
    std::cout << "  GET /energy   - métriques API\n";
    std::cout << "  GET /metrics  - format Prometheus\n";
    std::cout << "  GET /full     - tout\n";
    std::cout << "  POST /record  - enregistrer requête\n";

    // Start background metrics updater
    std::thread updater(metrics_updater);
    updater.detach();

    while (true) {
        int client = accept(server, nullptr, nullptr);
        if (client >= 0) {
            handle_request(client);
        }
    }

    running = false;
    return 0;
}
