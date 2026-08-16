# Attack Scenarios & Mitigations

The BOR-BOX PoC evaluates defensive performance against three specific DNS attack vectors grounded in recent academic literature.

## 1. Volumetric QPS Flood (Resource Exhaustion)
* **The Attack:** The attacker blasts high-volume, non-existent wildcard queries to starve the resolver's lookup queues.
* **The Rule:** Exact Domain Whitelisting.
* **The Mitigation:** Legitimate domains (`www.example.com`, `mail.example.com`) bypass limits. Unrecognized domains trigger a volumetric threshold (sliding window) and are demoted to the rate-limited queue.

## 2. DNS Water Torture (Random Subdomains)
* **The Attack:** The attacker generates high-entropy, random subdomains (e.g., `a8f9x01.example.com`) to bypass the resolver's cache and force NXDOMAIN processing storms.
* **The Rule:** Regex / Label Count Filter.
* **The Mitigation:** A compiled deterministic finite automaton (DFA) identifies subdomains with 8+ alphanumeric characters. Matches are instantly routed to the rate-limited queue.

## 3. Rapid Cache Poisoning Guessing Race
* **The Attack:** An off-path attacker rapidly floods the resolver with spoofed responses or transaction ID guesses targeting a specific, high-value domain.
* **The Rule:** Domain Request Density Rule.
* **The Mitigation:** If query velocity for a specific zone exceeds 10 queries within a 1-second rolling window, subsequent queries for that domain are rate-limited to protect the lookup buffers.
