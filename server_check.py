import socket
import urllib.request
import urllib.error
import ssl
import sys
import time

def check_port(host, port, timeout=5):
    """Check if a port is open."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            print(f"[OK] Port {port} on {host} is OPEN.")
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        print(f"[FAIL] Port {port} on {host} is CLOSED or unreachable.")
        return False

def check_http_status(url, timeout=10):
    """Check if the URL returns a valid HTTP response."""
    # Context to ignore self-signed certificate warnings
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(url, context=ctx, timeout=timeout) as response:
            status_code = response.getcode()
            if 200 <= status_code < 400:
                print(f"[OK] Service at {url} is responding (HTTP {status_code}).")
                return True
            else:
                print(f"[WARN] Service at {url} returned HTTP {status_code}.")
                return False
    except urllib.error.HTTPError as e:
        # HestiaCP login page might return 200, but let's handle errors
        print(f"[WARN] HTTP Error for {url}: {e.code} {e.reason}")
        # Even a 401/403 means the server is running, just not accessible without auth
        return True 
    except urllib.error.URLError as e:
        print(f"[FAIL] Failed to reach {url}. Reason: {e.reason}")
        return False
    except Exception as e:
        print(f"[FAIL] unexpected error checking {url}: {e}")
        return False

def main():
    HOST = 'localhost'
    PORT = 8083
    URL = f"https://{HOST}:{PORT}/login/"

    print(f"Checking HestiaCP status on {HOST}...")
    
    # 1. Check TCP Port
    port_open = check_port(HOST, PORT)
    
    if not port_open:
        print("\n[!] CRITICAL: HestiaCP port 8083 is not open. The service might be down.")
        sys.exit(1)

    # 2. Check HTTP Response
    print(f"Checking HTTP response from {URL}...")
    http_ok = check_http_status(URL)

    if port_open and http_ok:
        print("\n[SUCCESS] HestiaCP appears to be running correctly.")
        sys.exit(0)
    else:
        print("\n[!] WARNING: Port is open but HTTP check failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
