# Attack Scenarios & Mitigations

The BOR-BOX PoC evaluates defensive performance against four specific DNS attack vectors grounded in recent academic literature.

## 1. Volumetric QPS Flood (Resource Exhaustion)
* **The Attack:** The attacker blasts high-volume, non-existent wildcard queries to starve the resolver's lookup queues.
* **The Rule:** Exact Domain Whitelisting.
* **The Mitigation:** Legitimate domains (`www.example.com`, `mail.example.com`) bypass limits. Unrecognized domains trigger a volumetric threshold (sliding window) and are demoted to the rate-limited queue.

## 2. DNS Water Torture (Random Subdomains)
* **The Attack:** The attacker generates high-entropy, random subdomains (e.g., `a8f9x01.example.com`) to bypass the resolver's cache and force NXDOMAIN processing storms.
* **The Rule:** Regex / Label Count Filter.
* **The Mitigation:** A compiled deterministic finite automaton (DFA) identifies subdomains with 8+ alphanumeric characters. Matches are instantly routed to the rate-limited queue.

## 3. Rapid Cache Poisoning Guessing Race
* **The Attack:** An off-path attacker floods the resolver with spoofed responses targeting a specific query, randomizing the 16-bit Transaction ID (TXID) to race the legitimate authoritative answer.
* **The Rule:** Stateful Similarity Tracker (`EXCEPT txid`).
* **The Mitigation:** The proxy strips the randomized TXID from incoming responses and hashes the remaining payload. If 5 structurally identical responses are observed within a rolling 20-packet window, the circuit breaker trips, routing all subsequent forged guesses to the rate-limited queue and neutralizing the race condition.

## 4. TuDoor Attack (Malformed Logic Exploitation)
* **The Attack:** The attacker exploits logic vulnerabilities in the pre-processing phase by sending malformed queries containing multiple question sections. This triggers an endless CPU-draining loop, locking up the resolver's concurrency pipeline.
* **The Rule:** Intra-Packet Volumetric Counter (`IF NUMBER OF QUESTION_SECTION > 1 LIMIT`).
* **The Mitigation:** The engine instantaneously flags the packet as structurally illegal based strictly on internal counts. Diverting these floods to the rate-limited queue preserves backend processing capacity and avoids CPU lockups.
