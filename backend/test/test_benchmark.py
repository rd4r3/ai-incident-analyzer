import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import time
import psutil
import gc
import logging
import random
import string
import json
import tempfile

# Use a temporary directory for ChromaDB during tests
os.environ["CHROMA_DB_PATH"] = tempfile.mkdtemp()

from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from app.main import app
from app.incident_service import IncidentService


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class MetricsCollector:
    """Collect performance and resource metrics"""

    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.start_memory = 0
        self.start_cpu = 0
        self.start_time = 0
        self.peak_memory = 0
        self.peak_cpu = 0

    def start(self):
        """Start collecting metrics"""
        self.start_memory = self.process.memory_info().rss
        self.start_cpu = psutil.cpu_percent(interval=None)
        self.start_time = time.time()
        self.peak_memory = self.start_memory
        self.peak_cpu = self.start_cpu
        logger.info(f"Starting metrics collection. Initial memory: {self.start_memory} bytes, CPU: {self.start_cpu}%")

    def update(self):
        """Update peak metrics"""
        current_memory = self.process.memory_info().rss
        current_cpu = psutil.cpu_percent(interval=None)

        if current_memory > self.peak_memory:
            self.peak_memory = current_memory

        if current_cpu > self.peak_cpu:
            self.peak_cpu = current_cpu

    def stop(self) -> Dict[str, Any]:
        """Stop collecting metrics and return results"""
        end_time = time.time()
        duration = end_time - self.start_time
        end_memory = self.process.memory_info().rss
        end_cpu = psutil.cpu_percent(interval=None)

        # Force cleanup
        gc.collect()

        return {
            "duration": duration,
            "start_memory": self.start_memory,
            "peak_memory": self.peak_memory,
            "end_memory": end_memory,
            "memory_increase": self.peak_memory - self.start_memory,
            "start_cpu": self.start_cpu,
            "peak_cpu": self.peak_cpu,
            "end_cpu": end_cpu,
            "cpu_increase": self.peak_cpu - self.start_cpu
        }

def generate_random_incident() -> Dict[str, Any]:
    """Generate a random incident for testing"""
    def random_string(length=10):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    return {
        "incident_id": random_string(8),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "category": random.choice(["network", "security", "performance", "hardware"]),
        "severity": random.choice(["low", "medium", "high", "critical"]),
        "description": random_string(50),
        "resolution_time_mins": random.randint(5, 300)
    }

def test_memory_usage():
    """Test memory usage with different operations"""
    client = TestClient(app)
    metrics = MetricsCollector()

    # Test 1: Single incident addition
    metrics.start()
    incident = generate_random_incident()
    response = client.post("/api/incidents", json=incident)
    assert response.status_code == 200
    single_metrics = metrics.stop()
    logger.info(f"Single incident metrics: {single_metrics}")

    # Test 2: Batch incident addition
    metrics.start()
    incidents = [generate_random_incident() for _ in range(50)]
    response = client.post("/api/incidents/batch", json=incidents)
    assert response.status_code == 200
    batch_metrics = metrics.stop()
    logger.info(f"Batch incident metrics: {batch_metrics}")

    # Test 3: Search operations
    metrics.start()
    response = client.get("/api/search", params={"query": "network", "k": 5})
    assert response.status_code == 200
    search_metrics = metrics.stop()
    logger.info(f"Search metrics: {search_metrics}")

    # Test 4: Analysis operations
    metrics.start()
    response = client.post("/api/analyze/root-cause", json={"query": "network issues", "k": 5})
    assert response.status_code == 200
    analysis_metrics = metrics.stop()
    logger.info(f"Analysis metrics: {analysis_metrics}")

    return {
        "single_incident": single_metrics,
        "batch_incidents": batch_metrics,
        "search": search_metrics,
        "analysis": analysis_metrics
    }

def test_cache_performance():
    """Test cache performance"""
    service = IncidentService()
    metrics = MetricsCollector()

    # Warm up cache
    queries = ["network issues", "security breach", "performance degradation", "hardware failure"]
    for query in queries:
        service.analyze_root_cause(query)
        service.analyze_patterns(query)
        service.search_incidents(query)

    # Test cache hits
    cache_stats = service.query_cache.stats()
    logger.info(f"Cache stats after warmup: {cache_stats}")

    # Measure cached operations
    metrics.start()
    for _ in range(10):
        for query in queries:
            service.analyze_root_cause(query)
            service.analyze_patterns(query)
            service.search_incidents(query)
    cached_metrics = metrics.stop()

    # Measure non-cached operations
    metrics.start()
    for _ in range(10):
        for query in [q + str(i) for i in range(10) for q in queries]:
            service.analyze_root_cause(query)
            service.analyze_patterns(query)
            service.search_incidents(query)
    non_cached_metrics = metrics.stop()

    final_cache_stats = service.query_cache.stats()
    logger.info(f"Final cache stats: {final_cache_stats}")

    return {
        "cached_operations": cached_metrics,
        "non_cached_operations": non_cached_metrics,
        "cache_stats": final_cache_stats
    }

def test_concurrent_operations():
    """Test performance under concurrent load"""
    client = TestClient(app)
    metrics = MetricsCollector()

    def worker():
        """Simulate concurrent user operations"""
        for _ in range(10):
            # Random operation
            operation = random.choice(["add", "search", "analyze"])
            if operation == "add":
                incident = generate_random_incident()
                client.post("/api/incidents", json=incident)
            elif operation == "search":
                client.get("/api/search", params={"query": "network", "k": 5})
            else:
                client.post("/api/analyze/root-cause", json={"query": "network issues", "k": 5})

    # Run concurrent operations
    metrics.start()
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(worker) for _ in range(8)]
        for future in futures:
            future.result()
    concurrent_metrics = metrics.stop()

    return {"concurrent_operations": concurrent_metrics}

def main():
    """Run all benchmarks"""
    logger.info("Starting green coding benchmarks...")

    # Run memory tests
    memory_results = test_memory_usage()
    logger.info(f"Memory test results: {memory_results}")

    # Run cache tests
    cache_results = test_cache_performance()
    logger.info(f"Cache test results: {cache_results}")

    # Run concurrency tests
    concurrency_results = test_concurrent_operations()
    logger.info(f"Concurrency test results: {concurrency_results}")

    # Summary
    summary = {
        "memory_efficiency": {
            "single_incident_memory": memory_results["single_incident"]["memory_increase"],
            "batch_incident_memory": memory_results["batch_incidents"]["memory_increase"],
            "search_memory": memory_results["search"]["memory_increase"],
            "analysis_memory": memory_results["analysis"]["memory_increase"]
        },
        "cache_performance": {
            "hit_rate": cache_results["cache_stats"]["hit_rate"],
            "memory_savings": cache_results["cached_operations"]["memory_increase"] - cache_results["non_cached_operations"]["memory_increase"]
        },
        "concurrency": {
            "memory_increase": concurrency_results["concurrent_operations"]["memory_increase"],
            "duration": concurrency_results["concurrent_operations"]["duration"]
        }
    }

    logger.info(f"Benchmark summary: {summary}")
    logger.info("Green coding benchmarks completed.")

    # Export results to file
    with open("benchmark_results.json", "w") as f:
        json.dump({
            "memory_results": memory_results,
            "cache_results": cache_results,
            "concurrency_results": concurrency_results,
            "summary": summary
        }, f, indent=2)
        logger.info("Benchmark results exported to benchmark_results.json")

if __name__ == "__main__":
    main()
