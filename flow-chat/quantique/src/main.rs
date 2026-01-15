// quantique server - service de crypto post-quantique
use quantique::{keygen, hash_hex, sign, verify, verify_integrity, get_public_keys, encapsulate, decapsulate, establish_shared};
use tiny_http::{Server, Response, Method};
use serde::{Deserialize, Serialize};
use std::io::Read;

#[derive(Deserialize)]
struct SignRequest {
    message: String,
}

#[derive(Deserialize)]
struct VerifyRequest {
    message: String,
    signature: String,
    public_key: String,
}

#[derive(Deserialize)]
struct EncapRequest {
    peer_pk: String,
}

#[derive(Deserialize)]
struct DecapRequest {
    ciphertext: String,
}

#[derive(Deserialize)]
struct EstablishRequest {
    organ: String,
    peer_pk: String,
}

#[derive(Serialize)]
struct KeysResponse {
    kem_pk: String,
    sig_pk: String,
}

fn main() {
    // générer les clés au démarrage
    keygen();
    println!("🔐 quantique ready - post-quantum crypto");

    let server = Server::http("127.0.0.1:8095").unwrap();

    for mut req in server.incoming_requests() {
        let path = req.url().to_string();
        let method = req.method().clone();

        let response = match (method, path.as_str()) {
            (Method::Get, "/health") => {
                let integrity = verify_integrity();
                let status = if integrity { "secure" } else { "compromised" };
                Response::from_string(format!(r#"{{"organ":"quantique","status":"{}","integrity":{}}}"#, status, integrity))
            }

            (Method::Get, "/keys") => {
                match get_public_keys() {
                    Ok((kem, sig)) => {
                        let resp = KeysResponse {
                            kem_pk: hex::encode(&kem),
                            sig_pk: hex::encode(&sig),
                        };
                        Response::from_string(serde_json::to_string(&resp).unwrap())
                    }
                    Err(e) => Response::from_string(format!(r#"{{"error":"{}"}}"#, e))
                }
            }

            (Method::Post, "/hash") => {
                let mut body = String::new();
                req.as_reader().read_to_string(&mut body).ok();
                let h = hash_hex(body.as_bytes());
                Response::from_string(format!(r#"{{"hash":"{}"}}"#, h))
            }

            (Method::Post, "/sign") => {
                let mut body = String::new();
                req.as_reader().read_to_string(&mut body).ok();
                match serde_json::from_str::<SignRequest>(&body) {
                    Ok(r) => {
                        match sign(r.message.as_bytes()) {
                            Ok(sig) => Response::from_string(format!(r#"{{"signature":"{}"}}"#, hex::encode(&sig))),
                            Err(e) => Response::from_string(format!(r#"{{"error":"{}"}}"#, e))
                        }
                    }
                    Err(_) => Response::from_string(r#"{"error":"invalid json"}"#.to_string())
                }
            }

            (Method::Post, "/verify") => {
                let mut body = String::new();
                req.as_reader().read_to_string(&mut body).ok();
                match serde_json::from_str::<VerifyRequest>(&body) {
                    Ok(r) => {
                        let sig = hex::decode(&r.signature).unwrap_or_default();
                        let pk = hex::decode(&r.public_key).unwrap_or_default();
                        let valid = verify(r.message.as_bytes(), &sig, &pk);
                        Response::from_string(format!(r#"{{"valid":{}}}"#, valid))
                    }
                    Err(_) => Response::from_string(r#"{"error":"invalid json"}"#.to_string())
                }
            }

            (Method::Post, "/encapsulate") => {
                let mut body = String::new();
                req.as_reader().read_to_string(&mut body).ok();
                match serde_json::from_str::<EncapRequest>(&body) {
                    Ok(r) => {
                        let pk = hex::decode(&r.peer_pk).unwrap_or_default();
                        match encapsulate(&pk) {
                            Ok((ss, ct)) => Response::from_string(format!(
                                r#"{{"shared_secret":"{}","ciphertext":"{}"}}"#,
                                hex::encode(&ss), hex::encode(&ct)
                            )),
                            Err(e) => Response::from_string(format!(r#"{{"error":"{}"}}"#, e))
                        }
                    }
                    Err(_) => Response::from_string(r#"{"error":"invalid json"}"#.to_string())
                }
            }

            (Method::Post, "/decapsulate") => {
                let mut body = String::new();
                req.as_reader().read_to_string(&mut body).ok();
                match serde_json::from_str::<DecapRequest>(&body) {
                    Ok(r) => {
                        let ct = hex::decode(&r.ciphertext).unwrap_or_default();
                        match decapsulate(&ct) {
                            Ok(ss) => Response::from_string(format!(r#"{{"shared_secret":"{}"}}"#, hex::encode(&ss))),
                            Err(e) => Response::from_string(format!(r#"{{"error":"{}"}}"#, e))
                        }
                    }
                    Err(_) => Response::from_string(r#"{"error":"invalid json"}"#.to_string())
                }
            }

            (Method::Post, "/establish") => {
                let mut body = String::new();
                req.as_reader().read_to_string(&mut body).ok();
                match serde_json::from_str::<EstablishRequest>(&body) {
                    Ok(r) => {
                        let pk = hex::decode(&r.peer_pk).unwrap_or_default();
                        match establish_shared(&r.organ, &pk) {
                            Ok(ss) => Response::from_string(format!(
                                r#"{{"organ":"{}","shared_hash":"{}"}}"#,
                                r.organ, hash_hex(&ss)
                            )),
                            Err(e) => Response::from_string(format!(r#"{{"error":"{}"}}"#, e))
                        }
                    }
                    Err(_) => Response::from_string(r#"{"error":"invalid json"}"#.to_string())
                }
            }

            (Method::Get, "/integrity") => {
                let ok = verify_integrity();
                Response::from_string(format!(r#"{{"integrity":{},"status":"{}"}}"#, ok, if ok { "secure" } else { "alert" }))
            }

            _ => Response::from_string(r#"{"error":"not found"}"#.to_string())
        };

        let _ = req.respond(response.with_header(
            tiny_http::Header::from_bytes(&b"Content-Type"[..], &b"application/json"[..]).unwrap()
        ));
    }
}
