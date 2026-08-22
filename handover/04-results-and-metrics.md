================================================
FILE: handover/04-results-and-metrics.md
================================================
# Results and Metrics

The benchmarking suite automatically logs all legitimate client transactions to a CSV file and generates three key metrics charts (`client/charts/`). These metrics validate the product's core value propositions: Integrity and Availability.

## 1. Resolver Integrity (% Resolution Outcome)
* **File:** `slide_chart1_integrity.png`
* **Purpose:** A stacked bar chart measuring the exact payload outcome of the client's query (Clean, Poisoned, or Timeout). 
* **Expected Outcome:** During an unmitigated cache poisoning attack, a large percentage of resolutions will be compromised. When BOR-BOX is active, the stateful tracker preserves strict integrity, resulting in 0% poisoned payloads (trading a small margin of availability for absolute integrity).

## 2. Legitimate Query Latency (RTT in ms)
* **File:** `slide_chart2_latency.png`
* **Purpose:** A line chart tracking the round-trip time of legitimate queries over the duration of the test.
* **Expected Outcome:** Unmitigated volumetric attacks cause wild latency spikes and flatlined timeout ceilings. With BOR-BOX active, the latency line remains stable and mirrors the baseline, proving the high-priority queue successfully isolates standard traffic from the degraded rate-limited queue.

## 3. Outcome Scatter Plot
* **File:** `slide_chart3_scatter.png`
* **Purpose:** A chronological plot mapping the precise moment of each query resolution and its specific outcome state.
* **Expected Outcome:** Visually demonstrates the velocity of the race condition and the immediate cessation of corrupted packets the moment the BOR-BOX circuit breaker trips.
