#!/usr/bin/env python3
import argparse
import importlib.util
import os
import socket
import subprocess
import sys

# --- Configuration ---
DEFAULT_SERVICES = {
    22: "SSH",
    80: "HTTP",
    443: "HTTPS",
    8083: "HestiaCP",
    5432: "PostgreSQL",
    3306: "MySQL/MariaDB",
    27017: "MongoDB",
    6379: "Redis",
    8000: "Supabase/API",
    8443: "Supabase/Kong",
    3000: "React/Node",
    8080: "Alt HTTP",
}


def install_package(package):
    """Install a Python package via pip."""
    print(f"[INFO] Installing required library: {package}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"[SUCCESS] {package} installed.")
    except subprocess.CalledProcessError:
        print(f"[ERROR] Failed to install {package}. Please install it manually.")
        sys.exit(1)


def ensure_dependencies():
    """Check for 'rich' library and install if missing."""
    if importlib.util.find_spec("rich") is None:
        install_package("rich")


# Ensure dependencies before importing
ensure_dependencies()

from rich.console import Console
from rich.table import Table

console = Console()


def run_command(command, ignore_errors=True):
    """Run a shell command and return its output."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=not ignore_errors,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""


def check_root():
    if os.geteuid() != 0:
        console.print("[bold red][ERROR] This script must be run as root.[/bold red]")
        console.print("Try: [yellow]sudo python3 fix_check_firewall.py[/yellow]")
        sys.exit(1)


def is_port_listening(port):
    """Check if a process is listening on the given port locally."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(("127.0.0.1", port)) == 0


def check_ufw_status(port):
    """Check if port is allowed in UFW."""
    status = run_command("ufw status")
    if "Status: inactive" in status:
        return "Inactive"

    # Check for exact port match in status output
    # Matches "8083/tcp" or "8083 " or "8083/udp"
    if f"{port}" in status and "ALLOW" in status:
        return "Allowed"
    return "Blocked/Missing"


def check_iptables_status(port):
    """Check if port is allowed in iptables."""
    # This is a basic grep check. IPTables is complex, but presence usually indicates a rule.
    output = run_command(
        f"iptables -L -n | grep ':{port} '"
    )  # Matches destination port
    if not output:
        output = run_command(f"iptables -L -n | grep 'dpt:{port}'")

    return "Found" if output else "Not Found"


def fix_firewall_rule(port, service_name):
    """Attempt to open the port in UFW."""
    console.print(
        f"[yellow]Attempting to allow port {port} ({service_name})...[/yellow]"
    )

    # 1. UFW
    ufw_out = run_command(f"ufw allow {port}/tcp")
    if "Rule added" in ufw_out or "Skipping" in ufw_out:
        console.print(f"[green]✔ UFW rule added for {port}.[/green]")
    else:
        console.print(f"[red]✘ Failed to add UFW rule for {port}.[/red]")

    # 2. HestiaCP (if exists)
    hestia_bin = "/usr/local/hestia/bin/v-add-firewall-rule"
    if os.path.exists(hestia_bin):
        run_command(f"{hestia_bin} ACCEPT 0.0.0.0/0 {port} TCP '{service_name}'")
        run_command("/usr/local/hestia/bin/v-update-firewall")
        console.print(f"[green]✔ HestiaCP firewall updated for {port}.[/green]")


def main():
    check_root()

    parser = argparse.ArgumentParser(description="Check and Fix Server Firewall Ports")
    parser.add_argument("-p", "--port", type=int, help="Specific port to check and fix")
    parser.add_argument(
        "--fix", action="store_true", help="Automatically attempt to open blocked ports"
    )
    args = parser.parse_args()

    services = DEFAULT_SERVICES.copy()
    if args.port:
        services[args.port] = "Custom Port"

    table = Table(title="Server Port & Firewall Status")
    table.add_column("Port", style="cyan", no_wrap=True)
    table.add_column("Service", style="magenta")
    table.add_column("Listening (Local)", style="blue")
    table.add_column("UFW Status", style="yellow")
    table.add_column("IPTables Rule", style="green")
    table.add_column("Action Needed", style="red")

    ports_to_fix = []

    sorted_ports = sorted(services.keys())

    with console.status(
        "[bold green]Scanning ports and firewall rules...[/bold green]"
    ):
        for port in sorted_ports:
            name = services[port]

            is_listening = is_port_listening(port)
            listening_str = "[green]Yes[/green]" if is_listening else "[dim]No[/dim]"

            ufw_status = check_ufw_status(port)
            ufw_str = (
                f"[green]{ufw_status}[/green]"
                if ufw_status == "Allowed"
                else f"[red]{ufw_status}[/red]"
            )
            if ufw_status == "Inactive":
                ufw_str = "[dim]Inactive[/dim]"

            iptables_status = check_iptables_status(port)
            iptables_str = (
                "[green]Found[/green]"
                if iptables_status == "Found"
                else "[dim]Not Found[/dim]"
            )

            action = ""
            if is_listening:
                if ufw_status == "Blocked/Missing":
                    action = "Open Port"
                    ports_to_fix.append(port)
                elif iptables_status == "Not Found" and ufw_status != "Allowed":
                    action = "Check Rules"

            table.add_row(
                str(port),
                name,
                listening_str,
                ufw_str,
                iptables_str,
                f"[bold red]{action}[/bold red]" if action else "[green]OK[/green]",
            )

    console.print(table)

    if ports_to_fix:
        if args.fix:
            console.print("\n[bold]Applying fixes...[/bold]")
            for port in ports_to_fix:
                fix_firewall_rule(port, services[port])
            console.print(
                "\n[bold green]Fixes applied. Re-run script to verify.[/bold green]"
            )
        else:
            console.print(
                "\n[bold yellow]To automatically open blocked ports, run:[/bold yellow]"
            )
            console.print(f"python3 {sys.argv[0]} --fix")
            if args.port:
                console.print(f"python3 {sys.argv[0]} --port {args.port} --fix")


if __name__ == "__main__":
    main()
