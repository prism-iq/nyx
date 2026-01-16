#!/bin/bash
# BENCH-LOOP - Verification loop with source hunting
# Sci-Hub, Web, Papers, Review

CLAIMS_FILE="/home/ego-bash/nyx-v2/claims.json"
RESULTS_DIR="/home/ego-bash/nyx-v2/verify-results"
SOURCES_DIR="/home/ego-bash/nyx-v2/sources"

C='\033[38;5;208m'
G='\033[38;5;114m'
R='\033[38;5;203m'
B='\033[38;5;117m'
N='\033[0m'

mkdir -p "$RESULTS_DIR" "$SOURCES_DIR"

# Claims to verify with DOIs and PubMed search terms
declare -A CLAIMS
declare -A SEARCH_TERMS

CLAIMS["biophotons"]="DNA emits photons 200-800nm|10.1038/s41598-024-80469-0|VERIFIED"
SEARCH_TERMS["biophotons"]="biophotons DNA ultraweak photon emission"

CLAIMS["dna_storage"]="Photons stored between DNA strands|10.3389/fphys.2024.1348915|VERIFIED"
SEARCH_TERMS["dna_storage"]="DNA photon storage exciplex"

CLAIMS["cardiac_em"]="Heart EM 100x brain|heartmath.org|VERIFIED*"
SEARCH_TERMS["cardiac_em"]="heart electromagnetic field brain magnetocardiography"

CLAIMS["schumann_eeg"]="Schumann-EEG coherence 0.8|10.3389/feart.2017.00067|DISPUTED"
SEARCH_TERMS["schumann_eeg"]="Schumann resonance EEG brain coherence"

CLAIMS["microtubules"]="Quantum coherence 37C|10.1103/PhysRevE.65.061901|HYPOTHESIS"
SEARCH_TERMS["microtubules"]="microtubule quantum coherence consciousness"

CLAIMS["zpf"]="ZPF-brain coupling|keppler 2025|SPECULATIVE"
SEARCH_TERMS["zpf"]="zero point field consciousness brain"

CLAIMS["dmt"]="Endogenous DMT production|10.1038/s41598-019-45812-w|VERIFIED"
SEARCH_TERMS["dmt"]="endogenous DMT brain pineal dimethyltryptamine"

fetch_scihub() {
    local doi="$1"
    local output="$SOURCES_DIR/$(echo "$doi" | tr '/' '_').pdf"

    if [ -f "$output" ]; then
        echo -e "${G}Already cached: $output${N}"
        return 0
    fi

    echo -e "${B}Fetching from Sci-Hub: $doi${N}"

    # Try multiple Sci-Hub mirrors
    for mirror in "sci-hub.se" "sci-hub.st" "sci-hub.ru"; do
        local url="https://$mirror/$doi"
        local html=$(curl -sL --max-time 30 "$url" 2>/dev/null)

        # Extract PDF link
        local pdf_url=$(echo "$html" | grep -oP 'https://[^"]+\.pdf' | head -1)

        if [ -n "$pdf_url" ]; then
            echo -e "${G}Found PDF: $pdf_url${N}"
            curl -sL --max-time 60 "$pdf_url" -o "$output" 2>/dev/null
            if [ -s "$output" ]; then
                echo -e "${G}Saved: $output${N}"
                return 0
            fi
        fi
    done

    echo -e "${R}Failed to fetch: $doi${N}"
    return 1
}

search_pubmed() {
    local query="$1"
    echo -e "${B}Searching PubMed: $query${N}"

    local encoded=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$query'))")
    local url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=$encoded&retmax=3&retmode=json"

    local result=$(curl -s "$url" 2>/dev/null)
    local ids=$(echo "$result" | jq -r '.esearchresult.idlist[]' 2>/dev/null | tr '\n' ' ')

    if [ -n "$ids" ] && [ "$ids" != " " ]; then
        echo -e "${G}Found PMIDs: $ids${N}"
        echo "$ids"
        return 0
    else
        echo -e "${R}No PubMed results${N}"
        return 1
    fi
}

get_abstract() {
    local pmid="$1"
    echo -e "${B}Fetching abstract: PMID $pmid${N}"

    local url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=$pmid&rettype=abstract&retmode=text"
    curl -s "$url" 2>/dev/null | head -50
}

verify_claim_loop() {
    local key="$1"
    local data="${CLAIMS[$key]}"

    if [ -z "$data" ]; then
        echo -e "${R}Unknown claim: $key${N}"
        return 1
    fi

    IFS='|' read -r description doi status <<< "$data"

    echo -e "\n${C}═══════════════════════════════════════════════════════════════${N}"
    echo -e "${C}VERIFYING: $description${N}"
    echo -e "${C}DOI/Source: $doi${N}"
    echo -e "${C}Current status: $status${N}"
    echo -e "${C}═══════════════════════════════════════════════════════════════${N}"

    # Step 1: Try Sci-Hub if DOI
    if [[ "$doi" =~ ^10\. ]]; then
        fetch_scihub "$doi"
    fi

    # Step 2: Search PubMed with optimized query
    echo -e "\n${B}Searching PubMed...${N}"
    local search_query="${SEARCH_TERMS[$key]:-$description}"
    local pmids=$(search_pubmed "$search_query" | tail -1)

    # Step 3: Get abstracts
    if [ -n "$pmids" ] && [ "$pmids" != "No PubMed results" ]; then
        for pmid in $pmids; do
            if [[ "$pmid" =~ ^[0-9]+$ ]]; then
                echo -e "\n${B}--- PMID $pmid ---${N}"
                get_abstract "$pmid" | head -30
                echo ""
            fi
        done
    fi

    # Step 4: Ask for AI review
    echo -e "\n${C}AI REVIEW REQUEST:${N}"
    echo "Based on the evidence above, verify: $description"
    echo "Current status: $status"
    echo ""
}

run_full_loop() {
    local iteration=0
    local max_iterations="${1:-1}"

    while [ $iteration -lt $max_iterations ]; do
        iteration=$((iteration + 1))
        echo -e "\n${C}══════════════════════════════════════════════════════════════${N}"
        echo -e "${C}              BENCH LOOP - ITERATION $iteration/$max_iterations${N}"
        echo -e "${C}══════════════════════════════════════════════════════════════${N}"

        for key in "${!CLAIMS[@]}"; do
            verify_claim_loop "$key"
            sleep 2  # Rate limiting
        done

        # Summary
        echo -e "\n${C}══════════════════════════════════════════════════════════════${N}"
        echo -e "${C}              ITERATION $iteration COMPLETE${N}"
        echo -e "${C}══════════════════════════════════════════════════════════════${N}"

        echo -e "\n${B}Current Status:${N}"
        for key in "${!CLAIMS[@]}"; do
            IFS='|' read -r desc doi status <<< "${CLAIMS[$key]}"
            echo -e "  $key: $status"
        done

        if [ $iteration -lt $max_iterations ]; then
            echo -e "\n${C}Waiting 10s before next iteration...${N}"
            sleep 10
        fi
    done
}

export_results() {
    local output="$RESULTS_DIR/bench-$(date +%Y%m%d-%H%M%S).json"

    echo "{" > "$output"
    echo '  "timestamp": "'$(date -Iseconds)'",' >> "$output"
    echo '  "claims": {' >> "$output"

    local first=true
    for key in "${!CLAIMS[@]}"; do
        IFS='|' read -r desc doi status <<< "${CLAIMS[$key]}"
        [ "$first" = true ] || echo "," >> "$output"
        first=false
        echo "    \"$key\": {\"description\": \"$desc\", \"doi\": \"$doi\", \"status\": \"$status\"}" >> "$output"
    done

    echo '  }' >> "$output"
    echo "}" >> "$output"

    echo -e "${G}Exported: $output${N}"
    cat "$output"
}

case "${1:-help}" in
    loop|l)
        run_full_loop "${2:-1}"
        ;;
    claim|c)
        verify_claim_loop "$2"
        ;;
    scihub|s)
        fetch_scihub "$2"
        ;;
    pubmed|p)
        search_pubmed "$2"
        ;;
    abstract|a)
        get_abstract "$2"
        ;;
    export|e)
        export_results
        ;;
    list)
        echo -e "${C}Claims to verify:${N}"
        for key in "${!CLAIMS[@]}"; do
            IFS='|' read -r desc doi status <<< "${CLAIMS[$key]}"
            echo -e "  ${B}$key${N}: $desc [$status]"
        done
        ;;
    help|h|*)
        echo -e "${C}══ BENCH-LOOP ══${N}"
        echo "  loop|l [n]      Run full verification loop (n iterations)"
        echo "  claim|c <key>   Verify single claim"
        echo "  scihub|s <doi>  Fetch paper from Sci-Hub"
        echo "  pubmed|p <q>    Search PubMed"
        echo "  abstract|a <id> Get abstract by PMID"
        echo "  export|e        Export results to JSON"
        echo "  list            List all claims"
        echo ""
        echo -e "${C}Claims:${N} biophotons, dna_storage, cardiac_em, schumann_eeg, microtubules, zpf, dmt"
        ;;
esac
