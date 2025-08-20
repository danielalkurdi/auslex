"""
Circuit Breaker and Advanced Error Handling for OpenAI API Integration
"""

import asyncio
import time
import logging
from typing import Dict, Optional, Callable, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from functools import wraps
import httpx
from openai import OpenAI, APIError, RateLimitError, APIConnectionError, APITimeoutError
import json
import os

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit breaker tripped
    HALF_OPEN = "half_open"  # Testing if service recovered

class ErrorType(Enum):
    RATE_LIMIT = "rate_limit"
    API_ERROR = "api_error"
    TIMEOUT = "timeout"
    CONNECTION = "connection"
    AUTHENTICATION = "authentication"
    QUOTA_EXCEEDED = "quota_exceeded"
    MODEL_OVERLOADED = "model_overloaded"
    UNKNOWN = "unknown"

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior"""
    failure_threshold: int = 5  # Number of failures before opening circuit
    timeout_duration: float = 60.0  # Seconds to wait before trying again
    half_open_max_calls: int = 3  # Max calls in half-open state
    success_threshold: int = 2  # Successes needed to close circuit from half-open
    error_rate_threshold: float = 0.5  # Error rate threshold (0.5 = 50%)
    minimum_throughput: int = 10  # Minimum calls before considering error rate

@dataclass
class ErrorMetrics:
    """Track error metrics for circuit breaker decisions"""
    total_calls: int = 0
    failures: int = 0
    successes: int = 0
    last_failure_time: Optional[float] = None
    error_types: Dict[ErrorType, int] = None
    
    def __post_init__(self):
        if self.error_types is None:
            self.error_types = {error_type: 0 for error_type in ErrorType}
    
    @property
    def error_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.failures / self.total_calls

class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open"""
    def __init__(self, message: str, retry_after: Optional[float] = None):
        self.retry_after = retry_after
        super().__init__(message)

class FallbackHandler:
    """Handles fallback strategies when primary API fails"""
    
    def __init__(self):
        self.fallback_models = {
            "gpt-4o": ["gpt-4o-mini", "gpt-3.5-turbo"],
            "gpt-4": ["gpt-4o-mini", "gpt-3.5-turbo"],
            "gpt-4o-mini": ["gpt-3.5-turbo"],
        }
        
        # Cache for fallback responses
        self.response_cache: Dict[str, Dict] = {}
        self.cache_ttl = 300  # 5 minutes
    
    def get_fallback_models(self, primary_model: str) -> list:
        """Get list of fallback models for a primary model"""
        return self.fallback_models.get(primary_model, ["gpt-3.5-turbo"])
    
    def get_cached_response(self, cache_key: str) -> Optional[Dict]:
        """Get cached response if available and not expired"""
        if cache_key not in self.response_cache:
            return None
        
        cached_data = self.response_cache[cache_key]
        if time.time() - cached_data["timestamp"] > self.cache_ttl:
            del self.response_cache[cache_key]
            return None
        
        return cached_data["response"]
    
    def cache_response(self, cache_key: str, response: Dict):
        """Cache a successful response"""
        self.response_cache[cache_key] = {
            "response": response,
            "timestamp": time.time()
        }
    
    def generate_fallback_response(self, error_type: ErrorType, original_request: Dict) -> Dict:
        """Generate a fallback response when all API calls fail"""
        fallback_responses = {
            ErrorType.RATE_LIMIT: {
                "response": "I'm experiencing high demand right now. Please try your request again in a few minutes. "
                          "For immediate assistance, you can consult official legal resources like austlii.edu.au.",
                "error": "rate_limit_exceeded",
                "retry_after": 60
            },
            ErrorType.QUOTA_EXCEEDED: {
                "response": "The API quota has been exceeded. Please contact support or try again later.",
                "error": "quota_exceeded",
                "retry_after": 3600
            },
            ErrorType.MODEL_OVERLOADED: {
                "response": "The AI model is currently overloaded. Please try again in a few minutes.",
                "error": "model_overloaded",
                "retry_after": 300
            },
            ErrorType.TIMEOUT: {
                "response": "The request timed out. For complex legal queries, please try breaking them into smaller parts.",
                "error": "timeout",
                "retry_after": 30
            },
            ErrorType.AUTHENTICATION: {
                "response": "Authentication error occurred. Please contact support.",
                "error": "auth_error",
                "retry_after": None
            }
        }
        
        return fallback_responses.get(error_type, {
            "response": "I'm temporarily unable to process your request. Please try again later or contact support.",
            "error": "service_unavailable",
            "retry_after": 60
        })

class CircuitBreaker:
    """Advanced circuit breaker implementation for OpenAI API calls"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.metrics = ErrorMetrics()
        self.state_changed_time = time.time()
        self.half_open_calls = 0
        self.half_open_successes = 0
        self.fallback_handler = FallbackHandler()
        
    def _classify_error(self, error: Exception) -> ErrorType:
        """Classify the type of error for appropriate handling"""
        if isinstance(error, RateLimitError):
            return ErrorType.RATE_LIMIT
        elif isinstance(error, APITimeoutError):
            return ErrorType.TIMEOUT
        elif isinstance(error, APIConnectionError):
            return ErrorType.CONNECTION
        elif isinstance(error, APIError):
            if "quota" in str(error).lower():
                return ErrorType.QUOTA_EXCEEDED
            elif "overloaded" in str(error).lower() or "capacity" in str(error).lower():
                return ErrorType.MODEL_OVERLOADED
            elif "auth" in str(error).lower() or "key" in str(error).lower():
                return ErrorType.AUTHENTICATION
            else:
                return ErrorType.API_ERROR
        else:
            return ErrorType.UNKNOWN
    
    def _should_trip(self) -> bool:
        """Determine if circuit breaker should trip to OPEN state"""
        # Check failure threshold
        if self.metrics.failures >= self.config.failure_threshold:
            return True
        
        # Check error rate threshold
        if (self.metrics.total_calls >= self.config.minimum_throughput and 
            self.metrics.error_rate >= self.config.error_rate_threshold):
            return True
        
        return False
    
    def _can_attempt_call(self) -> bool:
        """Check if we can attempt a call based on current state"""
        current_time = time.time()
        
        if self.state == CircuitState.CLOSED:
            return True
        
        elif self.state == CircuitState.OPEN:
            # Check if timeout has passed
            if current_time - self.state_changed_time >= self.config.timeout_duration:
                self._transition_to_half_open()
                return True
            return False
        
        elif self.state == CircuitState.HALF_OPEN:
            # Allow limited calls in half-open state
            return self.half_open_calls < self.config.half_open_max_calls
        
        return False
    
    def _transition_to_half_open(self):
        """Transition circuit breaker to half-open state"""
        self.state = CircuitState.HALF_OPEN
        self.state_changed_time = time.time()
        self.half_open_calls = 0
        self.half_open_successes = 0
        logger.info(f"Circuit breaker {self.name} transitioned to HALF_OPEN")
    
    def _transition_to_open(self):
        """Transition circuit breaker to open state"""
        self.state = CircuitState.OPEN
        self.state_changed_time = time.time()
        logger.warning(f"Circuit breaker {self.name} OPENED - failures: {self.metrics.failures}, error_rate: {self.metrics.error_rate:.2f}")
    
    def _transition_to_closed(self):
        """Transition circuit breaker to closed state"""
        self.state = CircuitState.CLOSED
        self.state_changed_time = time.time()
        # Reset metrics for fresh start
        self.metrics = ErrorMetrics()
        logger.info(f"Circuit breaker {self.name} CLOSED - service recovered")
    
    def record_success(self):
        """Record a successful call"""
        self.metrics.total_calls += 1
        self.metrics.successes += 1
        
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_successes += 1
            if self.half_open_successes >= self.config.success_threshold:
                self._transition_to_closed()
    
    def record_failure(self, error: Exception):
        """Record a failed call"""
        self.metrics.total_calls += 1
        self.metrics.failures += 1
        self.metrics.last_failure_time = time.time()
        
        error_type = self._classify_error(error)
        self.metrics.error_types[error_type] += 1
        
        if self.state == CircuitState.CLOSED and self._should_trip():
            self._transition_to_open()
        elif self.state == CircuitState.HALF_OPEN:
            # Failure in half-open state immediately opens circuit
            self._transition_to_open()
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a function call with circuit breaker protection"""
        if not self._can_attempt_call():
            retry_after = self.config.timeout_duration - (time.time() - self.state_changed_time)
            raise CircuitBreakerError(
                f"Circuit breaker {self.name} is OPEN", 
                retry_after=max(1, retry_after)
            )
        
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_calls += 1
        
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            self.record_success()
            return result
            
        except Exception as e:
            self.record_failure(e)
            raise
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get circuit breaker metrics"""
        current_time = time.time()
        return {
            "name": self.name,
            "state": self.state.value,
            "metrics": {
                "total_calls": self.metrics.total_calls,
                "failures": self.metrics.failures,
                "successes": self.metrics.successes,
                "error_rate": self.metrics.error_rate,
                "error_types": {k.value: v for k, v in self.metrics.error_types.items()}
            },
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "timeout_duration": self.config.timeout_duration,
                "error_rate_threshold": self.config.error_rate_threshold
            },
            "state_info": {
                "time_in_current_state": current_time - self.state_changed_time,
                "half_open_calls": self.half_open_calls if self.state == CircuitState.HALF_OPEN else None,
                "time_until_retry": max(0, self.config.timeout_duration - (current_time - self.state_changed_time)) if self.state == CircuitState.OPEN else None
            }
        }

class RetryHandler:
    """Handles retry logic with exponential backoff and jitter"""
    
    def __init__(self):
        self.max_retries = int(os.getenv("OPENAI_MAX_RETRIES", "3"))
        self.base_delay = float(os.getenv("OPENAI_BASE_RETRY_DELAY", "1.0"))
        self.max_delay = float(os.getenv("OPENAI_MAX_RETRY_DELAY", "60.0"))
        
    def calculate_delay(self, attempt: int, error_type: ErrorType) -> float:
        """Calculate delay with exponential backoff and jitter"""
        # Base exponential backoff
        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
        
        # Adjust based on error type
        multipliers = {
            ErrorType.RATE_LIMIT: 2.0,
            ErrorType.MODEL_OVERLOADED: 1.5,
            ErrorType.QUOTA_EXCEEDED: 5.0,
            ErrorType.TIMEOUT: 1.2,
            ErrorType.CONNECTION: 1.3,
            ErrorType.API_ERROR: 1.0,
            ErrorType.UNKNOWN: 1.0
        }
        
        delay *= multipliers.get(error_type, 1.0)
        
        # Add jitter (±20%)
        import random
        jitter = delay * 0.2 * (random.random() * 2 - 1)
        
        return max(0.1, delay + jitter)
    
    def should_retry(self, error: Exception, attempt: int) -> bool:
        """Determine if an error should be retried"""
        if attempt >= self.max_retries:
            return False
        
        # Don't retry certain error types
        non_retryable_errors = {
            ErrorType.AUTHENTICATION,
            ErrorType.QUOTA_EXCEEDED
        }
        
        error_type = CircuitBreaker("temp", CircuitBreakerConfig())._classify_error(error)
        
        return error_type not in non_retryable_errors

# Global circuit breakers for different OpenAI endpoints
circuit_breakers = {
    "chat_completions": CircuitBreaker("chat_completions", CircuitBreakerConfig()),
    "embeddings": CircuitBreaker("embeddings", CircuitBreakerConfig(failure_threshold=10, timeout_duration=30)),
    "fine_tuning": CircuitBreaker("fine_tuning", CircuitBreakerConfig(failure_threshold=3, timeout_duration=300))
}

retry_handler = RetryHandler()

def circuit_breaker_decorator(endpoint: str = "chat_completions"):
    """Decorator to apply circuit breaker protection to OpenAI API calls"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            circuit_breaker = circuit_breakers[endpoint]
            
            # Try with circuit breaker protection
            try:
                return await circuit_breaker.call(func, *args, **kwargs)
            except CircuitBreakerError:
                # Circuit breaker is open, try fallback
                return circuit_breaker.fallback_handler.generate_fallback_response(
                    ErrorType.MODEL_OVERLOADED, 
                    {"args": args, "kwargs": kwargs}
                )
        return wrapper
    return decorator

def resilient_openai_call(endpoint: str = "chat_completions"):
    """Decorator that combines circuit breaker, retry logic, and fallback handling"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            circuit_breaker = circuit_breakers[endpoint]
            last_error = None
            
            for attempt in range(retry_handler.max_retries + 1):
                try:
                    return await circuit_breaker.call(func, *args, **kwargs)
                    
                except CircuitBreakerError as e:
                    # Circuit breaker is open
                    logger.warning(f"Circuit breaker open for {endpoint}: {e}")
                    return circuit_breaker.fallback_handler.generate_fallback_response(
                        ErrorType.MODEL_OVERLOADED,
                        {"args": args, "kwargs": kwargs}
                    )
                    
                except Exception as e:
                    last_error = e
                    error_type = circuit_breaker._classify_error(e)
                    
                    logger.warning(f"API call failed (attempt {attempt + 1}): {type(e).__name__}: {e}")
                    
                    # Check if we should retry
                    if not retry_handler.should_retry(e, attempt):
                        break
                    
                    # Calculate and apply delay
                    if attempt < retry_handler.max_retries:
                        delay = retry_handler.calculate_delay(attempt, error_type)
                        logger.info(f"Retrying in {delay:.2f} seconds...")
                        await asyncio.sleep(delay)
            
            # All retries failed, return fallback response
            logger.error(f"All retries failed for {endpoint}: {last_error}")
            error_type = circuit_breaker._classify_error(last_error) if last_error else ErrorType.UNKNOWN
            return circuit_breaker.fallback_handler.generate_fallback_response(
                error_type,
                {"args": args, "kwargs": kwargs}
            )
        
        return wrapper
    return decorator

async def get_circuit_breaker_status() -> Dict[str, Any]:
    """Get status of all circuit breakers"""
    return {name: cb.get_metrics() for name, cb in circuit_breakers.items()}

def reset_circuit_breaker(endpoint: str) -> bool:
    """Manually reset a circuit breaker"""
    if endpoint in circuit_breakers:
        circuit_breakers[endpoint]._transition_to_closed()
        logger.info(f"Circuit breaker {endpoint} manually reset")
        return True
    return False