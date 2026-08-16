# BOR-BOX PoC: Project Structure

This directory contains the Proof of Concept (PoC) environment for BOR-BOX, a DNS security middlebox designed to protect recursive resolvers from resource exhaustion.

## Directory Layout

* `docker-compose.yml`
  Defines the isolated `bor-net` subnet and provisions the four core containers (DNS Resolver, BOR-BOX Proxy, Attacker, and Client).
* `coredns/Corefile`
  Configuration file mapping the CoreDNS routing rules.
* `coredns/example.com.db`
  The authoritative zone file defining the legitimate, whitelisted subdomains for the PoC.
* `borbox/bor_box.py`
  The core Python proxy implementing the dual-queue architecture and stateful mitigation rules.
* `borbox/requirements.txt`
  Dependencies for the proxy (`dnspython`).
* `attacker/attacker.py`
  A multi-threaded Python script capable of launching three distinct DNS-based DDoS and cache poisoning attacks.
* `attacker/requirements.txt`
  Dependencies for the attack scripts (`scapy`, `dnspython`).
* `client/benchmark.py`
  The automated testing suite that simulates legitimate traffic, records latency/timeouts, and generates matplotlib charts.
* `client/requirements.txt`
  Dependencies for the benchmarking client (`dnspython`, `matplotlib`, `pandas`).
* `client/charts/`
  The output directory where the final presentation-ready PNG charts are saved after a benchmark run.
