from .pipeline import IncidentAnalyzer
from typing import List, Dict, Any, Optional, Tuple
import logging
import os
import gc
import psutil
from time import time
from functools import wraps

logger = logging.getLogger(__name__)

# Green coding: Cache for frequent queries
class QueryCache:
    def __init__(self, max_size: int = 100):
        self.cache: Dict[str, Any] = {}
        self.max_size = max_size
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Get cached value if available"""
        if key in self.cache:
            self.hits += 1
            return self.cache[key]
        self.misses += 1
        return None

    def set(self, key: str, value: Any):
        """Set cache value with size management"""
        if len(self.cache) >= self.max_size:
            # Remove oldest items (simple FIFO)
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]

        self.cache[key] = value

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "size": len(self.cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hits / (self.hits + self.misses) if (self.hits + self.misses) > 0 else 0
        }

class IncidentService:
    def __init__(self):
        self.analyzer = IncidentAnalyzer()
        self.query_cache = QueryCache(max_size=200)
        self.batch_cache: Dict[str, List[Dict[str, Any]]] = {}
        self.batch_size = int(os.getenv("BATCH_PROCESSING_SIZE", "50"))

    def _memory_check(self):
        """Check system memory and perform cleanup if needed"""
        process = psutil.Process()
        memory_info = process.memory_info()
        available_memory = psutil.virtual_memory().available

        if memory_info.rss > available_memory * 0.7:  # Using 70% of available memory
            logger.warning(f"High memory usage: {memory_info.rss} bytes. Performing cleanup.")
            gc.collect()
            if hasattr(torch, 'cuda') and torch.cuda.is_available():
                torch.cuda.empty_cache()

    def add_incident(self, incident_data: Dict[str, Any]) -> str:
        """Add a single incident with green coding optimizations"""
        self._memory_check()

        incident_id = incident_data.get('incident_id')
        if not incident_id:
            raise ValueError("Incident ID is required")

        # Green coding: Batch small incidents for more efficient processing
        if not self.batch_cache:
            self.batch_cache['incidents'] = []

        self.batch_cache['incidents'].append(incident_data)

        # Process batch when it reaches the configured size
        if len(self.batch_cache['incidents']) >= self.batch_size:
            success = self._process_batch()
            self.batch_cache['incidents'] = []
            if not success:
                raise Exception("Failed to add incident batch")
            return incident_id

        # Process individual incident if batching is disabled
        success = self.analyzer.ingest_incident(incident_data)
        if success:
            logger.info(f"Added incident {incident_id}")
            return incident_id
        else:
            raise Exception("Failed to add incident")

    def _process_batch(self) -> bool:
        """Process a batch of incidents efficiently"""
        if not self.batch_cache.get('incidents'):
            return True

        try:
            # Use the analyzer's batch method for better performance
            success_count = self.analyzer.ingest_incidents_batch(self.batch_cache['incidents'])
            logger.info(f"Processed batch of {len(self.batch_cache['incidents'])} incidents. Success: {success_count}")
            return success_count > 0
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            return False
        finally:
            # Clear batch and force cleanup
            self.batch_cache['incidents'] = []
            gc.collect()

    def add_incidents_batch(self, incidents: List[Dict[str, Any]]) -> int:
        """Add multiple incidents with green coding optimizations"""
        self._memory_check()

        if not incidents:
            return 0

        # Process in optimized batches
        total_success = 0
        for i in range(0, len(incidents), self.batch_size):
            batch = incidents[i:i + self.batch_size]
            try:
                success_count = self.analyzer.ingest_incidents_batch(batch)
                total_success += success_count
                logger.info(f"Processed batch {i//self.batch_size + 1}: {success_count}/{len(batch)} incidents")
            except Exception as e:
                logger.error(f"Batch processing failed: {e}")
            finally:
                # Force cleanup between batches
                gc.collect()

        return total_success

    def analyze_root_cause(self, query: str, k: int = 5) -> str:
        """Analyze root cause with caching"""
        # Check cache first
        cache_key = f"root_cause:{query}:{k}"
        cached_result = self.query_cache.get(cache_key)
        if cached_result:
            return cached_result

        result = self.analyzer.analyze_root_cause(query, k)
        self.query_cache.set(cache_key, result)
        return result

    def analyze_patterns(self, query: str, k: int = 5) -> str:
        """Analyze patterns with caching"""
        cache_key = f"patterns:{query}:{k}"
        cached_result = self.query_cache.get(cache_key)
        if cached_result:
            return cached_result

        result = self.analyzer.analyze_patterns(query, k)
        self.query_cache.set(cache_key, result)
        return result

    def search_incidents(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search incidents with optimized result formatting"""
        # Check cache first
        cache_key = f"search:{query}:{k}"
        cached_result = self.query_cache.get(cache_key)
        if cached_result:
            return cached_result

        docs = self.analyzer.search_incidents(query, k)
        results = []

        # Green coding: More efficient result formatting
        for doc in docs:
            # Only include essential metadata
            metadata = {
                "incident_id": doc.metadata.get("incident_id"),
                "timestamp": doc.metadata.get("timestamp"),
                "category": doc.metadata.get("category"),
                "severity": doc.metadata.get("severity")
            }

            # Truncate content efficiently
            content = doc.page_content
            if len(content) > 200:
                content = content[:197] + "..."

            results.append({
                "content": content,
                "metadata": metadata,
                "score": getattr(doc, 'score', None)
            })

        self.query_cache.set(cache_key, results)
        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics with cache info"""
        stats = self.analyzer.get_stats()
        stats["cache"] = self.query_cache.stats()
        return stats

    def get_incidents(self) -> List[Dict]:
        """Get incidents with memory check"""
        self._memory_check()
        return self.analyzer.get_incidents()
