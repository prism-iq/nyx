// quantique.rs - crypto post-quantique pour connexions internes
// Kyber1024 pour encapsulation, Dilithium5 pour signatures, SHA3-256 pour hash

use pqcrypto_kyber::kyber1024;
use pqcrypto_dilithium::dilithium5;
use pqcrypto_traits::kem::{PublicKey as KemPk, SecretKey as KemSk, SharedSecret, Ciphertext};
use pqcrypto_traits::sign::{PublicKey as SigPk, SecretKey as SigSk, SignedMessage, DetachedSignature};
use sha3::{Sha3_256, Digest};
use std::collections::HashMap;
use std::sync::RwLock;

// état global des clés
lazy_static::lazy_static! {
    static ref ORGAN_KEYS: RwLock<OrganKeys> = RwLock::new(OrganKeys::new());
}

pub struct OrganKeys {
    // Kyber pour chiffrement
    pub kem_pk: Option<Vec<u8>>,
    pub kem_sk: Option<Vec<u8>>,
    // Dilithium pour signatures
    pub sig_pk: Option<Vec<u8>>,
    pub sig_sk: Option<Vec<u8>>,
    // clés partagées avec autres organes
    pub shared: HashMap<String, Vec<u8>>,
    // hash de l'état pour intégrité
    pub state_hash: Vec<u8>,
}

impl OrganKeys {
    pub fn new() -> Self {
        OrganKeys {
            kem_pk: None, kem_sk: None,
            sig_pk: None, sig_sk: None,
            shared: HashMap::new(),
            state_hash: Vec::new(),
        }
    }
}

// génération de clés post-quantiques
pub fn keygen() -> (Vec<u8>, Vec<u8>, Vec<u8>, Vec<u8>) {
    let (kem_pk, kem_sk) = kyber1024::keypair();
    let (sig_pk, sig_sk) = dilithium5::keypair();

    let mut keys = ORGAN_KEYS.write().unwrap();
    keys.kem_pk = Some(kem_pk.as_bytes().to_vec());
    keys.kem_sk = Some(kem_sk.as_bytes().to_vec());
    keys.sig_pk = Some(sig_pk.as_bytes().to_vec());
    keys.sig_sk = Some(sig_sk.as_bytes().to_vec());
    keys.state_hash = hash_state(&keys);

    (
        kem_pk.as_bytes().to_vec(),
        kem_sk.as_bytes().to_vec(),
        sig_pk.as_bytes().to_vec(),
        sig_sk.as_bytes().to_vec(),
    )
}

// hash SHA3-256
pub fn hash(data: &[u8]) -> Vec<u8> {
    let mut hasher = Sha3_256::new();
    hasher.update(data);
    hasher.finalize().to_vec()
}

pub fn hash_hex(data: &[u8]) -> String {
    hex::encode(hash(data))
}

// hash de l'état pour vérification continue
fn hash_state(keys: &OrganKeys) -> Vec<u8> {
    let mut hasher = Sha3_256::new();
    if let Some(ref pk) = keys.kem_pk { hasher.update(pk); }
    if let Some(ref pk) = keys.sig_pk { hasher.update(pk); }
    for (k, v) in &keys.shared {
        hasher.update(k.as_bytes());
        hasher.update(v);
    }
    hasher.finalize().to_vec()
}

// vérifier l'intégrité de l'état
pub fn verify_integrity() -> bool {
    let keys = ORGAN_KEYS.read().unwrap();
    let current = hash_state(&keys);
    current == keys.state_hash
}

// encapsuler un secret pour un organe (Kyber)
pub fn encapsulate(peer_pk: &[u8]) -> Result<(Vec<u8>, Vec<u8>), &'static str> {
    let pk = kyber1024::PublicKey::from_bytes(peer_pk)
        .map_err(|_| "invalid public key")?;
    let (ss, ct) = kyber1024::encapsulate(&pk);
    Ok((ss.as_bytes().to_vec(), ct.as_bytes().to_vec()))
}

// décapsuler un secret reçu
pub fn decapsulate(ciphertext: &[u8]) -> Result<Vec<u8>, &'static str> {
    let keys = ORGAN_KEYS.read().unwrap();
    let sk_bytes = keys.kem_sk.as_ref().ok_or("no secret key")?;
    let sk = kyber1024::SecretKey::from_bytes(sk_bytes)
        .map_err(|_| "invalid secret key")?;
    let ct = kyber1024::Ciphertext::from_bytes(ciphertext)
        .map_err(|_| "invalid ciphertext")?;
    let ss = kyber1024::decapsulate(&ct, &sk);
    Ok(ss.as_bytes().to_vec())
}

// signer un message (Dilithium)
pub fn sign(message: &[u8]) -> Result<Vec<u8>, &'static str> {
    let keys = ORGAN_KEYS.read().unwrap();
    let sk_bytes = keys.sig_sk.as_ref().ok_or("no signing key")?;
    let sk = dilithium5::SecretKey::from_bytes(sk_bytes)
        .map_err(|_| "invalid signing key")?;
    let sig = dilithium5::detached_sign(message, &sk);
    Ok(sig.as_bytes().to_vec())
}

// vérifier une signature
pub fn verify(message: &[u8], signature: &[u8], peer_pk: &[u8]) -> bool {
    let pk = match dilithium5::PublicKey::from_bytes(peer_pk) {
        Ok(pk) => pk,
        Err(_) => return false,
    };
    let sig = match dilithium5::DetachedSignature::from_bytes(signature) {
        Ok(s) => s,
        Err(_) => return false,
    };
    dilithium5::verify_detached_signature(&sig, message, &pk).is_ok()
}

// établir un secret partagé avec un organe
pub fn establish_shared(organ: &str, peer_pk: &[u8]) -> Result<Vec<u8>, &'static str> {
    let (ss, _ct) = encapsulate(peer_pk)?;
    let mut keys = ORGAN_KEYS.write().unwrap();
    keys.shared.insert(organ.to_string(), ss.clone());
    keys.state_hash = hash_state(&keys);
    Ok(ss)
}

// obtenir le secret partagé avec un organe
pub fn get_shared(organ: &str) -> Option<Vec<u8>> {
    let keys = ORGAN_KEYS.read().unwrap();
    keys.shared.get(organ).cloned()
}

// export public key pour échange
pub fn get_public_keys() -> Result<(Vec<u8>, Vec<u8>), &'static str> {
    let keys = ORGAN_KEYS.read().unwrap();
    let kem_pk = keys.kem_pk.as_ref().ok_or("no kem key")?;
    let sig_pk = keys.sig_pk.as_ref().ok_or("no sig key")?;
    Ok((kem_pk.clone(), sig_pk.clone()))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_hash() {
        let h = hash(b"flow");
        assert_eq!(h.len(), 32);
    }

    #[test]
    fn test_keygen_and_sign() {
        keygen();
        let msg = b"test message";
        let sig = sign(msg).unwrap();
        let (_, sig_pk) = get_public_keys().unwrap();
        assert!(verify(msg, &sig, &sig_pk));
    }
}
