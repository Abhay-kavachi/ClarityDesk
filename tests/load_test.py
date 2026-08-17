"""
Automated Load Testing & Performance Benchmark Harness for ClarityDesk.

Runs concurrent simulated requests against the ClarityDesk backend APIs using FastAPI's TestClient
and concurrent worker threads to compute accurate latency percentiles (p50, p95, p99) and throughput (RPS).

Usage:
    python -m pytest tests/load_test.py -s
    # or directly:
    python tests/load_test.py
"""
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from statistics import mean, median, quantiles

from fastapi.testclient import TestClient

# Add backend directory to Python path before importing application modules.
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from main import app

client = TestClient(app)


def worker_ask_request(req_id: int) -> float:
    """Simulate a single RAG Q&A request and return latency in seconds."""
    start_time = time.perf_counter()
    response = client.post(
        "/api/ask",
        json={"question": f"What is the fundraising target for initiative {req_id}?"},
    )
    assert response.status_code == 200
    return time.perf_counter() - start_time


def worker_notes_request(req_id: int) -> float:
    """Simulate a single notes processing request and return latency in seconds."""
    start_time = time.perf_counter()
    notes = (
        f"Meeting #{req_id}: Alice will follow up with donor XYZ by tomorrow. "
        "Budget approved for $50,000."
    )
    response = client.post("/api/process-notes", json={"notes": notes})
    assert response.status_code == 200
    return time.perf_counter() - start_time


def run_benchmark(concurrency: int = 25, total_requests: int = 100) -> dict[str, float]:
    """Runs a multi-threaded benchmark against the endpoints and returns latency metrics."""
    print(
        f"\n[LOAD TEST] Launching Load Benchmark: "
        f"{total_requests} requests (Concurrency: {concurrency})..."
    )
    latencies: list[float] = []

    start_bench = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        # Mix ask and notes requests 50/50
        futures = []
        for i in range(total_requests):
            if i % 2 == 0:
                futures.append(executor.submit(worker_ask_request, i))
            else:
                futures.append(executor.submit(worker_notes_request, i))

        for future in as_completed(futures):
            latencies.append(future.result())

    total_time = time.perf_counter() - start_bench
    rps = total_requests / total_time

    p50 = float(median(latencies))
    percentile_values = quantiles(latencies, n=100, method="inclusive")
    p95 = float(percentile_values[94])
    p99 = float(percentile_values[98])
    avg_lat = float(mean(latencies))

    print("-" * 65)
    print("CLARITYDESK LOAD TESTING REPORT (CONCURRENT TESTCLIENT)")
    print("-" * 65)
    print(f"Total Requests Processed : {total_requests}")
    print(f"Concurrent Workers       : {concurrency}")
    print(f"Total Elapsed Time       : {total_time:.3f} s")
    print(f"Throughput (RPS)         : {rps:.2f} req/s")
    print(f"Average Latency          : {avg_lat * 1000:.2f} ms")
    print(f"p50 Latency              : {p50 * 1000:.2f} ms")
    print(f"p95 Latency              : {p95 * 1000:.2f} ms")
    print(f"p99 Latency              : {p99 * 1000:.2f} ms")
    print("Error Rate               : 0.00 %")
    print("-" * 65)

    return {
        "rps": round(rps, 2),
        "p50_ms": round(p50 * 1000, 2),
        "p95_ms": round(p95 * 1000, 2),
        "p99_ms": round(p99 * 1000, 2),
        "avg_ms": round(avg_lat * 1000, 2),
    }


def test_load_benchmark_pass():
    """Pytest integration test for performance benchmarking."""
    metrics = run_benchmark(concurrency=10, total_requests=40)
    assert metrics["rps"] > 0
    assert metrics["p95_ms"] >= 0


if __name__ == "__main__":
    run_benchmark(concurrency=20, total_requests=100)
