# Results and Metrics

The benchmarking suite automatically logs all legitimate client transactions to a CSV file and generates five key metrics charts (`client/charts/`). These metrics validate the product's core value propositions: Integrity and Availability.

## 1. Resolver Integrity (Stacked Bar Chart)
* **File:** `slide_chart1_integrity.png`
* **Purpose:** Measures the exact payload outcome of the client's query (Clean, Poisoned, or Timeout). 
* **Expected Outcome:** Validates the stateful similarity tracker by showing 0% cache corruption when BOR-BOX mitigates poisoning races.

## 2. Resolver Availability (Bar Chart)
* **File:** `slide_chart2_availability.png`
* **Purpose:** Measures the percentage of legitimate queries answered within the 250ms timeout window.
* **Expected Outcome:** Proves that BOR-BOX prevents service outages (100% availability) during CPU-exhaustion attacks like TuDoor.

## 3. Latency Jitter (Box Plot)
* **File:** `slide_chart3_latency_box.png`
* **Purpose:** Displays the statistical distribution of round-trip times to highlight computational instability.
* **Expected Outcome:** Unmitigated attacks stretch the box wildly, indicating severe CPU-draining loops and locked queues. BOR-BOX compresses the box, maintaining stable processing times identical to the baseline.

## 4. Legitimate Query Latency (Line Chart)
* **File:** `slide_chart4_latency_line.png`
* **Purpose:** A chronological line chart tracking the round-trip time of legitimate queries.
* **Expected Outcome:** Demonstrates that the high-priority queue successfully isolates standard traffic from the latency degradation of the rate-limited queue.

## 5. Outcome Scatter Plot
* **File:** `slide_chart5_scatter.png`
* **Purpose:** A scatter plot mapping the precise moment of each query resolution and its specific outcome state.
* **Expected Outcome:** Visually highlights the velocity of malicious races and the immediate cessation of corrupted packets the moment the circuit breaker trips.
