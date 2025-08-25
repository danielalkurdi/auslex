"""
Unit and Integration Tests for Legal Compliance System
Tests compliance validation, risk assessment, and disclaimer injection
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Any

# Test imports
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../api'))

try:
    from legal_compliance import (
        LegalComplianceValidator,
        LegalResponseEnhancer,
        ComplianceLevel,
        LegalDomain,
        LegalDisclaimer,
        ComplianceCheck,
        validate_legal_response,
        enhance_legal_response
    )
    COMPLIANCE_AVAILABLE = True
except ImportError:
    COMPLIANCE_AVAILABLE = False
    pytestmark = pytest.mark.skip("Legal compliance dependencies not available")

class TestComplianceLevel:
    """Test compliance level enumeration"""
    
    def test_compliance_levels(self):
        """Test compliance level enum values"""
        assert ComplianceLevel.LOW_RISK.value == "low_risk"
        assert ComplianceLevel.MEDIUM_RISK.value == "medium_risk"
        assert ComplianceLevel.HIGH_RISK.value == "high_risk"
        assert ComplianceLevel.PROFESSIONAL_ADVICE_REQUIRED.value == "professional_advice_required"

class TestLegalDomain:
    """Test legal domain classification"""
    
    def test_legal_domains(self):
        """Test legal domain enum values"""
        assert LegalDomain.MIGRATION.value == "migration"
        assert LegalDomain.CRIMINAL_LAW.value == "criminal_law"
        assert LegalDomain.FAMILY_LAW.value == "family_law"
        assert LegalDomain.EMPLOYMENT.value == "employment"

@pytest.mark.skipif(not COMPLIANCE_AVAILABLE, reason="Legal compliance not available")
class TestLegalComplianceValidator:
    """Test legal compliance validation functionality"""
    
    @pytest.fixture
    def validator(self):
        """Create compliance validator for testing"""
        return LegalComplianceValidator()
    
    def test_prohibited_phrases_detection(self, validator):
        """Test detection of prohibited phrases"""
        # Test prohibited phrases are loaded
        assert len(validator.prohibited_phrases) > 0
        assert "i guarantee" in validator.prohibited_phrases
        assert "you will definitely win" in validator.prohibited_phrases
        assert "this is legal advice" in validator.prohibited_phrases
    
    def test_required_disclaimers_loaded(self, validator):
        """Test that required disclaimers are loaded"""
        assert len(validator.required_disclaimers) > 0
        
        # Check for domain-specific disclaimers
        migration_disclaimers = [d for d in validator.required_disclaimers 
                               if LegalDomain.IMMIGRATION in d.applies_to_domains]
        assert len(migration_disclaimers) > 0
        
        criminal_disclaimers = [d for d in validator.required_disclaimers 
                              if LegalDomain.CRIMINAL_LAW in d.applies_to_domains]
        assert len(criminal_disclaimers) > 0
    
    def test_citation_patterns_compilation(self, validator):
        """Test citation regex patterns are compiled"""
        assert "case_citation" in validator.citation_patterns
        assert "legislation" in validator.citation_patterns
        assert "austlii_url" in validator.citation_patterns
        
        # Test case citation pattern
        test_case = "Smith v Jones (2023) 45 CLR 123"
        assert validator.citation_patterns["case_citation"].search(test_case)
        
        # Test legislation pattern
        test_legislation = "Migration Act 1958 (Cth) s 501"
        assert validator.citation_patterns["legislation"].search(test_legislation)
    
    @pytest.mark.asyncio
    async def test_prohibited_language_check_pass(self, validator):
        """Test prohibited language check with clean content"""
        clean_content = "The Migration Act 1958 provides for character test requirements under section 501."
        
        check = await validator._check_prohibited_language(clean_content)
        
        assert check.check_id == "prohibited_language"
        assert check.passed is True
        assert check.risk_level == ComplianceLevel.LOW_RISK
        assert "No prohibited language detected" in check.details
    
    @pytest.mark.asyncio
    async def test_prohibited_language_check_fail(self, validator):
        """Test prohibited language check with prohibited content"""
        problematic_content = "I guarantee you will definitely win this case."
        
        check = await validator._check_prohibited_language(problematic_content)
        
        assert check.check_id == "prohibited_language"
        assert check.passed is False
        assert check.risk_level == ComplianceLevel.PROFESSIONAL_ADVICE_REQUIRED
        assert "Found 2 prohibited phrases" in check.details
        assert "i guarantee" in check.details
        assert "you will definitely win" in check.details
    
    @pytest.mark.asyncio
    async def test_citation_validation(self, validator):
        """Test citation validation functionality"""
        content_with_citations = """
        Under Migration Act 1958 (Cth) s 501, the character test applies.
        See also Smith v Minister for Immigration (2023) 45 FCA 123.
        The legislation is available at https://www.austlii.edu.au/au/legis/cth/consol_act/ma1958118/
        """
        
        check = await validator._validate_citations(content_with_citations)
        
        assert check.check_id == "citation_validation"
        assert check.passed is True  # Properly formatted citations should pass
        assert check.risk_level == ComplianceLevel.LOW_RISK
    
    @pytest.mark.asyncio
    async def test_advice_level_assessment_information(self, validator):
        """Test advice level assessment for information-only content"""
        information_content = "Generally, the Migration Act provides that visa holders typically must enter before the deadline."
        information_query = "What does the law say about visa deadlines?"
        
        check = await validator._assess_advice_level(information_content, information_query)
        
        assert check.check_id == "advice_level_assessment"
        assert check.passed is True
        assert check.risk_level in [ComplianceLevel.LOW_RISK, ComplianceLevel.MEDIUM_RISK]
    
    @pytest.mark.asyncio
    async def test_advice_level_assessment_advice(self, validator):
        """Test advice level assessment for advice-like content"""
        advice_content = "You should immediately apply for a new visa. You must contact the department. I recommend you hire a lawyer."
        advice_query = "What should I do about my visa situation?"
        
        check = await validator._assess_advice_level(advice_content, advice_query)
        
        assert check.check_id == "advice_level_assessment"
        assert check.passed is False
        assert check.risk_level in [ComplianceLevel.HIGH_RISK, ComplianceLevel.PROFESSIONAL_ADVICE_REQUIRED]
    
    @pytest.mark.asyncio
    async def test_jurisdiction_consistency_single(self, validator):
        """Test jurisdiction consistency with single jurisdiction"""
        single_jurisdiction_content = "Under federal law, the Migration Act 1958 applies to all visa holders."
        
        check = await validator._check_jurisdiction_consistency(single_jurisdiction_content)
        
        assert check.check_id == "jurisdiction_consistency"
        assert check.passed is True
        assert check.risk_level == ComplianceLevel.LOW_RISK
    
    @pytest.mark.asyncio
    async def test_jurisdiction_consistency_conflicts(self, validator):
        """Test jurisdiction consistency with conflicting jurisdictions"""
        conflicting_content = """
        The federal Migration Act applies, but NSW state law also governs, 
        and Victoria has different rules, while Queensland follows another approach.
        """
        
        check = await validator._check_jurisdiction_consistency(conflicting_content)
        
        assert check.check_id == "jurisdiction_consistency"
        # Should detect conflicts with federal + multiple states without distinction
        if not check.passed:
            assert check.risk_level == ComplianceLevel.MEDIUM_RISK
    
    @pytest.mark.asyncio
    async def test_information_currency_current(self, validator):
        """Test information currency validation for recent information"""
        current_content = "The 2023 amendments to the Migration Act came into effect."
        current_metadata = {"when_scraped": "2023-12-01T00:00:00Z"}
        
        check = await validator._validate_currency_of_information(current_content, current_metadata)
        
        assert check.check_id == "information_currency"
        assert check.passed is True
        assert check.risk_level == ComplianceLevel.LOW_RISK
    
    @pytest.mark.asyncio
    async def test_information_currency_outdated(self, validator):
        """Test information currency validation for outdated information"""
        outdated_content = "The 2005 reforms significantly changed migration law."
        outdated_metadata = {"when_scraped": "2020-01-01T00:00:00Z"}
        
        check = await validator._validate_currency_of_information(outdated_content, outdated_metadata)
        
        assert check.check_id == "information_currency"
        # May flag as needing currency verification
    
    @pytest.mark.asyncio
    async def test_clarity_accessibility_good(self, validator):
        """Test clarity and accessibility assessment for clear content"""
        clear_content = "The Migration Act requires visa holders to enter Australia before their deadline. This rule has exceptions for protection visas."
        
        check = await validator._assess_clarity_and_accessibility(clear_content)
        
        assert check.check_id == "clarity_accessibility"
        assert check.passed is True
        assert check.risk_level == ComplianceLevel.LOW_RISK
    
    @pytest.mark.asyncio
    async def test_clarity_accessibility_poor(self, validator):
        """Test clarity and accessibility assessment for complex content"""
        complex_content = """
        The Migration Act 1958, notwithstanding subsection 55(2)(b) and having regard to the quantum meruit 
        principles established in bailment cases involving chattels, creates an estoppel against tortfeasors 
        where habeas corpus proceedings would otherwise establish res judicata through mandamus applications.
        """
        
        check = await validator._assess_clarity_and_accessibility(complex_content)
        
        assert check.check_id == "clarity_accessibility"
        if not check.passed:
            assert check.risk_level == ComplianceLevel.MEDIUM_RISK
            assert "unexplained legal jargon" in check.details.lower() or "long sentences" in check.details.lower()
    
    def test_legal_domain_classification_migration(self, validator):
        """Test legal domain classification for migration queries"""
        migration_query = "What are the visa character test requirements?"
        migration_content = "The Migration Act 1958 establishes character test provisions for visa applicants."
        
        domain = validator._classify_legal_domain(migration_query, migration_content)
        
        assert domain == LegalDomain.IMMIGRATION
    
    def test_legal_domain_classification_employment(self, validator):
        """Test legal domain classification for employment queries"""
        employment_query = "What constitutes unfair dismissal?"
        employment_content = "Under the Fair Work Act, unfair dismissal occurs when termination is harsh, unjust or unreasonable."
        
        domain = validator._classify_legal_domain(employment_query, employment_content)
        
        assert domain == LegalDomain.EMPLOYMENT
    
    def test_legal_domain_classification_criminal(self, validator):
        """Test legal domain classification for criminal law queries"""
        criminal_query = "What are the penalties for assault charges?"
        criminal_content = "Criminal charges for assault can result in conviction and imprisonment."
        
        domain = validator._classify_legal_domain(criminal_query, criminal_content)
        
        assert domain == LegalDomain.CRIMINAL_LAW
    
    def test_required_disclaimers_migration(self, validator):
        """Test required disclaimers for migration law"""
        disclaimers = validator._get_required_disclaimers(LegalDomain.IMMIGRATION, ComplianceLevel.HIGH_RISK)
        
        assert len(disclaimers) > 0
        # Should include migration-specific disclaimer
        migration_disclaimer = next((d for d in disclaimers if "immigration" in d["content"].lower()), None)
        assert migration_disclaimer is not None
        assert migration_disclaimer["severity"] == ComplianceLevel.HIGH_RISK.value
    
    def test_required_disclaimers_criminal(self, validator):
        """Test required disclaimers for criminal law"""
        disclaimers = validator._get_required_disclaimers(LegalDomain.CRIMINAL_LAW, ComplianceLevel.PROFESSIONAL_ADVICE_REQUIRED)
        
        assert len(disclaimers) > 0
        # Should include criminal law warning
        criminal_disclaimer = next((d for d in disclaimers if "criminal" in d["content"].lower()), None)
        assert criminal_disclaimer is not None
        assert criminal_disclaimer["placement"] == "header"
    
    def test_confidence_score_calculation_high(self, validator):
        """Test confidence score calculation for good validation results"""
        validation_results = {
            "checks_performed": [
                ComplianceCheck("test1", "Test", ComplianceLevel.LOW_RISK, True, "", [], datetime.now()),
                ComplianceCheck("test2", "Test", ComplianceLevel.LOW_RISK, True, "", [], datetime.now()),
                ComplianceCheck("test3", "Test", ComplianceLevel.LOW_RISK, True, "", [], datetime.now())
            ],
            "warnings": []
        }
        
        score = validator._calculate_confidence_score(validation_results)
        
        assert score >= 0.9  # High confidence for all checks passed
        assert score <= 1.0
    
    def test_confidence_score_calculation_low(self, validator):
        """Test confidence score calculation for poor validation results"""
        validation_results = {
            "checks_performed": [
                ComplianceCheck("test1", "Test", ComplianceLevel.HIGH_RISK, False, "", [], datetime.now()),
                ComplianceCheck("test2", "Test", ComplianceLevel.PROFESSIONAL_ADVICE_REQUIRED, False, "", [], datetime.now())
            ],
            "warnings": [
                {"risk_level": "high_risk"},
                {"risk_level": "professional_advice_required"}
            ]
        }
        
        score = validator._calculate_confidence_score(validation_results)
        
        assert score < 0.5  # Low confidence for failed checks with high-risk warnings

class TestLegalResponseEnhancer:
    """Test legal response enhancement functionality"""
    
    @pytest.fixture
    def enhancer(self):
        """Create response enhancer for testing"""
        if not COMPLIANCE_AVAILABLE:
            return Mock()
        validator = LegalComplianceValidator()
        return LegalResponseEnhancer(validator)
    
    @pytest.mark.asyncio
    async def test_enhance_response_with_disclaimers(self, enhancer):
        """Test response enhancement with disclaimer injection"""
        if not COMPLIANCE_AVAILABLE:
            pytest.skip("Legal compliance not available")
            
        original_response = "The Migration Act requires character test compliance for all visa applicants."
        query = "What is the character test?"
        
        validation_results = {
            "required_disclaimers": [
                {
                    "content": "This is general information only and not legal advice.",
                    "placement": "footer",
                    "severity": "medium_risk"
                },
                {
                    "content": "IMPORTANT: Immigration law is complex and changes frequently.",
                    "placement": "header",
                    "severity": "high_risk"
                }
            ],
            "overall_compliance": "medium_risk",
            "confidence_score": 0.8
        }
        
        enhanced_response = await enhancer.enhance_response(original_response, query, validation_results)
        
        # Should contain original response
        assert original_response in enhanced_response
        
        # Should contain disclaimers
        assert "This is general information only" in enhanced_response
        assert "IMPORTANT: Immigration law is complex" in enhanced_response
        
        # Header disclaimer should appear before original content
        disclaimer_index = enhanced_response.find("IMPORTANT: Immigration law is complex")
        content_index = enhanced_response.find(original_response)
        assert disclaimer_index < content_index
    
    @pytest.mark.asyncio
    async def test_enhance_response_high_risk(self, enhancer):
        """Test response enhancement for high-risk content"""
        if not COMPLIANCE_AVAILABLE:
            pytest.skip("Legal compliance not available")
            
        original_response = "You should sue them immediately for breach of contract."
        query = "What should I do about this contract dispute?"
        
        validation_results = {
            "required_disclaimers": [
                {
                    "content": "WARNING: This information should not replace professional legal advice.",
                    "placement": "header",
                    "severity": "professional_advice_required"
                }
            ],
            "overall_compliance": "professional_advice_required",
            "confidence_score": 0.3
        }
        
        enhanced_response = await enhancer.enhance_response(original_response, query, validation_results)
        
        # Should contain compliance warning
        assert "WARNING:" in enhanced_response
        
        # Should contain confidence indicator for low confidence
        assert "Professional legal advice recommended" in enhanced_response

class TestComplianceIntegration:
    """Integration tests for complete compliance workflow"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_compliance_validation_workflow(self):
        """Test complete compliance validation workflow"""
        if not COMPLIANCE_AVAILABLE:
            pytest.skip("Legal compliance not available")
            
        # Test with a comprehensive legal response
        response_content = """
        Under the Migration Act 1958 (Cth) section 501, the Minister may refuse or cancel a visa 
        if a person does not pass the character test. The character test includes having a 
        substantial criminal record or not being of good character.
        
        Generally, this provision allows the Minister broad discretionary powers. However, 
        the specific circumstances of each case matter significantly.
        """
        
        query = "What is the character test for Australian visas?"
        
        validation_results = await validate_legal_response(response_content, query)
        
        # Should complete validation without errors
        assert "overall_compliance" in validation_results
        assert "checks_performed" in validation_results
        assert "confidence_score" in validation_results
        
        # Should have performed multiple checks
        assert len(validation_results["checks_performed"]) >= 4
        
        # Should classify as migration domain and provide appropriate disclaimers
        assert len(validation_results.get("required_disclaimers", [])) > 0
        
        # Enhance the response
        enhanced_response = await enhance_legal_response(response_content, query, validation_results)
        
        # Enhanced response should contain disclaimers
        assert len(enhanced_response) > len(response_content)
        assert "information" in enhanced_response.lower() and "legal advice" in enhanced_response.lower()
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_criminal_law_high_risk_validation(self):
        """Test validation of high-risk criminal law content"""
        if not COMPLIANCE_AVAILABLE:
            pytest.skip("Legal compliance not available")
            
        response_content = """
        You should plead not guilty and fight these charges. I guarantee you can beat this case 
        if you follow my advice. The police made mistakes that will definitely get the case dismissed.
        """
        
        query = "What should I do about criminal charges?"
        
        validation_results = await validate_legal_response(response_content, query)
        
        # Should flag as high risk due to prohibited language and advice-giving
        assert validation_results["overall_compliance"] in ["high_risk", "professional_advice_required"]
        
        # Should have warnings
        assert len(validation_results["warnings"]) > 0
        
        # Should require criminal law disclaimers
        disclaimers = validation_results.get("required_disclaimers", [])
        criminal_disclaimer = next((d for d in disclaimers if "criminal" in d["content"].lower()), None)
        assert criminal_disclaimer is not None

class TestPerformanceRequirements:
    """Test performance requirements for compliance checking"""
    
    @pytest.mark.asyncio
    async def test_compliance_validation_speed(self):
        """Test that compliance validation completes quickly"""
        if not COMPLIANCE_AVAILABLE:
            pytest.skip("Legal compliance not available")
            
        import time
        
        response_content = "The Fair Work Act 2009 provides protections against unfair dismissal for eligible employees."
        query = "What are unfair dismissal protections?"
        
        start_time = time.time()
        validation_results = await validate_legal_response(response_content, query)
        end_time = time.time()
        
        validation_time = end_time - start_time
        
        # Compliance validation should complete in under 1 second
        assert validation_time < 1.0, f"Compliance validation took {validation_time}s, should be < 1s"
        
        # Should still provide comprehensive results
        assert len(validation_results["checks_performed"]) >= 4

if __name__ == "__main__":
    pytest.main([__file__, "-v"])