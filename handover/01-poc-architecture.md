# PoC Architecture

The BOR-BOX Proof of Concept utilizes a containerized micro-network to simulate a real-world DNS resolution environment under heavy attack. 

## Network Topology

The environment runs on a dedicated Docker bridge network (`bor-net` at `10.5.0.0/24`) consisting of four nodes:

1. **DNS Resolver (10.5.0.10):** A lightweight CoreDNS server acting as the target.
2. **BOR-BOX Proxy (10.5.0.20):** The security middlebox. All client and attacker traffic is routed here first.
3. **Attacker (10.5.0.30):** A multi-threaded container dedicated to flooding the network with malicious traffic.
4. **Client (10.5.0.40):** A benchmarking node generating legitimate queries to measure availability, latency, and integrity.

## The Dual-Queue Engine

To adhere to the "Availability First" design philosophy (zero hard drops), the BOR-BOX proxy implements a hybrid queueing system:

* **High-Priority Queue:** Traffic that passes all security rules is forwarded immediately to the upstream resolver.
* **Rate-Limited Queue:** Traffic matching malicious signatures, volumetric thresholds, or stateful similarity tracks is shunted to an asynchronous queue processed at a strict maximum of 10 QPS. 

## Concurrency & Simulated Vulnerabilities

To accurately simulate real-world resolver limits, BOR-BOX implements a Global Concurrency Limiter (an `asyncio.Semaphore` capped at 20 concurrent slots). 

Additionally, the proxy's upstream forwarding logic contains a simulated backend vulnerability. If it receives a malformed packet (e.g., multiple question sections), it forces a 300ms processing lock to simulate a logic panic and CPU exhaustion. 

When the proxy is disabled, attacker traffic triggers these vulnerabilities directly, consuming the concurrency slots and causing legitimate client packets to time out. When the proxy is active, malicious traffic is quarantined to the rate-limited queue, leaving the processing slots open for legitimate requests.
