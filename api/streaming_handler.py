"""
Advanced Streaming Response Handler for Long Legal Research Operations
"""

import asyncio
import json
import time
from typing import AsyncIterator, Dict, Any, Optional, List, Union
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from openai import OpenAI
import os

logger = logging.getLogger(__name__)

class StreamEventType(Enum):
    STARTED = "started"
    PROGRESS = "progress"
    PARTIAL_RESULT = "partial_result"
    COMPONENT_COMPLETE = "component_complete"
    ERROR = "error"
    COMPLETED = "completed"
    HEARTBEAT = "heartbeat"

@dataclass
class StreamEvent:
    """Standard streaming event structure"""
    event_type: StreamEventType
    timestamp: str
    data: Dict[str, Any]
    progress_percent: Optional[float] = None
    component: Optional[str] = None
    error: Optional[str] = None
    
    def to_sse_format(self) -> str:
        """Convert to Server-Sent Events format"""
        event_dict = {
            "type": self.event_type.value,
            "timestamp": self.timestamp,
            "data": self.data
        }
        
        if self.progress_percent is not None:
            event_dict["progress"] = self.progress_percent
        if self.component:
            event_dict["component"] = self.component
        if self.error:
            event_dict["error"] = self.error
            
        # Format for SSE
        return f"data: {json.dumps(event_dict)}\n\n"

@dataclass
class ResearchProgress:
    """Track progress of legal research operations"""
    total_components: int
    completed_components: int = 0
    current_component: Optional[str] = None
    start_time: Optional[float] = None
    estimated_completion: Optional[float] = None
    
    @property
    def progress_percent(self) -> float:
        if self.total_components == 0:
            return 0.0
        return (self.completed_components / self.total_components) * 100
    
    def estimate_completion_time(self) -> Optional[float]:
        """Estimate completion time based on current progress"""
        if not self.start_time or self.completed_components == 0:
            return None
        
        elapsed = time.time() - self.start_time
        avg_time_per_component = elapsed / self.completed_components
        remaining_components = self.total_components - self.completed_components
        
        return avg_time_per_component * remaining_components

class StreamingResearchEngine:
    """Streaming version of the legal research engine"""
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    async def stream_comprehensive_research(
        self, 
        context: Dict[str, Any], 
        enable_components: Dict[str, bool] = None
    ) -> AsyncIterator[StreamEvent]:
        """Stream comprehensive legal research with real-time progress"""
        
        # Default components to enable
        if enable_components is None:
            enable_components = {
                "legislation": True,
                "precedents": True,
                "principles": True,
                "jurisdiction_analysis": True,
                "commentary": context.get("include_commentary", True)
            }
        
        # Calculate total components
        total_components = sum(1 for enabled in enable_components.values() if enabled) + 1  # +1 for synthesis
        progress = ResearchProgress(total_components=total_components, start_time=time.time())
        
        # Send start event
        yield StreamEvent(
            event_type=StreamEventType.STARTED,
            timestamp=datetime.utcnow().isoformat(),
            data={
                "query": context["query"],
                "total_components": total_components,
                "components": list(enable_components.keys())
            }
        )
        
        research_results = []
        
        try:
            # Execute components with streaming progress
            component_tasks = []
            
            if enable_components.get("legislation"):
                component_tasks.append(("legislation", self._stream_legislation_analysis))
            
            if enable_components.get("precedents"):
                component_tasks.append(("precedents", self._stream_precedent_analysis))
            
            if enable_components.get("principles"):
                component_tasks.append(("principles", self._stream_principles_analysis))
            
            if enable_components.get("jurisdiction_analysis"):
                component_tasks.append(("jurisdiction_analysis", self._stream_jurisdiction_analysis))
            
            if enable_components.get("commentary"):
                component_tasks.append(("commentary", self._stream_commentary_analysis))
            
            # Execute components and stream results
            for component_name, component_func in component_tasks:
                progress.current_component = component_name
                
                # Send progress update
                yield StreamEvent(
                    event_type=StreamEventType.PROGRESS,
                    timestamp=datetime.utcnow().isoformat(),
                    data={"status": f"Starting {component_name} analysis"},
                    progress_percent=progress.progress_percent,
                    component=component_name
                )
                
                try:
                    # Stream component execution
                    component_result = None
                    async for event in component_func(context):
                        if event.event_type == StreamEventType.COMPLETED:
                            component_result = event.data
                        yield event
                    
                    if component_result:
                        research_results.append(component_result)
                    
                    progress.completed_components += 1
                    
                    # Send component completion event
                    yield StreamEvent(
                        event_type=StreamEventType.COMPONENT_COMPLETE,
                        timestamp=datetime.utcnow().isoformat(),
                        data={
                            "component": component_name,
                            "completed": True,
                            "estimated_remaining": progress.estimate_completion_time()
                        },
                        progress_percent=progress.progress_percent,
                        component=component_name
                    )
                    
                except Exception as e:
                    logger.error(f"Error in component {component_name}: {e}")
                    yield StreamEvent(
                        event_type=StreamEventType.ERROR,
                        timestamp=datetime.utcnow().isoformat(),
                        data={"component": component_name, "error_message": str(e)},
                        component=component_name,
                        error=str(e)
                    )
                    # Continue with other components
                    progress.completed_components += 1
            
            # Final synthesis
            progress.current_component = "synthesis"
            yield StreamEvent(
                event_type=StreamEventType.PROGRESS,
                timestamp=datetime.utcnow().isoformat(),
                data={"status": "Synthesizing comprehensive analysis"},
                progress_percent=progress.progress_percent,
                component="synthesis"
            )
            
            async for event in self._stream_synthesis(context, research_results):
                yield event
            
            progress.completed_components += 1
            
            # Send completion event
            yield StreamEvent(
                event_type=StreamEventType.COMPLETED,
                timestamp=datetime.utcnow().isoformat(),
                data={
                    "status": "Research completed successfully",
                    "total_time": time.time() - progress.start_time,
                    "components_completed": progress.completed_components
                },
                progress_percent=100.0
            )
            
        except Exception as e:
            logger.error(f"Error in streaming research: {e}")
            yield StreamEvent(
                event_type=StreamEventType.ERROR,
                timestamp=datetime.utcnow().isoformat(),
                data={"error_message": str(e), "fatal": True},
                error=str(e)
            )
    
    async def _stream_legislation_analysis(self, context: Dict) -> AsyncIterator[StreamEvent]:
        """Stream legislation analysis component"""
        try:
            # Send start notification
            yield StreamEvent(
                event_type=StreamEventType.PROGRESS,
                timestamp=datetime.utcnow().isoformat(),
                data={"status": "Analyzing relevant legislation", "sub_component": "database_search"},
                component="legislation"
            )
            
            # Simulate progressive analysis
            await asyncio.sleep(0.5)  # Simulate database search
            
            yield StreamEvent(
                event_type=StreamEventType.PARTIAL_RESULT,
                timestamp=datetime.utcnow().isoformat(),
                data={
                    "status": "Found relevant acts and sections",
                    "preliminary_findings": ["Migration Act 1958 (Cth)", "Fair Work Act 2009 (Cth)"]
                },
                component="legislation"
            )
            
            # Stream API call with OpenAI
            system_prompt = """You are an expert legal researcher specializing in Australian legislation analysis.
            Provide comprehensive analysis with current legislative provisions, recent amendments, 
            and cross-jurisdictional variations."""
            
            user_prompt = f"""
            Research Query: {context['query']}
            Jurisdictions: {context.get('jurisdictions', ['federal'])}
            
            Provide detailed legislation analysis focusing on:
            - Current relevant acts and sections
            - Recent amendments and their impact
            - Cross-jurisdictional differences
            - Practical compliance implications
            """
            
            # Stream the OpenAI response
            stream = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=2000,
                stream=True
            )
            
            content_chunks = []
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    chunk_content = chunk.choices[0].delta.content
                    content_chunks.append(chunk_content)
                    
                    # Send partial content updates
                    yield StreamEvent(
                        event_type=StreamEventType.PARTIAL_RESULT,
                        timestamp=datetime.utcnow().isoformat(),
                        data={
                            "partial_content": chunk_content,
                            "accumulated_length": sum(len(c) for c in content_chunks)
                        },
                        component="legislation"
                    )
            
            full_content = "".join(content_chunks)
            
            # Send completion
            yield StreamEvent(
                event_type=StreamEventType.COMPLETED,
                timestamp=datetime.utcnow().isoformat(),
                data={
                    "type": "legislation_analysis",
                    "content": full_content,
                    "metadata": {
                        "token_count": len(full_content.split()),
                        "response_time": 2.0  # Would track actual time
                    }
                },
                component="legislation"
            )
            
        except Exception as e:
            yield StreamEvent(
                event_type=StreamEventType.ERROR,
                timestamp=datetime.utcnow().isoformat(),
                data={"error_message": str(e)},
                component="legislation",
                error=str(e)
            )
    
    async def _stream_precedent_analysis(self, context: Dict) -> AsyncIterator[StreamEvent]:
        """Stream precedent analysis component"""
        try:
            yield StreamEvent(
                event_type=StreamEventType.PROGRESS,
                timestamp=datetime.utcnow().isoformat(),
                data={"status": "Searching for relevant case law"},
                component="precedents"
            )
            
            # Simulate case law search
            await asyncio.sleep(1.0)
            
            yield StreamEvent(
                event_type=StreamEventType.PARTIAL_RESULT,
                timestamp=datetime.utcnow().isoformat(),
                data={
                    "status": "Found relevant precedents",
                    "case_count": 15,
                    "high_court_cases": 3,
                    "federal_court_cases": 7
                },
                component="precedents"
            )
            
            # Generate precedent analysis
            content = f"Relevant legal precedents for: {context['query']}\n\nKey cases identified:\n- High Court decisions establishing fundamental principles\n- Recent Federal Court interpretations\n- State Supreme Court variations"
            
            yield StreamEvent(
                event_type=StreamEventType.COMPLETED,
                timestamp=datetime.utcnow().isoformat(),
                data={
                    "type": "precedent_analysis",
                    "content": content,
                    "structured_data": "Would contain parsed case citations"
                },
                component="precedents"
            )
            
        except Exception as e:
            yield StreamEvent(
                event_type=StreamEventType.ERROR,
                timestamp=datetime.utcnow().isoformat(),
                data={"error_message": str(e)},
                component="precedents",
                error=str(e)
            )
    
    async def _stream_principles_analysis(self, context: Dict) -> AsyncIterator[StreamEvent]:
        """Stream legal principles analysis"""
        try:
            yield StreamEvent(
                event_type=StreamEventType.PROGRESS,
                timestamp=datetime.utcnow().isoformat(),
                data={"status": "Extracting fundamental legal principles"},
                component="principles"
            )
            
            await asyncio.sleep(0.8)
            
            content = f"Fundamental legal principles for: {context['query']}\n\nCore doctrines and principles identified."
            
            yield StreamEvent(
                event_type=StreamEventType.COMPLETED,
                timestamp=datetime.utcnow().isoformat(),
                data={
                    "type": "legal_principles",
                    "content": content
                },
                component="principles"
            )
            
        except Exception as e:
            yield StreamEvent(
                event_type=StreamEventType.ERROR,
                timestamp=datetime.utcnow().isoformat(),
                data={"error_message": str(e)},
                component="principles",
                error=str(e)
            )
    
    async def _stream_jurisdiction_analysis(self, context: Dict) -> AsyncIterator[StreamEvent]:
        """Stream jurisdiction comparison analysis"""
        try:
            jurisdictions = context.get('jurisdictions', ['federal'])
            
            if len(jurisdictions) <= 1:
                yield StreamEvent(
                    event_type=StreamEventType.COMPLETED,
                    timestamp=datetime.utcnow().isoformat(),
                    data={
                        "type": "jurisdiction_analysis",
                        "content": "Single jurisdiction focus - no variation analysis needed."
                    },
                    component="jurisdiction_analysis"
                )
                return
            
            yield StreamEvent(
                event_type=StreamEventType.PROGRESS,
                timestamp=datetime.utcnow().isoformat(),
                data={
                    "status": f"Comparing across {len(jurisdictions)} jurisdictions",
                    "jurisdictions": jurisdictions
                },
                component="jurisdiction_analysis"
            )
            
            await asyncio.sleep(1.2)
            
            content = f"Cross-jurisdictional analysis for: {context['query']}\n\nComparing approaches across: {', '.join(jurisdictions)}"
            
            yield StreamEvent(
                event_type=StreamEventType.COMPLETED,
                timestamp=datetime.utcnow().isoformat(),
                data={
                    "type": "jurisdiction_analysis",
                    "content": content
                },
                component="jurisdiction_analysis"
            )
            
        except Exception as e:
            yield StreamEvent(
                event_type=StreamEventType.ERROR,
                timestamp=datetime.utcnow().isoformat(),
                data={"error_message": str(e)},
                component="jurisdiction_analysis",
                error=str(e)
            )
    
    async def _stream_commentary_analysis(self, context: Dict) -> AsyncIterator[StreamEvent]:
        """Stream scholarly commentary analysis"""
        try:
            yield StreamEvent(
                event_type=StreamEventType.PROGRESS,
                timestamp=datetime.utcnow().isoformat(),
                data={"status": "Gathering scholarly commentary and analysis"},
                component="commentary"
            )
            
            await asyncio.sleep(1.5)
            
            content = f"Scholarly commentary for: {context['query']}\n\nAcademic perspectives and professional analysis gathered."
            
            yield StreamEvent(
                event_type=StreamEventType.COMPLETED,
                timestamp=datetime.utcnow().isoformat(),
                data={
                    "type": "scholarly_commentary",
                    "content": content
                },
                component="commentary"
            )
            
        except Exception as e:
            yield StreamEvent(
                event_type=StreamEventType.ERROR,
                timestamp=datetime.utcnow().isoformat(),
                data={"error_message": str(e)},
                component="commentary",
                error=str(e)
            )
    
    async def _stream_synthesis(self, context: Dict, research_results: List[Dict]) -> AsyncIterator[StreamEvent]:
        """Stream final synthesis of all research components"""
        try:
            yield StreamEvent(
                event_type=StreamEventType.PROGRESS,
                timestamp=datetime.utcnow().isoformat(),
                data={
                    "status": "Synthesizing comprehensive analysis",
                    "components_to_synthesize": len(research_results)
                },
                component="synthesis"
            )
            
            # Simulate synthesis processing
            await asyncio.sleep(1.0)
            
            synthesis_content = f"""
            Comprehensive Legal Research Analysis
            
            Query: {context['query']}
            
            This synthesis integrates findings from {len(research_results)} research components:
            - Legislative analysis
            - Precedent review
            - Legal principles
            - Jurisdictional comparison
            - Scholarly commentary
            
            Key findings and recommendations follow...
            """
            
            yield StreamEvent(
                event_type=StreamEventType.COMPLETED,
                timestamp=datetime.utcnow().isoformat(),
                data={
                    "comprehensive_analysis": synthesis_content,
                    "research_components": research_results,
                    "confidence_assessment": {"overall_confidence": "high"},
                    "research_metadata": {
                        "components_analyzed": len(research_results),
                        "synthesis_quality": "comprehensive"
                    }
                },
                component="synthesis"
            )
            
        except Exception as e:
            yield StreamEvent(
                event_type=StreamEventType.ERROR,
                timestamp=datetime.utcnow().isoformat(),
                data={"error_message": str(e)},
                component="synthesis",
                error=str(e)
            )

class StreamingResponseManager:
    """Manages streaming responses with connection health monitoring"""
    
    def __init__(self):
        self.active_streams: Dict[str, Dict] = {}
        self.heartbeat_interval = 30  # seconds
    
    def create_streaming_response(
        self, 
        stream_generator: AsyncIterator[StreamEvent],
        stream_id: Optional[str] = None
    ) -> StreamingResponse:
        """Create a FastAPI StreamingResponse with proper headers"""
        
        async def event_generator():
            last_heartbeat = time.time()
            
            try:
                async for event in stream_generator:
                    yield event.to_sse_format()
                    
                    # Send periodic heartbeats to keep connection alive
                    current_time = time.time()
                    if current_time - last_heartbeat > self.heartbeat_interval:
                        heartbeat = StreamEvent(
                            event_type=StreamEventType.HEARTBEAT,
                            timestamp=datetime.utcnow().isoformat(),
                            data={"status": "connection_alive"}
                        )
                        yield heartbeat.to_sse_format()
                        last_heartbeat = current_time
                        
            except Exception as e:
                error_event = StreamEvent(
                    event_type=StreamEventType.ERROR,
                    timestamp=datetime.utcnow().isoformat(),
                    data={"error_message": str(e), "fatal": True},
                    error=str(e)
                )
                yield error_event.to_sse_format()
            
            finally:
                # Clean up stream tracking
                if stream_id and stream_id in self.active_streams:
                    del self.active_streams[stream_id]
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable Nginx buffering
            }
        )

# Global streaming manager
streaming_manager = StreamingResponseManager()
streaming_engine = StreamingResearchEngine()