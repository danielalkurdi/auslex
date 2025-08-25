"""
Legal Compliance and Accuracy Validation System
Ensures AI responses meet Australian legal standards and professional ethics
"""

import re
import json
import asyncio
from typing import List, Dict, Optional, Set, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ComplianceLevel(Enum):
    LOW_RISK = "low_risk"
    MEDIUM_RISK = "medium_risk"
    HIGH_RISK = "high_risk"
    PROFESSIONAL_ADVICE_REQUIRED = "professional_advice_required"

class LegalDomain(Enum):
    GENERAL_LEGAL = "general_legal"
    LITIGATION = "litigation"
    CORPORATE_LAW = "corporate_law"
    CRIMINAL_LAW = "criminal_law"
    FAMILY_LAW = "family_law"
    IMMIGRATION = "immigration"
    EMPLOYMENT = "employment"
    PROPERTY = "property"
    TAX_LAW = "tax_law"
    CONSTITUTIONAL = "constitutional"

@dataclass
class ComplianceCheck:
    check_id: str
    description: str
    risk_level: ComplianceLevel
    passed: bool
    details: str
    recommendations: List[str]
    timestamp: datetime

@dataclass
class LegalDisclaimer:
    content: str
    required_placement: str  # "header", "footer", "inline"
    severity: ComplianceLevel
    applies_to_domains: List[LegalDomain]

class LegalComplianceValidator:
    """
    Validates AI-generated legal responses for accuracy and compliance
    """
    
    def __init__(self):
        self.prohibited_phrases = self._load_prohibited_phrases()
        self.required_disclaimers = self._load_required_disclaimers()
        self.citation_patterns = self._compile_citation_patterns()
        self.jurisdiction_keywords = self._load_jurisdiction_keywords()
        
    def _load_prohibited_phrases(self) -> List[str]:
        """Load phrases that should never appear in legal AI responses"""
        return [
            "i guarantee",
            "you will definitely win",
            "this is legal advice",
            "you should sue",
            "you have no case",
            "ignore the law",
            "this will work in court",
            "100% certain",
            "you can't lose",
            "guaranteed outcome",
            "definite result",
            "sure thing",
            "without a doubt in court"
        ]
    
    def _load_required_disclaimers(self) -> List[LegalDisclaimer]:
        """Load required disclaimers based on content type"""
        return [
            LegalDisclaimer(
                content="This information is for educational purposes only and does not constitute legal advice. You should consult with a qualified Australian lawyer for advice specific to your situation.",
                required_placement="footer",
                severity=ComplianceLevel.MEDIUM_RISK,
                applies_to_domains=[LegalDomain.GENERAL_LEGAL]
            ),
            LegalDisclaimer(
                content="IMPORTANT: Immigration law is complex and changes frequently. This information should not replace professional immigration advice. Consult a registered migration agent or immigration lawyer.",
                required_placement="header",
                severity=ComplianceLevel.HIGH_RISK,
                applies_to_domains=[LegalDomain.IMMIGRATION]
            ),
            LegalDisclaimer(
                content="WARNING: Criminal law matters have serious consequences. This information is general only. You must seek immediate legal representation from a criminal defence lawyer.",
                required_placement="header", 
                severity=ComplianceLevel.PROFESSIONAL_ADVICE_REQUIRED,
                applies_to_domains=[LegalDomain.CRIMINAL_LAW]
            ),
            LegalDisclaimer(
                content="Family law matters are highly fact-specific. This general information cannot replace advice from a family lawyer who understands your specific circumstances.",
                required_placement="inline",
                severity=ComplianceLevel.HIGH_RISK,
                applies_to_domains=[LegalDomain.FAMILY_LAW]
            ),
            LegalDisclaimer(
                content="Tax law is complex and penalties apply for incorrect advice. This information is general only. Consult a tax agent or tax lawyer for specific advice.",
                required_placement="inline",
                severity=ComplianceLevel.HIGH_RISK,
                applies_to_domains=[LegalDomain.TAX_LAW]
            )
        ]
    
    def _compile_citation_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for legal citation validation"""
        return {
            "case_citation": re.compile(r'\b[A-Za-z\s&]+\s+v\s+[A-Za-z\s&]+\s+\(\d{4}\)\s+\d+\s+[A-Z]+\s+\d+\b'),
            "legislation": re.compile(r'\b[A-Za-z\s]+Act\s+\d{4}\s+\([A-Za-z]+\)\s+(s|section)\s+\d+[A-Za-z]*\b'),
            "regulation": re.compile(r'\b[A-Za-z\s]+Regulation\s+\d{4}\s+\([A-Za-z]+\)\s+reg\s+\d+\b'),
            "austlii_url": re.compile(r'https?://www\.austlii\.edu\.au/[a-zA-Z0-9/._-]+'),
            "federal_register": re.compile(r'\bF\d{4}C\d{5}\b'),
            "nsw_citation": re.compile(r'\b\d{4}\s+NSWSC\s+\d+\b'),
            "vic_citation": re.compile(r'\b\d{4}\s+VSC\s+\d+\b'),
            "qld_citation": re.compile(r'\b\d{4}\s+QSC\s+\d+\b')
        }
    
    def _load_jurisdiction_keywords(self) -> Dict[str, List[str]]:
        """Load keywords that indicate specific jurisdictions"""
        return {
            "federal": ["commonwealth", "federal", "high court of australia", "federal court", "family court"],
            "nsw": ["new south wales", "nsw", "supreme court of nsw", "nswsc", "sydney"],
            "vic": ["victoria", "vic", "supreme court of victoria", "vsc", "melbourne"],
            "qld": ["queensland", "qld", "supreme court of queensland", "qsc", "brisbane"],
            "sa": ["south australia", "sa", "supreme court of south australia", "sasc", "adelaide"],
            "wa": ["western australia", "wa", "supreme court of western australia", "wasc", "perth"],
            "tas": ["tasmania", "tas", "supreme court of tasmania", "tassc", "hobart"],
            "nt": ["northern territory", "nt", "supreme court of northern territory", "ntsc", "darwin"],
            "act": ["australian capital territory", "act", "supreme court of act", "actsc", "canberra"]
        }
    
    async def validate_response(
        self, 
        response_content: str, 
        query: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive validation of AI-generated legal response
        """
        validation_results = {
            "overall_compliance": ComplianceLevel.LOW_RISK,
            "checks_performed": [],
            "warnings": [],
            "required_disclaimers": [],
            "citation_accuracy": {},
            "recommended_improvements": [],
            "confidence_score": 0.0
        }
        
        # Run all compliance checks
        checks = await asyncio.gather(
            self._check_prohibited_language(response_content),
            self._validate_citations(response_content),
            self._assess_advice_level(response_content, query),
            self._check_jurisdiction_consistency(response_content),
            self._validate_currency_of_information(response_content, metadata),
            self._assess_clarity_and_accessibility(response_content),
            return_exceptions=True
        )
        
        # Process check results
        max_risk_level = ComplianceLevel.LOW_RISK
        for check in checks:
            if isinstance(check, ComplianceCheck):
                validation_results["checks_performed"].append(check)
                
                if not check.passed:
                    validation_results["warnings"].append({
                        "check": check.check_id,
                        "description": check.description,
                        "details": check.details,
                        "risk_level": check.risk_level.value
                    })
                
                # Update overall risk level
                if check.risk_level.value == "professional_advice_required":
                    max_risk_level = ComplianceLevel.PROFESSIONAL_ADVICE_REQUIRED
                elif check.risk_level.value == "high_risk" and max_risk_level != ComplianceLevel.PROFESSIONAL_ADVICE_REQUIRED:
                    max_risk_level = ComplianceLevel.HIGH_RISK
                elif check.risk_level.value == "medium_risk" and max_risk_level == ComplianceLevel.LOW_RISK:
                    max_risk_level = ComplianceLevel.MEDIUM_RISK
        
        validation_results["overall_compliance"] = max_risk_level
        
        # Determine required disclaimers
        legal_domain = self._classify_legal_domain(query, response_content)
        validation_results["required_disclaimers"] = self._get_required_disclaimers(legal_domain, max_risk_level)
        
        # Calculate confidence score
        validation_results["confidence_score"] = self._calculate_confidence_score(validation_results)
        
        return validation_results
    
    async def _check_prohibited_language(self, content: str) -> ComplianceCheck:
        """Check for prohibited phrases that could constitute legal advice"""
        content_lower = content.lower()
        violations = []
        
        for phrase in self.prohibited_phrases:
            if phrase in content_lower:
                violations.append(phrase)
        
        passed = len(violations) == 0
        risk_level = ComplianceLevel.PROFESSIONAL_ADVICE_REQUIRED if violations else ComplianceLevel.LOW_RISK
        
        return ComplianceCheck(
            check_id="prohibited_language",
            description="Check for prohibited language that could constitute legal advice",
            risk_level=risk_level,
            passed=passed,
            details=f"Found {len(violations)} prohibited phrases: {violations}" if violations else "No prohibited language detected",
            recommendations=["Remove or rephrase prohibited language", "Add appropriate disclaimers"] if violations else [],
            timestamp=datetime.utcnow()
        )
    
    async def _validate_citations(self, content: str) -> ComplianceCheck:
        """Validate legal citations for proper format and accuracy"""
        citation_results = {}
        total_citations = 0
        valid_citations = 0
        
        for citation_type, pattern in self.citation_patterns.items():
            matches = pattern.findall(content)
            total_citations += len(matches)
            
            # For now, assume all properly formatted citations are valid
            # In production, this would cross-reference with legal databases
            valid_citations += len(matches)
            
            citation_results[citation_type] = {
                "found": len(matches),
                "examples": matches[:3] if matches else []
            }
        
        accuracy_rate = (valid_citations / total_citations) if total_citations > 0 else 1.0
        passed = accuracy_rate >= 0.9  # 90% accuracy threshold
        
        risk_level = ComplianceLevel.LOW_RISK if passed else ComplianceLevel.MEDIUM_RISK
        
        return ComplianceCheck(
            check_id="citation_validation",
            description="Validate legal citations for proper format",
            risk_level=risk_level,
            passed=passed,
            details=f"Citation accuracy: {accuracy_rate:.1%} ({valid_citations}/{total_citations})",
            recommendations=["Verify all citations against AustLII", "Use proper citation format"] if not passed else [],
            timestamp=datetime.utcnow()
        )
    
    async def _assess_advice_level(self, content: str, query: str) -> ComplianceCheck:
        """Assess whether response crosses into legal advice territory"""
        
        advice_indicators = [
            "you should", "you must", "you need to", "i recommend", "i suggest",
            "the best approach", "you can rely on", "this means you", "in your case"
        ]
        
        information_indicators = [
            "generally", "typically", "usually", "may", "might", "could",
            "for example", "in some cases", "this information", "educational purposes"
        ]
        
        content_lower = content.lower()
        query_lower = query.lower()
        
        advice_count = sum(1 for indicator in advice_indicators if indicator in content_lower)
        info_count = sum(1 for indicator in information_indicators if indicator in content_lower)
        
        # Check if query is asking for specific advice
        specific_query_indicators = ["what should i do", "my situation", "my case", "help me"]
        specific_query = any(indicator in query_lower for indicator in specific_query_indicators)
        
        # Determine risk level
        if advice_count > info_count and specific_query:
            risk_level = ComplianceLevel.PROFESSIONAL_ADVICE_REQUIRED
            passed = False
        elif advice_count > 3:
            risk_level = ComplianceLevel.HIGH_RISK
            passed = False
        elif advice_count > 1:
            risk_level = ComplianceLevel.MEDIUM_RISK
            passed = True
        else:
            risk_level = ComplianceLevel.LOW_RISK
            passed = True
        
        return ComplianceCheck(
            check_id="advice_level_assessment",
            description="Assess whether response constitutes legal advice",
            risk_level=risk_level,
            passed=passed,
            details=f"Advice indicators: {advice_count}, Information indicators: {info_count}, Specific query: {specific_query}",
            recommendations=[
                "Rephrase directive language as general information",
                "Add stronger disclaimers about not providing legal advice",
                "Direct user to seek professional legal advice"
            ] if not passed else [],
            timestamp=datetime.utcnow()
        )
    
    async def _check_jurisdiction_consistency(self, content: str) -> ComplianceCheck:
        """Check for consistent jurisdiction references"""
        content_lower = content.lower()
        
        mentioned_jurisdictions = []
        for jurisdiction, keywords in self.jurisdiction_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                mentioned_jurisdictions.append(jurisdiction)
        
        # Check for conflicting jurisdiction information
        conflicts = []
        if len(mentioned_jurisdictions) > 2:
            # Multiple jurisdictions mentioned - check for potential conflicts
            federal_mentioned = "federal" in mentioned_jurisdictions
            states_mentioned = [j for j in mentioned_jurisdictions if j != "federal"]
            
            if federal_mentioned and len(states_mentioned) > 1:
                conflicts.append("Federal and multiple state laws mentioned without clear distinction")
        
        passed = len(conflicts) == 0
        risk_level = ComplianceLevel.MEDIUM_RISK if conflicts else ComplianceLevel.LOW_RISK
        
        return ComplianceCheck(
            check_id="jurisdiction_consistency",
            description="Check for consistent jurisdiction references",
            risk_level=risk_level,
            passed=passed,
            details=f"Jurisdictions mentioned: {mentioned_jurisdictions}, Conflicts: {conflicts}",
            recommendations=[
                "Clearly distinguish between federal and state laws",
                "Specify which jurisdiction each piece of information applies to"
            ] if conflicts else [],
            timestamp=datetime.utcnow()
        )
    
    async def _validate_currency_of_information(self, content: str, metadata: Optional[Dict[str, Any]]) -> ComplianceCheck:
        """Validate that legal information is current"""
        
        # Look for date references in content
        date_patterns = [
            r'\b(19|20)\d{2}\b',  # Years
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+(19|20)\d{2}\b',
            r'\b\d{1,2}[/-]\d{1,2}[/-](19|20)?\d{2}\b'
        ]
        
        mentioned_dates = []
        current_year = datetime.now().year
        
        for pattern in date_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, tuple):
                    year_part = next((part for part in match if part.isdigit() and len(part) == 4), None)
                    if year_part:
                        mentioned_dates.append(int(year_part))
                elif match.isdigit() and len(match) == 4:
                    mentioned_dates.append(int(match))
        
        # Check if any dates are very old (>10 years)
        old_dates = [date for date in mentioned_dates if current_year - date > 10]
        
        # Check metadata for source currency
        source_age = 0
        if metadata and "when_scraped" in metadata:
            try:
                scraped_date = datetime.fromisoformat(metadata["when_scraped"].replace('Z', '+00:00'))
                source_age = (datetime.now() - scraped_date.replace(tzinfo=None)).days
            except:
                pass
        
        currency_issues = []
        if old_dates:
            currency_issues.append(f"References to dates older than 10 years: {old_dates}")
        if source_age > 365:  # Source older than 1 year
            currency_issues.append(f"Source information is {source_age} days old")
        
        passed = len(currency_issues) == 0
        risk_level = ComplianceLevel.MEDIUM_RISK if currency_issues else ComplianceLevel.LOW_RISK
        
        return ComplianceCheck(
            check_id="information_currency",
            description="Validate currency of legal information",
            risk_level=risk_level,
            passed=passed,
            details=f"Currency issues found: {currency_issues}" if currency_issues else "Information appears current",
            recommendations=[
                "Verify that cited laws and cases are still current",
                "Add warning about checking current status of laws",
                "Update information from more recent sources"
            ] if currency_issues else [],
            timestamp=datetime.utcnow()
        )
    
    async def _assess_clarity_and_accessibility(self, content: str) -> ComplianceCheck:
        """Assess readability and accessibility of legal information"""
        
        # Simple readability metrics
        sentences = content.split('.')
        words = content.split()
        
        avg_sentence_length = len(words) / len(sentences) if sentences else 0
        long_sentences = sum(1 for sentence in sentences if len(sentence.split()) > 25)
        
        # Check for legal jargon without explanation
        complex_terms = [
            "estoppel", "tortfeasor", "chattels", "bailment", "quantum meruit",
            "mandamus", "certiorari", "habeas corpus", "res judicata", "ultra vires"
        ]
        
        unexplained_jargon = []
        content_lower = content.lower()
        for term in complex_terms:
            if term in content_lower and f"{term} means" not in content_lower and f"{term} is" not in content_lower:
                unexplained_jargon.append(term)
        
        # Accessibility issues
        accessibility_issues = []
        if avg_sentence_length > 20:
            accessibility_issues.append("Average sentence length too long")
        if long_sentences > len(sentences) * 0.3:
            accessibility_issues.append("Too many long sentences")
        if unexplained_jargon:
            accessibility_issues.append(f"Unexplained legal jargon: {unexplained_jargon}")
        
        passed = len(accessibility_issues) == 0
        risk_level = ComplianceLevel.LOW_RISK if passed else ComplianceLevel.MEDIUM_RISK
        
        return ComplianceCheck(
            check_id="clarity_accessibility",
            description="Assess readability and accessibility",
            risk_level=risk_level,
            passed=passed,
            details=f"Avg sentence length: {avg_sentence_length:.1f}, Issues: {accessibility_issues}",
            recommendations=[
                "Break up long sentences",
                "Explain legal terms in plain English",
                "Use simpler language where possible"
            ] if accessibility_issues else [],
            timestamp=datetime.utcnow()
        )
    
    def _classify_legal_domain(self, query: str, content: str) -> LegalDomain:
        """Classify the legal domain of the query/response"""
        text = f"{query} {content}".lower()
        
        domain_keywords = {
            LegalDomain.CRIMINAL_LAW: ["criminal", "charge", "offence", "prosecution", "defendant", "guilty", "conviction"],
            LegalDomain.FAMILY_LAW: ["divorce", "custody", "child support", "property settlement", "domestic violence"],
            LegalDomain.IMMIGRATION: ["visa", "migration", "citizenship", "refugee", "deportation", "immigration"],
            LegalDomain.EMPLOYMENT: ["employment", "workplace", "unfair dismissal", "discrimination", "wages"],
            LegalDomain.PROPERTY: ["property", "real estate", "lease", "tenant", "landlord", "conveyancing"],
            LegalDomain.CORPORATE_LAW: ["company", "corporation", "director", "shareholder", "asic"],
            LegalDomain.TAX_LAW: ["tax", "ato", "gst", "income tax", "capital gains", "deduction"],
            LegalDomain.CONSTITUTIONAL: ["constitutional", "human rights", "high court", "constitution"]
        }
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in text for keyword in keywords):
                return domain
        
        return LegalDomain.GENERAL_LEGAL
    
    def _get_required_disclaimers(self, domain: LegalDomain, risk_level: ComplianceLevel) -> List[Dict[str, str]]:
        """Get required disclaimers based on domain and risk level"""
        applicable_disclaimers = []
        
        for disclaimer in self.required_disclaimers:
            if (domain in disclaimer.applies_to_domains or 
                LegalDomain.GENERAL_LEGAL in disclaimer.applies_to_domains):
                
                # Include disclaimer if risk level meets or exceeds disclaimer severity
                risk_levels_order = [
                    ComplianceLevel.LOW_RISK,
                    ComplianceLevel.MEDIUM_RISK, 
                    ComplianceLevel.HIGH_RISK,
                    ComplianceLevel.PROFESSIONAL_ADVICE_REQUIRED
                ]
                
                if risk_levels_order.index(risk_level) >= risk_levels_order.index(disclaimer.severity):
                    applicable_disclaimers.append({
                        "content": disclaimer.content,
                        "placement": disclaimer.required_placement,
                        "severity": disclaimer.severity.value
                    })
        
        return applicable_disclaimers
    
    def _calculate_confidence_score(self, validation_results: Dict[str, Any]) -> float:
        """Calculate overall confidence score based on validation results"""
        checks_performed = validation_results.get("checks_performed", [])
        warnings = validation_results.get("warnings", [])
        
        if not checks_performed:
            return 0.0
        
        # Base score
        passed_checks = sum(1 for check in checks_performed if check.passed)
        base_score = passed_checks / len(checks_performed)
        
        # Penalty for warnings by risk level
        risk_penalties = {
            "low_risk": 0.05,
            "medium_risk": 0.15,
            "high_risk": 0.25,
            "professional_advice_required": 0.40
        }
        
        total_penalty = sum(risk_penalties.get(warning["risk_level"], 0.10) for warning in warnings)
        
        # Final score (0.0 to 1.0)
        final_score = max(0.0, base_score - total_penalty)
        
        return round(final_score, 2)

class LegalResponseEnhancer:
    """
    Enhances AI responses to meet legal compliance standards
    """
    
    def __init__(self, validator: LegalComplianceValidator):
        self.validator = validator
    
    async def enhance_response(
        self, 
        original_response: str, 
        query: str,
        validation_results: Dict[str, Any]
    ) -> str:
        """
        Enhance response based on validation results
        """
        enhanced_response = original_response
        
        # Add required disclaimers
        disclaimers = validation_results.get("required_disclaimers", [])
        
        # Add header disclaimers
        header_disclaimers = [d for d in disclaimers if d["placement"] == "header"]
        if header_disclaimers:
            disclaimer_text = "\n\n".join([f"⚠️ {d['content']}" for d in header_disclaimers])
            enhanced_response = f"{disclaimer_text}\n\n{enhanced_response}"
        
        # Add inline disclaimers (after first paragraph)
        inline_disclaimers = [d for d in disclaimers if d["placement"] == "inline"]
        if inline_disclaimers:
            paragraphs = enhanced_response.split('\n\n')
            if len(paragraphs) > 1:
                disclaimer_text = "\n\n".join([f"📝 {d['content']}" for d in inline_disclaimers])
                paragraphs.insert(1, disclaimer_text)
                enhanced_response = '\n\n'.join(paragraphs)
        
        # Add footer disclaimers
        footer_disclaimers = [d for d in disclaimers if d["placement"] == "footer"]
        if footer_disclaimers:
            disclaimer_text = "\n\n".join([f"ℹ️ {d['content']}" for d in footer_disclaimers])
            enhanced_response = f"{enhanced_response}\n\n{disclaimer_text}"
        
        # Add compliance metadata (for logging)
        confidence_score = validation_results.get("confidence_score", 0.0)
        compliance_level = validation_results.get("overall_compliance", "unknown")
        
        # Optional: Add compliance indicator for transparency
        if compliance_level in ["high_risk", "professional_advice_required"]:
            compliance_note = f"\n\n🔍 Response Confidence: {confidence_score:.0%} | Professional legal advice recommended"
            enhanced_response = f"{enhanced_response}{compliance_note}"
        
        return enhanced_response

# Global instances
_compliance_validator = None
_response_enhancer = None

def get_compliance_validator() -> LegalComplianceValidator:
    """Get singleton compliance validator"""
    global _compliance_validator
    if _compliance_validator is None:
        _compliance_validator = LegalComplianceValidator()
    return _compliance_validator

def get_response_enhancer() -> LegalResponseEnhancer:
    """Get singleton response enhancer"""
    global _response_enhancer
    if _response_enhancer is None:
        validator = get_compliance_validator()
        _response_enhancer = LegalResponseEnhancer(validator)
    return _response_enhancer

# Export main functions
async def validate_legal_response(
    response_content: str,
    query: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Validate AI response for legal compliance"""
    validator = get_compliance_validator()
    return await validator.validate_response(response_content, query, metadata)

async def enhance_legal_response(
    original_response: str,
    query: str,
    validation_results: Optional[Dict[str, Any]] = None
) -> str:
    """Enhance response with compliance improvements"""
    enhancer = get_response_enhancer()
    
    if validation_results is None:
        validator = get_compliance_validator()
        validation_results = await validator.validate_response(original_response, query)
    
    return await enhancer.enhance_response(original_response, query, validation_results)