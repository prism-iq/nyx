#!/bin/bash
# BENCH-VERIFY - Cross-verification with Opus + Gemini
# Vérifie les claims scientifiques avec deux LLMs

PAPER="/home/ego-bash/nyx-v2/PAPER.md"
RESULTS_DIR="/home/ego-bash/nyx-v2/verify-results"
GEMINI_KEY="${GEMINI_API_KEY:-}"

C='\033[38;5;208m'
G='\033[38;5;114m'
R='\033[38;5;203m'
B='\033[38;5;117m'
N='\033[0m'

mkdir -p "$RESULTS_DIR"

PROMPT_VERIFY='You are a scientific fact-checker. Evaluate ONLY the empirical claims below.
For each claim, respond with:
- VERIFIED: Strong peer-reviewed evidence exists
- DISPUTED: Evidence exists but contested or weak replication
- HYPOTHESIS: Theoretical, not yet proven
- FALSE: Contradicted by evidence
- SPECULATIVE: Not mainstream science

Be strict. Cite sources if possible. No philosophical commentary.

Claims to verify:
1. DNA emits photons 200-800nm (biophotons)
2. Heart EM field is 100x stronger than brain
3. Schumann-EEG coherence reaches 0.8
4. Microtubules maintain quantum coherence at 37C
5. ZPF couples with glutamate receptors (Keppler)
6. DMT is produced endogenously in human brain

Respond in JSON format:
{"claims": [{"id": 1, "status": "...", "confidence": 0.0-1.0, "note": "..."}]}'

verify_with_opus() {
    echo -e "${B}══ OPUS VERIFICATION ══${N}"

    local result_file="$RESULTS_DIR/opus-$(date +%Y%m%d-%H%M%S).json"

    # Use claude CLI directly
    echo "$PROMPT_VERIFY" | claude --print --dangerously-skip-permissions 2>/dev/null > "$result_file"

    if [ -s "$result_file" ]; then
        echo -e "${G}Opus response saved: $result_file${N}"
        cat "$result_file"
    else
        echo -e "${R}Opus verification failed${N}"
        return 1
    fi
}

verify_with_gemini() {
    echo -e "${B}══ GEMINI VERIFICATION ══${N}"

    if [ -z "$GEMINI_KEY" ]; then
        echo -e "${R}GEMINI_API_KEY not set${N}"
        echo -e "${C}Set with: export GEMINI_API_KEY=your_key${N}"
        return 1
    fi

    local result_file="$RESULTS_DIR/gemini-$(date +%Y%m%d-%H%M%S).json"

    # Gemini API call
    local response=$(curl -s "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=$GEMINI_KEY" \
        -H 'Content-Type: application/json' \
        -d "{
            \"contents\": [{
                \"parts\": [{\"text\": $(echo "$PROMPT_VERIFY" | jq -Rs .)}]
            }],
            \"generationConfig\": {
                \"temperature\": 0.1,
                \"maxOutputTokens\": 2048
            }
        }")

    # Extract text from response
    echo "$response" | jq -r '.candidates[0].content.parts[0].text // "ERROR"' > "$result_file"

    if [ -s "$result_file" ] && ! grep -q "ERROR" "$result_file"; then
        echo -e "${G}Gemini response saved: $result_file${N}"
        cat "$result_file"
    else
        echo -e "${R}Gemini verification failed${N}"
        echo "$response" | jq .
        return 1
    fi
}

compare_results() {
    echo -e "\n${C}══ COMPARISON ══${N}"

    local opus_latest=$(ls -t "$RESULTS_DIR"/opus-*.json 2>/dev/null | head -1)
    local gemini_latest=$(ls -t "$RESULTS_DIR"/gemini-*.json 2>/dev/null | head -1)

    if [ -z "$opus_latest" ] || [ -z "$gemini_latest" ]; then
        echo -e "${R}Missing results for comparison${N}"
        return 1
    fi

    echo -e "${B}Opus:${N} $opus_latest"
    echo -e "${B}Gemini:${N} $gemini_latest"

    # Simple diff
    echo -e "\n${C}Differences:${N}"
    diff --color=always "$opus_latest" "$gemini_latest" || true
}

quick_verify() {
    # Quick single-claim verification
    local claim="$1"
    echo -e "${C}Quick verify: $claim${N}"

    echo "Verify this scientific claim. Reply: VERIFIED/DISPUTED/HYPOTHESIS/FALSE with one sentence explanation: $claim" | \
        claude --print --dangerously-skip-permissions 2>/dev/null
}

case "${1:-help}" in
    opus|o)
        verify_with_opus
        ;;
    gemini|g)
        verify_with_gemini
        ;;
    both|b)
        verify_with_opus
        echo ""
        verify_with_gemini
        echo ""
        compare_results
        ;;
    compare|c)
        compare_results
        ;;
    quick|q)
        shift
        quick_verify "$*"
        ;;
    paper|p)
        echo -e "${C}Extracting claims from PAPER.md...${N}"
        grep -E "^\| .* \| .* \| (VERIFIED|HYPOTHESIS|DISPUTED|SPECULATIVE)" "$PAPER" | \
            while read -r line; do
                claim=$(echo "$line" | cut -d'|' -f2 | xargs)
                status=$(echo "$line" | cut -d'|' -f5 | xargs)
                echo -e "${B}$claim${N} → $status"
            done
        ;;
    help|h|*)
        echo -e "${C}══ BENCH-VERIFY ══${N}"
        echo "  opus|o       Verify with Claude Opus"
        echo "  gemini|g     Verify with Gemini (needs GEMINI_API_KEY)"
        echo "  both|b       Run both and compare"
        echo "  compare|c    Compare latest results"
        echo "  quick|q      Quick single claim: bench-verify quick 'claim here'"
        echo "  paper|p      List claims from PAPER.md"
        echo ""
        echo -e "${C}Examples:${N}"
        echo "  ./bench-verify.sh both"
        echo "  ./bench-verify.sh quick 'DNA emits biophotons'"
        echo "  GEMINI_API_KEY=xxx ./bench-verify.sh gemini"
        ;;
esac
