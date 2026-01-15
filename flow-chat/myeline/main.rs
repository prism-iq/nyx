// myeline.rs - cache ultra-rapide (port du Zig)
use std::collections::HashMap;
use std::sync::RwLock;
use std::time::{SystemTime, UNIX_EPOCH};

lazy_static::lazy_static! {
    static ref CACHE: RwLock<HashMap<String, (String, u64)>> = RwLock::new(HashMap::new());
}

fn now() -> u64 {
    SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs()
}

pub fn get(key: &str) -> Option<String> {
    let cache = CACHE.read().ok()?;
    let (val, ts) = cache.get(key)?;
    if now() - ts < 3600 { Some(val.clone()) } else { None }
}

pub fn set(key: &str, value: &str) {
    if let Ok(mut cache) = CACHE.write() {
        cache.insert(key.to_string(), (value.to_string(), now()));
    }
}

pub fn clear() {
    if let Ok(mut cache) = CACHE.write() { cache.clear(); }
}

pub fn size() -> usize {
    CACHE.read().map(|c| c.len()).unwrap_or(0)
}
