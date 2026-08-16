import argparse
import time
import socket
import csv
import os
import dns.message
import dns.rdatatype
import matplotlib.pyplot as plt
import pandas as pd

TARGET_IP = "10.5.0.20"
TARGET_PORT = 53
TIMEOUT = 0.25  # 250ms threshold for dropped/degraded packets

def run_benchmark(duration_sec=12, qps=30, output_csv="results.csv", scenario_label="Baseline"):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(TIMEOUT)
    
    end_time = time.time() + duration_sec
    interval = 1.0 / qps
    records = []
    
    print(f"[*] Running benchmark: '{scenario_label}' for {duration_sec}s...")
    start_epoch = time.time()
    
    while time.time() < end_time:
        t0 = time.time()
        elapsed_rel = t0 - start_epoch
        msg = dns.message.make_query("www.example.com.", dns.rdatatype.A)
        
        success = False
        rtt_ms = None
        try:
            sock.sendto(msg.to_wire(), (TARGET_IP, TARGET_PORT))
            data, _ = sock.recvfrom(4096)
            t1 = time.time()
            rtt_ms = (t1 - t0) * 1000.0
            success = True
        except socket.timeout:
            rtt_ms = TIMEOUT * 1000.0
            success = False
        except Exception:
            rtt_ms = TIMEOUT * 1000.0
            success = False
            
        records.append({
            "timestamp": round(elapsed_rel, 3),
            "scenario": scenario_label,
            "success": success,
            "rtt_ms": round(rtt_ms, 2)
        })
        time.sleep(interval)
        
    sock.close()
    
    file_exists = os.path.isfile(output_csv)
    with open(output_csv, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "scenario", "success", "rtt_ms"])
        if not file_exists:
            writer.writeheader()
        writer.writerows(records)
        
    print(f"[+] Benchmark finished. Total queries sent: {len(records)}")

def generate_charts(csv_file="results.csv", output_dir="/app/charts"):
    os.makedirs(output_dir, exist_ok=True)
    df = pd.read_csv(csv_file)
    
    # 1. Availability Bar Chart
    plt.figure(figsize=(8, 5))
    grouped_success = df.groupby("scenario", sort=False)["success"].mean() * 100
    colors = ['#2ca02c' if 'BOR-BOX Active' in s or 'Baseline' in s else '#d62728' for s in grouped_success.index]
    
    ax = grouped_success.plot(kind='bar', color=colors, edgecolor='black', width=0.45)
    plt.title("Resolver Availability (% Legitimate Queries Answered)", fontsize=13, fontweight='bold')
    plt.ylabel("Success Rate (%)", fontsize=11)
    plt.xlabel("Scenario", fontsize=11)
    plt.ylim(0, 115)
    plt.xticks(rotation=10)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    for p in ax.patches:
        ax.annotate(f"{p.get_height():.1f}%", (p.get_x() + p.get_width() / 2., p.get_height() + 2),
                    ha='center', va='bottom', fontsize=10, fontweight='bold')
    plt.tight_layout()
    plt.savefig(f"{output_dir}/slide_chart1_availability.png", dpi=300)
    plt.close()
    
    # 2. Latency Over Time Line Chart
    plt.figure(figsize=(9, 5))
    for scenario, group in df.groupby("scenario", sort=False):
        plt.plot(group["timestamp"], group["rtt_ms"], label=scenario, alpha=0.85, linewidth=2)
        
    plt.title("Legitimate Query Latency Under Attack (ms)", fontsize=13, fontweight='bold')
    plt.xlabel("Test Duration (Seconds)", fontsize=11)
    plt.ylabel("Round Trip Time / RTT (ms)", fontsize=11)
    plt.legend(loc="upper right")
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/slide_chart2_latency.png", dpi=300)
    plt.close()
    
    print(f"[✓] Charts generated successfully in {output_dir}/")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["run", "plot"], required=True)
    parser.add_argument("--scenario", type=str, default="Baseline")
    parser.add_argument("--duration", type=int, default=12)
    parser.add_argument("--csv", type=str, default="results.csv")
    args = parser.parse_args()

    if args.mode == "run":
        run_benchmark(args.duration, qps=30, output_csv=args.csv, scenario_label=args.scenario)
    elif args.mode == "plot":
        generate_charts(csv_file=args.csv)
