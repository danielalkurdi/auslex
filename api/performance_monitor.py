"""
Performance Monitoring System for AusLex AI
Tracks search performance, compliance metrics, and system health
"""

import time
import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from enum import Enum
import json
import threading
from collections import defaultdict, deque
import statistics

logger = logging.getLogger(__name__)

class MetricType(Enum):
    COUNTER = "counter"
    HISTOGRAM = "histogram" 
    GAUGE = "gauge"
    TIMER = "timer"

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class PerformanceMetric:
    name: str
    metric_type: MetricType
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    description: Optional[str] = None

@dataclass
class SearchMetrics:
    query: str
    search_method: str
    response_time: float
    relevance_scores: List[float]
    documents_found: int
    embedding_time: Optional[float] = None
    compliance_time: Optional[float] = None
    total_tokens: int = 0
    cache_hit: bool = False
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def avg_relevance_score(self) -> float:
        return statistics.mean(self.relevance_scores) if self.relevance_scores else 0.0
    
    @property
    def top3_avg_score(self) -> float:
        top3 = self.relevance_scores[:3]
        return statistics.mean(top3) if top3 else 0.0

@dataclass
class ComplianceMetrics:
    query: str
    risk_level: str
    confidence_score: float
    validation_time: float
    checks_performed: int
    warnings_count: int
    disclaimers_added: int
    prohibited_language_detected: bool = False
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class SystemHealthMetrics:
    cpu_usage: float
    memory_usage: float
    active_connections: int
    response_time_p95: float
    error_rate: float
    cache_hit_rate: float
    vector_db_latency: Optional[float] = None
    openai_api_latency: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

class PerformanceMonitor:
    """
    Comprehensive performance monitoring for AusLex AI system
    """
    
    def __init__(self, retention_hours: int = 24, alert_thresholds: Optional[Dict[str, float]] = None):
        self.retention_hours = retention_hours
        self.alert_thresholds = alert_thresholds or self._default_alert_thresholds()
        
        # Thread-safe storage
        self._lock = threading.RLock()
        self._metrics = defaultdict(deque)
        self._counters = defaultdict(float)
        self._gauges = defaultdict(float)
        self._timers = defaultdict(list)
        
        # Search and compliance tracking
        self._search_metrics = deque(maxlen=10000)
        self._compliance_metrics = deque(maxlen=10000)
        self._system_health = deque(maxlen=1000)
        
        # Performance tracking
        self._response_times = deque(maxlen=1000)
        self._error_counts = defaultdict(int)
        self._cache_stats = {'hits': 0, 'misses': 0}
        
        # Alert callbacks
        self._alert_callbacks = []
        
        # Background cleanup
        self._cleanup_task = None
        self._start_background_cleanup()
    
    def _default_alert_thresholds(self) -> Dict[str, float]:
        """Default alert thresholds for key metrics"""
        return {
            'response_time_p95': 3.0,      # 3 seconds
            'error_rate': 0.05,            # 5%
            'compliance_confidence': 0.7,   # 70%
            'search_relevance': 0.8,       # 80%
            'memory_usage': 0.85,          # 85%
            'vector_db_latency': 2.0       # 2 seconds
        }
    
    def record_search_metrics(self, metrics: SearchMetrics):
        """Record search performance metrics"""
        with self._lock:
            self._search_metrics.append(metrics)
            
            # Update aggregated metrics
            self._response_times.append(metrics.response_time)
            
            if metrics.cache_hit:
                self._cache_stats['hits'] += 1
            else:
                self._cache_stats['misses'] += 1
            
            # Check for alerts
            self._check_search_alerts(metrics)
    
    def record_compliance_metrics(self, metrics: ComplianceMetrics):
        """Record compliance validation metrics"""
        with self._lock:
            self._compliance_metrics.append(metrics)
            
            # Check for alerts
            self._check_compliance_alerts(metrics)
    
    def record_system_health(self, metrics: SystemHealthMetrics):
        """Record system health metrics"""
        with self._lock:
            self._system_health.append(metrics)
            
            # Update gauges
            self._gauges['cpu_usage'] = metrics.cpu_usage
            self._gauges['memory_usage'] = metrics.memory_usage
            self._gauges['active_connections'] = metrics.active_connections
            
            # Check for alerts
            self._check_system_health_alerts(metrics)
    
    def increment_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increment a counter metric"""
        with self._lock:
            key = f"{name}:{json.dumps(labels or {}, sort_keys=True)}"
            self._counters[key] += value
            
            self._metrics[name].append(PerformanceMetric(
                name=name,
                metric_type=MetricType.COUNTER,
                value=self._counters[key],
                timestamp=datetime.utcnow(),
                labels=labels or {}
            ))
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Set a gauge metric value"""
        with self._lock:
            key = f"{name}:{json.dumps(labels or {}, sort_keys=True)}"
            self._gauges[key] = value
            
            self._metrics[name].append(PerformanceMetric(
                name=name,
                metric_type=MetricType.GAUGE,
                value=value,
                timestamp=datetime.utcnow(),
                labels=labels or {}
            ))
    
    def record_timer(self, name: str, duration: float, labels: Optional[Dict[str, str]] = None):
        """Record a timer metric"""
        with self._lock:
            key = f"{name}:{json.dumps(labels or {}, sort_keys=True)}"
            self._timers[key].append(duration)
            
            # Keep only recent values
            if len(self._timers[key]) > 1000:
                self._timers[key] = self._timers[key][-1000:]
            
            self._metrics[name].append(PerformanceMetric(
                name=name,
                metric_type=MetricType.TIMER,
                value=duration,
                timestamp=datetime.utcnow(),
                labels=labels or {}
            ))
    
    def timer(self, name: str, labels: Optional[Dict[str, str]] = None):
        """Context manager for timing operations"""
        return TimerContext(self, name, labels)
    
    def get_search_analytics(self, hours: int = 1) -> Dict[str, Any]:
        """Get search performance analytics"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        with self._lock:
            recent_searches = [m for m in self._search_metrics if m.timestamp >= cutoff]
        
        if not recent_searches:
            return {'message': 'No search data available', 'count': 0}
        
        # Calculate analytics
        response_times = [m.response_time for m in recent_searches]
        relevance_scores = [m.avg_relevance_score for m in recent_searches]
        top3_scores = [m.top3_avg_score for m in recent_searches]
        
        search_methods = defaultdict(int)
        for m in recent_searches:
            search_methods[m.search_method] += 1
        
        return {
            'time_period_hours': hours,
            'total_searches': len(recent_searches),
            'response_time': {
                'avg': statistics.mean(response_times),
                'median': statistics.median(response_times),
                'p95': self._percentile(response_times, 95),
                'p99': self._percentile(response_times, 99),
                'min': min(response_times),
                'max': max(response_times)
            },
            'relevance': {
                'avg_score': statistics.mean(relevance_scores),
                'top3_avg_score': statistics.mean(top3_scores),
                'above_threshold': len([s for s in relevance_scores if s >= 0.8])
            },
            'search_methods': dict(search_methods),
            'cache_performance': {
                'hit_rate': self._cache_stats['hits'] / (self._cache_stats['hits'] + self._cache_stats['misses']) if (self._cache_stats['hits'] + self._cache_stats['misses']) > 0 else 0,
                'total_hits': self._cache_stats['hits'],
                'total_misses': self._cache_stats['misses']
            },
            'total_tokens_processed': sum(m.total_tokens for m in recent_searches)
        }
    
    def get_compliance_analytics(self, hours: int = 1) -> Dict[str, Any]:
        """Get compliance performance analytics"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        with self._lock:
            recent_compliance = [m for m in self._compliance_metrics if m.timestamp >= cutoff]
        
        if not recent_compliance:
            return {'message': 'No compliance data available', 'count': 0}
        
        # Risk level distribution
        risk_levels = defaultdict(int)
        confidence_scores = []
        validation_times = []
        
        for m in recent_compliance:
            risk_levels[m.risk_level] += 1
            confidence_scores.append(m.confidence_score)
            validation_times.append(m.validation_time)
        
        return {
            'time_period_hours': hours,
            'total_validations': len(recent_compliance),
            'risk_distribution': dict(risk_levels),
            'confidence_scores': {
                'avg': statistics.mean(confidence_scores),
                'median': statistics.median(confidence_scores),
                'min': min(confidence_scores),
                'max': max(confidence_scores)
            },
            'validation_performance': {
                'avg_time': statistics.mean(validation_times),
                'p95_time': self._percentile(validation_times, 95)
            },
            'safety_metrics': {
                'high_risk_queries': len([m for m in recent_compliance if m.risk_level in ['high_risk', 'professional_advice_required']]),
                'prohibited_language_detected': len([m for m in recent_compliance if m.prohibited_language_detected]),
                'avg_warnings_per_query': statistics.mean([m.warnings_count for m in recent_compliance])
            }
        }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get current system health metrics"""
        with self._lock:
            if not self._system_health:
                return {'message': 'No system health data available'}
            
            latest = self._system_health[-1]
            
            # Calculate trends from recent data
            recent_health = list(self._system_health)[-10:]  # Last 10 readings
            
            return {
                'timestamp': latest.timestamp.isoformat(),
                'current_metrics': asdict(latest),
                'trends': {
                    'cpu_usage_trend': self._calculate_trend([h.cpu_usage for h in recent_health]),
                    'memory_usage_trend': self._calculate_trend([h.memory_usage for h in recent_health]),
                    'response_time_trend': self._calculate_trend([h.response_time_p95 for h in recent_health])
                },
                'alerts': self._get_active_alerts(),
                'overall_status': self._get_overall_health_status(latest)
            }
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'reporting_period_hours': hours,
            'search_analytics': self.get_search_analytics(hours),
            'compliance_analytics': self.get_compliance_analytics(hours),
            'system_health': self.get_system_health(),
            'alerts': {
                'active_alerts': self._get_active_alerts(),
                'alert_history': self._get_alert_history(hours)
            }
        }
    
    def add_alert_callback(self, callback: Callable[[str, AlertLevel, Dict[str, Any]], None]):
        """Add callback for alert notifications"""
        self._alert_callbacks.append(callback)
    
    def _check_search_alerts(self, metrics: SearchMetrics):
        """Check for search performance alerts"""
        # Response time alert
        if metrics.response_time > self.alert_thresholds['response_time_p95']:
            self._trigger_alert(
                f"High search response time: {metrics.response_time:.2f}s",
                AlertLevel.WARNING,
                {'query': metrics.query, 'response_time': metrics.response_time}
            )
        
        # Relevance score alert
        if metrics.avg_relevance_score < self.alert_thresholds['search_relevance']:
            self._trigger_alert(
                f"Low search relevance: {metrics.avg_relevance_score:.2f}",
                AlertLevel.WARNING,
                {'query': metrics.query, 'relevance_score': metrics.avg_relevance_score}
            )
    
    def _check_compliance_alerts(self, metrics: ComplianceMetrics):
        """Check for compliance alerts"""
        # Low confidence alert
        if metrics.confidence_score < self.alert_thresholds['compliance_confidence']:
            self._trigger_alert(
                f"Low compliance confidence: {metrics.confidence_score:.2f}",
                AlertLevel.WARNING,
                {'query': metrics.query, 'confidence_score': metrics.confidence_score}
            )
        
        # High risk content alert
        if metrics.risk_level == 'professional_advice_required':
            self._trigger_alert(
                "High risk content detected - professional advice required",
                AlertLevel.ERROR,
                {'query': metrics.query, 'risk_level': metrics.risk_level}
            )
        
        # Prohibited language alert
        if metrics.prohibited_language_detected:
            self._trigger_alert(
                "Prohibited language detected in response",
                AlertLevel.CRITICAL,
                {'query': metrics.query}
            )
    
    def _check_system_health_alerts(self, metrics: SystemHealthMetrics):
        """Check for system health alerts"""
        # Memory usage alert
        if metrics.memory_usage > self.alert_thresholds['memory_usage']:
            self._trigger_alert(
                f"High memory usage: {metrics.memory_usage:.1%}",
                AlertLevel.WARNING,
                {'memory_usage': metrics.memory_usage}
            )
        
        # Error rate alert
        if metrics.error_rate > self.alert_thresholds['error_rate']:
            self._trigger_alert(
                f"High error rate: {metrics.error_rate:.1%}",
                AlertLevel.ERROR,
                {'error_rate': metrics.error_rate}
            )
        
        # Vector database latency alert
        if metrics.vector_db_latency and metrics.vector_db_latency > self.alert_thresholds['vector_db_latency']:
            self._trigger_alert(
                f"High vector database latency: {metrics.vector_db_latency:.2f}s",
                AlertLevel.WARNING,
                {'vector_db_latency': metrics.vector_db_latency}
            )
    
    def _trigger_alert(self, message: str, level: AlertLevel, context: Dict[str, Any]):
        """Trigger alert and notify callbacks"""
        logger.warning(f"ALERT [{level.value.upper()}]: {message}")
        
        for callback in self._alert_callbacks:
            try:
                callback(message, level, context)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile of data"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from values"""
        if len(values) < 2:
            return "insufficient_data"
        
        recent_avg = statistics.mean(values[-3:])
        older_avg = statistics.mean(values[:3]) if len(values) >= 6 else statistics.mean(values[:-3])
        
        if recent_avg > older_avg * 1.1:
            return "increasing"
        elif recent_avg < older_avg * 0.9:
            return "decreasing"
        else:
            return "stable"
    
    def _get_overall_health_status(self, health: SystemHealthMetrics) -> str:
        """Determine overall health status"""
        if (health.memory_usage > 0.9 or 
            health.error_rate > 0.1 or 
            (health.vector_db_latency and health.vector_db_latency > 5.0)):
            return "critical"
        elif (health.memory_usage > 0.8 or 
              health.error_rate > 0.05 or
              health.response_time_p95 > 3.0):
            return "warning"
        else:
            return "healthy"
    
    def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get currently active alerts"""
        # This would be implemented with a more sophisticated alert management system
        return []
    
    def _get_alert_history(self, hours: int) -> List[Dict[str, Any]]:
        """Get alert history for specified time period"""
        # This would be implemented with alert history storage
        return []
    
    def _start_background_cleanup(self):
        """Start background task for cleaning old metrics"""
        def cleanup_worker():
            while True:
                try:
                    cutoff = datetime.utcnow() - timedelta(hours=self.retention_hours)
                    
                    with self._lock:
                        # Clean search metrics
                        while (self._search_metrics and 
                               self._search_metrics[0].timestamp < cutoff):
                            self._search_metrics.popleft()
                        
                        # Clean compliance metrics
                        while (self._compliance_metrics and 
                               self._compliance_metrics[0].timestamp < cutoff):
                            self._compliance_metrics.popleft()
                        
                        # Clean system health metrics
                        while (self._system_health and 
                               self._system_health[0].timestamp < cutoff):
                            self._system_health.popleft()
                    
                    # Sleep for 1 hour before next cleanup
                    time.sleep(3600)
                    
                except Exception as e:
                    logger.error(f"Metrics cleanup error: {e}")
                    time.sleep(300)  # Sleep 5 minutes on error
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()

class TimerContext:
    """Context manager for timing operations"""
    
    def __init__(self, monitor: PerformanceMonitor, name: str, labels: Optional[Dict[str, str]] = None):
        self.monitor = monitor
        self.name = name
        self.labels = labels
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.monitor.record_timer(self.name, duration, self.labels)

# Global performance monitor instance
_performance_monitor = None

def get_performance_monitor(
    retention_hours: int = 24,
    alert_thresholds: Optional[Dict[str, float]] = None
) -> PerformanceMonitor:
    """Get or create global performance monitor"""
    global _performance_monitor
    
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor(retention_hours, alert_thresholds)
    
    return _performance_monitor

# Convenience functions for common operations
def record_search_performance(
    query: str,
    search_method: str,
    response_time: float,
    relevance_scores: List[float],
    documents_found: int,
    **kwargs
):
    """Record search performance metrics"""
    monitor = get_performance_monitor()
    
    metrics = SearchMetrics(
        query=query,
        search_method=search_method,
        response_time=response_time,
        relevance_scores=relevance_scores,
        documents_found=documents_found,
        **kwargs
    )
    
    monitor.record_search_metrics(metrics)

def record_compliance_performance(
    query: str,
    risk_level: str,
    confidence_score: float,
    validation_time: float,
    checks_performed: int,
    warnings_count: int,
    disclaimers_added: int,
    prohibited_language_detected: bool = False
):
    """Record compliance validation metrics"""
    monitor = get_performance_monitor()
    
    metrics = ComplianceMetrics(
        query=query,
        risk_level=risk_level,
        confidence_score=confidence_score,
        validation_time=validation_time,
        checks_performed=checks_performed,
        warnings_count=warnings_count,
        disclaimers_added=disclaimers_added,
        prohibited_language_detected=prohibited_language_detected
    )
    
    monitor.record_compliance_metrics(metrics)

def get_system_performance_report(hours: int = 24) -> Dict[str, Any]:
    """Get comprehensive system performance report"""
    monitor = get_performance_monitor()
    return monitor.get_performance_summary(hours)