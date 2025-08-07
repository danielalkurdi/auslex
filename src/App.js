import React, { useState, useRef, useEffect, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';
import ChatInterface from './components/ChatInterface';
import SettingsPanel from './components/SettingsPanel';
import AboutUs from './components/AboutUs';
import Sidebar from './components/Sidebar';
import AuthModal from './components/AuthModal';
import { AuthProvider, useAuth } from './contexts/AuthContext';

function AppContent() {
  const { isAuthenticated, user, login, logout, isLoading, getUserChats, updateUserChats } = useAuth();
  const [chats, setChats] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [currentPage, setCurrentPage] = useState('chat');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [settings, setSettings] = useState({
    apiEndpoint: process.env.REACT_APP_API_ENDPOINT || 'http://localhost:8000',
    maxTokens: 2048,
    temperature: 0.7,
    topP: 0.9,
  });

  const messagesEndRef = useRef(null);
  const sendingRef = useRef(false);

  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      // Load user-specific chats
      const userChats = getUserChats();
      const uniqueChats = userChats.reduce((acc, chat) => {
        if (!acc.some(existing => existing.id === chat.id)) {
          acc.push(chat);
        }
        return acc;
      }, []);
      setChats(uniqueChats);
    } else if (!isAuthenticated && !isLoading) {
      // Clear chats when not authenticated
      setChats([]);
      setActiveChatId(null);
    }
  }, [isAuthenticated, isLoading, getUserChats]);

  useEffect(() => {
    if (isAuthenticated) {
      updateUserChats(chats);
    }
  }, [chats, isAuthenticated, updateUserChats]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chats, activeChatId]);
  
  const handleNewChat = useCallback(() => {
    const newChatId = uuidv4();
    const newChat = {
      id: newChatId,
      title: 'New Chat',
      messages: [],
      timestamp: new Date().toISOString(),
    };
    
    setChats(prev => [newChat, ...prev]);
    setActiveChatId(newChatId);
    setCurrentPage('chat');
  }, []);

  const handleSaveChat = useCallback((chatId, newTitle) => {
    setChats(prev => prev.map(chat => 
      chat.id === chatId ? { ...chat, title: newTitle } : chat
    ));
  }, []);
  
  const handleDeleteChat = useCallback((chatId) => {
    setChats(prev => prev.filter(chat => chat.id !== chatId));
    if (activeChatId === chatId) {
      setActiveChatId(null);
    }
  }, [activeChatId]);

  const handleSelectChat = useCallback((chatId) => {
    setActiveChatId(chatId);
    setCurrentPage('chat');
  }, []);

  const handleSendMessage = async (message) => {
    if (!message.trim() || sendingRef.current) return;
    
    sendingRef.current = true;
    let currentChatId = activeChatId;
    
    // Create new chat if needed
    if (!currentChatId) {
      const newChatId = uuidv4();
      const newChat = {
        id: newChatId,
        title: message.substring(0, 30),
        messages: [],
        timestamp: new Date().toISOString(),
      };
      
      setChats(prev => [newChat, ...prev]);
      setActiveChatId(newChatId);
      currentChatId = newChatId;
    }

    const userMessageId = uuidv4();
    const userMessage = {
      id: userMessageId,
      content: message,
      role: 'user',
      timestamp: new Date().toISOString(),
    };
    
    // Add user message
    setChats(prev => prev.map(chat => 
      chat.id === currentChatId 
        ? { ...chat, messages: [...chat.messages, userMessage] }
        : chat
    ));
    setIsChatLoading(true);

    try {
      const response = await fetch(`${settings.apiEndpoint}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message,
          max_tokens: settings.maxTokens,
          temperature: settings.temperature,
          top_p: settings.topP,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Validate and sanitize API response
      if (!data || typeof data !== 'object') {
        throw new Error('Invalid response format');
      }
      
      const responseContent = data.response || data.message || 'No response received';
      if (typeof responseContent !== 'string') {
        throw new Error('Invalid response content');
      }
      
      const aiMessage = {
        id: uuidv4(),
        content: responseContent,
        role: 'assistant',
        timestamp: new Date().toISOString(),
      };

      setChats(prev => prev.map(chat =>
        chat.id === currentChatId
          ? { ...chat, messages: [...chat.messages, aiMessage] }
          : chat
      ));
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        id: uuidv4(),
        content: 'Sorry, I encountered an error while processing your request. Please try again or check your connection.',
        role: 'assistant',
        timestamp: new Date().toISOString(),
        isError: true,
      };
      
      setChats(prev => prev.map(chat =>
        chat.id === currentChatId
          ? { ...chat, messages: [...chat.messages, errorMessage] }
          : chat
      ));
    } finally {
      setIsChatLoading(false);
      sendingRef.current = false;
    }
  };

  const activeChat = chats.find(chat => chat.id === activeChatId);

  return (
    <div className="flex h-screen bg-background-primary text-text-primary">
      <Sidebar
        isCollapsed={isSidebarCollapsed}
        setIsCollapsed={setIsSidebarCollapsed}
        chats={chats}
        activeChatId={activeChatId}
        onNewChat={handleNewChat}
        onSelectChat={handleSelectChat}
        onDeleteChat={handleDeleteChat}
        onSaveChat={handleSaveChat}
        onSettingsClick={() => setShowSettings(true)}
        onAboutClick={() => setCurrentPage('about')}
        user={user}
        isAuthenticated={isAuthenticated}
        onAuthClick={() => setShowAuthModal(true)}
        onLogout={logout}
      />
      
      <main className={`flex-1 flex flex-col transition-all duration-300 ease-in-out ${isSidebarCollapsed ? 'ml-16' : 'ml-64'}`}>
        {currentPage === 'chat' ? (
          <ChatInterface
            key={activeChatId} // Force re-mount on chat change
            messages={activeChat ? activeChat.messages : []}
            onSendMessage={handleSendMessage}
            isLoading={isChatLoading}
            messagesEndRef={messagesEndRef}
          />
        ) : (
          <AboutUs />
        )}
      </main>

      {showSettings && (
        <SettingsPanel
          settings={settings}
          onSettingsChange={setSettings}
          onClose={() => setShowSettings(false)}
        />
      )}

      {showAuthModal && (
        <AuthModal
          isOpen={showAuthModal}
          onClose={() => setShowAuthModal(false)}
          onAuthSuccess={(userData) => {
            login(userData);
            setShowAuthModal(false);
          }}
        />
      )}
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
