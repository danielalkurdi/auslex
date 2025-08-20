# OpenAI API Integration - Enterprise Hardening Guide

## Overview

This guide covers the enterprise-grade hardening of OpenAI API integrations implemented in the AusLex legal research platform. The system includes comprehensive rate limiting, cost controls, streaming responses, circuit breakers, security hardening, and production monitoring.

## Architecture Components

### 1. Rate Limiting & Cost Control (`api/rate_limiter.py`)

**Features:**
- Multi-tier rate limiting (FREE, PREMIUM, ENTERPRISE, INTERNAL)
- Token-based and request-based limiting
- Daily and monthly cost budgets
- Real-time usage tracking
- Automatic cost calculation per model

**Configuration:**
```python
# Environment Variables
DEFAULT_RATE_LIMIT_TIER=premium
INTERNAL_API_KEYS=key1,key2,key3
ENTERPRISE_API_KEYS=ent_key1,ent_key2

# Tier Limits
FREE: 10 req/min, 10K tokens/min, $5/day, $50/month
PREMIUM: 60 req/min, 60K tokens/min, $50/day, $1000/month
ENTERPRISE: 300 req/min, 300K tokens/min, $500/day, $10K/month
INTERNAL: 500 req/min, 500K tokens/min, $1000/day, $20K/month
```

**Usage:**
```python
from api.rate_limiter import global_rate_limiter, rate_limit_decorator

@rate_limit_decorator(estimated_tokens_func=lambda msg: len(msg.split()) * 1.3)
async def api_call(user_id: str, messages: List[Dict]):
    # Your API call here
    pass
```

### 2. Circuit Breaker & Error Handling (`api/circuit_breaker.py`)

**Features:**
- Automatic failure detection and recovery
- Exponential backoff with jitter
- Model-specific fallback chains
- Response caching for resilience
- Comprehensive error classification

**Configuration:**
```python
# Circuit Breaker Settings
OPENAI_MAX_RETRIES=3
OPENAI_BASE_RETRY_DELAY=1.0
OPENAI_MAX_RETRY_DELAY=60.0

# Circuit breaker thresholds
failure_threshold=5  # failures before opening
timeout_duration=60.0  # seconds to wait
error_rate_threshold=0.5  # 50% error rate threshold
```

**Usage:**
```python
from api.circuit_breaker import resilient_openai_call

@resilient_openai_call("chat_completions")
async def make_api_call():
    # Automatically wrapped with circuit breaker protection
    return openai_client.chat.completions.create(...)
```

### 3. Streaming Responses (`api/streaming_handler.py`)

**Features:**
- Server-Sent Events (SSE) streaming
- Real-time progress tracking
- Component-level status updates
- Connection health monitoring
- Graceful error handling

**Usage:**
```python
from api.streaming_handler import streaming_manager, streaming_engine

@app.post("/research/streaming")
async def stream_research(request):
    stream_generator = streaming_engine.stream_comprehensive_research(context)
    return streaming_manager.create_streaming_response(stream_generator)
```

### 4. Token Optimization (`api/token_optimizer.py`)

**Features:**
- Intelligent prompt compression
- Response caching with TTL
- Token usage analytics
- Model-specific optimization
- Function call optimization

**Configuration:**
```python
# Optimization strategies
AGGRESSIVE: Maximum savings, slight quality reduction
BALANCED: Balance quality and efficiency
CONSERVATIVE: Prioritize quality, minimal optimization
```

**Usage:**
```python
from api.token_optimizer import token_optimized, OptimizationStrategy

@token_optimized(OptimizationStrategy.BALANCED)
async def optimized_api_call():
    # Automatically optimized prompts and cached responses
    pass
```

### 5. Security Hardening (`api/security_manager.py`)

**Features:**
- Prompt injection detection
- Input sanitization
- Response filtering
- IP whitelisting
- Request signing
- PII detection and masking

**Configuration:**
```python
# Environment Variables
IP_WHITELIST=192.168.1.0/24,10.0.0.0/8
HMAC_SECRET_KEY=your-secret-key
ENABLE_REQUEST_SIGNING=true
ENABLE_PROMPT_SCANNING=true
MAX_REQUEST_SIZE_MB=10
```

**Usage:**
```python
from api.security_manager import secure_endpoint, SecurityLevel

@secure_endpoint(SecurityLevel.HIGH)
async def protected_endpoint():
    # Automatically secured with input validation and output filtering
    pass
```

### 6. Production Configuration (`api/production_config.py`)

**Features:**
- Environment-specific configs
- Health checks
- Metrics collection
- Database configuration
- Monitoring setup

## Production Deployment

### Environment Variables

#### Required
```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-your-api-key
OPENAI_ORGANIZATION=org-your-org-id
OPENAI_PROJECT=proj-your-project-id

# Database (Neon Production)
NEON_PROD_HOST=your-neon-host
NEON_PROD_DATABASE=auslex_prod
NEON_PROD_USERNAME=app_writer
NEON_PROD_PASSWORD=your-secure-password

# Security
JWT_SECRET_KEY=your-jwt-secret
MASTER_ENCRYPTION_KEY=your-encryption-key
HMAC_SECRET_KEY=your-hmac-key

# Deployment
DEPLOYMENT_ENVIRONMENT=production
```

#### Optional
```bash
# Rate Limiting
DEFAULT_RATE_LIMIT_TIER=premium
OPENAI_MAX_REQUESTS_PER_MINUTE=60
OPENAI_MAX_TOKENS_PER_MINUTE=60000
OPENAI_DAILY_COST_LIMIT=100.0
OPENAI_MONTHLY_COST_LIMIT=1000.0

# Performance
WORKER_PROCESSES=4
WORKER_CONNECTIONS=1000
ENABLE_RESPONSE_COMPRESSION=true
ENABLE_HTTP2=true

# Monitoring
LOG_LEVEL=INFO
ENABLE_METRICS=true
SENTRY_DSN=your-sentry-dsn
DATADOG_API_KEY=your-datadog-key

# Security
CORS_ORIGINS=https://auslex.com,https://app.auslex.com
ENABLE_IP_WHITELIST=false
TRUSTED_PROXIES=10.0.0.0/8
```

### Docker Configuration

```dockerfile
# Production Dockerfile
FROM python:3.9-slim

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY api/ ./api/
COPY config/ ./config/

# Set production environment
ENV DEPLOYMENT_ENVIRONMENT=production
ENV PYTHONPATH=/app/api

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "api.hardened_endpoints:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Vercel Configuration

```json
{
  "version": 2,
  "functions": {
    "api/hardened_endpoints.py": {
      "runtime": "python3.9",
      "maxDuration": 30
    }
  },
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "/api/hardened_endpoints.py"
    }
  ],
  "env": {
    "DEPLOYMENT_ENVIRONMENT": "production",
    "PYTHONPATH": "./api"
  }
}
```

### Nginx Configuration

```nginx
upstream auslex_backend {
    server 127.0.0.1:8000 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

server {
    listen 443 ssl http2;
    server_name api.auslex.com;
    
    # SSL configuration
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    
    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
    
    # Proxy configuration
    location /api/ {
        proxy_pass http://auslex_backend;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 5s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffering for streaming
        proxy_buffering off;
        proxy_cache_bypass 1;
    }
    
    # Health check
    location /health {
        proxy_pass http://auslex_backend;
        access_log off;
    }
    
    # Metrics (restrict access)
    location /metrics {
        allow 10.0.0.0/8;
        deny all;
        proxy_pass http://auslex_backend;
    }
}
```

## Monitoring & Observability

### Health Checks

```bash
# Basic health check
curl https://api.auslex.com/health

# Detailed health check
curl https://api.auslex.com/health/detailed

# Metrics endpoint
curl https://api.auslex.com/metrics
```

### Key Metrics to Monitor

1. **Request Metrics**
   - `requests_total` - Total requests by endpoint/status
   - `request_duration_seconds` - Request latency histogram
   - `rate_limit_exceeded` - Rate limit violations

2. **OpenAI API Metrics**
   - `openai_requests_total` - API requests by model
   - `openai_tokens_used` - Token consumption
   - `openai_cost_dollars` - API costs
   - `openai_errors` - API errors by type

3. **Circuit Breaker Metrics**
   - `circuit_breaker_state` - Circuit breaker states
   - `circuit_breaker_failures` - Failure counts
   - `fallback_responses` - Fallback usage

4. **Security Metrics**
   - `security_violations` - Security event counts
   - `prompt_injections_detected` - Injection attempts
   - `requests_blocked` - Blocked requests

### Alerting Rules

```yaml
# Prometheus alerting rules
groups:
  - name: auslex-api
    rules:
      - alert: HighErrorRate
        expr: rate(requests_total{status=~"5.."}[5m]) > 0.1
        for: 2m
        annotations:
          summary: "High error rate detected"
      
      - alert: OpenAICostHigh
        expr: openai_daily_cost > 80
        annotations:
          summary: "OpenAI daily cost exceeding budget"
      
      - alert: CircuitBreakerOpen
        expr: circuit_breaker_state{state="open"} == 1
        for: 1m
        annotations:
          summary: "Circuit breaker is open"
```

## Cost Management Strategies

### 1. Multi-Tier Architecture
- Use `gpt-4o-mini` for standard queries
- Reserve `gpt-4o` for complex legal analysis
- Implement intelligent model selection

### 2. Prompt Optimization
- Automatic prompt compression
- Remove redundant phrases
- Use shorter system prompts

### 3. Caching Strategy
- Cache responses for 1 hour
- Cache based on normalized input
- Implement cache warming for common queries

### 4. Budget Controls
- Set daily/monthly limits per user tier
- Implement cost alerts at 80% budget
- Automatic throttling at budget limits

### 5. Usage Analytics
- Track per-user costs
- Identify high-cost queries
- Optimize expensive operations

## Security Best Practices

### 1. API Key Management
- Store encrypted API keys
- Rotate keys every 30 days
- Use separate keys for different environments

### 2. Input Validation
- Scan for prompt injection attempts
- Sanitize user inputs
- Validate request sizes

### 3. Output Filtering
- Filter sensitive information from responses
- Block harmful content patterns
- Log security events

### 4. Network Security
- Use HTTPS/TLS 1.2+ only
- Implement IP whitelisting if needed
- Set up Web Application Firewall (WAF)

### 5. Monitoring
- Log all API calls
- Monitor for unusual patterns
- Set up security alerts

## Troubleshooting

### Common Issues

1. **Rate Limit Exceeded**
   ```bash
   # Check user's current usage
   curl -H "Authorization: Bearer $TOKEN" \
     "https://api.auslex.com/api/admin/usage/analytics?user_id=user123"
   ```

2. **Circuit Breaker Open**
   ```bash
   # Check circuit breaker status
   curl "https://api.auslex.com/metrics" | jq '.circuit_breaker_status'
   
   # Reset circuit breaker
   curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
     "https://api.auslex.com/api/admin/circuit-breaker/reset" \
     -d '{"endpoint": "chat_completions"}'
   ```

3. **High API Costs**
   ```bash
   # Check cost breakdown
   curl -H "Authorization: Bearer $TOKEN" \
     "https://api.auslex.com/api/admin/usage/analytics?days=1"
   ```

4. **Security Violations**
   ```bash
   # Check security metrics
   curl -H "Authorization: Bearer $ADMIN_TOKEN" \
     "https://api.auslex.com/api/admin/security/metrics"
   ```

### Performance Optimization

1. **Enable Caching**
   - Set `OPENAI_ENABLE_CACHING=true`
   - Tune `OPENAI_CACHE_TTL` based on use case

2. **Optimize Prompts**
   - Enable `OPENAI_ENABLE_PROMPT_OPTIMIZATION=true`
   - Use `OptimizationStrategy.BALANCED`

3. **Use Streaming**
   - Enable streaming for long operations
   - Use `/api/research/streaming` endpoint

4. **Configure Workers**
   - Set `WORKER_PROCESSES` based on CPU cores
   - Tune `WORKER_CONNECTIONS` for concurrency

## Migration Guide

### From Basic Integration

1. **Install Dependencies**
   ```bash
   pip install tiktoken cryptography psutil
   ```

2. **Update Environment Variables**
   ```bash
   # Add new required variables
   DEPLOYMENT_ENVIRONMENT=production
   JWT_SECRET_KEY=your-secret
   MASTER_ENCRYPTION_KEY=your-key
   ```

3. **Replace Endpoint Usage**
   ```python
   # Old
   from api.index import app
   
   # New
   from api.hardened_endpoints import app
   ```

4. **Update Client Code**
   ```javascript
   // Add error handling for rate limits
   fetch('/api/chat/hardened', {
     method: 'POST',
     body: JSON.stringify(request)
   }).catch(err => {
     if (err.status === 429) {
       // Handle rate limit
     }
   });
   ```

This enterprise-grade integration provides comprehensive protection, monitoring, and optimization for OpenAI API usage while maintaining high performance and reliability for your legal research platform.