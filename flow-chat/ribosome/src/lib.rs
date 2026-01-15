// ribosome - synthèse, compile les réponses
use std::collections::HashMap;
use std::sync::RwLock;

static KNOWLEDGE: RwLock<Option<HashMap<String, String>>> = RwLock::new(None);

pub fn init() {
    let mut k = HashMap::new();
    k.insert("network".into(), "same pattern everywhere".into());
    k.insert("learning".into(), "universal adaptation".into());
    k.insert("entropy".into(), "info = disorder = life".into());
    k.insert("emergence".into(), "whole > sum of parts".into());
    *KNOWLEDGE.write().unwrap() = Some(k);
}

pub fn synthesize(input: &str) -> Option<String> {
    let k = KNOWLEDGE.read().unwrap();
    if let Some(ref map) = *k {
        let input_lower = input.to_lowercase();
        for (key, val) in map.iter() {
            if input_lower.contains(key) {
                return Some(val.clone());
            }
        }
    }
    None
}

fn main() {
    init();
    println!("🔬 ribosome ready");
    // FFI interface for other languages
}
