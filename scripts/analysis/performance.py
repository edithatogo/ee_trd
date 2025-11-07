"""
Performance Optimization

Parallel processing, memory optimization, and performance monitoring.
"""
from __future__ import annotations

import time
import psutil
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Callable, Any, Optional, Dict
from pathlib import Path

import numpy as np
import pandas as pd

__all__ = [
    "PerformanceMetrics",
    "PerformanceMonitor",
    "parallel_psa",
    "optimize_memory",
    "benchmark_analysis",
]


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    
    execution_time: float  # seconds
    peak_memory_mb: float
    cpu_percent: float
    iterations_per_second: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'execution_time_seconds': self.execution_time,
            'peak_memory_mb': self.peak_memory_mb,
            'cpu_percent': self.cpu_percent,
            'iterations_per_second': self.iterations_per_second,
        }


class PerformanceMonitor:
    """
    Monitor performance during analysis execution.
    """
    
    def __init__(self):
        """Initialize performance monitor."""
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.memory_samples: List[float] = []
        self.cpu_samples: List[float] = []
        self.process = psutil.Process()
    
    def start(self) -> None:
        """Start monitoring."""
        self.start_time = time.time()
        self.memory_samples = []
        self.cpu_samples = []
    
    def sample(self) -> None:
        """Take a performance sample."""
        # Memory usage in MB
        memory_mb = self.process.memory_info().rss / (1024 * 1024)
        self.memory_samples.append(memory_mb)
        
        # CPU usage percentage
        cpu_percent = self.process.cpu_percent(interval=0.1)
        self.cpu_samples.append(cpu_percent)
    
    def stop(self) -> PerformanceMetrics:
        """
        Stop monitoring and return metrics.
        
        Returns:
            PerformanceMetrics
        """
        self.end_time = time.time()
        
        # Calculate metrics
        execution_time = self.end_time - self.start_time
        peak_memory = max(self.memory_samples) if self.memory_samples else 0.0
        avg_cpu = np.mean(self.cpu_samples) if self.cpu_samples else 0.0
        
        return PerformanceMetrics(
            execution_time=execution_time,
            peak_memory_mb=peak_memory,
            cpu_percent=avg_cpu
        )


def parallel_psa(
    analysis_func: Callable,
    n_iterations: int,
    n_workers: int = 4,
    chunk_size: Optional[int] = None,
    **kwargs
) -> List[Any]:
    """
    Run PSA in parallel using multiprocessing.
    
    Args:
        analysis_func: Function to run for each iteration
        n_iterations: Number of PSA iterations
        n_workers: Number of parallel workers
        chunk_size: Size of chunks for parallel processing
        **kwargs: Additional arguments for analysis_func
    
    Returns:
        List of results from each iteration
    """
    if chunk_size is None:
        chunk_size = max(1, n_iterations // (n_workers * 4))
    
    # Create iteration indices
    iteration_indices = list(range(n_iterations))
    
    # Run in parallel
    results = []
    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        # Submit tasks
        futures = []
        for i in iteration_indices:
            future = executor.submit(analysis_func, i, **kwargs)
            futures.append(future)
        
        # Collect results
        for future in as_completed(futures):
            try:
                _result = future.result()
                results.append(_result)
            except Exception:
                # Error in parallel execution (log not available)
                results.append(None)
    
    return results


def optimize_memory(
    df: pd.DataFrame,
    aggressive: bool = False
) -> pd.DataFrame:
    """
    Optimize DataFrame memory usage.
    
    Args:
        df: DataFrame to optimize
        aggressive: Use aggressive optimization (may lose precision)
    
    Returns:
        Optimized DataFrame
    """
    df_optimized = df.copy()
    
    # Optimize numeric columns
    for col in df_optimized.select_dtypes(include=['int']).columns:
        col_min = df_optimized[col].min()
        col_max = df_optimized[col].max()
        
        # Choose smallest int type that fits
        if col_min >= 0:
            if col_max < 255:
                df_optimized[col] = df_optimized[col].astype(np.uint8)
            elif col_max < 65535:
                df_optimized[col] = df_optimized[col].astype(np.uint16)
            elif col_max < 4294967295:
                df_optimized[col] = df_optimized[col].astype(np.uint32)
        else:
            if col_min > -128 and col_max < 127:
                df_optimized[col] = df_optimized[col].astype(np.int8)
            elif col_min > -32768 and col_max < 32767:
                df_optimized[col] = df_optimized[col].astype(np.int16)
            elif col_min > -2147483648 and col_max < 2147483647:
                df_optimized[col] = df_optimized[col].astype(np.int32)
    
    # Optimize float columns
    for col in df_optimized.select_dtypes(include=['float']).columns:
        if aggressive:
            # Use float32 for aggressive optimization
            df_optimized[col] = df_optimized[col].astype(np.float32)
        else:
            # Check if float32 is sufficient
            col_min = df_optimized[col].min()
            col_max = df_optimized[col].max()
            
            if col_min > np.finfo(np.float32).min and col_max < np.finfo(np.float32).max:
                df_optimized[col] = df_optimized[col].astype(np.float32)
    
    # Optimize object columns (strings)
    for col in df_optimized.select_dtypes(include=['object']).columns:
        # Convert to category if few unique values
        n_unique = df_optimized[col].nunique()
        n_total = len(df_optimized[col])
        
        if n_unique / n_total < 0.5:  # Less than 50% unique
            df_optimized[col] = df_optimized[col].astype('category')
    
    return df_optimized


def benchmark_analysis(
    analysis_func: Callable,
    n_runs: int = 5,
    **kwargs
) -> Dict[str, Any]:
    """
    Benchmark analysis function performance.
    
    Args:
        analysis_func: Function to benchmark
        n_runs: Number of benchmark runs
        **kwargs: Arguments for analysis_func
    
    Returns:
        Dictionary with benchmark results
    """
    execution_times = []
    memory_usages = []
    
    for run in range(n_runs):
        monitor = PerformanceMonitor()
        monitor.start()
        
        # Run analysis
        try:
            _result = analysis_func(**kwargs)
            monitor.sample()
            metrics = monitor.stop()
            
            execution_times.append(metrics.execution_time)
            memory_usages.append(metrics.peak_memory_mb)
            
        except Exception:
            # Error in benchmark run (log not available)
            continue
    
    if not execution_times:
        return {
            'status': 'failed',
            'error': 'All benchmark runs failed'
        }
    
    # Calculate statistics
    benchmark_results = {
        'n_runs': len(execution_times),
        'execution_time': {
            'mean': np.mean(execution_times),
            'std': np.std(execution_times),
            'min': np.min(execution_times),
            'max': np.max(execution_times),
        },
        'memory_usage_mb': {
            'mean': np.mean(memory_usages),
            'std': np.std(memory_usages),
            'min': np.min(memory_usages),
            'max': np.max(memory_usages),
        },
    }
    
    return benchmark_results


def generate_optimization_recommendations(
    metrics: PerformanceMetrics,
    n_iterations: int,
    target_time: Optional[float] = None
) -> List[str]:
    """
    Generate optimization recommendations based on performance metrics.
    
    Args:
        metrics: Performance metrics
        n_iterations: Number of iterations
        target_time: Target execution time in seconds
    
    Returns:
        List of recommendations
    """
    recommendations = []
    
    # Check execution time
    if target_time and metrics.execution_time > target_time:
        speedup_needed = metrics.execution_time / target_time
        recommendations.append(
            f"Execution time ({metrics.execution_time:.1f}s) exceeds target ({target_time:.1f}s). "
            f"Consider using parallel processing with {int(speedup_needed) + 1} workers."
        )
    
    # Check memory usage
    if metrics.peak_memory_mb > 8000:  # > 8 GB
        recommendations.append(
            f"High memory usage ({metrics.peak_memory_mb:.0f} MB). "
            "Consider using memory optimization or processing in batches."
        )
    
    # Check iterations per second
    if metrics.iterations_per_second:
        if metrics.iterations_per_second < 10:
            recommendations.append(
                f"Low throughput ({metrics.iterations_per_second:.1f} iterations/second). "
                "Consider optimizing the analysis function or using compiled code (Numba/Cython)."
            )
    
    # Check CPU usage
    if metrics.cpu_percent < 50:
        recommendations.append(
            f"Low CPU utilization ({metrics.cpu_percent:.1f}%). "
            "Consider using parallel processing to utilize more cores."
        )
    
    if not recommendations:
        recommendations.append("Performance is within acceptable limits. No optimization needed.")
    
    return recommendations


def save_performance_report(
    metrics: PerformanceMetrics,
    recommendations: List[str],
    output_path: Path
) -> None:
    """
    Save performance report to file.
    
    Args:
        metrics: Performance metrics
        recommendations: Optimization recommendations
        output_path: Output file path
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    report_lines = [
        "# Performance Report",
        "",
        "## Metrics",
        "",
        f"- **Execution Time**: {metrics.execution_time:.2f} seconds",
        f"- **Peak Memory**: {metrics.peak_memory_mb:.1f} MB",
        f"- **CPU Usage**: {metrics.cpu_percent:.1f}%",
    ]
    
    if metrics.iterations_per_second:
        report_lines.append(f"- **Throughput**: {metrics.iterations_per_second:.1f} iterations/second")
    
    report_lines.extend([
        "",
        "## Recommendations",
        "",
    ])
    
    for i, recommendation in enumerate(recommendations, 1):
        report_lines.append(f"{i}. {recommendation}")
    
    report_lines.append("")
    report_lines.append("---")
    report_lines.append(f"*Report generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))
