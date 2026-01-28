use axum::{
    extract::{Path, State},
    http::StatusCode,
    response::Json,
    routing::{get, post},
    Router,
};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::{mpsc, RwLock};
use tower_http::cors::{Any, CorsLayer};
use tracing::{error, info, warn};

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServiceInfo {
    pub name: String,
    pub port: u16,
    pub status: ServiceStatus,
    pub last_seen: Option<DateTime<Utc>>,
    pub consecutive_failures: u32,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ServiceStatus {
    Healthy,
    Degraded,
    Down,
    Unknown,
}

impl std::fmt::Display for ServiceStatus {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ServiceStatus::Healthy => write!(f, "healthy"),
            ServiceStatus::Degraded => write!(f, "degraded"),
            ServiceStatus::Down => write!(f, "down"),
            ServiceStatus::Unknown => write!(f, "unknown"),
        }
    }
}

/// Events that can flow through the internal event bus.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum DaemonEvent {
    ServiceDown { name: String, port: u16 },
    ServiceRecovered { name: String, port: u16 },
    RestartRequested { name: String },
    HealthCheckComplete { healthy: usize, total: usize },
}

// ---------------------------------------------------------------------------
// Shared application state
// ---------------------------------------------------------------------------

#[derive(Debug)]
pub struct AppState {
    pub registry: RwLock<HashMap<String, ServiceInfo>>,
    pub event_tx: mpsc::Sender<DaemonEvent>,
    pub start_time: DateTime<Utc>,
}

// ---------------------------------------------------------------------------
// Known Pantheon services
// ---------------------------------------------------------------------------

fn known_services() -> Vec<(&'static str, u16)> {
    vec![
        ("athena", 9500),
        ("hermes", 9600),
        ("iris", 9601),
        ("echo", 9604),
        ("aegis", 9700),
        ("apollo", 9777),
    ]
}

// ---------------------------------------------------------------------------
// Health-check loop
// ---------------------------------------------------------------------------

async fn health_check_loop(state: Arc<AppState>) {
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(3))
        .build()
        .expect("failed to build HTTP client");

    let mut interval = tokio::time::interval(std::time::Duration::from_secs(10));

    loop {
        interval.tick().await;
        let mut healthy_count: usize = 0;
        let services = known_services();
        let total = services.len();

        for (name, port) in &services {
            let url = format!("http://127.0.0.1:{}/health", port);
            let result = client.get(&url).send().await;

            let mut reg = state.registry.write().await;
            let entry = reg.entry(name.to_string()).or_insert_with(|| ServiceInfo {
                name: name.to_string(),
                port: *port,
                status: ServiceStatus::Unknown,
                last_seen: None,
                consecutive_failures: 0,
            });

            let previous_status = entry.status;

            match result {
                Ok(resp) if resp.status().is_success() => {
                    entry.status = ServiceStatus::Healthy;
                    entry.last_seen = Some(Utc::now());
                    entry.consecutive_failures = 0;
                    healthy_count += 1;

                    if previous_status == ServiceStatus::Down
                        || previous_status == ServiceStatus::Unknown
                    {
                        info!(service = *name, port = *port, "service recovered");
                        let _ = state
                            .event_tx
                            .send(DaemonEvent::ServiceRecovered {
                                name: name.to_string(),
                                port: *port,
                            })
                            .await;
                    }
                }
                Ok(resp) => {
                    // Non-success status code -- mark degraded after 1, down after 3.
                    entry.consecutive_failures += 1;
                    if entry.consecutive_failures >= 3 {
                        entry.status = ServiceStatus::Down;
                    } else {
                        entry.status = ServiceStatus::Degraded;
                    }
                    warn!(
                        service = *name,
                        port = *port,
                        status = %resp.status(),
                        failures = entry.consecutive_failures,
                        "service returned non-success"
                    );
                }
                Err(err) => {
                    entry.consecutive_failures += 1;
                    let was_healthy =
                        previous_status == ServiceStatus::Healthy || previous_status == ServiceStatus::Unknown;

                    if entry.consecutive_failures >= 3 {
                        entry.status = ServiceStatus::Down;
                        if was_healthy || previous_status == ServiceStatus::Degraded {
                            error!(service = *name, port = *port, "service is DOWN");
                            let _ = state
                                .event_tx
                                .send(DaemonEvent::ServiceDown {
                                    name: name.to_string(),
                                    port: *port,
                                })
                                .await;
                        }
                    } else {
                        entry.status = ServiceStatus::Degraded;
                        warn!(
                            service = *name,
                            port = *port,
                            error = %err,
                            failures = entry.consecutive_failures,
                            "health check failed"
                        );
                    }
                }
            }
        }

        let _ = state
            .event_tx
            .send(DaemonEvent::HealthCheckComplete {
                healthy: healthy_count,
                total,
            })
            .await;

        info!(healthy = healthy_count, total = total, "health sweep complete");
    }
}

// ---------------------------------------------------------------------------
// Event bus consumer (stub -- logs events, extensible for future routing)
// ---------------------------------------------------------------------------

async fn event_bus_consumer(mut rx: mpsc::Receiver<DaemonEvent>) {
    while let Some(event) = rx.recv().await {
        match &event {
            DaemonEvent::ServiceDown { name, port } => {
                error!(
                    event = "service_down",
                    service = %name,
                    port = %port,
                    "EVENT BUS: service went down -- restart may be required"
                );
            }
            DaemonEvent::ServiceRecovered { name, port } => {
                info!(
                    event = "service_recovered",
                    service = %name,
                    port = %port,
                    "EVENT BUS: service recovered"
                );
            }
            DaemonEvent::RestartRequested { name } => {
                info!(
                    event = "restart_requested",
                    service = %name,
                    "EVENT BUS: restart requested (auto-restart not yet wired)"
                );
            }
            DaemonEvent::HealthCheckComplete { healthy, total } => {
                tracing::debug!(
                    event = "health_check_complete",
                    healthy,
                    total,
                    "EVENT BUS: sweep done"
                );
            }
        }
    }
}

// ---------------------------------------------------------------------------
// HTTP handlers
// ---------------------------------------------------------------------------

/// GET /health -- Nyx's own health.
async fn handle_health() -> Json<serde_json::Value> {
    Json(serde_json::json!({
        "status": "ok",
        "service": "nyx-daemon",
        "timestamp": Utc::now().to_rfc3339(),
    }))
}

/// GET /status -- Overview with uptime and per-service breakdown.
async fn handle_status(State(state): State<Arc<AppState>>) -> Json<serde_json::Value> {
    let registry = state.registry.read().await;
    let now = Utc::now();
    let uptime = now
        .signed_duration_since(state.start_time)
        .num_seconds();

    let total = registry.len();
    let healthy = registry.values().filter(|s| s.status == ServiceStatus::Healthy).count();
    let down = registry.values().filter(|s| s.status == ServiceStatus::Down).count();

    let services: Vec<serde_json::Value> = registry
        .values()
        .map(|s| {
            serde_json::json!({
                "name": s.name,
                "port": s.port,
                "status": s.status,
                "last_seen": s.last_seen.map(|t| t.to_rfc3339()),
                "consecutive_failures": s.consecutive_failures,
            })
        })
        .collect();

    Json(serde_json::json!({
        "service": "nyx-daemon",
        "uptime_seconds": uptime,
        "services_total": total,
        "services_healthy": healthy,
        "services_down": down,
        "services": services,
        "timestamp": now.to_rfc3339(),
    }))
}

/// GET /registry -- Raw service registry dump.
async fn handle_registry(State(state): State<Arc<AppState>>) -> Json<serde_json::Value> {
    let registry = state.registry.read().await;
    let map: HashMap<String, serde_json::Value> = registry
        .iter()
        .map(|(k, v)| {
            (
                k.clone(),
                serde_json::json!({
                    "port": v.port,
                    "status": v.status,
                    "last_seen": v.last_seen.map(|t| t.to_rfc3339()),
                    "consecutive_failures": v.consecutive_failures,
                }),
            )
        })
        .collect();

    Json(serde_json::json!(map))
}

/// POST /restart/{service} -- Request a restart for a named service.
async fn handle_restart(
    State(state): State<Arc<AppState>>,
    Path(service): Path<String>,
) -> Result<Json<serde_json::Value>, StatusCode> {
    let registry = state.registry.read().await;

    // Verify the service exists in the registry.
    if !registry.contains_key(&service) {
        return Err(StatusCode::NOT_FOUND);
    }
    drop(registry);

    info!(service = %service, "restart requested via API");

    let _ = state
        .event_tx
        .send(DaemonEvent::RestartRequested {
            name: service.clone(),
        })
        .await;

    Ok(Json(serde_json::json!({
        "action": "restart_requested",
        "service": service,
        "timestamp": Utc::now().to_rfc3339(),
    })))
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

#[tokio::main]
async fn main() {
    // Initialise tracing
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| tracing_subscriber::EnvFilter::new("info")),
        )
        .init();

    info!("nyx-daemon starting up");

    // Event bus channel (bounded)
    let (event_tx, event_rx) = mpsc::channel::<DaemonEvent>(256);

    // Seed the registry with known services
    let mut initial_registry = HashMap::new();
    for (name, port) in known_services() {
        initial_registry.insert(
            name.to_string(),
            ServiceInfo {
                name: name.to_string(),
                port,
                status: ServiceStatus::Unknown,
                last_seen: None,
                consecutive_failures: 0,
            },
        );
    }

    let state = Arc::new(AppState {
        registry: RwLock::new(initial_registry),
        event_tx,
        start_time: Utc::now(),
    });

    // Spawn background tasks
    tokio::spawn(health_check_loop(Arc::clone(&state)));
    tokio::spawn(event_bus_consumer(event_rx));

    // CORS layer -- permissive for local dev
    let cors = CorsLayer::new()
        .allow_origin(Any)
        .allow_methods(Any)
        .allow_headers(Any);

    // Router
    let app = Router::new()
        .route("/health", get(handle_health))
        .route("/status", get(handle_status))
        .route("/registry", get(handle_registry))
        .route("/restart/{service}", post(handle_restart))
        .layer(cors)
        .with_state(Arc::clone(&state));

    let bind_addr = "0.0.0.0:9999";
    info!(addr = bind_addr, "nyx-daemon listening");

    let listener = tokio::net::TcpListener::bind(bind_addr)
        .await
        .expect("failed to bind to port 9999");

    axum::serve(listener, app)
        .await
        .expect("server error");
}
