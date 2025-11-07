#!/usr/bin/env python3
"""
Progress indicator utilities for V3 NextGen Equity Framework.

Provides user feedback during long-running analyses with progress bars,
time estimates, and status updates.
"""

import time
import sys
from typing import Optional, Iterator
from contextlib import contextmanager
import threading
import itertools


class ProgressIndicator:
    """Simple progress indicator with spinner and timing."""
    
    def __init__(self, description: str, show_spinner: bool = True):
        """Initialize progress indicator."""
        self.description = description
        self.show_spinner = show_spinner
        self.start_time = None
        self.end_time = None
        self.spinner_thread = None
        self.spinner_active = False
        
        # Spinner characters
        self.spinner_chars = itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧'])
    
    def _spinner_worker(self):
        """Background spinner worker."""
        while self.spinner_active:
            if self.show_spinner and sys.stdout.isatty():
                elapsed = time.time() - self.start_time
                char = next(self.spinner_chars)
                sys.stdout.write(f'\r{char} {self.description} ({elapsed:.1f}s)')
                sys.stdout.flush()
                time.sleep(0.1)
            else:
                time.sleep(0.5)
    
    def start(self):
        """Start the progress indicator."""
        self.start_time = time.time()
        self.spinner_active = True
        
        if self.show_spinner:
            self.spinner_thread = threading.Thread(target=self._spinner_worker, daemon=True)
            self.spinner_thread.start()
        else:
            print(f"🚀 Starting: {self.description}")
    
    def stop(self, success: bool = True, message: Optional[str] = None):
        """Stop the progress indicator."""
        self.end_time = time.time()
        self.spinner_active = False
        
        if self.spinner_thread:
            self.spinner_thread.join(timeout=0.2)
        
        # Clear spinner line if present
        if self.show_spinner and sys.stdout.isatty():
            sys.stdout.write('\r' + ' ' * 80 + '\r')
            sys.stdout.flush()
        
        duration = self.end_time - self.start_time if self.start_time else 0
        status_icon = "✅" if success else "❌"
        status_text = "Completed" if success else "Failed"
        
        if message:
            print(f"{status_icon} {status_text}: {self.description} - {message} ({duration:.1f}s)")
        else:
            print(f"{status_icon} {status_text}: {self.description} ({duration:.1f}s)")
    
    def update(self, message: str):
        """Update progress message."""
        if not self.show_spinner:
            print(f"   {message}")


@contextmanager
def progress_context(description: str, show_spinner: bool = True) -> Iterator[ProgressIndicator]:
    """Context manager for progress indication."""
    indicator = ProgressIndicator(description, show_spinner)
    indicator.start()
    try:
        yield indicator
        indicator.stop(success=True)
    except Exception as e:
        indicator.stop(success=False, message=str(e))
        raise


class MultiStepProgress:
    """Progress tracker for multi-step processes."""
    
    def __init__(self, total_steps: int, description: str = "Processing"):
        """Initialize multi-step progress tracker."""
        self.total_steps = total_steps
        self.current_step = 0
        self.description = description
        self.step_times = []
        self.start_time = time.time()
        
        print(f"🎯 {self.description}: 0/{self.total_steps} steps")
    
    def step(self, step_description: str = None, success: bool = True):
        """Advance to next step."""
        self.current_step += 1
        step_time = time.time()
        self.step_times.append(step_time)
        
        # Calculate timing info
        elapsed = step_time - self.start_time
        if len(self.step_times) > 1:
            avg_step_time = elapsed / self.current_step
            remaining_time = avg_step_time * (self.total_steps - self.current_step)
            eta_str = f", ETA: {remaining_time:.1f}s"
        else:
            eta_str = ""
        
        # Status icon
        status_icon = "✅" if success else "❌"
        
        # Progress message
        progress_pct = (self.current_step / self.total_steps) * 100
        base_msg = f"{status_icon} {self.description}: {self.current_step}/{self.total_steps} steps ({progress_pct:.1f}%, {elapsed:.1f}s{eta_str})"
        
        if step_description:
            print(f"{base_msg} - {step_description}")
        else:
            print(base_msg)
    
    def complete(self, message: Optional[str] = None):
        """Mark process as complete."""
        total_time = time.time() - self.start_time
        if message:
            print(f"🎉 {self.description} completed: {message} ({total_time:.1f}s)")
        else:
            print(f"🎉 {self.description} completed ({total_time:.1f}s)")


class PSAProgressTracker:
    """Specialized progress tracker for PSA iterations."""
    
    def __init__(self, total_iterations: int, update_interval: int = 100):
        """Initialize PSA progress tracker."""
        self.total_iterations = total_iterations
        self.current_iteration = 0
        self.update_interval = update_interval
        self.start_time = time.time()
        self.last_update = 0
        
        print(f"🎲 PSA Analysis: 0/{self.total_iterations} iterations")
    
    def update(self, iteration: int):
        """Update progress for current iteration."""
        self.current_iteration = iteration
        
        # Only update display at intervals to avoid spam
        if iteration - self.last_update >= self.update_interval or iteration == self.total_iterations:
            elapsed = time.time() - self.start_time
            progress_pct = (iteration / self.total_iterations) * 100
            
            if iteration > 0:
                rate = iteration / elapsed
                remaining_time = (self.total_iterations - iteration) / rate
                eta_str = f", ETA: {remaining_time:.0f}s"
            else:
                eta_str = ""
            
            print(f"🎲 PSA Analysis: {iteration}/{self.total_iterations} iterations ({progress_pct:.1f}%, {elapsed:.1f}s{eta_str})")
            self.last_update = iteration
    
    def complete(self):
        """Mark PSA as complete."""
        total_time = time.time() - self.start_time
        rate = self.total_iterations / total_time
        print(f"✅ PSA Analysis completed: {self.total_iterations} iterations ({total_time:.1f}s, {rate:.1f} iter/s)")


def format_memory_usage(bytes_used: int) -> str:
    """Format memory usage in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_used < 1024.0:
            return f"{bytes_used:.1f} {unit}"
        bytes_used /= 1024.0
    return f"{bytes_used:.1f} TB"


def log_system_info():
    """Log basic system information for diagnostics."""
    try:
        import psutil
        memory = psutil.virtual_memory()
        print(f"💻 System: {memory.available / (1024**3):.1f} GB available memory")
    except ImportError:
        print("💻 System: psutil not available for memory monitoring")


# Progress decorators
def with_progress(description: str, show_spinner: bool = True):
    """Decorator to add progress indication to functions."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with progress_context(description, show_spinner) as _progress:
                return func(*args, **kwargs)
        return wrapper
    return decorator


# Example usage functions
def example_long_running_task():
    """Example of using progress indicators."""
    # Single task with spinner
    with progress_context("Loading data", show_spinner=True) as progress:
        time.sleep(2)
        progress.update("Data validated")
        time.sleep(1)
    
    # Multi-step process
    multi_progress = MultiStepProgress(3, "Analysis pipeline")
    
    time.sleep(1)
    multi_progress.step("Data preprocessing completed")
    
    time.sleep(2)
    multi_progress.step("Model fitting completed")
    
    time.sleep(1)
    multi_progress.step("Results generated")
    
    multi_progress.complete("All analyses finished successfully")
    
    # PSA simulation
    psa_progress = PSAProgressTracker(1000, update_interval=250)
    for i in range(1, 1001):
        time.sleep(0.001)  # Simulate computation
        psa_progress.update(i)
    psa_progress.complete()


if __name__ == "__main__":
    print("Testing V3 Progress Indicators")
    print("=" * 50)
    example_long_running_task()