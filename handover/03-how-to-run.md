# Execution Guide

Follow these steps to run the benchmark matrix from scratch. We utilize `docker restart` between phases to cleanly wipe any background Python processes before initiating the next test.

## 1. Environment Initialization

Start the network, clear old telemetry, and install all required Python dependencies:
`rm -f client/results.csv`
`docker-compose up -d`
`docker exec -it bor-box pip install -r requirements.txt`
`docker exec -it attacker pip install -r requirements.txt`
`docker exec -it client pip install -r requirements.txt`

## 2. Phase 1: Baseline Benchmark

Establish standard traffic latency and integrity without any attacks:
`docker restart bor-box attacker`
`docker exec -d bor-box sh -c "BORBOX_ENABLED=true python bor_box.py"`
`docker exec -it client python benchmark.py --mode run --scenario "1. Baseline" --duration 12`

## 3. Phase 2: Under Attack (Protection Disabled)

Simulate resolver vulnerability by running the attack in passthrough mode. Example below uses `tudoor` (requires optimized 8 threads):
`docker restart bor-box attacker`
`docker exec -d bor-box sh -c "BORBOX_ENABLED=false python bor_box.py"`
`docker exec -d attacker python attacker.py --mode tudoor --duration 16 --threads 8`
`docker exec -it client python benchmark.py --mode run --scenario "2. Attack (No BOR-BOX)" --duration 12`

*(Note: You can swap `--mode tudoor` with `cache_poison`, `qps_flood`, or `water_torture` to test other vectors).*

## 4. Phase 3: Under Attack (Protection Active)

Enable the dual-queue architecture and run the exact same attack to measure the mitigation success:
`docker restart bor-box attacker`
`docker exec -d bor-box sh -c "BORBOX_ENABLED=true python bor_box.py"`
`docker exec -d attacker python attacker.py --mode tudoor --duration 16 --threads 8`
`docker exec -it client python benchmark.py --mode run --scenario "3. Attack (BOR-BOX Active)" --duration 12`

## 5. Render Results

Compile the CSV logs into all five presentation-ready PNG charts:
`docker exec -it client python benchmark.py --mode plot`
