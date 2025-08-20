"""
Lightweight performance optimizer for Vercel serverless functions.
Optimized for cold start performance and memory efficiency.
"""

import os
import time
import functools
from typing import Any, Callable, Dict, Optional
import json

# Simple in-memory cache for serverless environments
_cache: Dict[str, Any] = {}
_cache_timestamps: Dict[str, float] = {}

def cache_with_ttl(ttl_seconds: int = 300):
    """
    Simple TTL cache decorator optimized for serverless functions.
    Uses in-memory storage with automatic cleanup.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            current_time = time.time()
            
            # Check if cached result exists and is still valid
            if (cache_key in _cache and 
                cache_key in _cache_timestamps and
                current_time - _cache_timestamps[cache_key] < ttl_seconds):
                return _cache[cache_key]
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            _cache[cache_key] = result
            _cache_timestamps[cache_key] = current_time
            
            # Simple cleanup: remove oldest entries if cache gets too large
            if len(_cache) > 100:  # Keep cache size reasonable
                oldest_key = min(_cache_timestamps.keys(), key=lambda k: _cache_timestamps[k])
                del _cache[oldest_key]
                del _cache_timestamps[oldest_key]
            
            return result
        return wrapper
    return decorator

def optimize_cold_start():
    """
    Optimize function for cold start performance.
    Should be called once at module initialization.
    """
    # Pre-import heavy modules to reduce cold start time
    try:
        import openai
        import json
        import re
        # Pre-compile common regex patterns
        global COMMON_PATTERNS
        COMMON_PATTERNS = {
            'section_ref': re.compile(r's\.?\s*(\d+[a-z]?)', re.IGNORECASE),
            'act_year': re.compile(r'(\d{4})', re.IGNORECASE),
            'citation': re.compile(r'([A-Z][a-z]+ Act \d{4} \([A-Z]+\))', re.IGNORECASE)
        }
    except ImportError:
        pass

def get_memory_usage():
    """Get current memory usage in MB (if available)."""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    except ImportError:
        return 0

def optimize_response_size(data: dict, max_size: int = 500000) -> dict:
    """
    Optimize response size for better network performance.
    Truncates large responses if they exceed max_size bytes.
    """
    response_str = json.dumps(data)
    if len(response_str) <= max_size:
        return data
    
    # If response is too large, try to truncate text fields
    if 'response' in data and isinstance(data['response'], str):
        # Calculate how much to truncate
        overhead = len(response_str) - len(data['response'])
        max_response_length = max_size - overhead - 100  # Leave some buffer
        
        if max_response_length > 0:
            truncated_response = data['response'][:max_response_length]
            # Try to end at a sentence boundary
            last_period = truncated_response.rfind('.')
            if last_period > max_response_length - 200:  # If period is near the end
                truncated_response = truncated_response[:last_period + 1]
            
            truncated_response += "\n\n[Response truncated due to size limits]"
            
            optimized_data = data.copy()
            optimized_data['response'] = truncated_response
            optimized_data['truncated'] = True
            return optimized_data
    
    return data

def measure_performance():
    """
    Decorator to measure function execution time and memory usage.
    Useful for monitoring API performance.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            start_memory = get_memory_usage()
            
            try:
                result = await func(*args, **kwargs)
                
                # Add performance metrics to response if it's a dict
                if isinstance(result, dict):
                    execution_time = time.time() - start_time
                    result['_performance'] = {
                        'execution_time': round(execution_time, 3),
                        'memory_usage_mb': round(get_memory_usage() - start_memory, 2)
                    }
                
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                print(f"Function {func.__name__} failed after {execution_time:.3f}s: {str(e)}")
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            start_memory = get_memory_usage()
            
            try:
                result = func(*args, **kwargs)
                
                if isinstance(result, dict):
                    execution_time = time.time() - start_time
                    result['_performance'] = {
                        'execution_time': round(execution_time, 3),
                        'memory_usage_mb': round(get_memory_usage() - start_memory, 2)
                    }
                
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                print(f"Function {func.__name__} failed after {execution_time:.3f}s: {str(e)}")
                raise
        
        # Return appropriate wrapper based on whether function is async
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def create_environment_info() -> dict:
    """
    Create environment information for debugging and monitoring.
    """
    return {
        'python_version': os.sys.version,
        'vercel_region': os.getenv('VERCEL_REGION', 'unknown'),
        'memory_limit': os.getenv('AWS_LAMBDA_FUNCTION_MEMORY_SIZE', 'unknown'),
        'function_name': os.getenv('AWS_LAMBDA_FUNCTION_NAME', 'unknown'),
        'cache_size': len(_cache),
        'environment': 'production' if os.getenv('VERCEL_ENV') == 'production' else 'development'
    }

# Initialize performance optimizations
optimize_cold_start()