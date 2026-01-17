// nyx neuron
use std::collections::HashMap;

const PHI: f64 = 1.618033988749895;

struct Neuron {
    id: String,
    weights: Vec<f64>,
    bias: f64,
}

impl Neuron {
    fn new(id: &str) -> Self {
        Neuron {
            id: id.to_string(),
            weights: vec![PHI; 8],
            bias: PHI / 2.0,
        }
    }

    fn think(&self, input: &[f64]) -> f64 {
        let sum: f64 = input.iter()
            .zip(&self.weights)
            .map(|(i, w)| i * w)
            .sum();
        (sum + self.bias).tanh()
    }
}

fn main() {
    let nyx = Neuron::new("nyx");
    println!("nyx alive");
}
