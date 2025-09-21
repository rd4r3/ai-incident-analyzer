# embeddings.py
from transformers import AutoTokenizer, AutoModel
import torch
import gc
import psutil
from typing import Dict, List, Optional

class TransformersEmbedding:
    def __init__(self, model_name: str = "all-mini-lm-l6-v2", max_cache_size: int = 10000):
        # Green coding: Use GPU only for large batches, otherwise CPU is more energy efficient
        self.cpu_device = torch.device("cpu")
        self.gpu_device = torch.device("cuda") if torch.cuda.is_available() else None
        self.current_device = self.cpu_device  # Default to CPU

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(self.cpu_device)
        self.model.eval()  # Set to evaluation mode

        # Green coding: Limit cache size to prevent excessive memory usage
        self.cache: Dict[str, List[float]] = {}
        self.max_cache_size = max_cache_size

        # Track memory usage
        self.memory_limit_mb = 80  # % of available memory to use
        self._update_memory_limit()

    def _update_memory_limit(self):
        """Update memory limit based on available system memory"""
        available_memory = psutil.virtual_memory().available
        self.memory_limit_bytes = int(available_memory * (self.memory_limit_mb / 100))

    def _should_use_gpu(self, batch_size: int) -> bool:
        """Determine if GPU should be used based on batch size and memory constraints"""
        if not self.gpu_device:
            return False

        # Use GPU for larger batches or when we have plenty of memory
        process = psutil.Process()
        current_memory = process.memory_info().rss

        return (batch_size > 16 and
                current_memory < self.memory_limit_bytes * 0.7)

    def _switch_device(self, use_gpu: bool):
        """Switch computation device based on workload"""
        target_device = self.gpu_device if use_gpu else self.cpu_device
        if self.current_device != target_device:
            self.model.to(target_device)
            self.current_device = target_device

    def _clear_cache_if_needed(self):
        """Clear cache if it grows too large"""
        if len(self.cache) > self.max_cache_size:
            # Keep only the most recently used items
            self.cache = dict(list(self.cache.items())[-self.max_cache_size//2:])

    def embed_documents(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """Embed documents with green coding optimizations"""
        if not texts:
            return []

        embeddings = []
        # Process texts in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            # Check cache first
            cached_embeddings = [self.cache.get(text) for text in batch]
            all_cached = all(embedding is not None for embedding in cached_embeddings)

            if all_cached:
                embeddings.extend(cached_embeddings)
                continue

            # Process uncached texts
            uncached_texts = [text for text, embedding in zip(batch, cached_embeddings)
                             if embedding is None]

            if not uncached_texts:
                continue

            # Green coding: Dynamically choose device based on workload
            use_gpu = self._should_use_gpu(len(uncached_texts))
            self._switch_device(use_gpu)

            # Tokenize with attention to memory usage
            encodings = self.tokenizer(
                uncached_texts,
                padding=True,
                truncation=True,
                return_tensors="pt"
            ).to(self.current_device)

            with torch.no_grad():
                output = self.model(**encodings).last_hidden_state
                batch_embeddings = output.mean(dim=1).cpu().tolist()

            # Update cache and manage memory
            for text, embedding in zip(uncached_texts, batch_embeddings):
                self.cache[text] = embedding
            self._clear_cache_if_needed()

            # Combine results maintaining original order
            batch_result = [
                self.cache[text] if text in self.cache else embedding
                for text, embedding in zip(batch, batch_embeddings)
            ]
            embeddings.extend(batch_result)

            # Force garbage collection to free memory
            gc.collect()
            if self.current_device.type == 'cuda':
                torch.cuda.empty_cache()

        return embeddings

    def embed_query(self, text: str) -> Optional[list[float]]:
        """Embed a single query with green coding optimizations"""
        if not text:
            return None

        if text in self.cache:
            return self.cache[text]

        # For single queries, prefer CPU to save energy
        if self.current_device != self.cpu_device:
            self._switch_device(False)

        return self.embed_documents([text])[0]
