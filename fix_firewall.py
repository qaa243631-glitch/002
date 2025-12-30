import os
import subprocess
import sys


def run_command(command, ignore_errors=False):
    """Run a shell command and return its output."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        if not ignore_errors:
            print(f"[ERROR] Command failed: {command}")
            print(f"Error output: {e.stderr.strip()}")
        return None


def check_root():
    if os.geteuid() != 0:
        print(
            "[ERROR] This script must be run as root. Try 'sudo python3 fix_firewall.py'"
        )
        sys.exit(1)


def fix_ufw():
    print("\n--- Checking UFW (Uncomplicated Firewall) ---")
    status = run_command("ufw status", ignore_errors=True)

    if status and "inactive" in status:
        print("[INFO] UFW is inactive. Configuring and enabling it...")
        # Allow essential ports first to avoid locking out
        run_command("ufw allow 22/tcp")
        run_command("ufw allow 80/tcp")
        run_command("ufw allow 443/tcp")
        run_command("ufw allow 8083/tcp")

        # Enable UFW non-interactively
        run_command("echo 'y' | ufw enable")
        print("[SUCCESS] UFW enabled and ports 22, 80, 443, 8083 allowed.")
    else:
        print("[INFO] UFW is active. Ensuring port 8083 is allowed...")
        run_command("ufw allow 8083/tcp")
        print("[SUCCESS] UFW rule for 8083 updated.")


def fix_hestia_firewall():
    print("\n--- Checking HestiaCP Firewall ---")
    hestia_bin = "/usr/local/hestia/bin"

    if not os.path.exists(hestia_bin):
        print("[WARN] HestiaCP binary directory not found. Is Hestia installed?")
        return

    # Try to add rule via Hestia CLI
    # v-add-firewall-rule ACTION IP PORT PROTOCOL [COMMENT]
    print("[INFO] Attempting to add HestiaCP firewall rule for port 8083...")
    # We ignore errors because the rule might already exist
    cmd = f"{hestia_bin}/v-add-firewall-rule ACCEPT 0.0.0.0/0 8083 TCP 'HestiaCP_Port'"
    run_command(cmd, ignore_errors=True)

    # Update firewall
    print("[INFO] forcing HestiaCP firewall update...")
    run_command(f"{hestia_bin}/v-update-firewall")
    print("[SUCCESS] HestiaCP firewall rules updated.")


def check_iptables():
    print("\n--- Verifying iptables ---")
    output = run_command("iptables -L -n | grep 8083", ignore_errors=True)
    if output:
        print("[SUCCESS] Port 8083 found in iptables rules:")
        print(output)
    else:
        print(
            "[WARN] Port 8083 NOT found in iptables! Something might still be blocking it."
        )


def main():
    check_root()
    fix_ufw()
    fix_hestia_firewall()
    check_iptables()
    print("\n[DONE] Firewall configuration attempt complete.")
    print(
        "NOTE: If you still cannot access port 8083, the issue is likely your CLOUD PROVIDER'S external firewall."
    )


if __name__ == "__main__":
    main()
