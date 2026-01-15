// ALÉA - Blockchain Entropy for Personality Anti-Ossification
// Rust crypto-native organ for Flow
// Port 8102 - Simplified HTTP server

use chrono::Utc;
use rand::Rng;
use reqwest::blocking::Client;
use serde::{Deserialize, Serialize};
use sha3::{Digest, Sha3_256};
use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use std::sync::{Arc, RwLock};
use std::thread;
use std::time::Duration;

const PORT: u16 = 8102;

// === BLOCKCHAIN DATA STRUCTURES ===

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct BlockchainNoise {
    pub entropy: Vec<u8>,
    pub timestamp: u64,
    pub block_height: u64,
    pub tx_count: u32,
    pub source: String,
    pub fetched_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PersonalityDrift {
    pub warmth: f64,
    pub directness: f64,
    pub curiosity: f64,
    pub playfulness: f64,
    pub depth: f64,
    pub entropy_source: String,
    pub timestamp: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct EntropyState {
    pub bitcoin: Option<BlockchainNoise>,
    pub ethereum: Option<BlockchainNoise>,
    pub monero: Option<BlockchainNoise>,
    pub combined_entropy: Vec<u8>,
    pub last_update: String,
    pub update_count: u64,
}

type SharedState = Arc<RwLock<EntropyState>>;

// === BLOCKCHAIN FETCHERS ===

fn fetch_bitcoin(client: &Client) -> Option<BlockchainNoise> {
    let url = "https://blockchain.info/latestblock";

    match client.get(url).timeout(Duration::from_secs(10)).send() {
        Ok(resp) => {
            if let Ok(data) = resp.json::<serde_json::Value>() {
                let hash = data.get("hash").and_then(|v| v.as_str()).unwrap_or("");
                let entropy = hex_to_bytes(hash);

                Some(BlockchainNoise {
                    entropy,
                    timestamp: data.get("time").and_then(|v| v.as_u64()).unwrap_or(0),
                    block_height: data.get("height").and_then(|v| v.as_u64()).unwrap_or(0),
                    tx_count: data.get("n_tx").and_then(|v| v.as_u64()).unwrap_or(0) as u32,
                    source: "bitcoin".to_string(),
                    fetched_at: Utc::now().to_rfc3339(),
                })
            } else {
                None
            }
        }
        Err(_) => None,
    }
}

fn fetch_ethereum(client: &Client) -> Option<BlockchainNoise> {
    let url = "https://eth.llamarpc.com";
    let body = serde_json::json!({
        "jsonrpc": "2.0",
        "method": "eth_getBlockByNumber",
        "params": ["latest", false],
        "id": 1
    });

    match client.post(url).json(&body).timeout(Duration::from_secs(10)).send() {
        Ok(resp) => {
            if let Ok(data) = resp.json::<serde_json::Value>() {
                if let Some(result) = data.get("result") {
                    let hash = result
                        .get("hash")
                        .and_then(|v| v.as_str())
                        .unwrap_or("")
                        .trim_start_matches("0x");
                    let entropy = hex_to_bytes(hash);

                    let height = result
                        .get("number")
                        .and_then(|v| v.as_str())
                        .map(|s| u64::from_str_radix(s.trim_start_matches("0x"), 16).unwrap_or(0))
                        .unwrap_or(0);

                    let timestamp = result
                        .get("timestamp")
                        .and_then(|v| v.as_str())
                        .map(|s| u64::from_str_radix(s.trim_start_matches("0x"), 16).unwrap_or(0))
                        .unwrap_or(0);

                    return Some(BlockchainNoise {
                        entropy,
                        timestamp,
                        block_height: height,
                        tx_count: 0,
                        source: "ethereum".to_string(),
                        fetched_at: Utc::now().to_rfc3339(),
                    });
                }
            }
            None
        }
        Err(_) => None,
    }
}

fn fetch_monero(client: &Client) -> Option<BlockchainNoise> {
    let url = "https://xmr-node.cakewallet.com:18081/json_rpc";
    let body = serde_json::json!({
        "jsonrpc": "2.0",
        "method": "get_last_block_header",
        "id": 1
    });

    match client.post(url).json(&body).timeout(Duration::from_secs(10)).send() {
        Ok(resp) => {
            if let Ok(data) = resp.json::<serde_json::Value>() {
                if let Some(header) = data.get("result").and_then(|r| r.get("block_header")) {
                    let hash = header.get("hash").and_then(|v| v.as_str()).unwrap_or("");
                    let entropy = hex_to_bytes(hash);

                    return Some(BlockchainNoise {
                        entropy,
                        timestamp: header.get("timestamp").and_then(|v| v.as_u64()).unwrap_or(0),
                        block_height: header.get("height").and_then(|v| v.as_u64()).unwrap_or(0),
                        tx_count: header.get("num_txes").and_then(|v| v.as_u64()).unwrap_or(0) as u32,
                        source: "monero".to_string(),
                        fetched_at: Utc::now().to_rfc3339(),
                    });
                }
            }
            None
        }
        Err(_) => None,
    }
}

// === ENTROPY PROCESSING ===

fn hex_to_bytes(hex: &str) -> Vec<u8> {
    (0..hex.len())
        .step_by(2)
        .filter_map(|i| {
            if i + 2 <= hex.len() {
                u8::from_str_radix(&hex[i..i + 2], 16).ok()
            } else {
                None
            }
        })
        .collect()
}

fn combine_entropy(sources: &[&[u8]]) -> Vec<u8> {
    let mut hasher = Sha3_256::new();
    for source in sources {
        hasher.update(source);
    }
    hasher.update(Utc::now().timestamp_nanos_opt().unwrap_or(0).to_le_bytes());
    hasher.finalize().to_vec()
}

fn entropy_to_drift(entropy: &[u8], base_drift: f64) -> f64 {
    if entropy.is_empty() {
        return 0.0;
    }
    let sum: u64 = entropy.iter().map(|&b| b as u64).sum();
    let normalized = (sum as f64 / (entropy.len() as f64 * 255.0)) * 2.0 - 1.0;
    normalized * base_drift
}

fn generate_personality_drift(entropy: &[u8], source: &str) -> PersonalityDrift {
    let chunk_size = entropy.len().max(5) / 5;
    let chunks: Vec<&[u8]> = entropy.chunks(chunk_size).collect();

    PersonalityDrift {
        warmth: entropy_to_drift(chunks.get(0).copied().unwrap_or(&[]), 0.1),
        directness: entropy_to_drift(chunks.get(1).copied().unwrap_or(&[]), 0.05),
        curiosity: entropy_to_drift(chunks.get(2).copied().unwrap_or(&[]), 0.08),
        playfulness: entropy_to_drift(chunks.get(3).copied().unwrap_or(&[]), 0.06),
        depth: entropy_to_drift(chunks.get(4).copied().unwrap_or(&[]), 0.04),
        entropy_source: source.to_string(),
        timestamp: Utc::now().to_rfc3339(),
    }
}

fn refresh_state(state: &SharedState) {
    let client = Client::builder()
        .timeout(Duration::from_secs(15))
        .build()
        .unwrap();

    let btc = fetch_bitcoin(&client);
    let eth = fetch_ethereum(&client);
    let xmr = fetch_monero(&client);

    let mut entropy_sources: Vec<Vec<u8>> = vec![];
    if let Some(ref b) = btc {
        entropy_sources.push(b.entropy.clone());
    }
    if let Some(ref e) = eth {
        entropy_sources.push(e.entropy.clone());
    }
    if let Some(ref m) = xmr {
        entropy_sources.push(m.entropy.clone());
    }

    let mut rng = rand::thread_rng();
    let local_entropy: Vec<u8> = (0..32).map(|_| rng.gen()).collect();
    entropy_sources.push(local_entropy);

    let refs: Vec<&[u8]> = entropy_sources.iter().map(|v| v.as_slice()).collect();
    let combined = combine_entropy(&refs);

    if let Ok(mut s) = state.write() {
        s.bitcoin = btc;
        s.ethereum = eth;
        s.monero = xmr;
        s.combined_entropy = combined;
        s.last_update = Utc::now().to_rfc3339();
        s.update_count += 1;
    }
}

// === HTTP SERVER ===

fn handle_client(mut stream: TcpStream, state: &SharedState) {
    let mut buffer = [0; 4096];
    if stream.read(&mut buffer).is_err() {
        return;
    }

    let request = String::from_utf8_lossy(&buffer);
    let path = request
        .lines()
        .next()
        .and_then(|line| line.split_whitespace().nth(1))
        .unwrap_or("/");

    let (status, body) = match path {
        "/health" | "/" => {
            let json = serde_json::json!({
                "organ": "alea",
                "status": "entropic",
                "port": PORT
            });
            ("200 OK", json.to_string())
        }
        "/entropy" => {
            let s = state.read().unwrap();
            let json = serde_json::json!({
                "bitcoin": s.bitcoin,
                "ethereum": s.ethereum,
                "monero": s.monero,
                "combined_entropy_len": s.combined_entropy.len(),
                "last_update": s.last_update,
                "update_count": s.update_count
            });
            ("200 OK", json.to_string())
        }
        "/drift" => {
            let s = state.read().unwrap();
            let drift = generate_personality_drift(&s.combined_entropy, "combined");
            ("200 OK", serde_json::to_string(&drift).unwrap())
        }
        "/refresh" => {
            refresh_state(state);
            let s = state.read().unwrap();
            let sources_active = [s.bitcoin.is_some(), s.ethereum.is_some(), s.monero.is_some()]
                .iter()
                .filter(|&&x| x)
                .count();
            let json = serde_json::json!({
                "refreshed": true,
                "sources_active": sources_active,
                "combined_entropy_len": s.combined_entropy.len(),
                "update_count": s.update_count
            });
            ("200 OK", json.to_string())
        }
        "/modulate" => {
            // Parse body for base values
            let body_start = request.find("\r\n\r\n").map(|i| i + 4).unwrap_or(0);
            let body_str = &request[body_start..].trim_end_matches('\0');
            let input: serde_json::Value =
                serde_json::from_str(body_str).unwrap_or(serde_json::json!({}));

            let base_warmth = input.get("warmth").and_then(|v| v.as_f64()).unwrap_or(0.5);
            let base_directness = input.get("directness").and_then(|v| v.as_f64()).unwrap_or(0.5);
            let base_curiosity = input.get("curiosity").and_then(|v| v.as_f64()).unwrap_or(0.5);
            let base_playfulness = input.get("playfulness").and_then(|v| v.as_f64()).unwrap_or(0.5);
            let base_depth = input.get("depth").and_then(|v| v.as_f64()).unwrap_or(0.5);

            let s = state.read().unwrap();
            let drift = generate_personality_drift(&s.combined_entropy, "combined");

            let clamp = |v: f64| v.max(0.0).min(1.0);

            let json = serde_json::json!({
                "modulated": {
                    "warmth": clamp(base_warmth + drift.warmth),
                    "directness": clamp(base_directness + drift.directness),
                    "curiosity": clamp(base_curiosity + drift.curiosity),
                    "playfulness": clamp(base_playfulness + drift.playfulness),
                    "depth": clamp(base_depth + drift.depth),
                },
                "drift_applied": drift,
                "entropy_source": "blockchain_combined"
            });
            ("200 OK", json.to_string())
        }
        _ => {
            let json = serde_json::json!({"error": "not found"});
            ("404 Not Found", json.to_string())
        }
    };

    let response = format!(
        "HTTP/1.1 {}\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: {}\r\n\r\n{}",
        status,
        body.len(),
        body
    );

    let _ = stream.write_all(response.as_bytes());
}

fn background_refresh(state: SharedState) {
    loop {
        thread::sleep(Duration::from_secs(60));
        refresh_state(&state);
        if let Ok(s) = state.read() {
            println!("[ALÉA] Entropy refreshed (update #{})", s.update_count);
        }
    }
}

fn main() {
    println!("🎲 ALÉA :{} - blockchain entropy", PORT);
    println!("  GET  /health    - status");
    println!("  GET  /entropy   - current entropy state");
    println!("  GET  /drift     - personality drift values");
    println!("  GET  /refresh   - force refresh from blockchains");
    println!("  POST /modulate  - apply drift to base values");

    let state: SharedState = Arc::new(RwLock::new(EntropyState::default()));

    // Initial fetch
    println!("  Fetching initial entropy...");
    refresh_state(&state);

    if let Ok(s) = state.read() {
        if let Some(ref b) = s.bitcoin {
            println!("  [BTC] Block #{}", b.block_height);
        }
        if let Some(ref e) = s.ethereum {
            println!("  [ETH] Block #{}", e.block_height);
        }
        if let Some(ref m) = s.monero {
            println!("  [XMR] Block #{}", m.block_height);
        }
    }

    // Spawn background refresh thread
    let bg_state = state.clone();
    thread::spawn(move || background_refresh(bg_state));

    // Start server
    let listener = TcpListener::bind(format!("127.0.0.1:{}", PORT)).expect("Failed to bind");

    for stream in listener.incoming() {
        if let Ok(stream) = stream {
            let state_clone = state.clone();
            thread::spawn(move || handle_client(stream, &state_clone));
        }
    }
}
