#!/bin/bash

# ==========================================
# 1. Initialization & Security Setup
# ==========================================
# Color codes for readable output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Secure Cleanup: Ensure password is wiped from memory upon exit or Ctrl+C
trap 'unset CERT_PASS; echo -e "${GREEN}[SECURE] Credentials securely wiped from memory.${NC}"' EXIT INT TERM

INPUT_FILE=""
OUTPUT_BASE=""

show_help() {
    local exit_code="${1:-0}"
    echo -e "${CYAN}Usage: $0 [options]${NC}"
    echo ""
    echo "Options:"
    echo "  --help              Show this help message and exit"
    echo "  --input <path>      Specify the input .pfx, .p12, or .p7b certificate file"
    echo "  --output <prefix>   Specify the base output file path/name (e.g., /tmp/mycert)"
    echo ""
    echo "Interactive Menu:"
    echo "  - Use the interactive menu after running the script; option 7 creates a combined .pem (private key, primary cert, then CA chain)."
    echo ""
    echo "Created By Richard Troiano - 2026"
    exit "$exit_code"
}

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --help) show_help 0 ;;
        --input) INPUT_FILE="$2"; shift ;;
        --output) OUTPUT_BASE="$2"; shift ;;
        *) echo -e "${RED}Error: Unknown parameter passed: $1${NC}"; exit 1 ;;
    esac
    shift
done

if [[ -z "$INPUT_FILE" || -z "$OUTPUT_BASE" ]]; then
    echo -e "${RED}Error: Both --input and --output arguments are required.${NC}"
    echo ""
    show_help 1
fi

if ! command -v openssl &> /dev/null; then
    echo -e "${RED}Error: openssl is not installed or not in your PATH.${NC}"
    exit 1
fi

clear
echo -e "${CYAN}======================================================${NC}"
echo -e "${CYAN}    OpenSSL Certificate Utility Tool                  ${NC}"
echo -e "${CYAN}======================================================${NC}"
echo ""

# ==========================================
# 2. Interactive Prompts
# ==========================================
if [[ ! -f "$INPUT_FILE" ]]; then
    echo -e "${RED}Error: Certificate file not found at '$INPUT_FILE'.${NC}"
    exit 1
fi

detect_input_format() {
    # Check for PKCS#7 PEM format first
    if openssl pkcs7 -inform PEM -in "$INPUT_FILE" -print_certs -out /dev/null 2>/dev/null; then
        INPUT_TYPE="p7b"
        PKCS7_FORMAT="PEM"
        return 0
    fi

    # Check for PKCS#7 DER format
    if openssl pkcs7 -inform DER -in "$INPUT_FILE" -print_certs -out /dev/null 2>/dev/null; then
        INPUT_TYPE="p7b"
        PKCS7_FORMAT="DER"
        return 0
    fi

    # Check for PKCS#12 (PFX/P12) format by probing with a dummy password
    local probe_err
    probe_err=$(openssl pkcs12 -in "$INPUT_FILE" -nokeys -passin pass:dummy_pass_probe -info 2>&1 >/dev/null)
    if [[ "$probe_err" == *"Mac verify error"* ]] || openssl pkcs12 -in "$INPUT_FILE" -nokeys -passin pass: -info >/dev/null 2>/dev/null; then
        INPUT_TYPE="pfx"
        return 0
    fi

    # Fallback to extension check if structure check is inconclusive
    case "${INPUT_FILE##*.}" in
        p7b|P7B)
            INPUT_TYPE="p7b"
            # Default format check fallback
            if openssl pkcs7 -inform DER -in "$INPUT_FILE" -print_certs -out /dev/null 2>/dev/null; then
                PKCS7_FORMAT="DER"
            else
                PKCS7_FORMAT="PEM"
            fi
            return 0
            ;;
        pfx|PFX|p12|P12)
            INPUT_TYPE="pfx"
            return 0
            ;;
    esac

    return 1
}

if ! detect_input_format; then
    echo -e "${RED}Error: Unsupported certificate type. File content is unrecognized and extension is unsupported.${NC}"
    exit 1
fi

if [[ -z "$OUTPUT_BASE" ]]; then
    out_dir=$(dirname "$INPUT_FILE")
    base_name=$(basename "$INPUT_FILE")
    OUTPUT_BASE="$out_dir/${base_name%.*}"
fi

prepare_certificate_input() {
    if [[ "$INPUT_TYPE" == "p7b" ]]; then
        export CERT_PASS=""
        return 0
    fi

    if openssl pkcs12 -in "$INPUT_FILE" -nokeys -passin pass: -info >/dev/null 2>&1; then
        export CERT_PASS=""
        return 0
    fi

    read -s -p "Enter the .pfx password: " raw_pass
    export CERT_PASS="$raw_pass"
    unset raw_pass
    echo -e "\n"
}

prepare_certificate_input

# ==========================================
# 3. Secure Execution Functions
# ==========================================

extract_cer() {
    echo -e "\n${YELLOW}[+] Extracting Public Certificate...${NC}"
    if [[ "$INPUT_TYPE" == "p7b" ]]; then
        openssl pkcs7 -in "$INPUT_FILE" -inform "$PKCS7_FORMAT" -print_certs -out "${OUTPUT_BASE}.cer"
    else
        openssl pkcs12 -in "$INPUT_FILE" -clcerts -nokeys -legacy -out "${OUTPUT_BASE}.cer" -passin env:CERT_PASS
    fi
    if [ $? -eq 0 ]; then echo -e "${GREEN} -> Created: ${OUTPUT_BASE}.cer${NC}"; fi
}

extract_ca_chain() {
    echo -e "\n${YELLOW}[+] Extracting CA Chain (Root/Intermediate)...${NC}"
    if [[ "$INPUT_TYPE" == "p7b" ]]; then
        openssl pkcs7 -in "$INPUT_FILE" -inform "$PKCS7_FORMAT" -print_certs -out "${OUTPUT_BASE}_ca_chain.cer"
    else
        openssl pkcs12 -in "$INPUT_FILE" -nokeys -cacerts -legacy -out "${OUTPUT_BASE}_ca_chain.cer" -passin env:CERT_PASS
    fi
    if [ $? -eq 0 ]; then echo -e "${GREEN} -> Created: ${OUTPUT_BASE}_ca_chain.cer${NC}"; fi
}

extract_pem() {
    if [[ "$INPUT_TYPE" == "p7b" ]]; then
        echo -e "\n${RED}[!] Error: .p7b files do not contain private keys, so PEM extraction is not supported.${NC}"
        return
    fi

    echo -e "\n${YELLOW}[+] Extracting Cert + Unencrypted Key (.pem)...${NC}"
    openssl pkcs12 -in "$INPUT_FILE" -out "${OUTPUT_BASE}.pem" -nodes -legacy -passin env:CERT_PASS
    if [ $? -eq 0 ]; then
        chmod 600 "${OUTPUT_BASE}.pem"
        echo -e "${GREEN} -> Created and Secured (chmod 600): ${OUTPUT_BASE}.pem${NC}"
    fi
}

extract_key() {
    if [[ "$INPUT_TYPE" == "p7b" ]]; then
        echo -e "\n${RED}[!] Error: .p7b files do not contain private keys, so key extraction is not supported.${NC}"
        return
    fi

    echo -e "\n${YELLOW}[+] Extracting Unencrypted Private Key (.key)...${NC}"
    openssl pkcs12 -in "$INPUT_FILE" -nocerts -out "${OUTPUT_BASE}.key" -nodes -legacy -passin env:CERT_PASS
    if [ $? -eq 0 ]; then
        chmod 600 "${OUTPUT_BASE}.key"
        echo -e "${GREEN} -> Created and Secured (chmod 600): ${OUTPUT_BASE}.key${NC}"
    fi
}

copy_p12() {
    if [[ "$INPUT_TYPE" == "p7b" ]]; then
        echo -e "\n${RED}[!] Error: .p7b files cannot be converted to .p12 because they do not contain private keys.${NC}"
        return
    fi

    echo -e "\n${YELLOW}[+] Copying to .p12 format...${NC}"
    cp "$INPUT_FILE" "${OUTPUT_BASE}.p12"
    echo -e "${GREEN} -> Created: ${OUTPUT_BASE}.p12${NC}"
}

view_cert_info() {
    if [[ ! -f "${OUTPUT_BASE}.cer" ]]; then
        echo -e "\n${RED}[!] Error: ${OUTPUT_BASE}.cer not found. Please extract the .cer file first.${NC}"
        return
    fi
    echo -e "\n${YELLOW}=== Certificate Details ===${NC}"
    openssl x509 -in "${OUTPUT_BASE}.cer" -noout -subject -issuer -dates
    echo -e "${CYAN}--- Subject Alternative Names (SANs) ---${NC}"
    openssl x509 -in "${OUTPUT_BASE}.cer" -noout -text | grep -A 1 "Subject Alternative Name" || echo "None found."
    echo -e "${YELLOW}===========================${NC}"
}

verify_match() {
    if [[ ! -f "${OUTPUT_BASE}.cer" ]] || [[ ! -f "${OUTPUT_BASE}.key" ]]; then
        echo -e "\n${RED}[!] Error: Both .cer and .key files must exist to verify.${NC}"
        return
    fi
    echo -e "\n${YELLOW}[+] Calculating Modulus hashes...${NC}"
    cert_mod=$(openssl x509 -noout -modulus -in "${OUTPUT_BASE}.cer" | openssl md5)
    key_mod=$(openssl rsa -noout -modulus -in "${OUTPUT_BASE}.key" | openssl md5)
    
    echo "Cert MD5: $cert_mod"
    echo "Key MD5:  $key_mod"
    
    if [[ "$cert_mod" == "$key_mod" ]]; then
        echo -e "${GREEN}[SUCCESS] The Certificate and Private Key match perfectly!${NC}"
    else
        echo -e "${RED}[FAILED] Mismatch detected! The key does not belong to this certificate.${NC}"
    fi
}

display_base64() {
    if [[ ! -f "${OUTPUT_BASE}.cer" ]]; then
        echo -e "\n${RED}[!] Error: Please extract the .cer file first.${NC}"
        return
    fi
    echo -e "\n${YELLOW}[+] Base64 String for Cloud/K8s Secrets:${NC}"
    echo -e "${CYAN}------------------------------------------------${NC}"
    cat "${OUTPUT_BASE}.cer" | base64 -w 0
    echo -e "\n${CYAN}------------------------------------------------${NC}"
}

generate_csr() {
    if [[ ! -f "${OUTPUT_BASE}.key" ]]; then
        echo -e "\n${RED}[!] Error: Please extract the private key first.${NC}"
        return
    fi
    echo -e "\n${YELLOW}[+] Generating new CSR...${NC}"
    openssl req -new -key "${OUTPUT_BASE}.key" -out "${OUTPUT_BASE}.csr"
    if [ $? -eq 0 ]; then echo -e "${GREEN}[SUCCESS] CSR generated at: ${OUTPUT_BASE}.csr${NC}"; fi
}

extract_combined_pem() {
    if [[ "$INPUT_TYPE" == "p7b" ]]; then
        echo -e "\n${RED}[!] Error: .p7b files do not contain private keys, so combined PEM cannot be created.${NC}"
        return
    fi

    echo -e "\n${YELLOW}[+] Creating Combined .pem (key -> cert -> root)...${NC}"

    # Ensure individual pieces exist (will extract if missing)
    if [[ ! -f "${OUTPUT_BASE}.key" ]]; then
        extract_key
    fi
    if [[ ! -f "${OUTPUT_BASE}.cer" ]]; then
        extract_cer
    fi
    if [[ ! -f "${OUTPUT_BASE}_ca_chain.cer" ]]; then
        extract_ca_chain
    fi

    if [[ ! -f "${OUTPUT_BASE}.key" ]] || [[ ! -f "${OUTPUT_BASE}.cer" ]]; then
        echo -e "${RED}[!] Error: Required files (.key and .cer) are missing; cannot build combined PEM.${NC}"
        return
    fi

    combined_file="${OUTPUT_BASE}.combined.pem"

    # Concatenate in the requested order: private key, primary cert, then root/chain
    cat "${OUTPUT_BASE}.key" > "$combined_file"
    echo "" >> "$combined_file"
    cat "${OUTPUT_BASE}.cer" >> "$combined_file"
    echo "" >> "$combined_file"
    if [[ -f "${OUTPUT_BASE}_ca_chain.cer" ]]; then
        cat "${OUTPUT_BASE}_ca_chain.cer" >> "$combined_file"
    fi

    chmod 600 "$combined_file"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN} -> Created and Secured (chmod 600): ${combined_file}${NC}"
    fi
}

check_expiration() {
    if [[ ! -f "${OUTPUT_BASE}.cer" ]]; then
        echo -e "\n${RED}[!] Error: ${OUTPUT_BASE}.cer not found. Please extract the .cer file first.${NC}"
        return
    fi

    echo -e "\n${YELLOW}[+] Checking Certificate Expiration...${NC}"
    
    # Extract the end date of the certificate
    local end_date
    end_date=$(openssl x509 -enddate -noout -in "${OUTPUT_BASE}.cer" | cut -d= -f2)
    
    # Convert dates to epoch timestamps
    local end_epoch
    end_epoch=$(date -d "$end_date" +%s 2>/dev/null)
    if [[ -z "$end_epoch" ]]; then
        end_epoch=$(date -d "$end_date" +%s)
    fi
    
    local current_epoch
    current_epoch=$(date +%s)
    
    local diff_sec=$((end_epoch - current_epoch))
    local diff_days=$((diff_sec / 86400))
    
    echo -e "Expiration Date: ${GREEN}$end_date${NC}"
    
    if [[ "$diff_sec" -lt 0 ]]; then
        local abs_days=$(( -diff_days ))
        echo -e "${RED}[WARNING] Certificate EXPIRED $abs_days days ago!${NC}"
    else
        if [[ "$diff_days" -lt 30 ]]; then
            echo -e "${YELLOW}[WARNING] Certificate will expire in $diff_days days!${NC}"
        else
            echo -e "${GREEN}[OK] Certificate is valid. Expires in $diff_days days.${NC}"
        fi
    fi
}

# ==========================================
# 4. Continuous Interactive Menu
# ==========================================
while true; do
    echo ""
    echo -e "${CYAN}Target Context: ${NC}$OUTPUT_BASE"
    echo "------------------------------------------------------"
    echo -e "${YELLOW}Extraction Options:${NC}"
    echo "  1) Extract .cer (Public Certificate)"
    echo "  2) Extract .key (Unencrypted Private Key - SECURED)"
    echo "  3) Extract .pem (Cert + Private Key - SECURED)"
    echo "  4) Extract CA Chain (Root/Intermediate certificates)"
    echo "  5) Copy to .p12 format"
    echo "  6) Extract All of the above"
    echo "  7) Create Combined .pem (private key, primary cert, CA chain)"
    echo ""
    echo -e "${YELLOW}Advanced Tools:${NC}"
    echo "  8) View Expiration Date & SANs (Requires .cer)"
    echo "  9) Verify Cert & Key Match     (Requires .cer & .key)"
    echo " 10) Print Cert as Base64        (Requires .cer)"
    echo " 11) Generate a new CSR          (Requires .key)"
    echo " 12) Check Days Until Expiration (Requires .cer)"
    echo ""
    echo -e "${RED} 13) Exit & Wipe Memory${NC}"
    echo ""
    
    read -p "Select an option [1-13]: " choice

    case $choice in
        1) extract_cer ;;
        2) extract_key ;;
        3) extract_pem ;;
        4) extract_ca_chain ;;
        5) copy_p12 ;;
        6) 
            echo -e "${YELLOW}--- Extracting All Formats ---${NC}"
            extract_cer; extract_key; extract_pem; extract_ca_chain 
            ;;
        7) extract_combined_pem ;;
        8) view_cert_info ;;
        9) verify_match ;;
       10) display_base64 ;;
       11) generate_csr ;;
       12) check_expiration ;;
       13) 
            echo -e "\nExiting. Have a great day!"
            exit 0 
            ;;
        *) 
            echo -e "\n${RED}[!] Invalid choice. Please try again.${NC}"
            ;;
    esac
done
