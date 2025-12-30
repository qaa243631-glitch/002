# Ubuntu 24.04 Server Setup Guide

This guide outlines the steps to set up a new Ubuntu 24.04 server, including essential tools, Node.js, and HestiaCP with PostgreSQL.

## Prerequisites

*   A fresh installation of Ubuntu 24.04.
*   Root access to the server.

## Installation Script: `install.sh`

The `install.sh` script automates the setup process. It performs the following actions:

1.  **Updates System Packages**: Ensures all existing packages are up to date.
2.  **Installs Dependencies**: Installs `build-essential`, `curl`, `git`, `python3-pip`, `python3-venv`, and `libpq-dev`.
3.  **Installs Node.js LTS**: Installs the latest Node.js LTS version if not already present.
4.  **Prepares HestiaCP**: Downloads the HestiaCP installer script.
5.  **Runs HestiaCP Installation**: Installs HestiaCP with specific configurations:
    *   Apache: No
    *   PHP-FPM: Yes
    *   Multi-PHP: No
    *   vsftpd: Yes
    *   proftpd: No
    *   Named (DNS): Yes
    *   MySQL: No
    *   PostgreSQL: Yes
    *   Exim (Mail Server): Yes
    *   Dovecot (IMAP/POP3): Yes
    *   ClamAV (Antivirus): No
    *   SpamAssassin: No
    *   iptables (Firewall): Yes
    *   Fail2Ban: Yes
    *   Quota: No
    *   API: Yes
    *   Interactive: No
    *   Hostname: Automatically set to your server's hostname.
    *   Email: `admin@$(hostname)` (Configurable)
    *   Password: `YourSecurePassword123` (Configurable - **CHANGE THIS!**)

### Configuration

Before running the script, you might want to adjust the following variables at the beginning of `install.sh`:

```E:\code\ubuntu24_server\install.sh#L3-5
LOG_FILE="/var/log/vps_setup.log"
USER_EMAIL="admin@$(hostname)"
ADMIN_PASSWORD="YourSecurePassword123" # Change this!
```

*   `LOG_FILE`: Path to the log file for the installation process.
*   `USER_EMAIL`: The email address for HestiaCP's administrative user.
*   `ADMIN_PASSWORD`: **CRITICAL**: Change `YourSecurePassword123` to a strong, unique password for your HestiaCP admin user.

### How to Use

1.  **Download the script**:
    ```bash
    wget https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/install.sh
    ```
    (Replace `YOUR_USERNAME` and `YOUR_REPO` with your actual GitHub username and repository if you've hosted the script there, or create the `install.sh` file manually on your server.)

2.  **Make the script executable**:
    ```bash
    chmod +x install.sh
    ```

3.  **Run the script as root**:
    ```bash
    sudo ./install.sh
    ```

The script will log its progress to `/var/log/vps_setup.log`. If any errors occur, they will be noted in the console output and the log file.

### Important Notes

*   **Security**: Always change the `ADMIN_PASSWORD` in the script before running it on a production server.
*   **HestiaCP**: The HestiaCP installation is non-interactive (`--interactive no`). You will not be prompted for input during its setup.
*   **Logging**: All output from the script, including info and error messages, will be redirected to the console and simultaneously saved to the specified `LOG_FILE`.

## After Installation

Once the script completes, you can access your HestiaCP control panel by navigating to `https://your_server_ip:8083` in your web browser. Use `admin` as the username and the password you set in the `ADMIN_PASSWORD` variable.