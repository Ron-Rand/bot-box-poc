# Results and Metrics

The benchmarking suite automatically logs all legitimate client transactions to a CSV file and generates two key metrics charts (`client/charts/`). These metrics validate the product's core value proposition.

## 1. Resolver Availability (Success Rate %)
* **Purpose:** Measures the percentage of legitimate queries successfully answered within the standard 250ms timeout window.
* **Expected Outcome:** During an unmitigated attack, availability drops significantly (often to 0%) due to socket exhaustion. When BOR-BOX is active, availability returns to ~100%, proving the "no hard drop" philosophy works without disrupting legitimate users.

## 2. Legitimate Query Latency (RTT in ms)
* **Purpose:** Tracks the round-trip time of legitimate queries over the duration of the test.
* **Expected Outcome:** Unmitigated attacks cause wild latency spikes and flatlined timeout ceilings. With BOR-BOX active, the latency line remains stable and mirrors the baseline, proving the high-priority queue successfully isolates standard traffic from the degraded performance of the rate-limited queue.
