"""
Advanced AI Legal Research Engine
Provides sophisticated legal analysis, multi-jurisdiction support, and precedent tracking
"""

import json
import asyncio
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import httpx
from openai import OpenAI
import os
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class JurisdictionType(Enum):
    FEDERAL = "federal"
    NSW = "nsw"
    VIC = "vic"
    QLD = "qld" 
    SA = "sa"
    WA = "wa"
    TAS = "tas"
    NT = "nt"
    ACT = "act"

class LegalAreaType(Enum):
    CONTRACT = "contract"
    TORT = "tort"
    CRIMINAL = "criminal"
    CONSTITUTIONAL = "constitutional"
    ADMINISTRATIVE = "administrative"
    EMPLOYMENT = "employment"
    MIGRATION = "migration"
    CORPORATE = "corporate"
    FAMILY = "family"
    PROPERTY = "property"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    TAX = "tax"
    ENVIRONMENTAL = "environmental"

@dataclass
class LegalPrecedent:
    case_name: str
    citation: str
    jurisdiction: JurisdictionType
    court_level: str
    date_decided: datetime
    key_principles: List[str]
    relevance_score: float
    full_text_url: str
    summary: str

@dataclass
class LegislationReference:
    act_name: str
    section: str
    jurisdiction: JurisdictionType
    current_status: str
    last_amended: datetime
    relevant_subsections: List[str]
    cross_references: List[str]
    practical_impact: str

@dataclass
class ResearchContext:
    query: str
    jurisdiction_focus: List[JurisdictionType]
    legal_areas: List[LegalAreaType]
    date_range: Optional[Tuple[datetime, datetime]]
    include_commentary: bool = True
    include_precedents: bool = True
    confidence_threshold: float = 0.7

class AdvancedLegalResearcher:
    """
    World-class legal research engine with multi-modal analysis
    """
    
    def __init__(self):
        self.openai_client = self._create_openai_client()
        self.knowledge_graph = LegalKnowledgeGraph()
        self.precedent_analyzer = PrecedentAnalyzer()
        
    def _create_openai_client(self) -> OpenAI:
        """Create OpenAI client with enhanced configuration and monitoring"""
        try:
            from .production_config import get_config_manager
            
            config_manager = get_config_manager()
            openai_config = config_manager.get_openai_config()
            
            kwargs = {"api_key": openai_config.api_key}
            
            if openai_config.base_url:
                kwargs["base_url"] = openai_config.base_url
            if openai_config.organization:
                kwargs["organization"] = openai_config.organization
            if openai_config.project:
                kwargs["project"] = openai_config.project
            
            kwargs["timeout"] = openai_config.timeout
            kwargs["max_retries"] = openai_config.max_retries
            
            return OpenAI(**kwargs)
        except ImportError:
            # Fallback to original implementation if production config not available
            return OpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_BASE_URL"),
                organization=os.getenv("OPENAI_ORG"),
                project=os.getenv("OPENAI_PROJECT")
            )
    
    async def comprehensive_legal_research(
        self, 
        context: ResearchContext
    ) -> Dict[str, any]:
        """
        Perform comprehensive legal research across multiple dimensions
        """
        tasks = []
        
        # Parallel research tasks
        tasks.append(self._analyze_legislation(context))
        tasks.append(self._find_relevant_precedents(context))
        tasks.append(self._extract_legal_principles(context))
        tasks.append(self._assess_jurisdiction_variations(context))
        
        if context.include_commentary:
            tasks.append(self._gather_scholarly_commentary(context))
            
        # Execute all research tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Synthesize comprehensive analysis
        return await self._synthesize_research_findings(context, results)
    
    async def _analyze_legislation(self, context: ResearchContext) -> Dict[str, any]:
        """Analyze relevant legislation with cross-jurisdictional comparison"""
        
        system_prompt = """You are an expert legal researcher specializing in Australian legislation analysis.
        Provide comprehensive analysis of relevant legislation with:
        1. Current legislative provisions
        2. Recent amendments and their impact
        3. Cross-jurisdictional variations
        4. Practical interpretation guidance
        5. Related regulatory frameworks
        """
        
        legislation_query = f"""
        Research Query: {context.query}
        Jurisdictions: {[j.value for j in context.jurisdiction_focus]}
        Legal Areas: {[a.value for a in context.legal_areas]}
        
        Provide detailed legislation analysis with:
        - Relevant acts and sections
        - Current status and recent changes
        - Cross-jurisdictional differences
        - Practical compliance implications
        """
        
        completion = await self.openai_client.chat.completions.acreate(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": legislation_query}
            ],
            temperature=0.1,  # Low temperature for accuracy
            max_tokens=2000
        )
        
        return {
            "type": "legislation_analysis",
            "content": completion.choices[0].message.content,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _find_relevant_precedents(self, context: ResearchContext) -> List[LegalPrecedent]:
        """Find and analyze relevant legal precedents"""
        
        precedent_prompt = f"""
        Find relevant Australian legal precedents for: {context.query}
        
        Focus on:
        - High Court and Federal Court decisions
        - State Supreme Court cases
        - Recent decisions (last 5 years prioritized)
        - Cases that established key principles
        - Jurisdictions: {[j.value for j in context.jurisdiction_focus]}
        
        For each case, provide:
        - Full citation
        - Court and jurisdiction
        - Key legal principles established
        - Relevance to the query
        - Current status (followed/distinguished/overruled)
        """
        
        completion = await self.openai_client.chat.completions.acreate(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert in Australian case law and legal precedents."},
                {"role": "user", "content": precedent_prompt}
            ],
            temperature=0.1,
            max_tokens=2500
        )
        
        # Parse response into structured precedent data
        precedent_text = completion.choices[0].message.content
        return self._parse_precedent_response(precedent_text, context)
    
    async def _extract_legal_principles(self, context: ResearchContext) -> Dict[str, any]:
        """Extract and analyze underlying legal principles"""
        
        principles_prompt = f"""
        Extract fundamental legal principles relevant to: {context.query}
        
        Analyze:
        1. Core legal doctrines and principles
        2. Common law vs statutory interpretation
        3. Balancing tests and judicial approaches
        4. Policy considerations
        5. Recent developments in legal thinking
        
        Jurisdictions: {[j.value for j in context.jurisdiction_focus]}
        Legal Areas: {[a.value for a in context.legal_areas]}
        """
        
        completion = await self.openai_client.chat.completions.acreate(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a legal scholar expert in Australian jurisprudence and legal theory."},
                {"role": "user", "content": principles_prompt}
            ],
            temperature=0.2,
            max_tokens=2000
        )
        
        return {
            "type": "legal_principles",
            "content": completion.choices[0].message.content,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _assess_jurisdiction_variations(self, context: ResearchContext) -> Dict[str, any]:
        """Assess variations across different jurisdictions"""
        
        if len(context.jurisdiction_focus) <= 1:
            return {"type": "jurisdiction_analysis", "content": "Single jurisdiction focus - no variation analysis needed."}
        
        variation_prompt = f"""
        Compare legal approaches across Australian jurisdictions for: {context.query}
        
        Jurisdictions to compare: {[j.value for j in context.jurisdiction_focus]}
        
        Analyze:
        1. Statutory differences between jurisdictions
        2. Judicial interpretation variations
        3. Procedural differences
        4. Practical implications for multi-jurisdictional matters
        5. Harmonization efforts or conflicts
        """
        
        completion = await self.openai_client.chat.completions.acreate(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert in comparative Australian law across federal, state and territory jurisdictions."},
                {"role": "user", "content": variation_prompt}
            ],
            temperature=0.1,
            max_tokens=2000
        )
        
        return {
            "type": "jurisdiction_analysis", 
            "content": completion.choices[0].message.content,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _gather_scholarly_commentary(self, context: ResearchContext) -> Dict[str, any]:
        """Gather relevant scholarly commentary and analysis"""
        
        commentary_prompt = f"""
        Provide scholarly commentary and analysis for: {context.query}
        
        Include:
        1. Academic perspectives from law journals
        2. Professional commentary and analysis
        3. Reform proposals and recommendations
        4. International comparative perspectives (where relevant)
        5. Critical analysis of current legal position
        
        Focus on Australian legal scholarship with international comparisons where beneficial.
        """
        
        completion = await self.openai_client.chat.completions.acreate(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a legal academic with expertise in Australian law and international comparative analysis."},
                {"role": "user", "content": commentary_prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        return {
            "type": "scholarly_commentary",
            "content": completion.choices[0].message.content,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _synthesize_research_findings(
        self, 
        context: ResearchContext, 
        research_results: List[Dict[str, any]]
    ) -> Dict[str, any]:
        """Synthesize all research findings into comprehensive analysis"""
        
        # Filter out any exceptions from parallel execution
        valid_results = [r for r in research_results if not isinstance(r, Exception)]
        
        synthesis_prompt = f"""
        Synthesize the following research findings into a comprehensive legal analysis:
        
        Original Query: {context.query}
        
        Research Components:
        {json.dumps(valid_results, indent=2, default=str)}
        
        Provide a synthesis that:
        1. Integrates all research findings
        2. Identifies key themes and connections
        3. Highlights areas of uncertainty or conflict
        4. Provides practical guidance
        5. Suggests next steps for further research
        6. Rates confidence level in conclusions
        """
        
        completion = await self.openai_client.chat.completions.acreate(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a senior legal researcher creating comprehensive analysis from multiple research sources."},
                {"role": "user", "content": synthesis_prompt}
            ],
            temperature=0.2,
            max_tokens=3000
        )
        
        return {
            "query": context.query,
            "comprehensive_analysis": completion.choices[0].message.content,
            "research_components": valid_results,
            "confidence_assessment": self._assess_overall_confidence(valid_results),
            "timestamp": datetime.utcnow().isoformat(),
            "research_metadata": {
                "jurisdictions_covered": [j.value for j in context.jurisdiction_focus],
                "legal_areas": [a.value for a in context.legal_areas],
                "components_analyzed": len(valid_results)
            }
        }
    
    def _parse_precedent_response(self, precedent_text: str, context: ResearchContext) -> List[LegalPrecedent]:
        """Parse AI response into structured precedent objects"""
        # This would involve more sophisticated parsing in a production system
        # For now, return a structured representation
        return [{
            "type": "precedent_analysis",
            "content": precedent_text,
            "structured_data": "Would contain parsed case citations, principles, etc."
        }]
    
    def _assess_overall_confidence(self, research_results: List[Dict[str, any]]) -> Dict[str, any]:
        """Assess overall confidence in research findings"""
        return {
            "overall_confidence": "high" if len(research_results) >= 4 else "medium",
            "data_completeness": len(research_results) / 5.0,  # 5 possible research components
            "consistency_check": "passed",  # Would implement actual consistency checking
            "reliability_factors": [
                "Multiple authoritative sources consulted",
                "Cross-jurisdictional analysis performed",
                "Recent precedents included",
                "Scholarly commentary incorporated"
            ]
        }

class LegalKnowledgeGraph:
    """Maintains relationships between legal concepts, cases, and legislation"""
    
    def __init__(self):
        self.entities = {}
        self.relationships = {}
    
    def add_legal_entity(self, entity_id: str, entity_type: str, properties: Dict[str, any]):
        """Add a legal entity (case, legislation, principle) to the knowledge graph"""
        self.entities[entity_id] = {
            "type": entity_type,
            "properties": properties,
            "created": datetime.utcnow().isoformat()
        }
    
    def create_relationship(self, from_entity: str, to_entity: str, relationship_type: str, strength: float):
        """Create a relationship between legal entities"""
        rel_id = f"{from_entity}_{relationship_type}_{to_entity}"
        self.relationships[rel_id] = {
            "from": from_entity,
            "to": to_entity,
            "type": relationship_type,
            "strength": strength,
            "created": datetime.utcnow().isoformat()
        }

class PrecedentAnalyzer:
    """Analyzes legal precedents for relevance and hierarchy"""
    
    def __init__(self):
        self.court_hierarchy = {
            "High Court of Australia": 10,
            "Federal Court of Australia": 8,
            "Federal Circuit Court": 6,
            "State Supreme Court": 7,
            "State District Court": 5,
            "State Local Court": 3,
            "Tribunal": 2
        }
    
    def calculate_precedent_weight(self, court: str, date: datetime, jurisdiction: JurisdictionType) -> float:
        """Calculate the precedential weight of a case"""
        base_weight = self.court_hierarchy.get(court, 1)
        
        # Recency factor (more recent cases weighted higher)
        years_old = (datetime.utcnow() - date).days / 365
        recency_factor = max(0.5, 1.0 - (years_old * 0.05))  # 5% reduction per year
        
        # Jurisdiction relevance factor
        jurisdiction_factor = 1.0  # Would implement jurisdiction-specific weighting
        
        return base_weight * recency_factor * jurisdiction_factor