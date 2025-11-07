#!/usr/bin/env python3
"""
V3 Performance Optimization and Benchmarking Suite.

Provides performance monitoring, optimization utilities, and benchmarking
tools for the NextGen Equity Framework.
"""

import time
import psutil
import gc
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from contextlib import contextmanager
from concurrent.futures import ProcessPoolExecutor, as_completed
import pandas as pd
import numpy as np
from functools import wraps
import cProfile
import pstats
from io import StringIO


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    
    function_name: str
    execution_time: float
    memory_used_mb: float
    cpu_percent: float
    iterations: int = 1
    
    def __str__(self):
        return (f"{self.function_name}: "
               f"{self.execution_time:.2f}s, "
               f"{self.memory_used_mb:.1f}MB, "
               f"{self.cpu_percent:.1f}% CPU")


class PerformanceMonitor:
    """Monitor and collect performance metrics."""
    
    def __init__(self):
        """Initialize performance monitor."""
        self.metrics: List[PerformanceMetrics] = []
        self.process = psutil.Process()
        
    def start_monitoring(self) -> Dict[str, Any]:
        """Start performance monitoring session."""
        return {
            'start_time': time.time(),
            'start_memory': self.process.memory_info().rss / 1024 / 1024,  # MB
            'start_cpu_percent': self.process.cpu_percent(),
        }
    
    def end_monitoring(self, start_data: Dict[str, Any], 
                      function_name: str, iterations: int = 1) -> PerformanceMetrics:
        """End monitoring and calculate metrics."""
        end_time = time.time()
        end_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        end_cpu_percent = self.process.cpu_percent()
        
        metrics = PerformanceMetrics(
            function_name=function_name,
            execution_time=(end_time - start_data['start_time']) / iterations,
            memory_used_mb=end_memory - start_data['start_memory'],
            cpu_percent=(end_cpu_percent + start_data['start_cpu_percent']) / 2,
            iterations=iterations
        )
        
        self.metrics.append(metrics)
        return metrics
    
    def get_summary(self) -> str:
        """Get performance summary report."""
        if not self.metrics:
            return "No performance data collected."
        
        lines = ["Performance Summary:", "=" * 50]
        
        total_time = sum(m.execution_time * m.iterations for m in self.metrics)
        total_memory = sum(m.memory_used_mb for m in self.metrics if m.memory_used_mb > 0)
        avg_cpu = np.mean([m.cpu_percent for m in self.metrics])
        
        lines.extend([
            f"Total execution time: {total_time:.2f}s",
            f"Total memory used: {total_memory:.1f}MB", 
            f"Average CPU usage: {avg_cpu:.1f}%",
            "",
            "Individual functions:"
        ])
        
        # Sort by execution time descending
        sorted_metrics = sorted(self.metrics, 
                              key=lambda m: m.execution_time * m.iterations, 
                              reverse=True)
        
        for metric in sorted_metrics:
            lines.append(f"  {metric}")
        
        return "\n".join(lines)


# Global performance monitor instance
_performance_monitor = PerformanceMonitor()


def benchmark(iterations: int = 1, warmup: int = 0):
    """Decorator to benchmark function performance."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Warmup runs
            for _ in range(warmup):
                func(*args, **kwargs)
                gc.collect()  # Clean up between runs
            
            # Actual benchmark runs
            start_data = _performance_monitor.start_monitoring()
            
            for _ in range(iterations):
                _result = func(*args, **kwargs)
                if iterations > 1:
                    gc.collect()  # Clean up between iterations
            
            metrics = _performance_monitor.end_monitoring(
                start_data, func.__name__, iterations
            )
            
            print(f"📊 {metrics}")
            
            return result
        return wrapper
    return decorator


@contextmanager
def performance_context(name: str):
    """Context manager for performance monitoring."""
    start_data = _performance_monitor.start_monitoring()
    try:
        yield
        metrics = _performance_monitor.end_monitoring(start_data, name)
        print(f"📊 {metrics}")
    except Exception:
        _performance_monitor.end_monitoring(start_data, f"{name} (FAILED)")
        raise


class ParallelProcessor:
    """Utilities for parallel processing optimization."""
    
    @staticmethod
    def optimal_worker_count() -> int:
        """Get optimal number of workers based on system resources."""
        cpu_count = psutil.cpu_count(logical=False) or 1
        memory_gb = psutil.virtual_memory().total / (1024**3)
        
        # Conservative approach: don't oversubscribe
        # Rule of thumb: 1 worker per 2GB RAM, max physical CPUs
        memory_workers = max(1, int(memory_gb / 2))
        
        return min(cpu_count, memory_workers, 8)  # Cap at 8 for reasonable overhead
    
    @staticmethod
    def parallel_psa_chunks(psa_data: pd.DataFrame, 
                          func: Callable, 
                          chunk_size: Optional[int] = None) -> List[Any]:
        """Process PSA data in parallel chunks."""
        if chunk_size is None:
            # Adaptive chunk size based on data size and available memory
            memory_gb = psutil.virtual_memory().available / (1024**3)
            rows_per_gb = 50000  # Estimate based on typical PSA data
            max_chunk_size = int(memory_gb * rows_per_gb / 4)  # Conservative
            chunk_size = min(max_chunk_size, max(1000, len(psa_data) // 10))
        
        chunks = [psa_data[i:i + chunk_size] 
                 for i in range(0, len(psa_data), chunk_size)]
        
        optimal_workers = ParallelProcessor.optimal_worker_count()
        
        with ProcessPoolExecutor(max_workers=optimal_workers) as executor:
            futures = [executor.submit(func, chunk) for chunk in chunks]
            results = [future.result() for future in as_completed(futures)]
        
        return results


class MemoryOptimizer:
    """Memory optimization utilities."""
    
    @staticmethod
    def get_memory_usage() -> Dict[str, float]:
        """Get current memory usage statistics."""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,
            'vms_mb': memory_info.vms / 1024 / 1024,
            'percent': process.memory_percent(),
            'available_mb': psutil.virtual_memory().available / 1024 / 1024
        }
    
    @staticmethod
    @contextmanager
    def memory_monitor(name: str, threshold_mb: float = 1000):
        """Monitor memory usage and warn if threshold exceeded."""
        start_memory = MemoryOptimizer.get_memory_usage()
        
        try:
            yield
            
            end_memory = MemoryOptimizer.get_memory_usage()
            memory_diff = end_memory['rss_mb'] - start_memory['rss_mb']
            
            if memory_diff > threshold_mb:
                print(f"⚠️  {name}: High memory usage ({memory_diff:.1f}MB)")
            
        except Exception as e:
            print(f"❌ {name}: Memory monitoring failed - {e}")
            raise
    
    @staticmethod
    def chunked_dataframe_processing(df: pd.DataFrame, 
                                   func: Callable,
                                   chunk_size: int = 10000) -> List[Any]:
        """Process large dataframes in memory-efficient chunks."""
        results = []
        
        for i in range(0, len(df), chunk_size):
            chunk = df.iloc[i:i + chunk_size].copy()  # Explicit copy to free original
            _result = func(chunk)
            results.append(result)
            
            # Explicit cleanup
            del chunk
            if i % (chunk_size * 5) == 0:  # Periodic garbage collection
                gc.collect()
        
        return results


class V3BenchmarkSuite:
    """Comprehensive benchmarking suite for V3 components."""
    
    def __init__(self):
        """Initialize benchmark suite."""
        self.monitor = PerformanceMonitor()
        self.results = {}
    
    def benchmark_psa_processing(self, 
                                sample_size: int = 10000,
                                n_therapies: int = 5) -> Dict[str, float]:
        """Benchmark PSA data processing."""
        # Generate synthetic PSA data
        np.random.seed(42)  # Reproducible results
        
        psa_data = pd.DataFrame({
            'Arm': np.random.choice([f'Therapy_{i}' for i in range(n_therapies)], 
                                  sample_size),
            'Cost': np.random.normal(1000, 200, sample_size),
            'Effect': np.random.normal(0.8, 0.1, sample_size),
            'Net_Benefit_50000': np.random.normal(39000, 5000, sample_size)
        })
        
        results = {}
        
        # Benchmark different processing approaches
        with performance_context("PSA_DataFrame_Creation"):
            test_df = psa_data.copy()
        
        with performance_context("PSA_Groupby_Operations"):
            _grouped = test_df.groupby('Arm')['Net_Benefit_50000'].agg(['mean', 'std'])
        
        with performance_context("PSA_Memory_Chunked"):
            _chunks = MemoryOptimizer.chunked_dataframe_processing(
                test_df, 
                lambda chunk: chunk.groupby('Arm')['Cost'].mean(),
                chunk_size=2000
            )
        
        # Store results
        for metric in self.monitor.metrics[-3:]:  # Last 3 benchmarks
            results[metric.function_name] = metric.execution_time
        
        return results
    
    def benchmark_plotting_performance(self) -> Dict[str, float]:
        """Benchmark plotting operations."""
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            # Generate test data
            np.random.seed(42)
            x = np.random.normal(0, 1, 1000)
            y = np.random.normal(0, 1, 1000)
            categories = np.random.choice(['A', 'B', 'C'], 1000)
            
            results = {}
            
            with performance_context("Plot_Scatter_Basic"):
                fig, ax = plt.subplots(figsize=(8, 6))
                ax.scatter(x, y, alpha=0.6)
                plt.close(fig)
            
            with performance_context("Plot_Scatter_Publication"):
                fig, ax = plt.subplots(figsize=(10, 8), dpi=300)
                _scatter = ax.scatter(x, y, c=categories, alpha=0.7, s=50)
                ax.set_xlabel("Cost Difference ($)", fontsize=12)
                ax.set_ylabel("Effect Difference (QALYs)", fontsize=12)
                ax.grid(True, alpha=0.3)
                plt.tight_layout()
                plt.close(fig)
            
            # Store results
            for metric in self.monitor.metrics[-2:]:
                results[metric.function_name] = metric.execution_time
            
            return results
            
        except ImportError:
            return {"Plot_Performance": 0.0}  # Skip if matplotlib not available
    
    def run_comprehensive_benchmark(self) -> str:
        """Run complete V3 benchmark suite."""
        print("🚀 Starting V3 Comprehensive Benchmark Suite")
        print("=" * 60)
        
        # System information
        print("📊 System Information:")
        memory = psutil.virtual_memory()
        print(f"   CPU cores: {psutil.cpu_count(logical=False)} physical, "
              f"{psutil.cpu_count(logical=True)} logical")
        print(f"   Memory: {memory.total / 1024**3:.1f} GB total, "
              f"{memory.available / 1024**3:.1f} GB available")
        print(f"   Optimal workers: {ParallelProcessor.optimal_worker_count()}")
        print()
        
        # Benchmark 1: PSA Processing
        print("🎲 Benchmarking PSA Processing...")
        psa_results = self.benchmark_psa_processing(sample_size=50000)
        
        # Benchmark 2: Plotting Performance
        print("📈 Benchmarking Plotting Performance...")
        plot_results = self.benchmark_plotting_performance()
        
        # Benchmark 3: Memory Efficiency
        print("💾 Benchmarking Memory Efficiency...")
        with MemoryOptimizer.memory_monitor("Large_DataFrame_Operations"):
            large_df = pd.DataFrame(np.random.rand(100000, 10))
            _result = large_df.groupby(large_df.index // 1000).sum()
        
        # Compile results
        _all_results = {**psa_results, **plot_results}
        
        # Generate report
        report = [
            "\n🎯 V3 Benchmark Results Summary:",
            "=" * 50,
            f"PSA Processing ({50000:,} rows):",
        ]
        
        for name, time_taken in psa_results.items():
            report.append(f"  {name}: {time_taken:.3f}s")
        
        report.append("Plotting Performance:")
        for name, time_taken in plot_results.items():
            report.append(f"  {name}: {time_taken:.3f}s")
        
        # Performance recommendations
        report.extend([
            "",
            "💡 Performance Recommendations:",
            f"  - Optimal worker count: {ParallelProcessor.optimal_worker_count()}",
            f"  - Available memory: {memory.available / 1024**3:.1f} GB",
            "  - Use chunked processing for datasets > 50,000 rows",
            "  - Enable parallel processing for PSA iterations > 10,000",
            "  - Monitor memory usage for DCEA analyses"
        ])
        
        return "\n".join(report)


def profile_function(func: Callable, *args, **kwargs) -> str:
    """Profile a function and return detailed performance report."""
    profiler = cProfile.Profile()
    
    profiler.enable()
    _result = func(*args, **kwargs)
    profiler.disable()
    
    # Generate report
    s = StringIO()
    stats = pstats.Stats(profiler, stream=s)
    stats.sort_stats('cumulative')
    stats.print_stats()
    
    return s.getvalue()


# Optimization utilities
def optimize_psa_processing(psa_file: str, output_dir: str):
    """Optimized PSA processing workflow."""
    
    with performance_context("PSA_Optimization_Complete"):
        
        # Memory-efficient loading
        with performance_context("PSA_Data_Loading"):
            chunk_list = []
            chunk_size = 25000
            
            for chunk in pd.read_csv(psa_file, chunksize=chunk_size):
                # Process chunk immediately to reduce memory
                processed_chunk = chunk.groupby('Arm').agg({
                    'Cost': ['mean', 'std'],
                    'Effect': ['mean', 'std'],
                    'Net_Benefit_50000': ['mean', 'std']
                }).reset_index()
                chunk_list.append(processed_chunk)
        
        # Combine processed chunks
        with performance_context("PSA_Data_Aggregation"):
            final_results = pd.concat(chunk_list, ignore_index=True)
            
        # Save optimized results
        with performance_context("PSA_Results_Export"):
            output_path = Path(output_dir) / "optimized_psa_results.csv"
            final_results.to_csv(output_path, index=False)
    
    return str(output_path)


if __name__ == "__main__":
    print("V3 Performance Optimization Suite")
    print("=" * 50)
    
    # Quick performance test
    suite = V3BenchmarkSuite()
    report = suite.run_comprehensive_benchmark()
    print(report)
    
    # Display overall performance summary
    print("\n" + _performance_monitor.get_summary())