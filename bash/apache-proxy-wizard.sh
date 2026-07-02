#!/bin/bash

# ==============================================================================
# COLOR DEFINITIONS
# ==============================================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# ==============================================================================
# FUNCTION: Root Privilege Check
# ==============================================================================
if [ "$EUID" -ne 0 ]; then 
  echo -e "${RED}[!] Error: Please run as root (use sudo).${NC}"
  exit 1
fi

echo -e "${CYAN}=======================================================${NC}"
echo -e "${CYAN}  🚀 Apache Reverse Proxy Configuration Wizard (SSL)   ${NC}"
echo -e "${CYAN}=======================================================${NC}"

# ==============================================================================
# SECTION: Environment Validation (Apache)
# ==============================================================================
if ! command -v apache2 >/dev/null 2>&1; then
    read -p "$(echo -e ${YELLOW}"Apache2 is not installed. Install it now? (y/n): "${NC})" inst_choice
    if [[ "$inst_choice" =~ ^[Yy]$ ]]; then
        echo -e "${CYAN}[*] Installing Apache2...${NC}"
        apt update && apt install -y apache2
    else
        echo -e "${RED}Exiting: Apache2 is required.${NC}"
        exit 1
    fi
fi

if ! systemctl is-active --quiet apache2; then
    read -p "$(echo -e ${YELLOW}"Apache2 service is not running. Start it now? (y/n): "${NC})" start_choice
    if [[ "$start_choice" =~ ^[Yy]$ ]]; then
        echo -e "${CYAN}[*] Starting Apache2...${NC}"
        systemctl start apache2
    else
        echo -e "${YELLOW}[!] Warning: Apache is not running. Configuration will continue.${NC}"
    fi
fi

# ==============================================================================
# SECTION: Firewall Validation (UFW)
# ==============================================================================
echo -e "\n${CYAN}--- Firewall Validation ---${NC}"
if command -v ufw >/dev/null 2>&1 && ufw status | grep -q "Status: active"; then
    echo -e "${CYAN}[*] UFW firewall is currently ACTIVE.${NC}"
    
    # Check Port 80
    if ! ufw status | grep -Eqw "80/tcp|Apache Full|Apache"; then
        read -p "$(echo -e ${YELLOW}"Port 80 (HTTP) is not explicitly open. Open it now? (y/n): "${NC})" open_80
        if [[ "$open_80" =~ ^[Yy]$ ]]; then
            ufw allow 80/tcp
            echo -e "${GREEN}[+] Port 80 opened.${NC}"
        fi
    else
         echo -e "${GREEN}[+] Port 80 (HTTP) is already open.${NC}"
    fi

    # Check Port 443
    if ! ufw status | grep -Eqw "443/tcp|Apache Full|Apache Secure"; then
        read -p "$(echo -e ${YELLOW}"Port 443 (HTTPS) is not explicitly open. Open it now? (y/n): "${NC})" open_443
        if [[ "$open_443" =~ ^[Yy]$ ]]; then
            ufw allow 443/tcp
            echo -e "${GREEN}[+] Port 443 opened.${NC}"
        fi
    else
         echo -e "${GREEN}[+] Port 443 (HTTPS) is already open.${NC}"
    fi
else
    echo -e "${YELLOW}[!] UFW is inactive or not installed. Skipping firewall checks.${NC}"
fi

# ==============================================================================
# SECTION: User Input Collection
# ==============================================================================
echo -e "\n${CYAN}--- Application Details ---${NC}"
read -p "Enter Application Name (e.g., myapp): " application
read -p "Enter Fully Qualified Domain Name (e.g., app.example.com): " fqdn
read -p "Enter Backend IP Address [127.0.0.1]: " ip_address
ip_address=${ip_address:-127.0.0.1} 
read -p "Enter Backend Port (e.g., 8080): " proxy_port

read -p "Enter Web Application Path (URL Proxy Path) [/]: " application_path
application_path=${application_path:-/}

echo -e "\n${CYAN}--- SSL Certificates ---${NC}"
read -p "Full path to .crt file: " certpath
read -p "Full path to .key file: " keypath
read -p "Full path to .pem file (optional): " pempath

echo -e "\n${CYAN}--- Extra Features ---${NC}"
read -p "Force HTTP to HTTPS redirect? (y/n): " redirect_choice

# ==============================================================================
# FUNCTION: validate_file
# ==============================================================================
validate_file() {
    local label=$1
    local file_path=$2
    
    if [ ! -f "$file_path" ]; then
        echo -e "${RED}[!] WARNING: $label not found at $file_path${NC}"
    else
        echo -e "${GREEN}[+] $label found.${NC}"
        read -p "    Display contents? (y/n): " show_file
        if [[ "$show_file" =~ ^[Yy]$ ]]; then
            echo -e "${CYAN}--- Start: $file_path ---${NC}"
            cat "$file_path"
            echo -e "${CYAN}--- End ---${NC}\n"
        fi
    fi
}

echo -e "\n${CYAN}[*] Validating certificate files...${NC}"
validate_file "Certificate (.crt)" "$certpath"
validate_file "Private Key (.key)" "$keypath"
if [ -n "$pempath" ]; then
    validate_file "Chain/PEM (.pem)" "$pempath"
fi

# ==============================================================================
# SECTION: Pre-Flight Summary
# ==============================================================================
echo -e "\n${CYAN}=======================================================${NC}"
echo -e "${CYAN}  Configuration Summary                                ${NC}"
echo -e "${CYAN}=======================================================${NC}"
echo -e "  App Name : ${GREEN}$application${NC}"
echo -e "  Domain   : ${GREEN}$fqdn${NC}"
echo -e "  Target   : ${GREEN}http://$ip_address:$proxy_port$application_path${NC}"
echo -e "  Redirect : $([[ "$redirect_choice" =~ ^[Yy]$ ]] && echo -e "${GREEN}Yes${NC}" || echo -e "${RED}No${NC}")"
echo -e "${CYAN}=======================================================${NC}"

read -p "Proceed with generating this configuration? (y/n): " confirm_build
if [[ ! "$confirm_build" =~ ^[Yy]$ ]]; then
    echo -e "${RED}Aborted by user.${NC}"
    exit 0 
fi

# ==============================================================================
# SECTION: Module Activation
# ==============================================================================
echo -e "\n${CYAN}[*] Enabling Apache modules...${NC}"
a2enmod ssl proxy proxy_http headers rewrite

# ==============================================================================
# SECTION: Configuration Generation (to /tmp)
# ==============================================================================
TMP_CONFIG="/tmp/${application}.conf"
DEST_CONFIG="/etc/apache2/sites-available/${application}.conf"

echo -e "${CYAN}[*] Writing configuration to sandbox at $TMP_CONFIG...${NC}"

cat <<EOF > "$TMP_CONFIG"
# ----------------------------------------------------------------------
# Automatically generated via Reverse Proxy Script
# Application: $application | Domain: $fqdn
# ----------------------------------------------------------------------
EOF

if [[ "$redirect_choice" =~ ^[Yy]$ ]]; then
cat <<EOF >> "$TMP_CONFIG"

<VirtualHost *:80>
    ServerName $fqdn
    Redirect permanent / https://$fqdn/
</VirtualHost>
EOF
fi

cat <<EOF >> "$TMP_CONFIG"

<VirtualHost *:443>
    ServerName $fqdn
    DocumentRoot /var/www/html

    SSLEngine on
    SSLCertificateFile $certpath
    SSLCertificateKeyFile $keypath
EOF

if [ -n "$pempath" ]; then
    echo "    SSLCertificateChainFile $pempath" >> "$TMP_CONFIG"
fi

cat <<EOF >> "$TMP_CONFIG"

    # SSL Hardening (disables SSLv3, TLS 1.0, TLS 1.1)
    SSLProtocol             all -SSLv3 -TLSv1 -TLSv1.1
    SSLCipherSuite          ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384
    SSLHonorCipherOrder     off
    SSLSessionTickets       off

    ProxyPreserveHost On
    ProxyRequests Off

    RequestHeader set X-Forwarded-Proto "https"
    RequestHeader set X-Forwarded-Port "443"

    ProxyPass $application_path http://$ip_address:$proxy_port/
    ProxyPassReverse $application_path http://$ip_address:$proxy_port/

    ErrorLog \${APACHE_LOG_DIR}/${application}_error.log
    CustomLog \${APACHE_LOG_DIR}/${application}_access.log combined
</VirtualHost>
EOF

# ==============================================================================
# SECTION: Sandbox Validation & Human Verification
# ==============================================================================
echo -e "\n${CYAN}--- Generated Configuration Review ---${NC}"
cat "$TMP_CONFIG"
echo -e "${CYAN}--------------------------------------${NC}"

echo -e "\n${CYAN}[*] Running pre-flight syntax validation on temporary config...${NC}"
# The -c flag allows us to append an Include directive dynamically during the config test
# so it tests your new file alongside the rest of Apache's configuration.
if apache2ctl -t -c "Include $TMP_CONFIG"; then
    echo -e "${GREEN}[+] Syntax OK. The configuration is valid.${NC}"
else
    echo -e "\n${RED}[!] ERROR: Syntax validation failed for the generated config!${NC}"
    echo -e "${YELLOW}Aborting deployment to protect Apache. Review the file at $TMP_CONFIG.${NC}"
    exit 1
fi

echo -e "\n${CYAN}--- Deployment Consent ---${NC}"
read -p "$(echo -e ${YELLOW}"Do you agree to copy this configuration to Apache and proceed? (y/n): "${NC})" agree_copy
if [[ ! "$agree_copy" =~ ^[Yy]$ ]]; then
    echo -e "${RED}Deployment aborted by user. Temporary config remains at $TMP_CONFIG.${NC}"
    exit 0
fi

# ==============================================================================
# SECTION: Deployment Strategy
# ==============================================================================
# Backup existing config if it exists
if [ -f "$DEST_CONFIG" ]; then
    echo -e "${YELLOW}[!] Existing configuration found. Backing up to ${application}.conf.bak...${NC}"
    cp "$DEST_CONFIG" "${DEST_CONFIG}.bak"
fi

echo -e "${GREEN}[*] Copying configuration to $DEST_CONFIG...${NC}"
cp "$TMP_CONFIG" "$DEST_CONFIG"

echo -e "\n${CYAN}--- Site Activation ---${NC}"
read -p "Enable site using 'a2ensite ${application}.conf'? (y/n): " a2ensite_choice
if [[ "$a2ensite_choice" =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}[*] Running a2ensite...${NC}"
    a2ensite "${application}.conf"
fi

# Final sanity check before restart
echo -e "\n${CYAN}[*] Running final Apache configuration syntax test...${NC}"
if ! apache2ctl configtest; then
    echo -e "\n${RED}[!] ERROR: Final configuration syntax is invalid!${NC}"
    read -p "Abort Apache restart to fix the config? (y/n): " abort_choice
    if [[ "$abort_choice" =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Aborting restart. Please check $DEST_CONFIG.${NC}"
        exit 1
    fi
fi

# ==============================================================================
# SECTION: Finalization
# ==============================================================================
echo -e "\n${CYAN}[*] Restarting Apache to apply changes...${NC}"
systemctl restart apache2

echo -e "\n${GREEN}=======================================================${NC}"
echo -e "${GREEN}  ✅ Setup Process Complete!                           ${NC}"
echo -e "${GREEN}=======================================================${NC}"
echo -e "  Domain: https://$fqdn$application_path"
echo -e "  Config: $DEST_CONFIG"
echo -e "${GREEN}=======================================================${NC}\n"
