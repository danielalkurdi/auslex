"""
Enterprise-grade Rate Limiting and Cost Control System for OpenAI API Integration
"""

import asyncio
import time
import json
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import httpx
import os
from functools import wraps

logger = logging.getLogger(__name__)

class RateLimitTier(Enum):
    """Different rate limit tiers based on user types or API keys"""
    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"
    INTERNAL = "internal"

class APIEndpoint(Enum):
    """Track different OpenAI endpoints separately"""
    CHAT_COMPLETION = "chat/completions"
    EMBEDDING = "embeddings"
    FINE_TUNING = "fine_tuning"

@dataclass
class TokenUsage:
    """Track token usage across different dimensions"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

@dataclass
class RateLimitConfig:
    """Configuration for rate limits"""
    requests_per_minute: int
    tokens_per_minute: int
    concurrent_requests: int
    daily_cost_limit: float
    monthly_cost_limit: float
    tier: RateLimitTier

# Default rate limit configurations
RATE_LIMIT_CONFIGS = {
    RateLimitTier.FREE: RateLimitConfig(
        requests_per_minute=10,
        tokens_per_minute=10000,
        concurrent_requests=2,
        daily_cost_limit=5.0,
        monthly_cost_limit=50.0,
        tier=RateLimitTier.FREE
    ),
    RateLimitTier.PREMIUM: RateLimitConfig(
        requests_per_minute=60,
        tokens_per_minute=60000,
        concurrent_requests=10,
        daily_cost_limit=50.0,
        monthly_cost_limit=1000.0,
        tier=RateLimitTier.PREMIUM
    ),
    RateLimitTier.ENTERPRISE: RateLimitConfig(
        requests_per_minute=300,
        tokens_per_minute=300000,
        concurrent_requests=50,
        daily_cost_limit=500.0,
        monthly_cost_limit=10000.0,
        tier=RateLimitTier.ENTERPRISE
    ),
    RateLimitTier.INTERNAL: RateLimitConfig(
        requests_per_minute=500,
        tokens_per_minute=500000,
        concurrent_requests=100,
        daily_cost_limit=1000.0,
        monthly_cost_limit=20000.0,
        tier=RateLimitTier.INTERNAL
    )
}

# Token pricing for different models (input/output per 1K tokens)
MODEL_PRICING = {
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    "text-embedding-3-small": {"input": 0.00002, "output": 0},
    "text-embedding-3-large": {"input": 0.00013, "output": 0}
}

class RateLimitExceeded(Exception):
    """Raised when rate limits are exceeded"""
    def __init__(self, message: str, retry_after: Optional[float] = None):
        self.retry_after = retry_after
        super().__init__(message)

class CostLimitExceeded(Exception):
    """Raised when cost limits are exceeded"""
    pass

class TokenBudgetManager:
    """Manages token budgets and cost tracking"""
    
    def __init__(self):
        self.usage_history: Dict[str, List[TokenUsage]] = {}
        self.daily_costs: Dict[str, Dict[str, float]] = {}  # {date: {user_id: cost}}
        self.monthly_costs: Dict[str, Dict[str, float]] = {}  # {month: {user_id: cost}}
        
    def calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost based on token usage and model pricing"""
        if model not in MODEL_PRICING:
            # Default to GPT-4o pricing for unknown models
            model = "gpt-4o"
            
        pricing = MODEL_PRICING[model]
        input_cost = (prompt_tokens / 1000) * pricing["input"]
        output_cost = (completion_tokens / 1000) * pricing["output"]
        
        return input_cost + output_cost
    
    def record_usage(self, user_id: str, model: str, prompt_tokens: int, completion_tokens: int):
        """Record token usage for a user"""
        cost = self.calculate_cost(model, prompt_tokens, completion_tokens)
        usage = TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            estimated_cost=cost
        )
        
        if user_id not in self.usage_history:
            self.usage_history[user_id] = []
        
        self.usage_history[user_id].append(usage)
        
        # Update daily and monthly costs
        today = datetime.utcnow().strftime("%Y-%m-%d")
        this_month = datetime.utcnow().strftime("%Y-%m")
        
        if today not in self.daily_costs:
            self.daily_costs[today] = {}
        if this_month not in self.monthly_costs:
            self.monthly_costs[this_month] = {}
            
        self.daily_costs[today][user_id] = self.daily_costs[today].get(user_id, 0) + cost
        self.monthly_costs[this_month][user_id] = self.monthly_costs[this_month].get(user_id, 0) + cost
    
    def get_daily_cost(self, user_id: str) -> float:
        """Get user's cost for today"""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        return self.daily_costs.get(today, {}).get(user_id, 0.0)
    
    def get_monthly_cost(self, user_id: str) -> float:
        """Get user's cost for this month"""
        this_month = datetime.utcnow().strftime("%Y-%m")
        return self.monthly_costs.get(this_month, {}).get(user_id, 0.0)
    
    def check_cost_limits(self, user_id: str, tier: RateLimitTier) -> None:
        """Check if user has exceeded cost limits"""
        config = RATE_LIMIT_CONFIGS[tier]
        
        daily_cost = self.get_daily_cost(user_id)
        monthly_cost = self.get_monthly_cost(user_id)
        
        if daily_cost >= config.daily_cost_limit:
            raise CostLimitExceeded(f"Daily cost limit exceeded: ${daily_cost:.2f} >= ${config.daily_cost_limit}")
            
        if monthly_cost >= config.monthly_cost_limit:
            raise CostLimitExceeded(f"Monthly cost limit exceeded: ${monthly_cost:.2f} >= ${config.monthly_cost_limit}")

class RateLimiter:
    """Advanced rate limiter with sliding window and multiple dimensions"""
    
    def __init__(self):
        self.request_timestamps: Dict[str, List[float]] = {}  # {user_id: [timestamps]}
        self.token_usage: Dict[str, List[Dict]] = {}  # {user_id: [{timestamp, tokens}]}
        self.concurrent_requests: Dict[str, int] = {}  # {user_id: count}
        self.budget_manager = TokenBudgetManager()
        
    def _clean_old_records(self, user_id: str, window_minutes: int = 1):
        """Remove records older than the sliding window"""
        cutoff_time = time.time() - (window_minutes * 60)
        
        if user_id in self.request_timestamps:
            self.request_timestamps[user_id] = [
                ts for ts in self.request_timestamps[user_id] if ts > cutoff_time
            ]
        
        if user_id in self.token_usage:
            self.token_usage[user_id] = [
                record for record in self.token_usage[user_id] 
                if record["timestamp"] > cutoff_time
            ]
    
    def _get_user_tier(self, user_id: str, api_key: str) -> RateLimitTier:
        """Determine user's rate limit tier"""
        # In production, this would check user subscription/payment status
        # For now, use environment variables or default to FREE
        default_tier = os.getenv("DEFAULT_RATE_LIMIT_TIER", "free")
        
        # Check if this is an internal API key
        internal_keys = os.getenv("INTERNAL_API_KEYS", "").split(",")
        if api_key in internal_keys:
            return RateLimitTier.INTERNAL
            
        # Check enterprise API keys
        enterprise_keys = os.getenv("ENTERPRISE_API_KEYS", "").split(",")
        if api_key in enterprise_keys:
            return RateLimitTier.ENTERPRISE
        
        # Default tier mapping
        tier_map = {
            "free": RateLimitTier.FREE,
            "premium": RateLimitTier.PREMIUM,
            "enterprise": RateLimitTier.ENTERPRISE,
            "internal": RateLimitTier.INTERNAL
        }
        
        return tier_map.get(default_tier, RateLimitTier.FREE)
    
    async def check_rate_limit(self, user_id: str, api_key: str, estimated_tokens: int = 0) -> None:
        """Check if request is within rate limits"""
        tier = self._get_user_tier(user_id, api_key)
        config = RATE_LIMIT_CONFIGS[tier]
        
        self._clean_old_records(user_id)
        
        # Check concurrent requests
        current_concurrent = self.concurrent_requests.get(user_id, 0)
        if current_concurrent >= config.concurrent_requests:
            raise RateLimitExceeded(
                f"Concurrent request limit exceeded: {current_concurrent} >= {config.concurrent_requests}",
                retry_after=60.0
            )
        
        # Check requests per minute
        if user_id not in self.request_timestamps:
            self.request_timestamps[user_id] = []
        
        requests_in_window = len(self.request_timestamps[user_id])
        if requests_in_window >= config.requests_per_minute:
            oldest_request = min(self.request_timestamps[user_id])
            retry_after = 60.0 - (time.time() - oldest_request)
            raise RateLimitExceeded(
                f"Request rate limit exceeded: {requests_in_window} >= {config.requests_per_minute}",
                retry_after=max(1.0, retry_after)
            )
        
        # Check tokens per minute
        if user_id not in self.token_usage:
            self.token_usage[user_id] = []
        
        tokens_in_window = sum(record["tokens"] for record in self.token_usage[user_id])
        if tokens_in_window + estimated_tokens > config.tokens_per_minute:
            raise RateLimitExceeded(
                f"Token rate limit exceeded: {tokens_in_window + estimated_tokens} > {config.tokens_per_minute}",
                retry_after=60.0
            )
        
        # Check cost limits
        self.budget_manager.check_cost_limits(user_id, tier)
    
    def record_request_start(self, user_id: str):
        """Record the start of a request"""
        current_time = time.time()
        
        if user_id not in self.request_timestamps:
            self.request_timestamps[user_id] = []
        
        self.request_timestamps[user_id].append(current_time)
        self.concurrent_requests[user_id] = self.concurrent_requests.get(user_id, 0) + 1
    
    def record_request_end(self, user_id: str, model: str, prompt_tokens: int, completion_tokens: int):
        """Record the end of a request with token usage"""
        current_time = time.time()
        total_tokens = prompt_tokens + completion_tokens
        
        # Record token usage
        if user_id not in self.token_usage:
            self.token_usage[user_id] = []
        
        self.token_usage[user_id].append({
            "timestamp": current_time,
            "tokens": total_tokens
        })
        
        # Update concurrent request count
        self.concurrent_requests[user_id] = max(0, self.concurrent_requests.get(user_id, 1) - 1)
        
        # Record in budget manager
        self.budget_manager.record_usage(user_id, model, prompt_tokens, completion_tokens)
    
    def get_usage_stats(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive usage statistics for a user"""
        tier = self._get_user_tier(user_id, "")
        config = RATE_LIMIT_CONFIGS[tier]
        
        self._clean_old_records(user_id)
        
        requests_in_window = len(self.request_timestamps.get(user_id, []))
        tokens_in_window = sum(record["tokens"] for record in self.token_usage.get(user_id, []))
        concurrent_requests = self.concurrent_requests.get(user_id, 0)
        
        return {
            "tier": tier.value,
            "limits": asdict(config),
            "current_usage": {
                "requests_per_minute": requests_in_window,
                "tokens_per_minute": tokens_in_window,
                "concurrent_requests": concurrent_requests,
                "daily_cost": self.budget_manager.get_daily_cost(user_id),
                "monthly_cost": self.budget_manager.get_monthly_cost(user_id)
            },
            "utilization": {
                "requests": (requests_in_window / config.requests_per_minute) * 100,
                "tokens": (tokens_in_window / config.tokens_per_minute) * 100,
                "concurrent": (concurrent_requests / config.concurrent_requests) * 100,
                "daily_cost": (self.budget_manager.get_daily_cost(user_id) / config.daily_cost_limit) * 100,
                "monthly_cost": (self.budget_manager.get_monthly_cost(user_id) / config.monthly_cost_limit) * 100
            }
        }

# Global rate limiter instance
global_rate_limiter = RateLimiter()

def rate_limit_decorator(estimated_tokens_func=None):
    """Decorator to apply rate limiting to API calls"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user_id and api_key from context
            user_id = kwargs.get('user_id', 'anonymous')
            api_key = os.getenv("OPENAI_API_KEY", "")
            
            # Estimate tokens if function provided
            estimated_tokens = 0
            if estimated_tokens_func:
                estimated_tokens = estimated_tokens_func(*args, **kwargs)
            
            # Check rate limits
            await global_rate_limiter.check_rate_limit(user_id, api_key, estimated_tokens)
            
            # Record request start
            global_rate_limiter.record_request_start(user_id)
            
            try:
                # Execute the function
                result = await func(*args, **kwargs)
                
                # Extract token usage from result if available
                prompt_tokens = getattr(result, 'prompt_tokens', 0)
                completion_tokens = getattr(result, 'completion_tokens', 0)
                model = kwargs.get('model', 'gpt-4o-mini')
                
                # Record request end
                global_rate_limiter.record_request_end(user_id, model, prompt_tokens, completion_tokens)
                
                return result
                
            except Exception as e:
                # Still decrement concurrent requests on error
                global_rate_limiter.concurrent_requests[user_id] = max(
                    0, global_rate_limiter.concurrent_requests.get(user_id, 1) - 1
                )
                raise
        
        return wrapper
    return decorator

def estimate_tokens_from_messages(messages: List[Dict], model: str = "gpt-4o-mini") -> int:
    """Estimate token count from message content"""
    # Rough estimation: ~4 characters per token
    total_chars = sum(len(str(msg.get("content", ""))) for msg in messages)
    return max(100, total_chars // 4)  # Minimum 100 tokens

async def check_and_enforce_budget(user_id: str, estimated_cost: float) -> None:
    """Check and enforce budget constraints before making expensive calls"""
    tier = global_rate_limiter._get_user_tier(user_id, "")
    config = RATE_LIMIT_CONFIGS[tier]
    
    current_daily = global_rate_limiter.budget_manager.get_daily_cost(user_id)
    current_monthly = global_rate_limiter.budget_manager.get_monthly_cost(user_id)
    
    if current_daily + estimated_cost > config.daily_cost_limit:
        raise CostLimitExceeded(f"Request would exceed daily budget: ${current_daily + estimated_cost:.2f} > ${config.daily_cost_limit}")
        
    if current_monthly + estimated_cost > config.monthly_cost_limit:
        raise CostLimitExceeded(f"Request would exceed monthly budget: ${current_monthly + estimated_cost:.2f} > ${config.monthly_cost_limit}")