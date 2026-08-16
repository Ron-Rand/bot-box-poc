# PoC Architecture

The BOR-BOX Proof of Concept utilizes a containerized micro-network to simulate a real-world DNS resolution environment under heavy attack. 

## Network Topology

The environment runs on a dedicated Docker bridge network (`bor-net` at `10.5.0.0/24`) consisting of four nodes:

1. **DNS Resolver (10.5.0.10):** A lightweight CoreDNS server acting as the target.
2. **BOR-BOX Proxy (10.5.0.20):** The security middlebox. All client and attacker traffic is routed here first.
3. **Attacker (10.5.0.30):** A multi-threaded container dedicated to flooding the network with malicious traffic.
4. **Client (10.5.0.40):** A benchmarking node generating legitimate queries (`www.example.com`) to measure availability and latency.

## The Dual-Queue Engine

To adhere to the "Availability First" design philosophy (zero hard drops), the BOR-BOX proxy implements a hybrid queueing system:

* **High-Priority Queue:** Traffic that passes all security rules is forwarded immediately to the upstream resolver.
* **Rate-Limited Queue:** Traffic matching malicious signatures or volumetric thresholds is shunted to an asynchronous queue processed at a strict maximum of 10 QPS. 

## Concurrency Limiting

To accurately simulate real-world resolver resource exhaustion, BOR-BOX implements a Global Concurrency Limiter (an `asyncio.Semaphore` capped at 20 concurrent slots). When the proxy is disabled, attack traffic instantly consumes these slots, causing legitimate client packets to time out. When the proxy is active, malicious traffic is quarantined, leaving the processing slots open for legitimate requests.
