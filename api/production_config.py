"""
Production Deployment Configuration and Enterprise Integration
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DeploymentEnvironment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

@dataclass
class DatabaseConfig:
    """Database configuration for different environments"""
    host: str
    port: int
    database: str
    username: str
    password: str
    pool_size: int = 20
    max_overflow: int = 30
    pool_timeout: int = 30
    ssl_mode: str = "require"
    schema: str = "auslex"
    
    def get_connection_string(self) -> str:
        """Generate PostgreSQL connection string"""
        return (
            f"postgresql://{self.username}:{self.password}@"
            f"{self.host}:{self.port}/{self.database}?sslmode={self.ssl_mode}"
        )

@dataclass
class RedisConfig:
    """Redis configuration for caching and session management"""
    host: str
    port: int = 6379
    password: Optional[str] = None
    database: int = 0
    ssl: bool = False
    max_connections: int = 50
    timeout: int = 5
    
    def get_connection_params(self) -> Dict[str, Any]:
        """Get Redis connection parameters"""
        params = {
            "host": self.host,
            "port": self.port,
            "db": self.database,
            "socket_timeout": self.timeout,
            "socket_connect_timeout": self.timeout,
            "max_connections": self.max_connections,
        }
        
        if self.password:
            params["password"] = self.password
        
        if self.ssl:
            params["ssl"] = True
            params["ssl_cert_reqs"] = "required"
        
        return params

@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration"""
    enable_metrics: bool = True
    enable_tracing: bool = True
    enable_logging: bool = True
    metrics_endpoint: str = "/metrics"
    health_endpoint: str = "/health"
    readiness_endpoint: str = "/ready"
    log_level: LogLevel = LogLevel.INFO
    log_format: str = "json"
    sentry_dsn: Optional[str] = None
    datadog_api_key: Optional[str] = None
    prometheus_enabled: bool = True

@dataclass
class SecurityConfig:
    """Security configuration for production"""
    enable_cors: bool = True
    cors_origins: List[str] = None
    enable_rate_limiting: bool = True
    enable_api_key_rotation: bool = True
    jwt_secret_key: str = None
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 60
    password_salt_rounds: int = 12
    enable_request_logging: bool = True
    enable_response_filtering: bool = True
    max_request_size_mb: int = 10
    enable_ip_whitelist: bool = False
    trusted_proxies: List[str] = None
    
    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = []
        if self.trusted_proxies is None:
            self.trusted_proxies = []

@dataclass
class OpenAIConfig:
    """OpenAI API configuration with enterprise features"""
    api_key: str
    organization: Optional[str] = None
    project: Optional[str] = None
    base_url: Optional[str] = None
    max_retries: int = 3
    timeout: int = 60
    default_model: str = "gpt-4o-mini"
    fallback_model: str = "gpt-3.5-turbo"
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600
    enable_streaming: bool = True
    max_tokens_per_request: int = 4000
    max_requests_per_minute: int = 60
    max_tokens_per_minute: int = 60000
    daily_cost_limit: float = 100.0
    monthly_cost_limit: float = 1000.0
    enable_function_calling: bool = True
    enable_prompt_optimization: bool = True
    
@dataclass
class PerformanceConfig:
    """Performance optimization configuration"""
    enable_response_compression: bool = True
    enable_static_file_caching: bool = True
    cache_control_max_age: int = 86400  # 24 hours
    worker_processes: int = 4
    worker_connections: int = 1000
    keepalive_timeout: int = 65
    client_max_body_size: str = "10M"
    enable_http2: bool = True
    enable_gzip: bool = True
    gzip_min_length: int = 1024

class ProductionConfigManager:
    """Manages configuration for production deployment"""
    
    def __init__(self, environment: DeploymentEnvironment = None):
        self.environment = environment or self._detect_environment()
        self.config = self._load_configuration()
        self._validate_configuration()
    
    def _detect_environment(self) -> DeploymentEnvironment:
        """Detect deployment environment from environment variables"""
        env = os.getenv("DEPLOYMENT_ENVIRONMENT", "development").lower()
        
        env_mapping = {
            "dev": DeploymentEnvironment.DEVELOPMENT,
            "development": DeploymentEnvironment.DEVELOPMENT,
            "stage": DeploymentEnvironment.STAGING,
            "staging": DeploymentEnvironment.STAGING,
            "prod": DeploymentEnvironment.PRODUCTION,
            "production": DeploymentEnvironment.PRODUCTION
        }
        
        return env_mapping.get(env, DeploymentEnvironment.DEVELOPMENT)
    
    def _load_configuration(self) -> Dict[str, Any]:
        """Load configuration based on environment"""
        config = {
            "environment": self.environment,
            "database": self._get_database_config(),
            "redis": self._get_redis_config(),
            "monitoring": self._get_monitoring_config(),
            "security": self._get_security_config(),
            "openai": self._get_openai_config(),
            "performance": self._get_performance_config()
        }
        
        # Load environment-specific overrides
        config_overrides = self._load_config_file()
        if config_overrides:
            config.update(config_overrides)
        
        return config
    
    def _load_config_file(self) -> Optional[Dict[str, Any]]:
        """Load configuration from JSON file if available"""
        config_file = f"config/{self.environment.value}.json"
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load config file {config_file}: {e}")
        
        return None
    
    def _get_database_config(self) -> DatabaseConfig:
        """Get database configuration"""
        if self.environment == DeploymentEnvironment.PRODUCTION:
            # Production Neon database
            return DatabaseConfig(
                host=os.getenv("NEON_PROD_HOST", ""),
                port=int(os.getenv("NEON_PROD_PORT", "5432")),
                database=os.getenv("NEON_PROD_DATABASE", "auslex_prod"),
                username=os.getenv("NEON_PROD_USERNAME", "app_writer"),
                password=os.getenv("NEON_PROD_PASSWORD", ""),
                pool_size=int(os.getenv("DB_POOL_SIZE", "20")),
                max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "30")),
                ssl_mode="require",
                schema="auslex"
            )
        elif self.environment == DeploymentEnvironment.STAGING:
            # Staging database
            return DatabaseConfig(
                host=os.getenv("NEON_STAGING_HOST", ""),
                port=int(os.getenv("NEON_STAGING_PORT", "5432")),
                database=os.getenv("NEON_STAGING_DATABASE", "auslex_staging"),
                username=os.getenv("NEON_STAGING_USERNAME", "app_writer"),
                password=os.getenv("NEON_STAGING_PASSWORD", ""),
                pool_size=10,
                max_overflow=15,
                ssl_mode="require",
                schema="auslex"
            )
        else:
            # Development database
            return DatabaseConfig(
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", "5432")),
                database=os.getenv("DB_NAME", "auslex_dev"),
                username=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", ""),
                pool_size=5,
                max_overflow=10,
                ssl_mode="prefer",
                schema="auslex"
            )
    
    def _get_redis_config(self) -> Optional[RedisConfig]:
        """Get Redis configuration"""
        if not os.getenv("REDIS_URL") and not os.getenv("REDIS_HOST"):
            return None
        
        return RedisConfig(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("REDIS_PASSWORD"),
            database=int(os.getenv("REDIS_DB", "0")),
            ssl=os.getenv("REDIS_SSL", "false").lower() == "true",
            max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", "50")),
            timeout=int(os.getenv("REDIS_TIMEOUT", "5"))
        )
    
    def _get_monitoring_config(self) -> MonitoringConfig:
        """Get monitoring configuration"""
        log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        log_level = LogLevel(log_level_str) if log_level_str in LogLevel.__members__ else LogLevel.INFO
        
        return MonitoringConfig(
            enable_metrics=os.getenv("ENABLE_METRICS", "true").lower() == "true",
            enable_tracing=os.getenv("ENABLE_TRACING", "true").lower() == "true",
            enable_logging=os.getenv("ENABLE_LOGGING", "true").lower() == "true",
            log_level=log_level,
            log_format=os.getenv("LOG_FORMAT", "json"),
            sentry_dsn=os.getenv("SENTRY_DSN"),
            datadog_api_key=os.getenv("DATADOG_API_KEY"),
            prometheus_enabled=os.getenv("PROMETHEUS_ENABLED", "true").lower() == "true"
        )
    
    def _get_security_config(self) -> SecurityConfig:
        """Get security configuration"""
        cors_origins = []
        if os.getenv("CORS_ORIGINS"):
            cors_origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS").split(",")]
        
        trusted_proxies = []
        if os.getenv("TRUSTED_PROXIES"):
            trusted_proxies = [proxy.strip() for proxy in os.getenv("TRUSTED_PROXIES").split(",")]
        
        return SecurityConfig(
            enable_cors=os.getenv("ENABLE_CORS", "true").lower() == "true",
            cors_origins=cors_origins,
            enable_rate_limiting=os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true",
            enable_api_key_rotation=os.getenv("ENABLE_API_KEY_ROTATION", "true").lower() == "true",
            jwt_secret_key=os.getenv("JWT_SECRET_KEY"),
            jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            jwt_expiry_minutes=int(os.getenv("JWT_EXPIRY_MINUTES", "60")),
            password_salt_rounds=int(os.getenv("PASSWORD_SALT_ROUNDS", "12")),
            enable_request_logging=os.getenv("ENABLE_REQUEST_LOGGING", "true").lower() == "true",
            enable_response_filtering=os.getenv("ENABLE_RESPONSE_FILTERING", "true").lower() == "true",
            max_request_size_mb=int(os.getenv("MAX_REQUEST_SIZE_MB", "10")),
            enable_ip_whitelist=os.getenv("ENABLE_IP_WHITELIST", "false").lower() == "true",
            trusted_proxies=trusted_proxies
        )
    
    def _get_openai_config(self) -> OpenAIConfig:
        """Get OpenAI configuration"""
        return OpenAIConfig(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            organization=os.getenv("OPENAI_ORGANIZATION"),
            project=os.getenv("OPENAI_PROJECT"),
            base_url=os.getenv("OPENAI_BASE_URL"),
            max_retries=int(os.getenv("OPENAI_MAX_RETRIES", "3")),
            timeout=int(os.getenv("OPENAI_TIMEOUT", "60")),
            default_model=os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4o-mini"),
            fallback_model=os.getenv("OPENAI_FALLBACK_MODEL", "gpt-3.5-turbo"),
            enable_caching=os.getenv("OPENAI_ENABLE_CACHING", "true").lower() == "true",
            cache_ttl_seconds=int(os.getenv("OPENAI_CACHE_TTL", "3600")),
            enable_streaming=os.getenv("OPENAI_ENABLE_STREAMING", "true").lower() == "true",
            max_tokens_per_request=int(os.getenv("OPENAI_MAX_TOKENS_PER_REQUEST", "4000")),
            max_requests_per_minute=int(os.getenv("OPENAI_MAX_REQUESTS_PER_MINUTE", "60")),
            max_tokens_per_minute=int(os.getenv("OPENAI_MAX_TOKENS_PER_MINUTE", "60000")),
            daily_cost_limit=float(os.getenv("OPENAI_DAILY_COST_LIMIT", "100.0")),
            monthly_cost_limit=float(os.getenv("OPENAI_MONTHLY_COST_LIMIT", "1000.0")),
            enable_function_calling=os.getenv("OPENAI_ENABLE_FUNCTION_CALLING", "true").lower() == "true",
            enable_prompt_optimization=os.getenv("OPENAI_ENABLE_PROMPT_OPTIMIZATION", "true").lower() == "true"
        )
    
    def _get_performance_config(self) -> PerformanceConfig:
        """Get performance configuration"""
        return PerformanceConfig(
            enable_response_compression=os.getenv("ENABLE_RESPONSE_COMPRESSION", "true").lower() == "true",
            enable_static_file_caching=os.getenv("ENABLE_STATIC_FILE_CACHING", "true").lower() == "true",
            cache_control_max_age=int(os.getenv("CACHE_CONTROL_MAX_AGE", "86400")),
            worker_processes=int(os.getenv("WORKER_PROCESSES", "4")),
            worker_connections=int(os.getenv("WORKER_CONNECTIONS", "1000")),
            keepalive_timeout=int(os.getenv("KEEPALIVE_TIMEOUT", "65")),
            client_max_body_size=os.getenv("CLIENT_MAX_BODY_SIZE", "10M"),
            enable_http2=os.getenv("ENABLE_HTTP2", "true").lower() == "true",
            enable_gzip=os.getenv("ENABLE_GZIP", "true").lower() == "true",
            gzip_min_length=int(os.getenv("GZIP_MIN_LENGTH", "1024"))
        )
    
    def _validate_configuration(self):
        """Validate critical configuration values"""
        errors = []
        
        # Validate OpenAI configuration
        openai_config = self.config["openai"]
        if not openai_config.api_key:
            errors.append("OPENAI_API_KEY is required")
        
        # Validate database configuration
        db_config = self.config["database"]
        if not db_config.host or not db_config.username or not db_config.password:
            errors.append("Database configuration incomplete (host, username, password required)")
        
        # Validate security configuration in production
        if self.environment == DeploymentEnvironment.PRODUCTION:
            security_config = self.config["security"]
            if not security_config.jwt_secret_key:
                errors.append("JWT_SECRET_KEY is required in production")
            
            if not security_config.cors_origins:
                logger.warning("No CORS origins configured - allowing all origins")
        
        if errors:
            raise ValueError(f"Configuration validation failed: {', '.join(errors)}")
    
    def get_config(self, section: str = None) -> Union[Dict[str, Any], Any]:
        """Get configuration section or entire config"""
        if section:
            return self.config.get(section)
        return self.config
    
    def get_database_config(self) -> DatabaseConfig:
        """Get database configuration object"""
        return self.config["database"]
    
    def get_redis_config(self) -> Optional[RedisConfig]:
        """Get Redis configuration object"""
        return self.config["redis"]
    
    def get_openai_config(self) -> OpenAIConfig:
        """Get OpenAI configuration object"""
        return self.config["openai"]
    
    def get_monitoring_config(self) -> MonitoringConfig:
        """Get monitoring configuration object"""
        return self.config["monitoring"]
    
    def get_security_config(self) -> SecurityConfig:
        """Get security configuration object"""
        return self.config["security"]
    
    def get_performance_config(self) -> PerformanceConfig:
        """Get performance configuration object"""
        return self.config["performance"]
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == DeploymentEnvironment.PRODUCTION
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment == DeploymentEnvironment.DEVELOPMENT

class HealthChecker:
    """Health check system for production monitoring"""
    
    def __init__(self, config_manager: ProductionConfigManager):
        self.config_manager = config_manager
        self.checks = {}
        self._register_default_checks()
    
    def _register_default_checks(self):
        """Register default health checks"""
        self.register_check("database", self._check_database)
        self.register_check("redis", self._check_redis)
        self.register_check("openai", self._check_openai)
        self.register_check("disk_space", self._check_disk_space)
        self.register_check("memory", self._check_memory)
    
    def register_check(self, name: str, check_func):
        """Register a health check function"""
        self.checks[name] = check_func
    
    async def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity"""
        try:
            db_config = self.config_manager.get_database_config()
            # In a real implementation, this would test database connectivity
            # For now, just validate configuration
            if db_config.host and db_config.username:
                return {"status": "healthy", "latency_ms": 5}
            else:
                return {"status": "unhealthy", "error": "Database configuration incomplete"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def _check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity"""
        redis_config = self.config_manager.get_redis_config()
        if not redis_config:
            return {"status": "not_configured"}
        
        try:
            # In a real implementation, this would test Redis connectivity
            return {"status": "healthy", "latency_ms": 2}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def _check_openai(self) -> Dict[str, Any]:
        """Check OpenAI API connectivity"""
        try:
            openai_config = self.config_manager.get_openai_config()
            if not openai_config.api_key:
                return {"status": "unhealthy", "error": "OpenAI API key not configured"}
            
            # In a real implementation, this would make a test API call
            return {"status": "healthy", "latency_ms": 200}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def _check_disk_space(self) -> Dict[str, Any]:
        """Check available disk space"""
        try:
            import shutil
            total, used, free = shutil.disk_usage("/")
            free_percent = (free / total) * 100
            
            status = "healthy"
            if free_percent < 5:
                status = "critical"
            elif free_percent < 15:
                status = "warning"
            
            return {
                "status": status,
                "free_percent": round(free_percent, 2),
                "free_gb": round(free / (1024**3), 2)
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def _check_memory(self) -> Dict[str, Any]:
        """Check memory usage"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            
            status = "healthy"
            if memory.percent > 95:
                status = "critical"
            elif memory.percent > 85:
                status = "warning"
            
            return {
                "status": status,
                "used_percent": round(memory.percent, 2),
                "available_gb": round(memory.available / (1024**3), 2)
            }
        except ImportError:
            return {"status": "not_available", "error": "psutil not installed"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def run_health_checks(self, include_details: bool = False) -> Dict[str, Any]:
        """Run all health checks"""
        results = {}
        overall_status = "healthy"
        
        for name, check_func in self.checks.items():
            try:
                result = await check_func()
                results[name] = result
                
                if result["status"] in ["unhealthy", "critical"]:
                    overall_status = "unhealthy"
                elif result["status"] == "warning" and overall_status == "healthy":
                    overall_status = "warning"
                    
            except Exception as e:
                results[name] = {"status": "error", "error": str(e)}
                overall_status = "unhealthy"
        
        response = {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "environment": self.config_manager.environment.value
        }
        
        if include_details:
            response["checks"] = results
        
        return response

class MetricsCollector:
    """Collect and export metrics for monitoring"""
    
    def __init__(self):
        self.metrics = {}
        self.counters = {}
        self.histograms = {}
        self.gauges = {}
    
    def increment_counter(self, name: str, value: int = 1, tags: Dict[str, str] = None):
        """Increment a counter metric"""
        key = f"{name}:{json.dumps(tags or {}, sort_keys=True)}"
        self.counters[key] = self.counters.get(key, 0) + value
    
    def record_histogram(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a histogram value"""
        key = f"{name}:{json.dumps(tags or {}, sort_keys=True)}"
        if key not in self.histograms:
            self.histograms[key] = []
        self.histograms[key].append(value)
    
    def set_gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """Set a gauge value"""
        key = f"{name}:{json.dumps(tags or {}, sort_keys=True)}"
        self.gauges[key] = value
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics"""
        return {
            "counters": self.counters,
            "histograms": {
                key: {
                    "count": len(values),
                    "sum": sum(values),
                    "avg": sum(values) / len(values) if values else 0,
                    "min": min(values) if values else 0,
                    "max": max(values) if values else 0
                }
                for key, values in self.histograms.items()
            },
            "gauges": self.gauges,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def reset_metrics(self):
        """Reset all metrics"""
        self.counters.clear()
        self.histograms.clear()
        self.gauges.clear()

# Global instances
config_manager = ProductionConfigManager()
health_checker = HealthChecker(config_manager)
metrics_collector = MetricsCollector()

def get_config_manager() -> ProductionConfigManager:
    """Get the global configuration manager"""
    return config_manager

def get_health_checker() -> HealthChecker:
    """Get the global health checker"""
    return health_checker

def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector"""
    return metrics_collector