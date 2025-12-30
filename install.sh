#!/bin/bash

# --- MAIN CONFIGURATION ---
LOG_FILE="/var/log/vps_setup.log"
# USER_EMAIL="admin@$(hostname)"
USER_EMAIL="realmarkdean@outlook.com"
ADMIN_PASSWORD="YourSecurePassword123" # Change this!

# --- HELPERS ---
echo_info() { echo -e "\e[34m[INFO]\e[0m $1"; }
echo_error() { echo -e "\e[31m[ERROR]\e[0m $1" >&2; }

# Trap errors
cleanup() {
    if [ "$?" -ne 0 ]; then
        echo_error "Installation failed! Check $LOG_FILE for details."
    fi
}
trap cleanup EXIT

# Ensure running as root
if [[ $EUID -ne 0 ]]; then
   echo_error "This script must be run as root"
   exit 1
fi

exec > >(tee -i $LOG_FILE) 2>&1

set -euo pipefail

# 1. Update System
echo_info "Updating system packages..."
apt update && apt upgrade -y

# 2. Install Dependencies
echo_info "Installing build essentials and libs..."
apt install -y build-essential curl git python3-pip python3-venv libpq-dev

# 3. Install Node.js LTS (Check if exists first)
if ! command -v node &> /dev/null; then
    echo_info "Installing Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt install -y nodejs
else
    echo_info "Node.js already installed."
fi

# 4. Prepare HestiaCP
echo_info "Downloading HestiaCP installer..."
if [ ! -f hst-install.sh ]; then
    wget https://raw.githubusercontent.com/hestiacp/hestiacp/release/install/hst-install.sh
fi

# 5. Run HestiaCP Installation
# Note: We check if Hestia is already installed to avoid double-install errors
if [ ! -d "/usr/local/hestia" ]; then
    echo_info "Starting HestiaCP installation (this will take a few minutes)..."
    bash hst-install.sh --apache no --phpfpm yes --multiphp no --vsftpd yes --proftpd no \
    --named yes --mysql no --postgresql yes --exim yes --dovecot yes --clamav no \
    --spamassassin no --iptables yes --fail2ban yes --quota no --api yes \
    --force --interactive no --hostname "$(hostname)" --email "$USER_EMAIL" --password "$ADMIN_PASSWORD"
else
    echo_info "HestiaCP is already installed. Skipping."
fi

echo_info "Setup complete! Logs available at $LOG_FILE"