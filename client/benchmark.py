import argparse
import time
import socket
import csv
import os
import random
import dns.message
import dns.rdatatype
import matplotlib.pyplot as plt
import pandas as pd

TARGET_IP = "10.5.0.20"
TARGET_PORT = 53
TIMEOUT = 0.25  

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
        msg = dns.message.make_query("target-banking.example.com.", dns.rdatatype.A)
        # Force the client into the Fishbowl guessing space
        msg.id = random.randint(1, 250)
        
        success = False
        outcome = "Timeout"
        rtt_ms = None
        try:
            sock.sendto(msg.to_wire(), (TARGET_IP, TARGET_PORT))
            data, _ = sock.recvfrom(4096)
            t1 = time.time()
            rtt_ms = (t1 - t0) * 1000.0
            
            resp_msg = dns.message.from_wire(data)
            answer_ip = ""
            if resp_msg.answer:
                for rr in resp_msg.answer[0]:
                    answer_ip = rr.to_text()
            
            if answer_ip == "6.6.6.6":
                outcome = "Poisoned"
                success = False
            else:
                outcome = "Clean"
                success = True

        except socket.timeout:
            rtt_ms = TIMEOUT * 1000.0
        except Exception:
            rtt_ms = TIMEOUT * 1000.0
            
        records.append({
            "timestamp": round(elapsed_rel, 3),
            "scenario": scenario_label,
            "success": success,
            "rtt_ms": round(rtt_ms, 2),
            "outcome": outcome
        })
        time.sleep(interval)
        
    sock.close()
    
    file_exists = os.path.isfile(output_csv)
    with open(output_csv, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "scenario", "success", "rtt_ms", "outcome"])
        if not file_exists:
            writer.writeheader()
        writer.writerows(records)
        
    print(f"[+] Benchmark finished. Total queries sent: {len(records)}")

def generate_charts(csv_file="results.csv", output_dir="/app/charts"):
    os.makedirs(output_dir, exist_ok=True)
    df = pd.read_csv(csv_file)
    
    # 1. Integrity Stacked Bar Chart
    plt.figure(figsize=(9, 6))
    outcomes = df.groupby(['scenario', 'outcome']).size().unstack(fill_value=0)
    for col in ['Clean', 'Poisoned', 'Timeout']:
        if col not in outcomes.columns:
            outcomes[col] = 0
    outcomes = outcomes[['Clean', 'Poisoned', 'Timeout']]
    outcomes_pct = outcomes.div(outcomes.sum(axis=1), axis=0) * 100
    
    colors = ['#2ca02c', '#d62728', '#7f7f7f']
    ax = outcomes_pct.plot(kind='bar', stacked=True, color=colors, edgecolor='black', figsize=(9, 6))
    plt.title("Resolver Integrity (% Resolution Outcome)", fontsize=13, fontweight='bold')
    plt.ylabel("Percentage (%)", fontsize=11)
    plt.xlabel("Scenario", fontsize=11)
    plt.xticks(rotation=10)
    plt.legend(title="Outcome", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(f"{output_dir}/slide_chart1_integrity.png", dpi=300)
    plt.close()
    
    # 2. Latency Line Chart
    plt.figure(figsize=(9, 5))
    for scenario, group in df.groupby("scenario", sort=False):
        plt.plot(group["timestamp"], group["rtt_ms"], label=scenario, alpha=0.85, linewidth=2)
        
    plt.title("Legitimate Query Latency (ms)", fontsize=13, fontweight='bold')
    plt.xlabel("Test Duration (Seconds)", fontsize=11)
    plt.ylabel("Round Trip Time / RTT (ms)", fontsize=11)
    plt.legend(loc="upper right")
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/slide_chart2_latency.png", dpi=300)
    plt.close()
    
    # 3. Outcome Scatter Plot
    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True, sharey=True)
    colors_map = {'Clean': '#2ca02c', 'Poisoned': '#d62728', 'Timeout': '#7f7f7f'}
    markers_map = {'Clean': 'o', 'Poisoned': 'X', 'Timeout': 's'}
    
    for i, scenario in enumerate(df['scenario'].unique()):
        subset = df[df['scenario'] == scenario]
        for outcome in ['Clean', 'Poisoned', 'Timeout']:
            out_sub = subset[subset['outcome'] == outcome]
            if not out_sub.empty:
                axes[i].scatter(out_sub['timestamp'], out_sub['rtt_ms'], 
                                color=colors_map[outcome], marker=markers_map[outcome], 
                                label=outcome, alpha=0.7)
        axes[i].set_title(scenario)
        axes[i].grid(True, linestyle='--', alpha=0.5)
        if i == 0:
            axes[i].legend(loc='upper right')
            
    plt.xlabel("Test Duration (Seconds)")
    fig.text(0.04, 0.5, 'RTT (ms)', va='center', rotation='vertical')
    plt.tight_layout(rect=[0.05, 0, 1, 1])
    plt.savefig(f"{output_dir}/slide_chart3_scatter.png", dpi=300)
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
