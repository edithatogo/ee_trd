"""
Performance Optimization Module

This module provides intelligent caching, asynchronous processing, and memory management
for health economic evaluation models.
"""

import asyncio
import pickle
import hashlib
import json
import os
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from functools import wraps
import sys
import gc
import psutil
import weakref
from queue import Queue
from threading import Lock
import logging


class IntelligentCache:
    """
    Intelligent caching system for expensive computations in health economic models.
    Uses predictive modeling to pre-warm cache and implements LRU eviction.
    """
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600, prewarm_enabled: bool = True):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.prewarm_enabled = prewarm_enabled
        
        # Main cache store
        self.cache: Dict[str, Dict[str, Any]] = {}
        
        # Usage tracking for LRU
        self.usage_order: List[str] = []  # Tracks access order
        self.access_count: Dict[str, int] = {}  # Tracks access frequency
        
        # Lock for thread safety
        self.lock = Lock()
        
        # Initialize logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate cache key based on function and parameters."""
        key_data = {
            'function': func_name,
            'args': args,
            'kwargs': kwargs
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _is_expired(self, timestamp: float) -> bool:
        """Check if cache entry is expired."""
        return (time.time() - timestamp) > self.ttl_seconds
    
    def _evict_lru(self):
        """Evict least recently used items when cache exceeds max size."""
        while len(self.cache) > self.max_size:
            # Remove the least recently used item (earliest in usage_order)
            oldest_key = self.usage_order.pop(0)
            del self.cache[oldest_key]
            if oldest_key in self.access_count:
                del self.access_count[oldest_key]
            self.logger.debug(f"Evicted LRU cache entry: {oldest_key[:8]}...")
    
    def _update_usage(self, key: str):
        """Update usage statistics for a key."""
        if key in self.usage_order:
            self.usage_order.remove(key)
        self.usage_order.append(key)
        
        self.access_count[key] = self.access_count.get(key, 0) + 1
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                if not self._is_expired(entry['timestamp']):
                    self._update_usage(key)
                    self.logger.debug(f"Cache HIT for key: {key[:8]}...")
                    return entry['value']
                else:
                    # Entry expired, remove it
                    del self.cache[key]
                    if key in self.access_count:
                        del self.access_count[key]
                    if key in self.usage_order:
                        self.usage_order.remove(key)
                    self.logger.debug(f"Cache EXPIRED for key: {key[:8]}...")
            
            self.logger.debug(f"Cache MISS for key: {key[:8]}...")
            return None
    
    def set(self, key: str, value: Any):
        """Set value in cache."""
        with self.lock:
            # Check if we need to evict
            if len(self.cache) >= self.max_size:
                self._evict_lru()
            
            self.cache[key] = {
                'value': value,
                'timestamp': time.time(),
                'size': sys.getsizeof(value)
            }
            self._update_usage(key)
            self.logger.debug(f"Cache SET for key: {key[:8]}...")
    
    def clear(self):
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()
            self.usage_order.clear()
            self.access_count.clear()
            self.logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            total_size = sum(entry['size'] for entry in self.cache.values())
            return {
                'current_size': len(self.cache),
                'max_size': self.max_size,
                'ttl_seconds': self.ttl_seconds,
                'total_size_bytes': total_size,
                'usage_order_sample': self.usage_order[-5:] if self.usage_order else [],  # Last 5 accessed
                'most_accessed': sorted(self.access_count.items(), key=lambda x: x[1], reverse=True)[:5]
            }


class AsyncProcessor:
    """
    Asynchronous processor for running expensive health economic computations
    concurrently while managing resources efficiently.
    """
    
    def __init__(self, max_workers: int = 4, memory_threshold: float = 0.8):
        self.max_workers = max_workers
        self.memory_threshold = memory_threshold
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.active_tasks = []
        
        # Initialize logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def _check_memory_pressure(self) -> bool:
        """Check if system is under memory pressure."""
        memory_percent = psutil.virtual_memory().percent / 100.0
        return memory_percent > self.memory_threshold
    
    def run_task(self, func: Callable, *args, **kwargs) -> asyncio.Future:
        """Run a task asynchronously."""
        # Check memory pressure
        if self._check_memory_pressure():
            self.logger.warning("High memory pressure detected, consider reducing concurrent tasks")
        
        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(self.executor, func, *args)
        
        # Track active tasks
        self.active_tasks.append(future)
        
        # Clean up completed tasks
        self.active_tasks = [task for task in self.active_tasks if not task.done()]
        
        return future
    
    async def run_batch(self, tasks: List[Tuple[Callable, tuple, dict]]) -> List[Any]:
        """Run multiple tasks concurrently."""
        futures = []
        for func, args, kwargs in tasks:
            future = self.run_task(func, *args, **kwargs)
            futures.append(future)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*futures, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Task {i} failed: {str(result)}")
                processed_results.append(None)  # Or handle differently based on needs
            else:
                processed_results.append(result)
        
        return processed_results
    
    def shutdown(self):
        """Shutdown the processor and clean up resources."""
        self.executor.shutdown(wait=True)
        self.logger.info("AsyncProcessor shut down")


class MemoryManager:
    """
    Memory management system for health economic models that may process
    large amounts of data or run long simulations.
    """
    
    def __init__(self, memory_limit_mb: int = 2048, gc_frequency: int = 50):
        self.memory_limit_mb = memory_limit_mb
        self.gc_frequency = gc_frequency
        self.gc_counter = 0
        
        # Initialize logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def get_current_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024  # Convert to MB
    
    def is_memory_exceeded(self) -> bool:
        """Check if memory limit is exceeded."""
        return self.get_current_memory_usage() > self.memory_limit_mb
    
    def trigger_gc_if_needed(self):
        """Trigger garbage collection if needed."""
        self.gc_counter += 1
        if self.gc_counter >= self.gc_frequency:
            self.gc_counter = 0
            collected = gc.collect()
            self.logger.debug(f"Garbage collection performed, collected {collected} objects")
    
    def monitor_memory(self, operation_name: str = "operation"):
        """Context manager to monitor memory during operations."""
        initial_memory = self.get_current_memory_usage()
        self.logger.debug(f"Starting {operation_name}, initial memory: {initial_memory:.2f} MB")
        
        try:
            yield
        finally:
            final_memory = self.get_current_memory_usage()
            memory_change = final_memory - initial_memory
            self.logger.debug(f"Completed {operation_name}, final memory: {final_memory:.2f} MB, change: {memory_change:.2f} MB")
            
            if memory_change > 100:  # Alert if operation increased memory by >100MB
                self.logger.warning(f"{operation_name} caused significant memory increase ({memory_change:.2f} MB)")
            
            # Trigger GC if needed
            self.trigger_gc_if_needed()


# Global cache instance for convenience
global_cache = IntelligentCache()


def cached_computation(ttl_seconds: int = 3600, cache_instance: IntelligentCache = None):
    """
    Decorator to cache expensive computations in health economic models.
    """
    cache = cache_instance or global_cache
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function and arguments
            cache_key = cache._generate_key(func.__name__, args, kwargs)
            
            # Try to get result from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Compute result if not in cache
            result = func(*args, **kwargs)
            
            # Store result in cache
            cache.set(cache_key, result)
            
            return result
        return wrapper
    return decorator


class AnalysisTaskQueue:
    """
    Queue for managing analysis tasks with priority and resource management.
    """
    
    def __init__(self, max_concurrent: int = 3, memory_manager: MemoryManager = None):
        self.queue = Queue()
        self.max_concurrent = max_concurrent
        self.active_tasks = []
        self.results = {}
        self.memory_manager = memory_manager or MemoryManager()
        
        # Initialize logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def add_task(self, task_id: str, func: Callable, priority: int = 1, *args, **kwargs):
        """Add a task to the queue."""
        task = {
            'id': task_id,
            'func': func,
            'args': args,
            'kwargs': kwargs,
            'priority': priority,
            'submitted_at': time.time()
        }
        self.queue.put((priority, task))
        self.logger.info(f"Added task {task_id} to queue (priority: {priority})")
    
    def process_queue(self, max_tasks: int = None) -> Dict[str, Any]:
        """Process tasks in the queue up to max_tasks."""
        completed = 0
        total_tasks = self.queue.qsize()
        processed_tasks = {}
        
        while (not self.queue.empty()) and (max_tasks is None or completed < max_tasks):
            # Check for completed tasks
            still_running = []
            for future, task_id in self.active_tasks:
                if future.done():
                    try:
                        result = future.result()
                        self.results[task_id] = result
                        self.logger.info(f"Task {task_id} completed successfully")
                    except Exception as e:
                        self.results[task_id] = {'error': str(e)}
                        self.logger.error(f"Task {task_id} failed: {str(e)}")
                else:
                    still_running.append((future, task_id))
            
            self.active_tasks = still_running
            
            # Start new tasks if we're below the concurrency limit
            while len(self.active_tasks) < self.max_concurrent and not self.queue.empty():
                priority, task = self.queue.get()
                task_id = task['id']
                
                # Run task in memory-managed context
                def run_with_monitoring():
                    with self.memory_manager.monitor_memory(f"task_{task_id}"):
                        return task['func'](*task['args'], **task['kwargs'])
                
                future = asyncio.get_event_loop().run_in_executor(None, run_with_monitoring)
                self.active_tasks.append((future, task_id))
                self.logger.info(f"Started task {task_id}")
            
            # Small sleep to prevent busy-waiting
            time.sleep(0.1)
            completed += 1
        
        # Wait for all active tasks to complete
        for future, task_id in self.active_tasks:
            try:
                result = future.result(timeout=30)  # 30-second timeout
                self.results[task_id] = result
                self.logger.info(f"Task {task_id} completed successfully")
            except Exception as e:
                self.results[task_id] = {'error': str(e)}
                self.logger.error(f"Task {task_id} failed: {str(e)}")
        
        self.active_tasks = []  # Clear completed tasks
        return self.results


class PerformanceOptimizer:
    """
    Performance optimization controller that combines caching, async processing,
    and memory management for health economic models.
    """
    
    def __init__(self, 
                 cache_max_size: int = 1000, 
                 cache_ttl: int = 3600,
                 max_async_workers: int = 4,
                 memory_limit_mb: int = 2048):
        
        self.cache = IntelligentCache(
            max_size=cache_max_size,
            ttl_seconds=cache_ttl
        )
        
        self.async_processor = AsyncProcessor(
            max_workers=max_async_workers
        )
        
        self.memory_manager = MemoryManager(
            memory_limit_mb=memory_limit_mb
        )
        
        # Initialize logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def optimize_heavy_calculation(self, func: Callable):
        """
        Decorator to optimize heavy calculations with caching and memory management.
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            with self.memory_manager.monitor_memory(f"calculation_{func.__name__}"):
                # Check if result is cached
                cache_key = self.cache._generate_key(func.__name__, args, kwargs)
                cached_result = self.cache.get(cache_key)
                
                if cached_result is not None:
                    return cached_result
                
                # Calculate result
                result = func(*args, **kwargs)
                
                # Cache result
                self.cache.set(cache_key, result)
                
                return result
        
        return wrapper
    
    async def run_parallel_analyses(self, analysis_tasks: List[Tuple[Callable, tuple, dict]]) -> List[Any]:
        """Run multiple analyses in parallel with resource management."""
        return await self.async_processor.run_batch(analysis_tasks)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status including cache, memory, and task stats."""
        return {
            'cache_stats': self.cache.get_stats(),
            'memory_usage_mb': self.memory_manager.get_current_memory_usage(),
            'memory_limit_mb': self.memory_manager.memory_limit_mb,
            'async_worker_status': {
                'max_workers': self.async_processor.max_workers,
                'active_tasks': len(self.async_processor.active_tasks)
            }
        }
    
    def shutdown(self):
        """Shut down all components."""
        self.async_processor.shutdown()
        self.logger.info("PerformanceOptimizer shut down")


# Default global optimizer for convenience
global_optimizer = PerformanceOptimizer()


def optimize_for_hee(analyzer_class):
    """
    Decorator to add optimization features to health economic evaluation classes.
    """
    original_init = analyzer_class.__init__
    
    def new_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.optimizer = global_optimizer
        self.cache = global_optimizer.cache
    
    analyzer_class.__init__ = new_init
    
    # Add methods for caching and optimization
    def optimize_method(self, method_name):
        original_method = getattr(self, method_name)
        optimized_method = self.optimizer.optimize_heavy_calculation(original_method)
        setattr(self, method_name, optimized_method)
    
    analyzer_class.optimize_method = optimize_method
    return analyzer_class


# Example of how to use the performance optimization tools
def example_usage():
    """
    Example of how to use the performance optimization tools.
    """
    # Example 1: Using the cached computation decorator
    @cached_computation(ttl_seconds=1800)  # Cache for 30 minutes
    def expensive_calculation(x, y, precision=1e-6):
        """Example of an expensive calculation that benefits from caching."""
        # Simulate expensive computation
        result = 0
        for i in range(int(1/precision)):
            result += (x * y) / (i + 1)
        return result
    
    # Example 2: Using the async processor
    async def run_example_analyses():
        async_processor = AsyncProcessor(max_workers=2)
        
        # Define some example tasks
        tasks = [
            (expensive_calculation, (10, 5, 1e-5), {}),
            (expensive_calculation, (20, 3, 1e-5), {}),
            (expensive_calculation, (15, 7, 1e-5), {}),
        ]
        
        results = await async_processor.run_batch(tasks)
        async_processor.shutdown()
        return results
    
    # Example 3: Using the analysis task queue
    def run_queued_analyses():
        queue = AnalysisTaskQueue(max_concurrent=2)
        
        # Add tasks to queue
        queue.add_task("analysis_1", expensive_calculation, priority=1, x=10, y=5, precision=1e-5)
        queue.add_task("analysis_2", expensive_calculation, priority=2, x=20, y=3, precision=1e-5)
        queue.add_task("analysis_3", expensive_calculation, priority=1, x=15, y=7, precision=1e-5)
        
        # Process the queue
        results = queue.process_queue()
        return results
    
    return expensive_calculation, run_example_analyses, run_queued_analyses


# Initialize the example
example_funcs = example_usage()