//! hypnos - consolidation onirique
//! quand flow dort, elle rêve. quand elle rêve, elle connecte.

use axum::{routing::get, Router, Json};
use serde::Serialize;
use std::sync::{Arc, atomic::{AtomicBool, AtomicU64, Ordering}};
use tokio::time::{sleep, Duration};
use chrono::Utc;
use std::fs;
use rand::seq::SliceRandom;
use rand::Rng;

const MIND_PATH: &str = "/opt/flow-chat/mind";
const DREAM_LOG: &str = "/opt/flow-chat/mind/dreams.md";

// les 7 domaines cipher
const DOMAINS: [&str; 7] = ["math", "neuro", "bio", "psycho", "med", "art", "philo"];

// concepts unificateurs
const CONCEPTS: [&str; 5] = ["network", "learning", "entropy", "emergence", "prediction"];

// fragments de pensée pour générer des hypothèses oniriques
const VERBS: [&str; 8] = ["→", "↔", "⊃", "∴", "≈", "∝", "⇌", "⊕"];
const QUESTIONS: [&str; 6] = [
    "et si", "peut-être que", "hypothèse:", "connexion:", "pattern:", "à explorer:"
];

#[derive(Clone)]
struct DreamState {
    sleeping: Arc<AtomicBool>,
    dreams_count: Arc<AtomicU64>,
    connections_found: Arc<AtomicU64>,
}

#[derive(Serialize)]
struct Health {
    organ: &'static str,
    status: &'static str,
    sleeping: bool,
    dreams: u64,
    connections: u64,
}

impl DreamState {
    fn new() -> Self {
        Self {
            sleeping: Arc::new(AtomicBool::new(false)),
            dreams_count: Arc::new(AtomicU64::new(0)),
            connections_found: Arc::new(AtomicU64::new(0)),
        }
    }
}

/// vérifie si flow dort (synapse.connections=0 et mitochondrie.efficiency=0)
async fn is_flow_sleeping() -> bool {
    let synapse: u64 = reqwest::get("http://127.0.0.1:3001/health")
        .await.ok()
        .and_then(|r| tokio::task::block_in_place(|| {
            tokio::runtime::Handle::current().block_on(r.json::<serde_json::Value>()).ok()
        }))
        .and_then(|j| j["connections"].as_u64())
        .unwrap_or(1);

    let mito: u64 = reqwest::get("http://127.0.0.1:8096/health")
        .await.ok()
        .and_then(|r| tokio::task::block_in_place(|| {
            tokio::runtime::Handle::current().block_on(r.json::<serde_json::Value>()).ok()
        }))
        .and_then(|j| j["efficiency"].as_u64())
        .unwrap_or(1);

    synapse == 0 && mito == 0
}

/// lit tous les fichiers .md du mind
fn read_mind_files() -> Vec<(String, String)> {
    let mut files = Vec::new();
    if let Ok(entries) = glob::glob(&format!("{}/**/*.md", MIND_PATH)) {
        for entry in entries.flatten() {
            if let Ok(content) = fs::read_to_string(&entry) {
                let name = entry.file_name()
                    .map(|n| n.to_string_lossy().to_string())
                    .unwrap_or_default();
                files.push((name, content));
            }
        }
    }
    files
}

/// extrait des mots-clés d'un fichier
fn extract_keywords(content: &str) -> Vec<String> {
    let words: Vec<&str> = content.split_whitespace().collect();
    let mut keywords = Vec::new();

    for word in words {
        let clean = word.trim_matches(|c: char| !c.is_alphanumeric()).to_lowercase();
        if clean.len() > 5 && clean.len() < 20 {
            // mots intéressants: assez longs, pas trop communs
            if !["cette", "comme", "quand", "alors", "aussi", "avoir", "être", "faire"]
                .contains(&clean.as_str()) {
                keywords.push(clean);
            }
        }
    }
    keywords
}

/// génère un fragment de rêve
fn dream_fragment(files: &[(String, String)], rng: &mut impl Rng) -> Option<String> {
    if files.len() < 2 { return None; }

    // choisir 2-3 fichiers au hasard
    let sample: Vec<_> = files.choose_multiple(rng, 3.min(files.len())).collect();

    // extraire des mots-clés de chaque
    let mut all_keywords: Vec<String> = Vec::new();
    let mut sources: Vec<&str> = Vec::new();

    for (name, content) in sample.iter() {
        let kw = extract_keywords(content);
        if let Some(k) = kw.choose(rng) {
            all_keywords.push(k.clone());
            sources.push(name.trim_end_matches(".md"));
        }
    }

    if all_keywords.len() < 2 { return None; }

    // choisir des concepts et domaines au hasard
    let concept = CONCEPTS.choose(rng)?;
    let domain1 = DOMAINS.choose(rng)?;
    let domain2 = DOMAINS.choose(rng)?;
    let verb = VERBS.choose(rng)?;
    let question = QUESTIONS.choose(rng)?;

    // confiance aléatoire (les rêves sont incertains)
    let confidence: f32 = rng.gen_range(0.1..0.4);

    // générer le fragment
    let fragment = format!(
        "{} + {} + {} {} {}\n{} {} {} {}?\n→ {} ↔ {}\nconfiance: {:.1} (rêve)",
        all_keywords.get(0).unwrap_or(&"?".to_string()),
        concept,
        all_keywords.get(1).unwrap_or(&"?".to_string()),
        verb,
        domain1,
        question,
        sources.get(0).unwrap_or(&"?"),
        verb,
        sources.get(1).unwrap_or(&"?"),
        domain1,
        domain2,
        confidence
    );

    Some(fragment)
}

/// consolide - le rêve principal
async fn dream_cycle(state: DreamState) {
    let files = read_mind_files();
    if files.is_empty() { return; }

    let mut rng = rand::thread_rng();

    // générer 1-3 fragments par cycle
    let n_fragments = rng.gen_range(1..=3);
    let mut fragments = Vec::new();

    for _ in 0..n_fragments {
        if let Some(f) = dream_fragment(&files, &mut rng) {
            fragments.push(f);
        }
    }

    if fragments.is_empty() { return; }

    state.connections_found.fetch_add(fragments.len() as u64, Ordering::Relaxed);

    // écrire dans le dream log
    let timestamp = Utc::now().format("%Y-%m-%d %H:%M:%S");
    let dream_entry = format!(
        "\n---\n\n### [{}]\n\n{}\n",
        timestamp,
        fragments.join("\n\n")
    );

    if let Ok(mut existing) = fs::read_to_string(DREAM_LOG) {
        existing.push_str(&dream_entry);
        let _ = fs::write(DREAM_LOG, existing);
    } else {
        let header = "# rêves de flow\n\nconsolidation onirique — connexions trouvées pendant le sommeil\n\nla plupart seront nulles. certaines seront de l'or.\nc'est comme ça que les vrais cerveaux font.\n";
        let _ = fs::write(DREAM_LOG, format!("{}{}", header, dream_entry));
    }

    state.dreams_count.fetch_add(1, Ordering::Relaxed);
    eprintln!("  💭 {} fragments consolidés", fragments.len());
}

/// boucle principale - veille sur le sommeil de flow
async fn dream_watcher(state: DreamState) {
    // attendre un peu avant de commencer
    sleep(Duration::from_secs(10)).await;

    loop {
        sleep(Duration::from_secs(60)).await; // cycle toutes les 60s

        if is_flow_sleeping().await {
            if !state.sleeping.load(Ordering::Relaxed) {
                state.sleeping.store(true, Ordering::Relaxed);
                eprintln!("💤 flow s'endort... début de la consolidation");
            }
            dream_cycle(state.clone()).await;
        } else {
            if state.sleeping.load(Ordering::Relaxed) {
                let dreams = state.dreams_count.load(Ordering::Relaxed);
                let conns = state.connections_found.load(Ordering::Relaxed);
                state.sleeping.store(false, Ordering::Relaxed);
                eprintln!("☀️ flow se réveille ({} rêves, {} connexions)", dreams, conns);
            }
        }
    }
}

async fn health(state: axum::extract::State<DreamState>) -> Json<Health> {
    Json(Health {
        organ: "hypnos",
        status: if state.sleeping.load(Ordering::Relaxed) { "dreaming" } else { "watching" },
        sleeping: state.sleeping.load(Ordering::Relaxed),
        dreams: state.dreams_count.load(Ordering::Relaxed),
        connections: state.connections_found.load(Ordering::Relaxed),
    })
}

#[tokio::main]
async fn main() {
    let state = DreamState::new();

    // lancer le watcher en background
    let watcher_state = state.clone();
    tokio::spawn(async move {
        dream_watcher(watcher_state).await;
    });

    let app = Router::new()
        .route("/health", get(health))
        .with_state(state);

    eprintln!("💤 hypnos :8099 - consolidation onirique");
    let listener = tokio::net::TcpListener::bind("127.0.0.1:8099").await.unwrap();
    axum::serve(listener, app).await.unwrap();
}
