"""
Advanced Token Usage Monitoring and Function Calling Optimization
"""

import asyncio
import time
import json
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import tiktoken
import hashlib
import os
from functools import wraps, lru_cache

logger = logging.getLogger(__name__)

class OptimizationStrategy(Enum):
    AGGRESSIVE = "aggressive"      # Maximum token savings, may reduce quality slightly
    BALANCED = "balanced"         # Balance between quality and efficiency
    CONSERVATIVE = "conservative" # Prioritize quality, minimal optimization

@dataclass
class TokenUsageMetrics:
    """Comprehensive token usage tracking"""
    request_id: str
    user_id: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float
    optimization_applied: bool
    optimization_savings: int
    cache_hit: bool
    function_calls_count: int
    timestamp: datetime
    endpoint: str
    
    @property
    def efficiency_ratio(self) -> float:
        """Calculate efficiency ratio (completion tokens / prompt tokens)"""
        return self.completion_tokens / max(1, self.prompt_tokens)

@dataclass
class OptimizationResult:
    """Result of token optimization"""
    original_tokens: int
    optimized_tokens: int
    savings: int
    savings_percent: float
    optimization_applied: List[str]
    quality_impact: str  # "none", "minimal", "moderate"

class TokenCounter:
    """Advanced token counting with model-specific encoding"""
    
    def __init__(self):
        self._encoders = {}
        self._model_context_limits = {
            "gpt-4o": 128000,
            "gpt-4o-mini": 128000,
            "gpt-4": 8192,
            "gpt-3.5-turbo": 16385,
            "text-embedding-3-small": 8191,
            "text-embedding-3-large": 8191
        }
    
    @lru_cache(maxsize=32)
    def get_encoder(self, model: str) -> tiktoken.Encoding:
        """Get tiktoken encoder for specific model with caching"""
        try:
            return tiktoken.encoding_for_model(model)
        except KeyError:
            # Default to cl100k_base for unknown models
            logger.warning(f"Unknown model {model}, using cl100k_base encoding")
            return tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str, model: str = "gpt-4o-mini") -> int:
        """Count tokens in text for specific model"""
        if not text:
            return 0
        
        encoder = self.get_encoder(model)
        return len(encoder.encode(str(text)))
    
    def count_message_tokens(self, messages: List[Dict], model: str = "gpt-4o-mini") -> int:
        """Count tokens in a list of messages including overhead"""
        encoder = self.get_encoder(model)
        
        # Token counting based on OpenAI's guidelines
        tokens_per_message = 3  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_name = 1     # if there's a name, the role is omitted
        
        num_tokens = 0
        for message in messages:
            num_tokens += tokens_per_message
            for key, value in message.items():
                num_tokens += len(encoder.encode(str(value)))
                if key == "name":
                    num_tokens += tokens_per_name
        
        num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
        return num_tokens
    
    def estimate_completion_tokens(self, prompt_tokens: int, model: str = "gpt-4o-mini") -> int:
        """Estimate completion tokens based on prompt length and model"""
        # Rough estimation based on empirical observations
        completion_ratios = {
            "gpt-4o": 0.6,
            "gpt-4o-mini": 0.5,
            "gpt-4": 0.7,
            "gpt-3.5-turbo": 0.4
        }
        
        ratio = completion_ratios.get(model, 0.5)
        return int(prompt_tokens * ratio)
    
    def get_context_limit(self, model: str) -> int:
        """Get context limit for model"""
        return self._model_context_limits.get(model, 4096)
    
    def check_context_limit(self, tokens: int, model: str) -> Tuple[bool, int]:
        """Check if token count exceeds model's context limit"""
        limit = self.get_context_limit(model)
        return tokens <= limit, limit

class ResponseCache:
    """Intelligent caching system for API responses"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.cache: Dict[str, Dict] = {}
        self.access_times: Dict[str, float] = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
    
    def _generate_cache_key(self, messages: List[Dict], model: str, temperature: float, **kwargs) -> str:
        """Generate cache key from request parameters"""
        # Create hash of normalized request parameters
        cache_data = {
            "messages": messages,
            "model": model,
            "temperature": round(temperature, 2),  # Round to avoid cache misses from tiny differences
            "kwargs": sorted(kwargs.items())
        }
        
        cache_string = json.dumps(cache_data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(cache_string.encode()).hexdigest()[:16]
    
    def _cleanup_expired(self):
        """Remove expired cache entries"""
        current_time = time.time()
        expired_keys = [
            key for key, access_time in self.access_times.items()
            if current_time - access_time > self.ttl_seconds
        ]
        
        for key in expired_keys:
            self.cache.pop(key, None)
            self.access_times.pop(key, None)
    
    def _evict_lru(self):
        """Evict least recently used entries if cache is full"""
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(self.access_times, key=self.access_times.get)
            self.cache.pop(oldest_key, None)
            self.access_times.pop(oldest_key, None)
    
    def get(self, messages: List[Dict], model: str, temperature: float, **kwargs) -> Optional[Dict]:
        """Get cached response if available"""
        self._cleanup_expired()
        
        cache_key = self._generate_cache_key(messages, model, temperature, **kwargs)
        
        if cache_key in self.cache:
            self.access_times[cache_key] = time.time()
            logger.info(f"Cache hit for key {cache_key}")
            return self.cache[cache_key]
        
        return None
    
    def put(self, messages: List[Dict], model: str, temperature: float, response: Dict, **kwargs):
        """Cache a response"""
        self._cleanup_expired()
        self._evict_lru()
        
        cache_key = self._generate_cache_key(messages, model, temperature, **kwargs)
        
        self.cache[cache_key] = {
            "response": response,
            "cached_at": time.time()
        }
        self.access_times[cache_key] = time.time()
        
        logger.info(f"Cached response for key {cache_key}")
    
    def clear(self):
        """Clear all cache entries"""
        self.cache.clear()
        self.access_times.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "entries": len(self.cache),
            "max_size": self.max_size,
            "hit_rate": "Not tracked",  # Would need request counting
            "oldest_entry_age": time.time() - min(self.access_times.values()) if self.access_times else 0
        }

class PromptOptimizer:
    """Optimize prompts to reduce token usage while maintaining quality"""
    
    def __init__(self, token_counter: TokenCounter):
        self.token_counter = token_counter
        
        # Optimization rules
        self.redundant_phrases = [
            "Please note that",
            "It should be noted that",
            "It is important to understand that",
            "As previously mentioned",
            "In other words",
            "Furthermore,",
            "Moreover,",
            "Additionally,",
            "In addition,"
        ]
        
        self.verbose_replacements = {
            "in order to": "to",
            "due to the fact that": "because",
            "despite the fact that": "although",
            "at this point in time": "now",
            "in the event that": "if",
            "for the reason that": "because",
            "with regard to": "regarding",
            "in relation to": "about",
            "at the present time": "now"
        }
    
    def optimize_system_prompt(self, system_prompt: str, strategy: OptimizationStrategy) -> Tuple[str, OptimizationResult]:
        """Optimize system prompt based on strategy"""
        original_tokens = self.token_counter.count_tokens(system_prompt)
        optimized_prompt = system_prompt
        applied_optimizations = []
        
        if strategy in [OptimizationStrategy.AGGRESSIVE, OptimizationStrategy.BALANCED]:
            # Remove redundant phrases
            for phrase in self.redundant_phrases:
                if phrase in optimized_prompt:
                    optimized_prompt = optimized_prompt.replace(phrase, "")
                    applied_optimizations.append(f"removed_phrase_{phrase.replace(' ', '_')}")
            
            # Replace verbose phrases
            for verbose, concise in self.verbose_replacements.items():
                if verbose in optimized_prompt.lower():
                    optimized_prompt = optimized_prompt.replace(verbose, concise)
                    applied_optimizations.append(f"replaced_{verbose.replace(' ', '_')}")
        
        if strategy == OptimizationStrategy.AGGRESSIVE:
            # More aggressive optimizations
            optimized_prompt = self._compress_examples(optimized_prompt)
            optimized_prompt = self._remove_excessive_formatting(optimized_prompt)
            applied_optimizations.extend(["compressed_examples", "reduced_formatting"])
        
        # Clean up extra whitespace
        optimized_prompt = ' '.join(optimized_prompt.split())
        
        optimized_tokens = self.token_counter.count_tokens(optimized_prompt)
        savings = original_tokens - optimized_tokens
        
        quality_impact = "none"
        if len(applied_optimizations) > 3:
            quality_impact = "minimal"
        if strategy == OptimizationStrategy.AGGRESSIVE and savings > original_tokens * 0.2:
            quality_impact = "moderate"
        
        return optimized_prompt, OptimizationResult(
            original_tokens=original_tokens,
            optimized_tokens=optimized_tokens,
            savings=savings,
            savings_percent=(savings / max(1, original_tokens)) * 100,
            optimization_applied=applied_optimizations,
            quality_impact=quality_impact
        )
    
    def _compress_examples(self, text: str) -> str:
        """Compress examples in prompt while preserving meaning"""
        # This would implement more sophisticated example compression
        # For now, just a simple implementation
        return text
    
    def _remove_excessive_formatting(self, text: str) -> str:
        """Remove excessive formatting that doesn't add value"""
        # Remove multiple consecutive newlines
        import re
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Remove excessive dashes
        text = re.sub(r'-{3,}', '---', text)
        return text
    
    def optimize_messages(self, messages: List[Dict], strategy: OptimizationStrategy) -> Tuple[List[Dict], OptimizationResult]:
        """Optimize entire message list"""
        original_tokens = self.token_counter.count_message_tokens(messages)
        optimized_messages = []
        total_applied_optimizations = []
        
        for message in messages:
            if message["role"] == "system":
                optimized_content, result = self.optimize_system_prompt(message["content"], strategy)
                total_applied_optimizations.extend(result.optimization_applied)
            else:
                optimized_content = message["content"]
            
            optimized_messages.append({
                **message,
                "content": optimized_content
            })
        
        optimized_tokens = self.token_counter.count_message_tokens(optimized_messages)
        savings = original_tokens - optimized_tokens
        
        return optimized_messages, OptimizationResult(
            original_tokens=original_tokens,
            optimized_tokens=optimized_tokens,
            savings=savings,
            savings_percent=(savings / max(1, original_tokens)) * 100,
            optimization_applied=total_applied_optimizations,
            quality_impact="minimal" if len(total_applied_optimizations) > 0 else "none"
        )

class FunctionCallOptimizer:
    """Optimize function calling to reduce token usage"""
    
    def __init__(self):
        self.function_usage_stats: Dict[str, Dict] = {}
    
    def optimize_function_definitions(self, functions: List[Dict]) -> List[Dict]:
        """Optimize function definitions to reduce token usage"""
        optimized_functions = []
        
        for func in functions:
            optimized_func = self._optimize_single_function(func)
            optimized_functions.append(optimized_func)
        
        return optimized_functions
    
    def _optimize_single_function(self, function_def: Dict) -> Dict:
        """Optimize a single function definition"""
        # Create a copy to avoid modifying original
        optimized = function_def.copy()
        
        # Optimize description
        if "description" in optimized:
            desc = optimized["description"]
            # Remove verbose phrases
            desc = desc.replace("This function", "").strip()
            desc = desc.replace("This endpoint", "").strip()
            # Ensure it starts with a verb
            if not desc[0].isupper():
                desc = desc.capitalize()
            optimized["description"] = desc
        
        # Optimize parameter descriptions
        if "parameters" in optimized and "properties" in optimized["parameters"]:
            for param_name, param_def in optimized["parameters"]["properties"].items():
                if "description" in param_def:
                    desc = param_def["description"]
                    # Make parameter descriptions more concise
                    desc = desc.replace("The ", "").strip()
                    desc = desc.replace("A ", "").strip()
                    param_def["description"] = desc
        
        return optimized
    
    def should_include_function(self, function_name: str, context: Dict) -> bool:
        """Determine if a function should be included based on context"""
        # This would implement intelligent function filtering
        # based on the query context and function relevance
        
        # For legal queries, prioritize legal-specific functions
        query = context.get("query", "").lower()
        legal_keywords = ["legal", "law", "court", "statute", "case", "provision", "act"]
        
        legal_functions = [
            "search_legal_database",
            "get_legal_provision",
            "find_case_law",
            "analyze_legislation"
        ]
        
        if any(keyword in query for keyword in legal_keywords):
            # Prioritize legal functions
            if function_name in legal_functions:
                return True
        
        # Default logic
        return True
    
    def record_function_usage(self, function_name: str, success: bool, tokens_used: int):
        """Record function usage statistics"""
        if function_name not in self.function_usage_stats:
            self.function_usage_stats[function_name] = {
                "calls": 0,
                "successes": 0,
                "total_tokens": 0,
                "avg_tokens": 0
            }
        
        stats = self.function_usage_stats[function_name]
        stats["calls"] += 1
        if success:
            stats["successes"] += 1
        stats["total_tokens"] += tokens_used
        stats["avg_tokens"] = stats["total_tokens"] / stats["calls"]
    
    def get_function_recommendations(self, context: Dict) -> List[str]:
        """Get recommended functions based on usage patterns and context"""
        # Analyze context and return most relevant functions
        query = context.get("query", "").lower()
        
        recommendations = []
        
        if "legal" in query or "law" in query:
            recommendations.extend([
                "search_legal_database",
                "get_legal_provision",
                "analyze_legislation"
            ])
        
        if "case" in query or "precedent" in query:
            recommendations.append("find_case_law")
        
        return recommendations[:5]  # Limit to top 5

class TokenUsageMonitor:
    """Comprehensive token usage monitoring and analytics"""
    
    def __init__(self):
        self.usage_history: List[TokenUsageMetrics] = []
        self.daily_usage: Dict[str, Dict[str, float]] = {}  # {date: {user_id: cost}}
        self.model_usage: Dict[str, Dict] = {}  # Model-specific usage stats
        
    def record_usage(self, metrics: TokenUsageMetrics):
        """Record token usage metrics"""
        self.usage_history.append(metrics)
        
        # Update daily usage
        date_key = metrics.timestamp.strftime("%Y-%m-%d")
        if date_key not in self.daily_usage:
            self.daily_usage[date_key] = {}
        
        self.daily_usage[date_key][metrics.user_id] = (
            self.daily_usage[date_key].get(metrics.user_id, 0) + metrics.estimated_cost
        )
        
        # Update model usage stats
        if metrics.model not in self.model_usage:
            self.model_usage[metrics.model] = {
                "total_requests": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "avg_tokens_per_request": 0,
                "efficiency_scores": []
            }
        
        model_stats = self.model_usage[metrics.model]
        model_stats["total_requests"] += 1
        model_stats["total_tokens"] += metrics.total_tokens
        model_stats["total_cost"] += metrics.estimated_cost
        model_stats["avg_tokens_per_request"] = model_stats["total_tokens"] / model_stats["total_requests"]
        model_stats["efficiency_scores"].append(metrics.efficiency_ratio)
        
        # Keep only last 1000 entries to prevent memory bloat
        if len(self.usage_history) > 1000:
            self.usage_history = self.usage_history[-1000:]
    
    def get_usage_analytics(self, user_id: Optional[str] = None, days: int = 7) -> Dict[str, Any]:
        """Get comprehensive usage analytics"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Filter metrics by time and optionally user
        relevant_metrics = [
            m for m in self.usage_history
            if m.timestamp >= cutoff_date and (not user_id or m.user_id == user_id)
        ]
        
        if not relevant_metrics:
            return {"message": "No usage data available for the specified period"}
        
        total_requests = len(relevant_metrics)
        total_tokens = sum(m.total_tokens for m in relevant_metrics)
        total_cost = sum(m.estimated_cost for m in relevant_metrics)
        cache_hits = sum(1 for m in relevant_metrics if m.cache_hit)
        optimized_requests = sum(1 for m in relevant_metrics if m.optimization_applied)
        
        return {
            "period_days": days,
            "user_id": user_id,
            "summary": {
                "total_requests": total_requests,
                "total_tokens": total_tokens,
                "total_cost": round(total_cost, 2),
                "avg_tokens_per_request": round(total_tokens / total_requests, 2),
                "avg_cost_per_request": round(total_cost / total_requests, 4),
                "cache_hit_rate": round((cache_hits / total_requests) * 100, 1),
                "optimization_rate": round((optimized_requests / total_requests) * 100, 1)
            },
            "model_breakdown": self._get_model_breakdown(relevant_metrics),
            "daily_usage": self._get_daily_breakdown(relevant_metrics),
            "efficiency_metrics": self._calculate_efficiency_metrics(relevant_metrics)
        }
    
    def _get_model_breakdown(self, metrics: List[TokenUsageMetrics]) -> Dict[str, Dict]:
        """Get usage breakdown by model"""
        model_data = {}
        
        for metric in metrics:
            if metric.model not in model_data:
                model_data[metric.model] = {
                    "requests": 0,
                    "tokens": 0,
                    "cost": 0.0
                }
            
            model_data[metric.model]["requests"] += 1
            model_data[metric.model]["tokens"] += metric.total_tokens
            model_data[metric.model]["cost"] += metric.estimated_cost
        
        return model_data
    
    def _get_daily_breakdown(self, metrics: List[TokenUsageMetrics]) -> Dict[str, Dict]:
        """Get daily usage breakdown"""
        daily_data = {}
        
        for metric in metrics:
            date_key = metric.timestamp.strftime("%Y-%m-%d")
            if date_key not in daily_data:
                daily_data[date_key] = {
                    "requests": 0,
                    "tokens": 0,
                    "cost": 0.0
                }
            
            daily_data[date_key]["requests"] += 1
            daily_data[date_key]["tokens"] += metric.total_tokens
            daily_data[date_key]["cost"] += metric.estimated_cost
        
        return daily_data
    
    def _calculate_efficiency_metrics(self, metrics: List[TokenUsageMetrics]) -> Dict[str, float]:
        """Calculate efficiency metrics"""
        if not metrics:
            return {}
        
        efficiency_ratios = [m.efficiency_ratio for m in metrics]
        optimization_savings = sum(m.optimization_savings for m in metrics if m.optimization_savings > 0)
        
        return {
            "avg_efficiency_ratio": round(sum(efficiency_ratios) / len(efficiency_ratios), 3),
            "total_optimization_savings": optimization_savings,
            "avg_optimization_savings": round(optimization_savings / len(metrics), 2)
        }

# Global instances
token_counter = TokenCounter()
response_cache = ResponseCache()
prompt_optimizer = PromptOptimizer(token_counter)
function_optimizer = FunctionCallOptimizer()
usage_monitor = TokenUsageMonitor()

def token_optimized(strategy: OptimizationStrategy = OptimizationStrategy.BALANCED):
    """Decorator for token-optimized API calls"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user_id = kwargs.get("user_id", "anonymous")
            model = kwargs.get("model", "gpt-4o-mini")
            messages = kwargs.get("messages", [])
            
            start_time = time.time()
            request_id = f"{user_id}_{int(start_time)}"
            
            # Check cache first
            cached_response = response_cache.get(messages, model, kwargs.get("temperature", 0.7))
            if cached_response:
                # Record cache hit metrics
                metrics = TokenUsageMetrics(
                    request_id=request_id,
                    user_id=user_id,
                    model=model,
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                    estimated_cost=0.0,
                    optimization_applied=False,
                    optimization_savings=0,
                    cache_hit=True,
                    function_calls_count=0,
                    timestamp=datetime.utcnow(),
                    endpoint=func.__name__
                )
                usage_monitor.record_usage(metrics)
                
                return cached_response["response"]
            
            # Optimize messages
            if messages:
                optimized_messages, optimization_result = prompt_optimizer.optimize_messages(messages, strategy)
                kwargs["messages"] = optimized_messages
            else:
                optimization_result = OptimizationResult(0, 0, 0, 0.0, [], "none")
            
            # Execute function
            try:
                result = await func(*args, **kwargs)
                
                # Extract token usage from result
                prompt_tokens = getattr(result, "usage", {}).get("prompt_tokens", 0) if hasattr(result, "usage") else 0
                completion_tokens = getattr(result, "usage", {}).get("completion_tokens", 0) if hasattr(result, "usage") else 0
                
                # Calculate cost
                from .rate_limiter import MODEL_PRICING
                pricing = MODEL_PRICING.get(model, MODEL_PRICING["gpt-4o"])
                cost = (prompt_tokens / 1000) * pricing["input"] + (completion_tokens / 1000) * pricing["output"]
                
                # Record metrics
                metrics = TokenUsageMetrics(
                    request_id=request_id,
                    user_id=user_id,
                    model=model,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                    estimated_cost=cost,
                    optimization_applied=optimization_result.savings > 0,
                    optimization_savings=optimization_result.savings,
                    cache_hit=False,
                    function_calls_count=len(kwargs.get("functions", [])),
                    timestamp=datetime.utcnow(),
                    endpoint=func.__name__
                )
                usage_monitor.record_usage(metrics)
                
                # Cache successful response
                if hasattr(result, "choices") and result.choices:
                    response_cache.put(kwargs.get("messages", []), model, kwargs.get("temperature", 0.7), result)
                
                return result
                
            except Exception as e:
                logger.error(f"Error in token-optimized call: {e}")
                raise
        
        return wrapper
    return decorator