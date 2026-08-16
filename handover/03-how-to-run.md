# Execution Guide

Follow these steps to run the benchmark matrix from scratch. We utilize `docker restart` between phases to cleanly wipe any background Python processes before initiating the next test.

## 1. Environment Initialization

Start the network and install all required Python dependencies:
`docker-compose up -d`
`docker exec -it bor-box pip install -r requirements.txt`
`docker exec -it attacker pip install -r requirements.txt`
`docker exec -it client pip install -r requirements.txt`

## 2. Phase 1: Baseline Benchmark

Establish standard traffic latency without any attacks:
`docker restart bor-box`
`docker exec -d bor-box python bor_box.py`
`docker exec -it client python benchmark.py --mode run --scenario "1. Baseline" --duration 12`

## 3. Phase 2: Under Attack (Protection Disabled)

Simulate resolver failure by running the attack in passthrough mode (No BOR-BOX). Choose one attack mode (`water_torture`, `qps_flood`, or `cache_poison`):
`docker restart bor-box`
`docker exec -d bor-box sh -c "BORBOX_ENABLED=false python bor_box.py"`
`docker exec -d attacker python attacker.py --mode water_torture --duration 16 --threads 12`
`docker exec -it client python benchmark.py --mode run --scenario "2. Attack (No BOR-BOX)" --duration 12`

## 4. Phase 3: Under Attack (Protection Active)

Enable the dual-queue architecture and run the exact same attack to measure the mitigation success:
`docker restart bor-box`
`docker exec -d bor-box sh -c "BORBOX_ENABLED=true python bor_box.py"`
`docker exec -d attacker python attacker.py --mode water_torture --duration 16 --threads 12`
`docker exec -it client python benchmark.py --mode run --scenario "3. Attack (BOR-BOX Active)" --duration 12`

## 5. Render Results

Compile the CSV logs into presentation-ready PNG charts:
`docker exec -it client python benchmark.py --mode plot`
