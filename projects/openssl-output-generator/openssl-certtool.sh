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
    echo -e "${CYAN}Usage: $0 [options]${NC}"
    echo ""
    echo "Options:"
    echo "  --help              Show this help message and exit"
    echo "  --input <path>      Specify the input .pfx, .p12, or .p7b certificate file"
    echo "  --output <prefix>   Specify the base output file path/name (e.g., /tmp/mycert)"
    echo ""
    echo "Created By Richard Troiano - 2026"
    exit 0
}

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --help) show_help ;;
        --input) INPUT_FILE="$2"; shift ;;
        --output) OUTPUT_BASE="$2"; shift ;;
        *) echo -e "${RED}Error: Unknown parameter passed: $1${NC}"; exit 1 ;;
    esac
    shift
done

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
if [[ -z "$INPUT_FILE" ]]; then
    read -p "Enter the full path to the certificate file [Default: ./cert.pfx]: " INPUT_FILE
    INPUT_FILE="${INPUT_FILE:-./cert.pfx}"
fi

if [[ ! -f "$INPUT_FILE" ]]; then
    echo -e "${RED}Error: Certificate file not found at '$INPUT_FILE'.${NC}"
    exit 1
fi

case "${INPUT_FILE##*.}" in
    p7b|P7B)
        INPUT_TYPE="p7b"
        ;;
    pfx|PFX|p12|P12)
        INPUT_TYPE="pfx"
        ;;
    *)
        echo -e "${RED}Error: Unsupported certificate type. Use .pfx, .p12, or .p7b.${NC}"
        exit 1
        ;;
esac

if [[ -z "$OUTPUT_BASE" ]]; then
    out_dir=$(dirname "$INPUT_FILE")
    base_name=$(basename "$INPUT_FILE")
    OUTPUT_BASE="$out_dir/${base_name%.*}"
fi

detect_p7b_format() {
    if openssl pkcs7 -inform DER -in "$INPUT_FILE" -print_certs -out /dev/null 2>/dev/null; then
        PKCS7_FORMAT="DER"
        return 0
    fi

    if openssl pkcs7 -inform PEM -in "$INPUT_FILE" -print_certs -out /dev/null 2>/dev/null; then
        PKCS7_FORMAT="PEM"
        return 0
    fi

    echo -e "${RED}Error: Unable to parse .p7b file format.${NC}"
    exit 1
}

prepare_certificate_input() {
    if [[ "$INPUT_TYPE" == "p7b" ]]; then
        export CERT_PASS=""
        detect_p7b_format
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
    echo ""
    echo -e "${YELLOW}Advanced Tools:${NC}"
    echo "  7) View Expiration Date & SANs (Requires .cer)"
    echo "  8) Verify Cert & Key Match     (Requires .cer & .key)"
    echo "  9) Print Cert as Base64        (Requires .cer)"
    echo " 10) Generate a new CSR          (Requires .key)"
    echo ""
    echo -e "${RED} 11) Exit & Wipe Memory${NC}"
    echo ""
    
    read -p "Select an option [1-11]: " choice

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
        7) view_cert_info ;;
        8) verify_match ;;
        9) display_base64 ;;
       10) generate_csr ;;
       11) 
            echo -e "\nExiting. Have a great day!"
            exit 0 
            ;;
        *) 
            echo -e "\n${RED}[!] Invalid choice. Please try again.${NC}"
            ;;
    esac
done
