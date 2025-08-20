import React, { useState, useEffect, useRef } from 'react';
import { Users, Share2, MessageCircle, FileText, Plus, UserPlus, Settings, Video } from 'lucide-react';

const CollaborationPanel = ({ onClose, currentUser }) => {
  const [activeWorkspace, setActiveWorkspace] = useState(null);
  const [workspaces, setWorkspaces] = useState([]);
  const [activeParticipants, setActiveParticipants] = useState([]);
  const [sharedDocuments, setSharedDocuments] = useState([]);
  const [annotations, setAnnotations] = useState([]);
  const [collaborationSocket, setCollaborationSocket] = useState(null);
  const [isCreatingWorkspace, setIsCreatingWorkspace] = useState(false);
  const [newWorkspaceName, setNewWorkspaceName] = useState('');
  const [inviteEmail, setInviteEmail] = useState('');
  const [activeTab, setActiveTab] = useState('workspace');

  const socketRef = useRef(null);

  // Mock collaboration data for demonstration
  const mockWorkspaces = [
    {
      workspace_id: '1',
      name: 'Corporate Merger Analysis',
      description: 'Due diligence for ABC Corp acquisition',
      owner_id: 'user_1',
      participants: [
        { user_id: 'user_1', name: 'Sarah Chen', role: 'partner', status: 'active' },
        { user_id: 'user_2', name: 'Michael Rodriguez', role: 'associate', status: 'active' },
        { user_id: 'user_3', name: 'Jennifer Kim', role: 'paralegal', status: 'away' }
      ],
      shared_documents: [
        { document_id: '1', title: 'Due Diligence Checklist', type: 'checklist', shared_by_name: 'Sarah Chen' },
        { document_id: '2', title: 'Regulatory Compliance Analysis', type: 'legal_memo', shared_by_name: 'Michael Rodriguez' }
      ],
      annotations: [
        { annotation_id: '1', document_id: '2', user_name: 'Jennifer Kim', content: 'Need to verify ACCC requirements', type: 'question' }
      ]
    },
    {
      workspace_id: '2', 
      name: 'Employment Law Updates',
      description: 'Tracking recent changes in Fair Work legislation',
      owner_id: 'user_1',
      participants: [
        { user_id: 'user_1', name: 'Sarah Chen', role: 'partner', status: 'active' },
        { user_id: 'user_4', name: 'David Thompson', role: 'associate', status: 'busy' }
      ],
      shared_documents: [
        { document_id: '3', title: 'Fair Work Amendment Analysis', type: 'legal_memo', shared_by_name: 'David Thompson' }
      ],
      annotations: []
    }
  ];

  useEffect(() => {
    // Initialize with mock data
    setWorkspaces(mockWorkspaces);
    if (mockWorkspaces.length > 0) {
      setActiveWorkspace(mockWorkspaces[0]);
      setActiveParticipants(mockWorkspaces[0].participants);
      setSharedDocuments(mockWorkspaces[0].shared_documents);
      setAnnotations(mockWorkspaces[0].annotations);
    }

    // In a real implementation, establish WebSocket connection here
    // const socket = new WebSocket('ws://localhost:8000/ws/collaboration');
    // setCollaborationSocket(socket);
    
    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, []);

  const handleCreateWorkspace = () => {
    if (!newWorkspaceName.trim()) return;

    const newWorkspace = {
      workspace_id: Date.now().toString(),
      name: newWorkspaceName,
      description: '',
      owner_id: currentUser?.id || 'user_1',
      participants: [{
        user_id: currentUser?.id || 'user_1',
        name: currentUser?.name || 'Current User',
        role: 'partner',
        status: 'active'
      }],
      shared_documents: [],
      annotations: []
    };

    setWorkspaces(prev => [...prev, newWorkspace]);
    setActiveWorkspace(newWorkspace);
    setActiveParticipants(newWorkspace.participants);
    setSharedDocuments([]);
    setAnnotations([]);
    setIsCreatingWorkspace(false);
    setNewWorkspaceName('');
  };

  const handleInviteUser = () => {
    if (!inviteEmail.trim()) return;
    
    // Mock invite - in real implementation, would send invitation
    console.log('Inviting user:', inviteEmail);
    setInviteEmail('');
  };

  const getRoleColor = (role) => {
    switch (role) {
      case 'partner': return 'text-accent-gold';
      case 'associate': return 'text-blue-400';
      case 'paralegal': return 'text-green-400';
      case 'client': return 'text-purple-400';
      default: return 'text-text-secondary';
    }
  };

  const getStatusIndicator = (status) => {
    const colors = {
      active: 'bg-green-500',
      away: 'bg-yellow-500',
      busy: 'bg-red-500'
    };
    return colors[status] || 'bg-gray-500';
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-background-primary rounded-lg shadow-2xl w-full max-w-7xl h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border-primary">
          <div className="flex items-center space-x-3">
            <Users className="w-6 h-6 text-accent-gold" />
            <h2 className="text-xl font-semibold">Legal Collaboration</h2>
          </div>
          <button
            onClick={onClose}
            className="text-text-secondary hover:text-text-primary transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="flex-1 flex overflow-hidden">
          {/* Workspace Sidebar */}
          <div className="w-80 border-r border-border-primary flex flex-col">
            {/* Workspace List */}
            <div className="p-4 border-b border-border-primary">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-medium">Workspaces</h3>
                <button
                  onClick={() => setIsCreatingWorkspace(true)}
                  className="p-1 text-text-secondary hover:text-accent-gold transition-colors"
                  title="Create workspace"
                >
                  <Plus className="w-5 h-5" />
                </button>
              </div>

              <div className="space-y-2 max-h-40 overflow-y-auto">
                {workspaces.map(workspace => (
                  <button
                    key={workspace.workspace_id}
                    onClick={() => {
                      setActiveWorkspace(workspace);
                      setActiveParticipants(workspace.participants);
                      setSharedDocuments(workspace.shared_documents);
                      setAnnotations(workspace.annotations);
                    }}
                    className={`w-full text-left p-3 rounded-lg transition-colors ${
                      activeWorkspace?.workspace_id === workspace.workspace_id
                        ? 'bg-accent-gold/10 text-accent-gold'
                        : 'hover:bg-background-secondary text-text-primary'
                    }`}
                  >
                    <div className="font-medium text-sm">{workspace.name}</div>
                    <div className="text-xs text-text-muted mt-1">
                      {workspace.participants.length} participants
                    </div>
                  </button>
                ))}
              </div>

              {isCreatingWorkspace && (
                <div className="mt-4 space-y-3">
                  <input
                    type="text"
                    value={newWorkspaceName}
                    onChange={(e) => setNewWorkspaceName(e.target.value)}
                    placeholder="Workspace name"
                    className="w-full px-3 py-2 bg-background-secondary border border-border-primary rounded-md text-sm"
                    onKeyPress={(e) => e.key === 'Enter' && handleCreateWorkspace()}
                  />
                  <div className="flex space-x-2">
                    <button
                      onClick={handleCreateWorkspace}
                      className="px-3 py-1 bg-accent-gold text-surface-dark text-sm rounded-md hover:bg-accent-gold/90"
                    >
                      Create
                    </button>
                    <button
                      onClick={() => setIsCreatingWorkspace(false)}
                      className="px-3 py-1 text-text-secondary text-sm hover:text-text-primary"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Active Participants */}
            <div className="p-4 flex-1 overflow-y-auto">
              <div className="flex items-center justify-between mb-4">
                <h4 className="font-medium text-sm">Active Participants</h4>
                <button
                  className="p-1 text-text-secondary hover:text-accent-gold transition-colors"
                  title="Invite user"
                >
                  <UserPlus className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-3">
                {activeParticipants.map(participant => (
                  <div key={participant.user_id} className="flex items-center space-x-3">
                    <div className="relative">
                      <div className="w-8 h-8 bg-accent-gold/20 rounded-full flex items-center justify-center">
                        <span className="text-xs font-medium text-accent-gold">
                          {participant.name.split(' ').map(n => n[0]).join('')}
                        </span>
                      </div>
                      <div className={`absolute -bottom-1 -right-1 w-3 h-3 rounded-full border-2 border-background-primary ${getStatusIndicator(participant.status)}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-text-primary truncate">
                        {participant.name}
                      </div>
                      <div className={`text-xs capitalize ${getRoleColor(participant.role)}`}>
                        {participant.role}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Invite User */}
              <div className="mt-6">
                <input
                  type="email"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  placeholder="Invite by email..."
                  className="w-full px-3 py-2 bg-background-secondary border border-border-primary rounded-md text-sm"
                  onKeyPress={(e) => e.key === 'Enter' && handleInviteUser()}
                />
              </div>
            </div>
          </div>

          {/* Main Collaboration Area */}
          <div className="flex-1 flex flex-col">
            {activeWorkspace ? (
              <>
                {/* Workspace Header */}
                <div className="p-6 border-b border-border-primary">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-medium">{activeWorkspace.name}</h3>
                      <p className="text-text-secondary text-sm mt-1">
                        {activeWorkspace.description || 'No description'}
                      </p>
                    </div>
                    <div className="flex items-center space-x-2">
                      <button className="p-2 text-text-secondary hover:text-accent-gold transition-colors" title="Video call">
                        <Video className="w-5 h-5" />
                      </button>
                      <button className="p-2 text-text-secondary hover:text-accent-gold transition-colors" title="Settings">
                        <Settings className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                  
                  <div className="flex space-x-1 mt-4">
                    {['workspace', 'documents', 'annotations'].map(tab => (
                      <button
                        key={tab}
                        onClick={() => setActiveTab(tab)}
                        className={`px-4 py-2 text-sm rounded-md transition-colors capitalize ${
                          activeTab === tab
                            ? 'bg-accent-gold text-surface-dark'
                            : 'text-text-secondary hover:text-text-primary hover:bg-background-secondary'
                        }`}
                      >
                        {tab}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Workspace Content */}
                <div className="flex-1 p-6 overflow-y-auto">
                  {activeTab === 'workspace' && (
                    <div className="space-y-6">
                      <div>
                        <h4 className="font-medium mb-3">Recent Activity</h4>
                        <div className="space-y-3">
                          <div className="flex items-center space-x-3 p-3 bg-background-secondary rounded-lg">
                            <FileText className="w-5 h-5 text-blue-400" />
                            <div className="flex-1">
                              <div className="text-sm text-text-primary">
                                <span className="font-medium">Michael Rodriguez</span> shared 
                                <span className="text-accent-gold"> Regulatory Compliance Analysis</span>
                              </div>
                              <div className="text-xs text-text-muted">2 hours ago</div>
                            </div>
                          </div>
                          
                          <div className="flex items-center space-x-3 p-3 bg-background-secondary rounded-lg">
                            <MessageCircle className="w-5 h-5 text-green-400" />
                            <div className="flex-1">
                              <div className="text-sm text-text-primary">
                                <span className="font-medium">Jennifer Kim</span> added annotation to 
                                <span className="text-accent-gold"> Due Diligence Checklist</span>
                              </div>
                              <div className="text-xs text-text-muted">4 hours ago</div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {activeTab === 'documents' && (
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <h4 className="font-medium">Shared Documents</h4>
                        <button className="px-3 py-2 bg-accent-gold text-surface-dark text-sm rounded-md hover:bg-accent-gold/90 flex items-center space-x-2">
                          <Plus className="w-4 h-4" />
                          <span>Share Document</span>
                        </button>
                      </div>
                      
                      <div className="space-y-3">
                        {sharedDocuments.map(doc => (
                          <div key={doc.document_id} className="p-4 bg-background-secondary rounded-lg hover:bg-background-secondary/80 cursor-pointer transition-colors">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center space-x-3">
                                <FileText className="w-5 h-5 text-accent-gold" />
                                <div>
                                  <div className="font-medium text-text-primary">{doc.title}</div>
                                  <div className="text-xs text-text-muted">
                                    Shared by {doc.shared_by_name} • {doc.type.replace('_', ' ')}
                                  </div>
                                </div>
                              </div>
                              <Share2 className="w-4 h-4 text-text-secondary" />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {activeTab === 'annotations' && (
                    <div className="space-y-4">
                      <h4 className="font-medium">Recent Annotations</h4>
                      
                      <div className="space-y-3">
                        {annotations.map(annotation => (
                          <div key={annotation.annotation_id} className="p-4 bg-background-secondary rounded-lg">
                            <div className="flex items-start space-x-3">
                              <MessageCircle className="w-5 h-5 text-accent-gold mt-0.5" />
                              <div className="flex-1">
                                <div className="flex items-center space-x-2 mb-2">
                                  <span className="font-medium text-text-primary text-sm">
                                    {annotation.user_name}
                                  </span>
                                  <span className="text-xs text-text-muted">
                                    {annotation.type}
                                  </span>
                                </div>
                                <div className="text-sm text-text-primary">{annotation.content}</div>
                              </div>
                            </div>
                          </div>
                        ))}
                        
                        {annotations.length === 0 && (
                          <div className="text-center py-8 text-text-muted">
                            <MessageCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
                            <p>No annotations yet</p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center text-text-secondary">
                <div className="text-center">
                  <Users className="w-16 h-16 mx-auto mb-4 text-accent-gold/50" />
                  <p className="text-lg">Select or create a workspace to start collaborating</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CollaborationPanel;