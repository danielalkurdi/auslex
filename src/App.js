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
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
  const [jurisdiction, setJurisdiction] = useState('');
  const [asAt, setAsAt] = useState('');
    const [settings, setSettings] = useState({
      apiEndpoint: process.env.REACT_APP_API_ENDPOINT || 'http://localhost:8787',
    maxTokens: 2048,
    temperature: 0.7,
    topP: 0.9,
  });

  const messagesEndRef = useRef(null);
  const sendingRef = useRef(false);

  // Handle window resize for mobile detection
  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      // Auto-collapse sidebar on mobile
      if (mobile) {
        setIsSidebarCollapsed(true);
      }
    };

    window.addEventListener('resize', handleResize);
    handleResize(); // Initial check
    return () => window.removeEventListener('resize', handleResize);
  }, []);

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
    // Close mobile sidebar after selection
    if (isMobile) {
      setIsMobileSidebarOpen(false);
    }
  }, [isMobile]);

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
      const response = await fetch(`${settings.apiEndpoint}/api/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: message, jurisdiction: jurisdiction || undefined, asAt: asAt || undefined }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      if (!data || typeof data !== 'object') {
        throw new Error('Invalid response format');
      }
      const responseContent = data?.answer?.answer || 'No answer';
      if (typeof responseContent !== 'string') throw new Error('Invalid response content');

      const aiMessage = {
        id: uuidv4(),
        content: responseContent,
        role: 'assistant',
        timestamp: new Date().toISOString(),
        structured: {
          answer: data?.answer || null,
          snippets: data?.snippets || [],
          asAt: asAt || null,
          jurisdiction: jurisdiction || null
        }
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
    <div className="flex h-screen bg-background-primary text-text-primary relative overflow-hidden">
      {/* Mobile menu button */}
      {isMobile && (
        <button
          onClick={() => setIsMobileSidebarOpen(!isMobileSidebarOpen)}
          className="fixed top-4 left-4 z-50 p-2 bg-background-secondary rounded-lg shadow-lg md:hidden"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
      )}

      {/* Mobile overlay */}
      {isMobile && isMobileSidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={() => setIsMobileSidebarOpen(false)}
        />
      )}

      <Sidebar
        isCollapsed={isSidebarCollapsed}
        setIsCollapsed={setIsSidebarCollapsed}
        chats={chats}
        activeChatId={activeChatId}
        onNewChat={handleNewChat}
        onSelectChat={handleSelectChat}
        onDeleteChat={handleDeleteChat}
        onSaveChat={handleSaveChat}
        onSettingsClick={() => {
          setShowSettings(true);
          setIsMobileSidebarOpen(false);
        }}
        onAboutClick={() => {
          setCurrentPage('about');
          setIsMobileSidebarOpen(false);
        }}
        user={user}
        isAuthenticated={isAuthenticated}
        onAuthClick={() => {
          setShowAuthModal(true);
          setIsMobileSidebarOpen(false);
        }}
        onLogout={logout}
        isMobile={isMobile}
        isMobileSidebarOpen={isMobileSidebarOpen}
        setIsMobileSidebarOpen={setIsMobileSidebarOpen}
      />
      
      <main className={`flex-1 flex flex-col transition-all duration-300 ease-in-out ${!isMobile ? (isSidebarCollapsed ? 'ml-16' : 'ml-64') : 'ml-0'}`}>
        {currentPage === 'chat' ? (
          <ChatInterface
            key={activeChatId} // Force re-mount on chat change
            messages={activeChat ? activeChat.messages : []}
            onSendMessage={handleSendMessage}
            isLoading={isChatLoading}
            messagesEndRef={messagesEndRef}
            jurisdiction={jurisdiction}
            setJurisdiction={setJurisdiction}
            asAt={asAt}
            setAsAt={setAsAt}
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
