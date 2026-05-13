import asyncio
import sys

PORT = 25575
TIMEOUT = 0.7
CONCURRENCY = 2000

async def check_host(ip, sem):
    async with sem:
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, PORT),
                timeout=TIMEOUT
            )
            writer.close()
            await writer.wait_closed()
            print(f"[OPEN] {ip}")
            return ip
        except:
            return None

async def worker_batch(ips, sem):
    return await asyncio.gather(*(check_host(ip, sem) for ip in ips))

async def main():
    if len(sys.argv) < 2:
        print(f"Usage: python3 {sys.argv[0]} ips.txt")
        return
    with open(sys.argv[1]) as f:
        ips = [line.strip() for line in f if line.strip()]
    print(f"[*] Loaded {len(ips)} IPs")
    sem = asyncio.Semaphore(CONCURRENCY)
    chunk_size = 5000
    results = []
    for i in range(0, len(ips), chunk_size):
        chunk = ips[i:i + chunk_size]
        print(f"[*] Batch {i//chunk_size} scanning {len(chunk)} IPs")
        batch_results = await worker_batch(chunk, sem)
        results.extend([ip for ip in batch_results if ip])
    with open("open_ips.txt", "w") as f:
        for ip in results:
            f.write(ip + "\n")
    print(f"\n[*] Done. Found {len(results)} open hosts.")

if __name__ == "__main__":
    asyncio.run(main())