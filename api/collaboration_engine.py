"""
Real-time Collaboration Engine for Legal Research
Enables team collaboration, document sharing, and synchronized research sessions
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import websockets
import logging

logger = logging.getLogger(__name__)

class CollaborationEventType(Enum):
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    RESEARCH_STARTED = "research_started"
    RESEARCH_COMPLETED = "research_completed"
    ANNOTATION_ADDED = "annotation_added"
    DOCUMENT_SHARED = "document_shared"
    COMMENT_ADDED = "comment_added"
    WORKSPACE_UPDATED = "workspace_updated"

@dataclass
class CollaborationUser:
    user_id: str
    name: str
    email: str
    role: str  # "partner", "associate", "paralegal", "client"
    avatar_url: Optional[str] = None
    status: str = "active"  # "active", "away", "busy"
    permissions: Set[str] = None
    
    def __post_init__(self):
        if self.permissions is None:
            self.permissions = self._default_permissions()
    
    def _default_permissions(self) -> Set[str]:
        role_permissions = {
            "partner": {"read", "write", "admin", "share", "delete"},
            "associate": {"read", "write", "share"},
            "paralegal": {"read", "write"},
            "client": {"read", "comment"}
        }
        return role_permissions.get(self.role, {"read"})

@dataclass 
class ResearchWorkspace:
    workspace_id: str
    name: str
    description: str
    owner_id: str
    created_at: datetime
    participants: List[CollaborationUser]
    research_sessions: List[Dict[str, Any]]
    shared_documents: List[Dict[str, Any]]
    annotations: List[Dict[str, Any]]
    access_level: str = "private"  # "private", "team", "public"
    
class CollaborationManager:
    """Manages real-time collaboration sessions and workspaces"""
    
    def __init__(self):
        self.active_sessions: Dict[str, Set[str]] = {}  # workspace_id -> set of user_ids
        self.user_connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.workspaces: Dict[str, ResearchWorkspace] = {}
        self.event_handlers = {
            CollaborationEventType.USER_JOINED: self._handle_user_joined,
            CollaborationEventType.USER_LEFT: self._handle_user_left,
            CollaborationEventType.RESEARCH_STARTED: self._handle_research_started,
            CollaborationEventType.RESEARCH_COMPLETED: self._handle_research_completed,
            CollaborationEventType.ANNOTATION_ADDED: self._handle_annotation_added,
            CollaborationEventType.DOCUMENT_SHARED: self._handle_document_shared,
            CollaborationEventType.COMMENT_ADDED: self._handle_comment_added,
            CollaborationEventType.WORKSPACE_UPDATED: self._handle_workspace_updated,
        }
    
    async def create_workspace(
        self, 
        name: str, 
        description: str, 
        owner: CollaborationUser,
        access_level: str = "private"
    ) -> ResearchWorkspace:
        """Create a new collaborative research workspace"""
        
        workspace_id = str(uuid.uuid4())
        workspace = ResearchWorkspace(
            workspace_id=workspace_id,
            name=name,
            description=description,
            owner_id=owner.user_id,
            created_at=datetime.utcnow(),
            participants=[owner],
            research_sessions=[],
            shared_documents=[],
            annotations=[],
            access_level=access_level
        )
        
        self.workspaces[workspace_id] = workspace
        self.active_sessions[workspace_id] = {owner.user_id}
        
        await self._broadcast_event(workspace_id, {
            "type": CollaborationEventType.WORKSPACE_UPDATED.value,
            "workspace": asdict(workspace),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return workspace
    
    async def join_workspace(self, workspace_id: str, user: CollaborationUser) -> bool:
        """Add user to a collaborative workspace"""
        
        if workspace_id not in self.workspaces:
            return False
        
        workspace = self.workspaces[workspace_id]
        
        # Check permissions
        if not self._can_access_workspace(user, workspace):
            return False
        
        # Add user to participants if not already present
        if not any(p.user_id == user.user_id for p in workspace.participants):
            workspace.participants.append(user)
        
        # Add to active session
        if workspace_id not in self.active_sessions:
            self.active_sessions[workspace_id] = set()
        self.active_sessions[workspace_id].add(user.user_id)
        
        await self._broadcast_event(workspace_id, {
            "type": CollaborationEventType.USER_JOINED.value,
            "user": asdict(user),
            "workspace_id": workspace_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return True
    
    async def leave_workspace(self, workspace_id: str, user_id: str):
        """Remove user from workspace session"""
        
        if workspace_id in self.active_sessions:
            self.active_sessions[workspace_id].discard(user_id)
            
            await self._broadcast_event(workspace_id, {
                "type": CollaborationEventType.USER_LEFT.value,
                "user_id": user_id,
                "workspace_id": workspace_id,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def start_collaborative_research(
        self, 
        workspace_id: str, 
        research_query: str, 
        initiated_by: str
    ) -> str:
        """Start a collaborative research session"""
        
        if workspace_id not in self.workspaces:
            raise ValueError("Workspace not found")
        
        research_session_id = str(uuid.uuid4())
        research_session = {
            "session_id": research_session_id,
            "query": research_query,
            "initiated_by": initiated_by,
            "started_at": datetime.utcnow().isoformat(),
            "status": "active",
            "participants": list(self.active_sessions.get(workspace_id, set())),
            "results": []
        }
        
        self.workspaces[workspace_id].research_sessions.append(research_session)
        
        await self._broadcast_event(workspace_id, {
            "type": CollaborationEventType.RESEARCH_STARTED.value,
            "research_session": research_session,
            "workspace_id": workspace_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return research_session_id
    
    async def add_research_annotation(
        self, 
        workspace_id: str, 
        document_id: str,
        annotation: Dict[str, Any],
        user: CollaborationUser
    ):
        """Add annotation to a research document"""
        
        if workspace_id not in self.workspaces:
            return False
        
        if not self._user_can_annotate(user, self.workspaces[workspace_id]):
            return False
        
        annotation_data = {
            "annotation_id": str(uuid.uuid4()),
            "document_id": document_id,
            "user_id": user.user_id,
            "user_name": user.name,
            "content": annotation["content"],
            "position": annotation.get("position", {}),
            "type": annotation.get("type", "comment"),  # comment, highlight, question
            "created_at": datetime.utcnow().isoformat(),
            "replies": []
        }
        
        self.workspaces[workspace_id].annotations.append(annotation_data)
        
        await self._broadcast_event(workspace_id, {
            "type": CollaborationEventType.ANNOTATION_ADDED.value,
            "annotation": annotation_data,
            "workspace_id": workspace_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return True
    
    async def share_document(
        self, 
        workspace_id: str, 
        document: Dict[str, Any],
        shared_by: CollaborationUser
    ):
        """Share a document with the workspace"""
        
        if workspace_id not in self.workspaces:
            return False
        
        if not self._user_can_share(shared_by, self.workspaces[workspace_id]):
            return False
        
        shared_document = {
            "document_id": str(uuid.uuid4()),
            "title": document["title"],
            "content": document["content"],
            "type": document.get("type", "legal_memo"),
            "shared_by": shared_by.user_id,
            "shared_by_name": shared_by.name,
            "shared_at": datetime.utcnow().isoformat(),
            "access_permissions": document.get("permissions", ["read"]),
            "version": 1
        }
        
        self.workspaces[workspace_id].shared_documents.append(shared_document)
        
        await self._broadcast_event(workspace_id, {
            "type": CollaborationEventType.DOCUMENT_SHARED.value,
            "document": shared_document,
            "workspace_id": workspace_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return shared_document["document_id"]
    
    async def handle_websocket_connection(
        self, 
        websocket: websockets.WebSocketServerProtocol, 
        user_id: str
    ):
        """Handle WebSocket connection for real-time collaboration"""
        
        self.user_connections[user_id] = websocket
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._handle_websocket_message(user_id, data)
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format"
                    }))
                except Exception as e:
                    logger.error(f"Error handling websocket message: {e}")
                    await websocket.send(json.dumps({
                        "type": "error", 
                        "message": "Internal error processing message"
                    }))
        finally:
            # Clean up connection
            if user_id in self.user_connections:
                del self.user_connections[user_id]
            
            # Remove from all active sessions
            for workspace_id in list(self.active_sessions.keys()):
                if user_id in self.active_sessions[workspace_id]:
                    await self.leave_workspace(workspace_id, user_id)
    
    async def _handle_websocket_message(self, user_id: str, data: Dict[str, Any]):
        """Process incoming WebSocket messages"""
        
        message_type = data.get("type")
        if message_type in ["join_workspace", "leave_workspace", "start_research", "add_annotation"]:
            # Route to appropriate handler
            handler = getattr(self, f"_ws_handle_{message_type}", None)
            if handler:
                await handler(user_id, data)
    
    async def _broadcast_event(self, workspace_id: str, event_data: Dict[str, Any]):
        """Broadcast event to all users in workspace"""
        
        if workspace_id not in self.active_sessions:
            return
        
        active_users = self.active_sessions[workspace_id]
        message = json.dumps(event_data)
        
        # Send to all connected users in workspace
        disconnected_users = set()
        for user_id in active_users:
            if user_id in self.user_connections:
                try:
                    await self.user_connections[user_id].send(message)
                except websockets.exceptions.ConnectionClosed:
                    disconnected_users.add(user_id)
        
        # Clean up disconnected users
        for user_id in disconnected_users:
            if user_id in self.user_connections:
                del self.user_connections[user_id]
            self.active_sessions[workspace_id].discard(user_id)
    
    def _can_access_workspace(self, user: CollaborationUser, workspace: ResearchWorkspace) -> bool:
        """Check if user can access workspace"""
        
        # Owner can always access
        if user.user_id == workspace.owner_id:
            return True
        
        # Check access level
        if workspace.access_level == "public":
            return True
        elif workspace.access_level == "team":
            # Would check team membership in production
            return True
        else:  # private
            # Check if user is already a participant
            return any(p.user_id == user.user_id for p in workspace.participants)
    
    def _user_can_annotate(self, user: CollaborationUser, workspace: ResearchWorkspace) -> bool:
        """Check if user can add annotations"""
        return "write" in user.permissions or user.user_id == workspace.owner_id
    
    def _user_can_share(self, user: CollaborationUser, workspace: ResearchWorkspace) -> bool:
        """Check if user can share documents"""
        return "share" in user.permissions or user.user_id == workspace.owner_id
    
    # Event handlers
    async def _handle_user_joined(self, workspace_id: str, event_data: Dict[str, Any]):
        """Handle user joined event"""
        pass
    
    async def _handle_user_left(self, workspace_id: str, event_data: Dict[str, Any]):
        """Handle user left event"""
        pass
    
    async def _handle_research_started(self, workspace_id: str, event_data: Dict[str, Any]):
        """Handle research started event"""
        pass
    
    async def _handle_research_completed(self, workspace_id: str, event_data: Dict[str, Any]):
        """Handle research completed event"""
        pass
    
    async def _handle_annotation_added(self, workspace_id: str, event_data: Dict[str, Any]):
        """Handle annotation added event"""
        pass
    
    async def _handle_document_shared(self, workspace_id: str, event_data: Dict[str, Any]):
        """Handle document shared event"""
        pass
    
    async def _handle_comment_added(self, workspace_id: str, event_data: Dict[str, Any]):
        """Handle comment added event"""
        pass
    
    async def _handle_workspace_updated(self, workspace_id: str, event_data: Dict[str, Any]):
        """Handle workspace updated event"""
        pass

# Global collaboration manager instance
collaboration_manager = CollaborationManager()