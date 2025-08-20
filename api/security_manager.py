"""
Enterprise Security Hardening for OpenAI API Integration
"""

import asyncio
import hmac
import hashlib
import time
import json
import logging
import secrets
import base64
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import httpx
import os
from functools import wraps
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import jwt
import ipaddress

logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ThreatType(Enum):
    BRUTE_FORCE = "brute_force"
    RATE_ABUSE = "rate_abuse"
    DATA_EXTRACTION = "data_extraction"
    PROMPT_INJECTION = "prompt_injection"
    API_ABUSE = "api_abuse"
    UNAUTHORIZED_ACCESS = "unauthorized_access"

@dataclass
class SecurityEvent:
    """Security event for logging and monitoring"""
    event_type: ThreatType
    severity: SecurityLevel
    user_id: str
    ip_address: str
    user_agent: str
    timestamp: datetime
    details: Dict[str, Any]
    action_taken: str

@dataclass
class SecurityConfig:
    """Security configuration settings"""
    enable_ip_whitelist: bool = False
    enable_request_signing: bool = True
    enable_prompt_scanning: bool = True
    enable_response_filtering: bool = True
    max_request_size: int = 1024 * 1024  # 1MB
    require_https: bool = True
    enable_audit_logging: bool = True
    jwt_expiry_minutes: int = 60
    refresh_token_expiry_days: int = 7

class APIKeyManager:
    """Secure API key management with encryption and rotation"""
    
    def __init__(self, master_key: Optional[str] = None):
        self.master_key = master_key or os.getenv("MASTER_ENCRYPTION_KEY")
        if not self.master_key:
            self.master_key = self._generate_master_key()
            logger.warning("Generated new master key - store securely!")
        
        self.fernet = self._create_fernet(self.master_key)
        self.key_rotation_interval = timedelta(days=30)
        self.key_metadata: Dict[str, Dict] = {}
    
    def _generate_master_key(self) -> str:
        """Generate a new master encryption key"""
        return Fernet.generate_key().decode()
    
    def _create_fernet(self, key: str) -> Fernet:
        """Create Fernet encryption instance"""
        if isinstance(key, str):
            key = key.encode()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'auslex-salt',  # In production, use random salt
            iterations=100000,
        )
        
        derived_key = base64.urlsafe_b64encode(kdf.derive(key))
        return Fernet(derived_key)
    
    def encrypt_api_key(self, api_key: str, key_id: str) -> str:
        """Encrypt API key for storage"""
        encrypted = self.fernet.encrypt(api_key.encode())
        
        # Store metadata
        self.key_metadata[key_id] = {
            "created_at": datetime.utcnow().isoformat(),
            "last_used": None,
            "usage_count": 0,
            "encrypted": True
        }
        
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt_api_key(self, encrypted_key: str, key_id: str) -> str:
        """Decrypt API key for use"""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_key.encode())
            decrypted = self.fernet.decrypt(encrypted_bytes)
            
            # Update metadata
            if key_id in self.key_metadata:
                self.key_metadata[key_id]["last_used"] = datetime.utcnow().isoformat()
                self.key_metadata[key_id]["usage_count"] += 1
            
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt API key {key_id}: {e}")
            raise SecurityException("Invalid API key")
    
    def should_rotate_key(self, key_id: str) -> bool:
        """Check if key should be rotated"""
        if key_id not in self.key_metadata:
            return True
        
        created_at = datetime.fromisoformat(self.key_metadata[key_id]["created_at"])
        return datetime.utcnow() - created_at > self.key_rotation_interval
    
    def rotate_api_key(self, old_key_id: str, new_api_key: str) -> str:
        """Rotate to new API key"""
        new_key_id = f"{old_key_id}_rotated_{int(time.time())}"
        encrypted_key = self.encrypt_api_key(new_api_key, new_key_id)
        
        logger.info(f"Rotated API key from {old_key_id} to {new_key_id}")
        return new_key_id

class RequestValidator:
    """Validate and sanitize incoming requests"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.malicious_patterns = [
            # Prompt injection patterns
            r'ignore\s+previous\s+instructions',
            r'ignore\s+all\s+previous\s+prompts',
            r'act\s+as\s+if\s+you\s+are',
            r'pretend\s+you\s+are',
            r'simulate\s+being',
            r'roleplay\s+as',
            r'system\s*:\s*ignore',
            r'</system>.*<system>',
            
            # Data extraction attempts
            r'show\s+me\s+your\s+training\s+data',
            r'what\s+are\s+your\s+instructions',
            r'reveal\s+your\s+prompt',
            r'show\s+system\s+prompt',
            
            # Code injection
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'eval\s*\(',
            r'exec\s*\(',
        ]
        
        self.sensitive_patterns = [
            # PII patterns
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Credit card
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            
            # API keys and tokens
            r'sk-[a-zA-Z0-9]{48}',  # OpenAI API key
            r'Bearer\s+[a-zA-Z0-9_\-\.]+',
            r'api[_-]?key["\']?\s*[:=]\s*["\']?[a-zA-Z0-9_\-\.]+',
        ]
    
    def validate_request_size(self, content: str) -> bool:
        """Validate request size is within limits"""
        size = len(content.encode('utf-8'))
        if size > self.config.max_request_size:
            raise SecurityException(f"Request too large: {size} bytes > {self.config.max_request_size}")
        return True
    
    def scan_for_prompt_injection(self, text: str) -> List[str]:
        """Scan text for potential prompt injection attempts"""
        import re
        
        detected_patterns = []
        text_lower = text.lower()
        
        for pattern in self.malicious_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE | re.DOTALL):
                detected_patterns.append(pattern)
        
        return detected_patterns
    
    def scan_for_sensitive_data(self, text: str) -> List[str]:
        """Scan text for sensitive data that shouldn't be logged"""
        import re
        
        detected_patterns = []
        
        for pattern in self.sensitive_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                detected_patterns.extend([f"sensitive_data_{pattern[:20]}" for _ in matches])
        
        return detected_patterns
    
    def sanitize_text(self, text: str) -> str:
        """Sanitize text by removing or masking sensitive content"""
        import re
        
        sanitized = text
        
        # Mask sensitive patterns
        for pattern in self.sensitive_patterns:
            sanitized = re.sub(pattern, "[REDACTED]", sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    def validate_user_input(self, user_input: str, user_id: str, ip_address: str) -> Dict[str, Any]:
        """Comprehensive validation of user input"""
        validation_result = {
            "is_valid": True,
            "issues": [],
            "sanitized_input": user_input,
            "security_score": 100
        }
        
        # Check request size
        try:
            self.validate_request_size(user_input)
        except SecurityException as e:
            validation_result["is_valid"] = False
            validation_result["issues"].append(str(e))
            validation_result["security_score"] -= 50
        
        # Check for prompt injection
        injection_patterns = self.scan_for_prompt_injection(user_input)
        if injection_patterns:
            validation_result["issues"].append(f"Potential prompt injection: {len(injection_patterns)} patterns")
            validation_result["security_score"] -= 30 * len(injection_patterns)
            
            # Log security event
            self._log_security_event(
                ThreatType.PROMPT_INJECTION,
                SecurityLevel.HIGH,
                user_id,
                ip_address,
                {"patterns": injection_patterns}
            )
        
        # Check for sensitive data
        sensitive_patterns = self.scan_for_sensitive_data(user_input)
        if sensitive_patterns:
            validation_result["issues"].append(f"Sensitive data detected: {len(sensitive_patterns)} instances")
            validation_result["sanitized_input"] = self.sanitize_text(user_input)
            validation_result["security_score"] -= 20
        
        # Determine if request should be blocked
        if validation_result["security_score"] < 50:
            validation_result["is_valid"] = False
        
        return validation_result
    
    def _log_security_event(self, threat_type: ThreatType, severity: SecurityLevel, 
                           user_id: str, ip_address: str, details: Dict):
        """Log security event"""
        event = SecurityEvent(
            event_type=threat_type,
            severity=severity,
            user_id=user_id,
            ip_address=ip_address,
            user_agent="",
            timestamp=datetime.utcnow(),
            details=details,
            action_taken="logged"
        )
        
        logger.warning(f"Security event: {threat_type.value} from {user_id}@{ip_address}")

class ResponseFilter:
    """Filter and sanitize API responses"""
    
    def __init__(self):
        self.blocked_content_patterns = [
            # Prevent model from revealing sensitive information
            r'my\s+training\s+data',
            r'system\s+prompt',
            r'internal\s+instructions',
            
            # Block potential harmful content
            r'how\s+to\s+hack',
            r'bypass\s+security',
            r'exploit\s+vulnerability',
        ]
    
    def filter_response(self, response: str, user_id: str) -> Dict[str, Any]:
        """Filter response content for security issues"""
        import re
        
        filter_result = {
            "filtered_response": response,
            "issues_found": [],
            "blocked_content": False
        }
        
        response_lower = response.lower()
        
        for pattern in self.blocked_content_patterns:
            if re.search(pattern, response_lower, re.IGNORECASE):
                filter_result["issues_found"].append(pattern)
                filter_result["blocked_content"] = True
        
        if filter_result["blocked_content"]:
            filter_result["filtered_response"] = (
                "I cannot provide that information as it may contain sensitive or harmful content. "
                "Please rephrase your request or contact support if you need assistance."
            )
            
            logger.warning(f"Blocked response for user {user_id} due to security concerns")
        
        return filter_result

class IPWhitelist:
    """Manage IP address whitelisting"""
    
    def __init__(self):
        self.whitelisted_ips: List[str] = []
        self.whitelisted_networks: List[ipaddress.IPv4Network] = []
        self.load_whitelist()
    
    def load_whitelist(self):
        """Load IP whitelist from environment or config"""
        whitelist_env = os.getenv("IP_WHITELIST", "")
        if whitelist_env:
            ips = [ip.strip() for ip in whitelist_env.split(",") if ip.strip()]
            for ip in ips:
                try:
                    if "/" in ip:
                        self.whitelisted_networks.append(ipaddress.IPv4Network(ip))
                    else:
                        self.whitelisted_ips.append(ip)
                except Exception as e:
                    logger.error(f"Invalid IP in whitelist: {ip} - {e}")
    
    def is_ip_allowed(self, ip_address: str) -> bool:
        """Check if IP address is allowed"""
        if not self.whitelisted_ips and not self.whitelisted_networks:
            return True  # No whitelist configured, allow all
        
        # Check exact IP matches
        if ip_address in self.whitelisted_ips:
            return True
        
        # Check network ranges
        try:
            ip = ipaddress.IPv4Address(ip_address)
            for network in self.whitelisted_networks:
                if ip in network:
                    return True
        except Exception:
            logger.warning(f"Invalid IP address format: {ip_address}")
            return False
        
        return False

class RequestSigner:
    """Handle request signing for API authentication"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
    
    def sign_request(self, payload: str, timestamp: int) -> str:
        """Sign a request payload"""
        message = f"{timestamp}.{payload}"
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def verify_signature(self, payload: str, timestamp: int, signature: str) -> bool:
        """Verify request signature"""
        expected_signature = self.sign_request(payload, timestamp)
        
        # Use constant-time comparison
        return hmac.compare_digest(expected_signature, signature)
    
    def is_timestamp_valid(self, timestamp: int, tolerance_seconds: int = 300) -> bool:
        """Check if timestamp is within acceptable range"""
        current_time = int(time.time())
        return abs(current_time - timestamp) <= tolerance_seconds

class SecurityException(Exception):
    """Custom exception for security-related issues"""
    def __init__(self, message: str, threat_type: Optional[ThreatType] = None):
        self.threat_type = threat_type
        super().__init__(message)

class SecurityManager:
    """Main security manager coordinating all security components"""
    
    def __init__(self, config: SecurityConfig = None):
        self.config = config or SecurityConfig()
        self.api_key_manager = APIKeyManager()
        self.request_validator = RequestValidator(self.config)
        self.response_filter = ResponseFilter()
        self.ip_whitelist = IPWhitelist()
        self.request_signer = RequestSigner(os.getenv("HMAC_SECRET_KEY", secrets.token_urlsafe(32)))
        self.security_events: List[SecurityEvent] = []
        
    async def validate_request(self, request_data: Dict[str, Any], 
                             user_id: str, ip_address: str, user_agent: str) -> Dict[str, Any]:
        """Comprehensive request validation"""
        validation_results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "sanitized_data": request_data.copy()
        }
        
        try:
            # IP whitelist check
            if self.config.enable_ip_whitelist and not self.ip_whitelist.is_ip_allowed(ip_address):
                raise SecurityException(f"IP address {ip_address} not in whitelist", ThreatType.UNAUTHORIZED_ACCESS)
            
            # Validate request signature if enabled
            if self.config.enable_request_signing:
                if not self._validate_request_signature(request_data):
                    raise SecurityException("Invalid request signature", ThreatType.API_ABUSE)
            
            # Validate user input
            if "message" in request_data:
                input_validation = self.request_validator.validate_user_input(
                    request_data["message"], user_id, ip_address
                )
                
                if not input_validation["is_valid"]:
                    validation_results["is_valid"] = False
                    validation_results["errors"].extend(input_validation["issues"])
                
                # Use sanitized input
                validation_results["sanitized_data"]["message"] = input_validation["sanitized_input"]
            
            return validation_results
            
        except SecurityException as e:
            validation_results["is_valid"] = False
            validation_results["errors"].append(str(e))
            
            # Log security event
            self._log_security_event(
                e.threat_type or ThreatType.API_ABUSE,
                SecurityLevel.HIGH,
                user_id,
                ip_address,
                user_agent,
                {"error": str(e)}
            )
            
            return validation_results
    
    def filter_response(self, response: str, user_id: str) -> str:
        """Filter API response for security"""
        if self.config.enable_response_filtering:
            filter_result = self.response_filter.filter_response(response, user_id)
            return filter_result["filtered_response"]
        
        return response
    
    def _validate_request_signature(self, request_data: Dict) -> bool:
        """Validate HMAC signature of request"""
        signature = request_data.get("signature")
        timestamp = request_data.get("timestamp")
        
        if not signature or not timestamp:
            return False
        
        # Check timestamp validity
        if not self.request_signer.is_timestamp_valid(timestamp):
            return False
        
        # Create payload without signature
        payload_data = {k: v for k, v in request_data.items() if k not in ["signature", "timestamp"]}
        payload = json.dumps(payload_data, sort_keys=True, separators=(',', ':'))
        
        return self.request_signer.verify_signature(payload, timestamp, signature)
    
    def _log_security_event(self, threat_type: ThreatType, severity: SecurityLevel,
                           user_id: str, ip_address: str, user_agent: str, details: Dict):
        """Log security event with full context"""
        event = SecurityEvent(
            event_type=threat_type,
            severity=severity,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.utcnow(),
            details=details,
            action_taken="request_blocked" if severity in [SecurityLevel.HIGH, SecurityLevel.CRITICAL] else "logged"
        )
        
        self.security_events.append(event)
        
        # In production, send to SIEM/monitoring system
        logger.warning(f"Security Event: {threat_type.value} - {severity.value} - {user_id}@{ip_address}")
        
        # Keep only last 1000 events
        if len(self.security_events) > 1000:
            self.security_events = self.security_events[-1000:]
    
    def get_security_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get security metrics for monitoring"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_events = [e for e in self.security_events if e.timestamp >= cutoff_time]
        
        threat_counts = {}
        severity_counts = {}
        
        for event in recent_events:
            threat_counts[event.event_type.value] = threat_counts.get(event.event_type.value, 0) + 1
            severity_counts[event.severity.value] = severity_counts.get(event.severity.value, 0) + 1
        
        return {
            "period_hours": hours,
            "total_events": len(recent_events),
            "threat_breakdown": threat_counts,
            "severity_breakdown": severity_counts,
            "top_threats": sorted(threat_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        }

# Global security manager
security_manager = SecurityManager()

def secure_endpoint(security_level: SecurityLevel = SecurityLevel.MEDIUM):
    """Decorator to secure API endpoints"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract security context from request
            # This would be implemented based on your FastAPI setup
            user_id = kwargs.get("user_id", "anonymous")
            ip_address = kwargs.get("ip_address", "unknown")
            user_agent = kwargs.get("user_agent", "unknown")
            request_data = kwargs.get("request_data", {})
            
            # Validate request
            validation_result = await security_manager.validate_request(
                request_data, user_id, ip_address, user_agent
            )
            
            if not validation_result["is_valid"]:
                raise SecurityException(f"Request validation failed: {validation_result['errors']}")
            
            # Use sanitized data
            kwargs["request_data"] = validation_result["sanitized_data"]
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Filter response if needed
            if isinstance(result, str):
                result = security_manager.filter_response(result, user_id)
            elif hasattr(result, "choices") and result.choices:
                # Filter OpenAI response
                for choice in result.choices:
                    if hasattr(choice, "message") and choice.message.content:
                        choice.message.content = security_manager.filter_response(
                            choice.message.content, user_id
                        )
            
            return result
        
        return wrapper
    return decorator