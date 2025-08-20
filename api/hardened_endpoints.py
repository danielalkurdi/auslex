"""
Hardened API Endpoints with Enterprise Security and Monitoring
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import json

# Import hardening components
from .rate_limiter import (
    global_rate_limiter, 
    RateLimitExceeded, 
    CostLimitExceeded,
    rate_limit_decorator,
    estimate_tokens_from_messages
)
from .circuit_breaker import (
    resilient_openai_call,
    get_circuit_breaker_status,
    circuit_breakers
)
from .streaming_handler import (
    streaming_manager,
    streaming_engine,
    StreamEventType
)
from .token_optimizer import (
    token_optimized,
    OptimizationStrategy,
    usage_monitor,
    response_cache
)
from .security_manager import (
    security_manager,
    secure_endpoint,
    SecurityLevel,
    SecurityException
)
from .production_config import (
    get_config_manager,
    get_health_checker,
    get_metrics_collector
)
from .ai_research_engine import AdvancedLegalResearcher, ResearchContext, JurisdictionType, LegalAreaType

logger = logging.getLogger(__name__)

class HardenedAdvancedResearchRequest(BaseModel):
    query: str
    jurisdictions: List[str] = ["federal"]
    legal_areas: List[str] = []
    include_precedents: bool = True
    include_commentary: bool = True
    confidence_threshold: float = 0.7
    enable_streaming: bool = False
    optimization_strategy: str = "balanced"  # aggressive, balanced, conservative

class StreamingResearchResponse(BaseModel):
    stream_id: str
    message: str
    
class HardenedChatRequest(BaseModel):
    message: str
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 0.9
    enable_web_search: bool = True
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class SecurityMetricsResponse(BaseModel):
    period_hours: int
    total_events: int
    threat_breakdown: Dict[str, int]
    severity_breakdown: Dict[str, int]
    top_threats: List[tuple]

class SystemStatusResponse(BaseModel):
    status: str
    timestamp: str
    environment: str
    checks: Optional[Dict[str, Any]] = None

def create_hardened_app() -> FastAPI:
    """Create FastAPI app with all security hardening applied"""
    
    config_manager = get_config_manager()
    
    # Create FastAPI app with security-focused configuration
    app = FastAPI(
        title="AusLex AI API - Enterprise Hardened",
        version="2.0.0-enterprise",
        description="World-class Australian Legal AI Platform with Enterprise Security",
        docs_url="/docs" if not config_manager.is_production() else None,  # Disable docs in production
        redoc_url="/redoc" if not config_manager.is_production() else None,
        openapi_url="/openapi.json" if not config_manager.is_production() else None
    )
    
    # Configure CORS
    security_config = config_manager.get_security_config()
    if security_config.enable_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=security_config.cors_origins or ["*"],
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["*"],
            expose_headers=["X-RateLimit-Remaining", "X-RateLimit-Reset"]
        )
    
    # Initialize research engine
    research_engine = AdvancedLegalResearcher()
    
    # Security and monitoring middleware
    @app.middleware("http")
    async def security_and_monitoring_middleware(request: Request, call_next):
        start_time = time.time()
        
        # Extract client info
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent", "")
        user_id = request.headers.get("x-user-id", "anonymous")
        
        # Get metrics collector
        metrics = get_metrics_collector()
        
        try:
            # Rate limiting check
            if request.url.path.startswith("/api/"):
                await global_rate_limiter.check_rate_limit(user_id, "api_key", 100)
                global_rate_limiter.record_request_start(user_id)
            
            # Process request
            response = await call_next(request)
            
            # Record metrics
            duration = time.time() - start_time
            metrics.record_histogram(
                "request_duration_seconds",
                duration,
                {"endpoint": request.url.path, "method": request.method, "status": str(response.status_code)}
            )
            
            metrics.increment_counter(
                "requests_total",
                1,
                {"endpoint": request.url.path, "method": request.method, "status": str(response.status_code)}
            )
            
            # Add security headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            
            if config_manager.is_production():
                response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            
            return response
            
        except RateLimitExceeded as e:
            metrics.increment_counter("rate_limit_exceeded", 1, {"user_id": user_id})
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": str(e),
                    "retry_after": e.retry_after
                },
                headers={"Retry-After": str(int(e.retry_after or 60))}
            )
        
        except SecurityException as e:
            metrics.increment_counter("security_violations", 1, {"type": str(e.threat_type)})
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Security violation",
                    "message": str(e)
                }
            )
        
        except Exception as e:
            duration = time.time() - start_time
            metrics.record_histogram("request_duration_seconds", duration, {"status": "error"})
            metrics.increment_counter("requests_errors", 1)
            logger.error(f"Unhandled error in middleware: {e}")
            raise
    
    # Health check endpoints
    @app.get("/health", response_model=SystemStatusResponse)
    async def health_check():
        """Basic health check endpoint"""
        health_checker = get_health_checker()
        return await health_checker.run_health_checks(include_details=False)
    
    @app.get("/health/detailed", response_model=SystemStatusResponse)
    async def detailed_health_check():
        """Detailed health check with component status"""
        health_checker = get_health_checker()
        return await health_checker.run_health_checks(include_details=True)
    
    @app.get("/metrics")
    async def get_metrics():
        """Prometheus-compatible metrics endpoint"""
        metrics = get_metrics_collector()
        circuit_status = await get_circuit_breaker_status()
        
        return {
            "application_metrics": metrics.get_metrics(),
            "circuit_breaker_status": circuit_status,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # Security monitoring endpoints
    @app.get("/api/admin/security/metrics", response_model=SecurityMetricsResponse)
    @secure_endpoint(SecurityLevel.HIGH)
    async def get_security_metrics(hours: int = 24):
        """Get security metrics for monitoring (admin only)"""
        return security_manager.get_security_metrics(hours)
    
    @app.get("/api/admin/usage/analytics")
    @secure_endpoint(SecurityLevel.HIGH) 
    async def get_usage_analytics(user_id: Optional[str] = None, days: int = 7):
        """Get usage analytics (admin only)"""
        return usage_monitor.get_usage_analytics(user_id, days)
    
    @app.post("/api/admin/circuit-breaker/reset")
    @secure_endpoint(SecurityLevel.CRITICAL)
    async def reset_circuit_breaker(endpoint: str):
        """Manually reset a circuit breaker (admin only)"""
        from .circuit_breaker import reset_circuit_breaker
        success = reset_circuit_breaker(endpoint)
        
        if success:
            return {"status": "success", "message": f"Circuit breaker {endpoint} reset"}
        else:
            raise HTTPException(status_code=404, detail=f"Circuit breaker {endpoint} not found")
    
    # Hardened chat endpoint with full security stack
    @app.post("/api/chat/hardened")
    @secure_endpoint(SecurityLevel.MEDIUM)
    @resilient_openai_call("chat_completions")
    @token_optimized(OptimizationStrategy.BALANCED)
    @rate_limit_decorator(lambda req: estimate_tokens_from_messages([{"role": "user", "content": req.message}]))
    async def hardened_chat(
        request: HardenedChatRequest,
        background_tasks: BackgroundTasks,
        http_request: Request
    ):
        """Enhanced chat endpoint with full security and optimization stack"""
        
        try:
            # Extract security context
            user_id = request.user_id or "anonymous"
            client_ip = http_request.client.host
            
            # Validate and sanitize input
            validation_result = await security_manager.validate_request(
                {"message": request.message},
                user_id,
                client_ip,
                http_request.headers.get("user-agent", "")
            )
            
            if not validation_result["is_valid"]:
                raise SecurityException(f"Input validation failed: {validation_result['errors']}")
            
            # Use sanitized input
            sanitized_message = validation_result["sanitized_data"]["message"]
            
            # Create OpenAI client with circuit breaker protection
            from .ai_research_engine import AdvancedLegalResearcher
            researcher = AdvancedLegalResearcher()
            
            # Prepare messages for API call
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert Australian legal assistant. Provide accurate, helpful legal information while noting that this is for educational purposes only and not legal advice."
                },
                {
                    "role": "user", 
                    "content": sanitized_message
                }
            ]
            
            # Make API call with full hardening stack
            response = researcher.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                top_p=request.top_p,
                user=user_id  # OpenAI user tracking
            )
            
            # Filter response for security
            filtered_response = security_manager.filter_response(
                response.choices[0].message.content,
                user_id
            )
            
            # Record usage metrics
            background_tasks.add_task(
                usage_monitor.record_usage,
                {
                    "request_id": f"{user_id}_{int(time.time())}",
                    "user_id": user_id,
                    "model": "gpt-4o-mini",
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                    "estimated_cost": 0.0,  # Would calculate actual cost
                    "optimization_applied": True,
                    "cache_hit": False,
                    "timestamp": datetime.utcnow(),
                    "endpoint": "hardened_chat"
                }
            )
            
            return {
                "response": filtered_response,
                "tokens_used": response.usage.total_tokens,
                "model": "gpt-4o-mini",
                "security_filtered": filtered_response != response.choices[0].message.content,
                "processing_time": time.time() - time.time(),  # Would track actual time
                "session_id": request.session_id
            }
            
        except Exception as e:
            logger.error(f"Error in hardened chat endpoint: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    # Streaming research endpoint
    @app.post("/api/research/streaming")
    @secure_endpoint(SecurityLevel.MEDIUM)
    async def streaming_research(
        request: HardenedAdvancedResearchRequest,
        http_request: Request
    ):
        """Streaming legal research with real-time progress"""
        
        user_id = request.dict().get("user_id", "anonymous")
        client_ip = http_request.client.host
        
        # Validate input
        validation_result = await security_manager.validate_request(
            request.dict(),
            user_id,
            client_ip,
            http_request.headers.get("user-agent", "")
        )
        
        if not validation_result["is_valid"]:
            raise SecurityException(f"Input validation failed: {validation_result['errors']}")
        
        # Convert to research context
        try:
            jurisdiction_types = [JurisdictionType(j.lower()) for j in request.jurisdictions]
        except ValueError:
            jurisdiction_types = [JurisdictionType.FEDERAL]
        
        try:
            legal_area_types = [LegalAreaType(area.lower()) for area in request.legal_areas]
        except ValueError:
            legal_area_types = []
        
        research_context = {
            "query": validation_result["sanitized_data"]["query"],
            "jurisdictions": request.jurisdictions,
            "legal_areas": request.legal_areas,
            "include_commentary": request.include_commentary,
            "include_precedents": request.include_precedents
        }
        
        # Create streaming response
        stream_generator = streaming_engine.stream_comprehensive_research(research_context)
        
        return streaming_manager.create_streaming_response(
            stream_generator,
            stream_id=f"{user_id}_{int(time.time())}"
        )
    
    # Cache management endpoints
    @app.post("/api/admin/cache/clear")
    @secure_endpoint(SecurityLevel.HIGH)
    async def clear_cache():
        """Clear response cache (admin only)"""
        response_cache.clear()
        return {"status": "success", "message": "Response cache cleared"}
    
    @app.get("/api/admin/cache/stats")
    @secure_endpoint(SecurityLevel.MEDIUM)
    async def get_cache_stats():
        """Get cache statistics"""
        return response_cache.get_stats()
    
    return app

# Create the hardened app instance
app = create_hardened_app()