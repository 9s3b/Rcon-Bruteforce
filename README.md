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

# Plugin Exploitation (Post-Compromise)

Once attackers gain access through exposed or weakly protected RCON, they may abuse installed plugins to escalate privileges, maintain persistence, or access sensitive player/server data.

## Essentials / EssentialsX

```bash
/lp user attacker permission set essentials.sudo true
/sudo target say test
```

### Important clarification

EssentialsX itself does not normally provide operating-system command execution.

However, attackers with administrative access may abuse features such as `/sudo` for:
- impersonation,
- moderation abuse,
- social engineering,
- or persistence after compromise.

---

## LuckPerms

```bash
/lp user attacker permission set * true
```

### What this does

If an attacker already has sufficient RCON or console access, they can grant themselves wildcard permissions (`*`) or operator-equivalent privileges.

### Real risk

* Full administrative control
* Hidden persistence groups
* Access to moderation/admin plugins
* Long-term privilege escalation

### Important clarification

LuckPerms itself is not the vulnerability here — it is being abused after initial compromise.

---

## Log4Shell

Many Minecraft servers and modded ecosystems were historically affected by Log4Shell (CVE-2021-44228).

### Conditions required

Servers were primarily vulnerable if they:

* used unpatched Java/Log4j versions,
* ran affected server software/mods,
* and had not applied Mojang or Java mitigations.

### Real risk

* Historical remote code execution (RCE)

### Current status

Modern Java runtimes, updated Paper/Spigot/Purpur builds, and maintained plugins generally mitigate this issue.

---

# Why This Is Dangerous

## 1. Scale

Some internet-wide scans and community research have found that a measurable percentage of publicly exposed RCON services were vulnerable due to:

* weak passwords,
* reused credentials,
* or insecure configurations.

One internet-wide scan commonly cited in community research found that roughly **~6% of publicly exposed RCON services** were accessible due to weak or guessable credentials.

### Real risk

Attackers routinely scan for:

* TCP/25575 (RCON)
* weak credentials
* exposed game administration services
* outdated management software

---

## 2. Pivot Attacks

The same weak or reused password may also work on:

* SSH (port 22) → full host access
* MySQL/MariaDB (port 3306) → database theft
* Web panels (port 8080/8081) → infrastructure control
* FTP/SFTP services → file modification

---


# Mitigation for Server Owners

## If you run a Minecraft server with RCON enabled:

### 1. Use a Strong Unique Password

```properties
# server.properties
rcon.password=LONG_RANDOM_UNIQUE_PASSWORD
```

Recommended:

* 20–32 random characters
* unique credentials
* password manager storage

---

### 2. Restrict Port 25575

```bash
# Allow only your IP
sudo ufw allow from YOUR_IP to any port 25575 proto tcp
```

Prefer binding RCON to localhost where possible.

---

### 3. Use SSH Tunneling or a VPN

```bash
ssh -L 25575:localhost:25575 user@server
```

This avoids exposing RCON directly to the internet.

---

### 4. Keep Software Updated

Update:

* Java runtime
* Paper/Spigot/Purpur
* plugins/mods
* server management panels

Especially:

* authentication plugins
* permission systems
* administration plugins

---

### 5. Audit Logs

```bash
grep -i "rcon" logs/latest.log
```

Look for:

* unknown IPs,
* unusual commands,
* permission changes,
* or unexpected operator assignments.

---

### 6. Disable RCON if Unnecessary

```properties
enable-rcon=false
```

---

# Detection (For Network Defenders)

## Indicators of Exposure or Compromise

### 1. Open RCON Port

```bash
nmap -p 25575 --open TARGET
```

---

### 2. Suspicious RCON Connections

```text
[INFO]: RCON connection from x.x.x.x
```

---

### 3. Permission Escalation Activity

```text
/ lp user attacker permission set * true
```

---

### 4. Unexpected Operator Grants

```text
Made UnknownPlayer a server operator
```

---

### 5. Suspicious Plugin Activity

Look for:

* newly added `.jar` files,
* modified startup scripts,
* cron/systemd persistence,
* or unusual scheduled tasks.

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
