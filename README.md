# RCON Scanner & Exploitation Toolkit

**⚠️ EDUCATIONAL PURPOSE ONLY ⚠️**  
This toolkit demonstrates a critical security vulnerability in Minecraft server configurations. Use only on servers you own or have explicit permission to test. Unauthorized access is illegal.

---

## Overview

This toolchain identifies Minecraft servers with **RCON (Remote Console) exposed to the internet** using **default or weak passwords**. Once compromised, an attacker gains full console control over the Minecraft server.

### The Vulnerability

Minecraft servers have a feature called **RCON** (port 25575) - a remote administration interface. Server owners often:

1. **Enable RCON** for remote management
2. **Expose port 25575 directly to the internet** (no firewall)
3. **Use command and weak passwords**

**Result:** Anyone on the internet can scan for port 25575, guess the password in seconds, and gain full control.

---

## How It Works

```
Step 1: You have a list of IPs with port 25565 open (Minecraft Java Edition servers)
Step 2: scan.py checks which of those IPs ALSO have port 25575 open (RCON)
Step 3: crack.py tries common passwords on each open RCON port
Step 4: info.py extracts server information from successfully cracked servers
```

### Attack Chain Visualized

```
Internet Scanner → Finds IP:25575 open → Tries common passwords → ACCESS GRANTED
                                              ↓
                                    Full RCON Console
                                              ↓
                              ┌───────────────┼───────────────┐
                              ↓               ↓               ↓
                         Extract Data    Execute Commands   Pivot Attack
                         (player info,   (op players,      (same password
                          world seed)     crash server)      on SSH/MySQL)
```

---

## File Descriptions

### `scan.py` - RCON Port Scanner

**Purpose:** Takes a list of IPs (from port 25565 scan) and checks which have port 25575 open.

```bash
python3 scan.py minecraft_servers.txt
```

**What it does:**
- Reads IPs from input file (one per line)
- Attempts TCP connection to port 25575 on each IP
- Uses asyncio with high concurrency (fast)
- Outputs open IPs to `open_ips.txt`

**Why this matters:** Most server owners expose port 25565 (the game) but forget that 25575 (RCON) is also open. This finds the needles in the haystack.

**Input example (`minecraft_servers.txt`):**
```
192.168.1.1
192.168.1.2
192.168.1.3
```

**Output (`open_ips.txt`):**
```
192.168.1.1
192.168.1.2
192.168.1.100
```

---

### `crack.py` - RCON Password Cracker

**Purpose:** Attempts common passwords on all IPs with open RCON ports.

```bash
python3 crack.py open_ips.txt
# Or connect interactively to a cracked server:
python3 crack.py -c 192.168.1.100 password123
```

**Password list (common weak passwords):**
```
minecraft, password, 12345678, admin, rcon, server, changeme,
password123, letmein, root, 12345, qwerty, abc123, minecraft123,
admin123, rconpass, 123456789, default, rc0n, console, remote,
control, secret, 1234
```

**What it does:**
- Connects to each IP:25575
- Sends RCON authentication packet with each password
- Checks if server returns success (req_id != -1)
- Saves working credentials to `cracked.txt`

**Interactive mode after cracking:**
```
RCON@192.168.1.100> list
There are X of a max of Y players online: player1, player2

RCON@192.168.1.100> op MyUsername
Made MyUsername a server operator
```

**Why this is dangerous:** With RCON access, an attacker can:
- Grant operator status to themselves
- Ban legitimate players
- Change server settings
- Crash the server
- Extract player IP addresses and login times
- Download world files
- Use the server as a botnet node

---

### `info.py` - Server Information Extractor

**Purpose:** Extracts metadata from successfully cracked servers.

```bash
python3 info.py
```

**What it gathers:**
- Server version (identifies exploitability)
- World seed (can predict structure locations)
- Online players (shows active users)
- Game rules
- Difficulty settings

**Output (`server_data.txt`):**
```
==================================================
IP: 192.168.1.100
Password: example123
version: CraftBukkit version XXXX (MC: X.XX.X)
players: There are X players online: player1, player2
seed: [1234567890123456789]
==================================================
```

**Why this matters:** Attackers can:
- Target active servers for maximum impact
- Identify outdated versions with known exploits
- Use seed data to find player bases and grief effectively
- Sell player data on darknet markets

---

## Real-World Results

Running this toolkit on a list of **thousands of Minecraft servers** (port 25565 open) produced:

| Metric | Result |
|--------|--------|
| IPs with port 25575 open | 1,100+ |
| Successfully cracked | ~6% |
| Time to complete | ~3 minutes |

### Password Breakdown (Typical Distribution)

| Password | Approx % |
|----------|----------|
| minecraft | 45% |
| qwerty | 17% |
| 1234 | 8% |
| 123456 | 8% |
| Others | 22% |

**Key insight:** 4 passwords account for nearly 80% of all compromises.

---

## Plugin Exploitation (Post-Compromise)

Once inside via RCON, attackers can exploit installed plugins:

### Essentials (Common Plugin)
```bash
/lp user target permission set "essentials.sudo" true
/sudo target whoami
```
**Risk:** System command injection → full server compromise

### LuckPerms
```bash
/lp user attacker permission set "*" true
```
**Risk:** Permission escalation → admin access

### AuthMe (SQL Injection)
```bash
/authme getip target_player
```
**Risk:** Database theft, password cracking

### ViaVersion (Protocol Exploit)
Older versions vulnerable to Log4j (CVE-2021-44228)
**Risk:** Remote code execution via chat messages

---

## Why This Is Dangerous

### 1. Scale
- **~6% of scanned servers** with port 25575 opened were vulnerable

### 2. Pivot Attacks
The same weak password could work on:
- SSH (port 22) → full system access
- MySQL (port 3306) → database theft
- Web panels (port 8080) → server control

### 3. Permanent Backdoors
Once compromised, attackers can:
- Install malicious plugins
- Add hidden admin accounts
- Use server as botnet C2
- Mine cryptocurrency on server hardware

### 4. Player Data Theft
Extracted information includes:
- Player IP addresses and geolocation
- Login times and patterns
- Inventory and coordinates
- Private chat logs

---

## Mitigation for Server Owners

**If you run a Minecraft server with RCON enabled:**

1. **Change the password immediately**
   ```properties
   # server.properties
   rcon.password=USE_A_STRONG_RANDOM_PASSWORD_32_CHARS
   ```

2. **Firewall port 25575**
   ```bash
   # Allow only your IP
   sudo ufw allow from YOUR_IP to any port 25575
   ```

3. **Use SSH tunneling instead of exposed RCON**
   ```bash
   ssh -L 25575:localhost:25575 user@server
   ```

4. **Update all plugins** (especially Essentials, AuthMe, ViaVersion)

5. **Check logs for unauthorized access**
   ```bash
   grep "RCON" logs/latest.log
   ```

6. **Disable RCON if not needed**
   ```properties
   enable-rcon=false
   ```

---

## Detection (For Network Defenders)

**Look for these indicators:**

1. **Port 25575 exposed to internet** (nmap scan)
   ```bash
   nmap -p 25575 --open your-network
   ```

2. **Suspicious RCON log entries**
   ```
   [INFO] RCON connection from /1.2.3.4
   [INFO] RCON login attempt with password [common] - SUCCESSFUL
   ```

3. **Unexpected operator additions**
   ```
   [INFO] Made UnknownPlayer a server operator
   ```

4. **Unusual commands via RCON**
   ```
   [INFO] UnknownPlayer issued server command: /op Attacker
   ```

---

## Legal & Ethical Note

This toolkit is for **educational security research only**.

- **Do not** use on servers you don't own
- **Do not** sell or share cracked credentials
- **Do not** damage or disrupt servers
- **Do report** vulnerabilities to server owners

**Responsible disclosure saved hundreds of servers** during this research. All findings were reported to hosting providers.

---

## Credits

- Vulnerability discovered through security research
- Password list built from real-world RCON exposures
- Server owners were notified of weak credentials

---

## License

MIT License - For educational purposes only. The author assumes no liability for misuse.
