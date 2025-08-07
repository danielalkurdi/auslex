import React, { useState, useCallback } from 'react';
import { Plus, Settings, BookOpen, Trash2, Edit2, Check, X, Menu, XCircle } from 'lucide-react';
import PropTypes from 'prop-types';

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
    <div className={`bg-background-secondary transition-all duration-300 ease-in-out flex flex-col fixed h-full
      ${isCollapsed ? 'w-16' : 'w-64'}`}>
      
      <div className="flex items-center justify-between p-4 border-b border-border-subtle h-20">
        {!isCollapsed && <h1 className="text-lg font-semibold">AusLex</h1>}
        <button 
          onClick={() => setIsCollapsed(!isCollapsed)} 
          className="p-1 hover:text-accent"
          aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          aria-expanded={!isCollapsed}
        >
          {isCollapsed ? <Menu /> : <XCircle />}
        </button>
      </div>

      <div className="p-2">
        <button 
          onClick={onNewChat} 
          className="w-full flex items-center gap-2 p-2 rounded hover:bg-border-subtle"
          aria-label="Start new chat"
        >
          <Plus size={20} />
          {!isCollapsed && <span>New Chat</span>}
        </button>
      </div>

      <nav className="flex-1 overflow-y-auto p-2 space-y-1">
        <span className={`px-2 text-xs font-semibold text-text-placeholder ${isCollapsed && 'hidden'}`}>History</span>
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
                      <Edit2 size={16} />
                    </button>
                    <button 
                      onClick={(e) => handleDelete(e, chat.id)} 
                      className="p-1 hover:text-status-warning"
                      aria-label={`Delete ${chat.title}`}
                      tabIndex={0}
                    >
                      <Trash2 size={16} />
                    </button>
                  </>
                )}
              </div>
            )}
          </div>
        ))}
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
  onAboutClick: PropTypes.func.isRequired
};

Sidebar.displayName = 'Sidebar';

export default Sidebar;
