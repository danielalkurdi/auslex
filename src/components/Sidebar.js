import React, { useState, useCallback } from 'react';
import { Plus, Settings, BookOpen, Check, X, LogIn, LogOut, User } from 'lucide-react';
import PropTypes from 'prop-types';

// Bootstrap Icons as React components
const LayoutSidebarInsetReverseIcon = ({ size = 20, className = "" }) => (
  <svg width={size} height={size} fill="currentColor" className={className} viewBox="0 0 16 16">
    <path d="M2 2a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V3a1 1 0 0 0-1-1H2zm12-1a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V3a2 2 0 0 1 2-2h12zM13 4a1 1 0 0 1 1 1v6a1 1 0 0 1-1 1V4z"/>
  </svg>
);

const ArrowsExpandVerticalIcon = ({ size = 20, className = "" }) => (
  <svg width={size} height={size} fill="currentColor" className={className} viewBox="0 0 16 16">
    <path fillRule="evenodd" d="m7.646 4.646-3 3a.5.5 0 0 0 .708.708L8 5.707l2.646 2.647a.5.5 0 0 0 .708-.708l-3-3a.5.5 0 0 0-.708 0zM8 10.293 5.354 7.646a.5.5 0 1 0-.708.708l3 3a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8 10.293z"/>
  </svg>
);

const PencilSquareIcon = ({ size = 16, className = "" }) => (
  <svg width={size} height={size} fill="currentColor" className={className} viewBox="0 0 16 16">
    <path d="M15.502 1.94a.5.5 0 0 1 0 .706L14.459 3.69l-2-2L13.502.646a.5.5 0 0 1 .707 0l1.293 1.293zm-1.75 2.456-2-2L4.939 9.21a.5.5 0 0 0-.121.196l-.805 2.414a.25.25 0 0 0 .316.316l2.414-.805a.5.5 0 0 0 .196-.12l6.813-6.814z"/>
    <path fillRule="evenodd" d="M1 13.5A1.5 1.5 0 0 0 2.5 15h11a1.5 1.5 0 0 0 1.5-1.5v-6a.5.5 0 0 0-1 0v6a.5.5 0 0 1-.5.5h-11a.5.5 0 0 1-.5-.5v-11a.5.5 0 0 1 .5-.5H9a.5.5 0 0 0 0-1H2.5A1.5 1.5 0 0 0 1 2.5v11z"/>
  </svg>
);

const Trash3Icon = ({ size = 16, className = "" }) => (
  <svg width={size} height={size} fill="currentColor" className={className} viewBox="0 0 16 16">
    <path d="M6.5 1h3a.5.5 0 0 1 .5.5v1H6v-1a.5.5 0 0 1 .5-.5ZM11 2.5v-1A1.5 1.5 0 0 0 9.5 0h-3A1.5 1.5 0 0 0 5 1.5v1H2.506a.58.58 0 0 0-.01 0H1.5a.5.5 0 0 0 0 1h.538l.853 10.66A2 2 0 0 0 4.885 16h6.23a2 2 0 0 0 1.994-1.84l.853-10.66h.538a.5.5 0 0 0 0-1h-.995a.59.59 0 0 0-.01 0H11Zm1.958 1-.846 10.58a1 1 0 0 1-.997.92h-6.23a1 1 0 0 1-.997-.92L3.042 3.5h9.916Zm-7.487 1a.5.5 0 0 1 .528.47l.5 8.5a.5.5 0 0 1-.998.06L5 5.03a.5.5 0 0 1 .47-.53Zm5.058 0a.5.5 0 0 1 .47.53l-.5 8.5a.5.5 0 1 1-.998-.06l.5-8.5a.5.5 0 0 1 .528-.47ZM8 4.5a.5.5 0 0 1 .5.5v8.5a.5.5 0 0 1-1 0V5a.5.5 0 0 1 .5-.5Z"/>
  </svg>
);

const Sidebar = React.memo(({
  isCollapsed,
  setIsCollapsed,
  chats,
  activeChatId,
  onNewChat,
  onSelectChat,
  onDeleteChat,
  onSaveChat,
  onSettingsClick,
  onAboutClick,
  user,
  isAuthenticated,
  onAuthClick,
  onLogout,
  isMobile,
  isMobileSidebarOpen,
  setIsMobileSidebarOpen,
}) => {
  const [editingChatId, setEditingChatId] = useState(null);
  const [editingTitle, setEditingTitle] = useState('');

  const handleEdit = useCallback((chat) => {
    setEditingChatId(chat.id);
    setEditingTitle(chat.title);
  }, []);

  const handleSave = useCallback((e) => {
    e.stopPropagation();
    onSaveChat(editingChatId, editingTitle);
    setEditingChatId(null);
  }, [editingChatId, editingTitle, onSaveChat]);

  const handleCancel = useCallback((e) => {
    e.stopPropagation();
    setEditingChatId(null);
  }, []);

  const handleDelete = useCallback((e, chatId) => {
    e.stopPropagation();
    onDeleteChat(chatId);
  }, [onDeleteChat]);

  return (
    <div className={`bg-background-secondary transition-all duration-300 ease-in-out flex flex-col h-full
      ${isMobile ? 'fixed left-0 top-0 z-50 w-64' : 'fixed'}
      ${isMobile && !isMobileSidebarOpen ? '-translate-x-full' : 'translate-x-0'}
      ${!isMobile && isCollapsed ? 'w-16' : 'w-64'}`}>
      
      <div className="flex items-center justify-between p-4 border-b border-border-subtle h-20">
        {(isMobile || !isCollapsed) && (
          <div className="flex items-center gap-2">
            <img src="/logo.svg" alt="AusLex Logo" className="w-6 h-6" />
            <h1 className="text-lg font-semibold">AusLex</h1>
          </div>
        )}
        {!isMobile && isCollapsed && (
          <div className="group relative w-full flex justify-center">
            <img src="/logo.svg" alt="AusLex Logo" className="w-6 h-6 cursor-pointer" onClick={() => setIsCollapsed(false)} />
            <button 
              onClick={() => setIsCollapsed(false)}
              className="absolute inset-0 opacity-0 group-hover:opacity-100 flex items-center justify-center text-accent transition-opacity duration-200"
              aria-label="Expand sidebar"
            >
              <ArrowsExpandVerticalIcon size={16} />
            </button>
          </div>
        )}
        {isMobile ? (
          <button
            onClick={() => setIsMobileSidebarOpen(false)}
            className="p-1 hover:text-accent md:hidden"
            aria-label="Close sidebar"
          >
            <X size={20} />
          </button>
        ) : (
          !isCollapsed && (
            <button 
              onClick={() => setIsCollapsed(true)} 
              className="p-1 hover:text-accent"
              aria-label="Collapse sidebar"
              aria-expanded={!isCollapsed}
            >
              <LayoutSidebarInsetReverseIcon />
            </button>
          )
        )}
      </div>

      <div className="p-2">
        <button 
          onClick={() => {
            if (!isMobile && isCollapsed) {
              setIsCollapsed(false);
            }
            onNewChat();
            if (isMobile) {
              setIsMobileSidebarOpen(false);
            }
          }} 
          className={`w-full flex items-center p-2 rounded hover:bg-border-subtle ${
            !isMobile && isCollapsed ? 'justify-center' : 'gap-2'
          }`}
          aria-label="Start new chat"
        >
          <Plus size={20} />
          {(isMobile || !isCollapsed) && <span>New Chat</span>}
        </button>
      </div>

      <nav className="flex-1 overflow-y-auto p-2 space-y-1">
        {(isMobile || !isCollapsed) && (
          <>
            <span className="px-2 text-xs font-semibold text-text-placeholder">History</span>
            {chats.map(chat => (
          <div key={chat.id} className={`group flex items-center justify-between p-2 rounded cursor-pointer
            ${activeChatId === chat.id ? 'bg-border-subtle' : 'hover:bg-border-subtle'}`}
            onClick={() => onSelectChat(chat.id)}>

            {editingChatId === chat.id ? (
              <input 
                type="text"
                value={editingTitle}
                onChange={(e) => setEditingTitle(e.target.value)}
                className="bg-transparent w-full outline-none"
                autoFocus
                aria-label="Edit chat title"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleSave(e);
                  if (e.key === 'Escape') handleCancel(e);
                }}
              />
            ) : (
              <span className="truncate">{chat.title}</span>
            )}
            
            {!isCollapsed && (
              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 focus-within:opacity-100">
                {editingChatId === chat.id ? (
                  <>
                    <button 
                      onClick={handleSave} 
                      className="p-1 hover:text-status-success"
                      aria-label="Save title"
                      tabIndex={0}
                    >
                      <Check size={16} />
                    </button>
                    <button 
                      onClick={handleCancel} 
                      className="p-1 hover:text-status-warning"
                      aria-label="Cancel editing"
                      tabIndex={0}
                    >
                      <X size={16} />
                    </button>
                  </>
                ) : (
                  <>
                    <button 
                      onClick={(e) => {e.stopPropagation(); handleEdit(chat)}} 
                      className="p-1 hover:text-accent"
                      aria-label={`Edit ${chat.title}`}
                      tabIndex={0}
                    >
                      <PencilSquareIcon size={16} />
                    </button>
                    <button 
                      onClick={(e) => handleDelete(e, chat.id)} 
                      className="p-1 hover:text-status-warning"
                      aria-label={`Delete ${chat.title}`}
                      tabIndex={0}
                    >
                      <Trash3Icon size={16} />
                    </button>
                  </>
                )}
              </div>
            )}
          </div>
            ))}
          </>
        )}
      </nav>

      <div className="p-2 border-t border-border-subtle">
        <button 
          onClick={onAboutClick} 
          className="w-full flex items-center gap-2 p-2 rounded hover:bg-border-subtle"
          aria-label="About AusLex"
        >
          <BookOpen size={20} />
          {!isCollapsed && <span>About</span>}
        </button>
        <button 
          onClick={onSettingsClick} 
          className="w-full flex items-center gap-2 p-2 rounded hover:bg-border-subtle"
          aria-label="Open settings"
        >
          <Settings size={20} />
          {!isCollapsed && <span>Settings</span>}
        </button>
        
        {/* Authentication Section */}
        {isAuthenticated ? (
          <>
            {!isCollapsed && (
              <div className="px-2 py-1 border-t border-border-subtle mt-2 pt-3">
                <div className="flex items-center gap-2 p-2 text-text-placeholder text-sm">
                  <User size={16} />
                  <span className="truncate">{user?.name}</span>
                </div>
              </div>
            )}
            <button 
              onClick={onLogout} 
              className="w-full flex items-center gap-2 p-2 rounded hover:bg-border-subtle text-status-warning hover:text-status-warning"
              aria-label="Sign out"
            >
              <LogOut size={20} />
              {!isCollapsed && <span>Sign Out</span>}
            </button>
          </>
        ) : (
          <button 
            onClick={onAuthClick} 
            className="w-full flex items-center gap-2 p-2 rounded hover:bg-border-subtle text-accent hover:text-accent-focus"
            aria-label="Sign in"
          >
            <LogIn size={20} />
            {!isCollapsed && <span>Sign In</span>}
          </button>
        )}
      </div>
    </div>
  );
});

Sidebar.propTypes = {
  isCollapsed: PropTypes.bool.isRequired,
  setIsCollapsed: PropTypes.func.isRequired,
  chats: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      title: PropTypes.string.isRequired,
      timestamp: PropTypes.string.isRequired
    })
  ).isRequired,
  activeChatId: PropTypes.string,
  onNewChat: PropTypes.func.isRequired,
  onSelectChat: PropTypes.func.isRequired,
  onDeleteChat: PropTypes.func.isRequired,
  onSaveChat: PropTypes.func.isRequired,
  onSettingsClick: PropTypes.func.isRequired,
  onAboutClick: PropTypes.func.isRequired,
  user: PropTypes.object,
  isAuthenticated: PropTypes.bool.isRequired,
  onAuthClick: PropTypes.func.isRequired,
  onLogout: PropTypes.func.isRequired
};

Sidebar.displayName = 'Sidebar';

export default Sidebar;
