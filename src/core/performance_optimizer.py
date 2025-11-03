import time
from typing import Callable, Any, Dict
import functools
import tracemalloc

class PerformanceOptimizer:
    """Comprehensive performance monitoring and optimization utility"""

    @staticmethod
    def measure_time(func: Callable) -> Callable:
        """
        Decorator to measure function execution time

        Args:
            func: Function to measure

        Returns:
            Wrapped function with timing information
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()

            execution_time = end_time - start_time
            print(f"{func.__name__} took {execution_time:.4f} seconds")

            return result
        return wrapper

    @staticmethod
    def measure_memory(func: Callable) -> Callable:
        """
        Decorator to track memory usage of a function

        Args:
            func: Function to monitor

        Returns:
            Wrapped function with memory tracking
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tracemalloc.start()
            result = func(*args, **kwargs)
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            print(f"{func.__name__}:")
            print(f"  Current memory usage: {current / 10**6:.2f} MB")
            print(f"  Peak memory usage: {peak / 10**6:.2f} MB")

            return result
        return wrapper

    @staticmethod
    def cache_results(maxsize: int = 128):
        """
        Decorator to cache function results with configurable size

        Args:
            maxsize: Maximum number of cached results

        Returns:
            Wrapped function with caching
        """
        return functools.lru_cache(maxsize=maxsize)

    @staticmethod
    def benchmark(
        func: Callable,
        *args,
        num_runs: int = 10,
        **kwargs
    ) -> Dict[str, float]:
        """
        Comprehensive function benchmarking

        Args:
            func: Function to benchmark
            num_runs: Number of execution runs
            *args, **kwargs: Function arguments

        Returns:
            Benchmark statistics
        """
        execution_times = []
        memory_usages = []

        for _ in range(num_runs):
            tracemalloc.start()
            start_time = time.perf_counter()

            result = func(*args, **kwargs)

            end_time = time.perf_counter()
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            execution_times.append(end_time - start_time)
            memory_usages.append(peak / 10**6)

        return {
            'avg_execution_time': sum(execution_times) / num_runs,
            'min_execution_time': min(execution_times),
            'max_execution_time': max(execution_times),
            'avg_memory_usage': sum(memory_usages) / num_runs,
            'min_memory_usage': min(memory_usages),
            'max_memory_usage': max(memory_usages)
        }