import React, { useState, useRef, useEffect, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';
import ChatInterface from './components/ChatInterface';
import SettingsPanel from './components/SettingsPanel';
import AboutUs from './components/AboutUs';
import Sidebar from './components/Sidebar';

function App() {
  const [chats, setChats] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
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

  useEffect(() => {
    const savedChats = localStorage.getItem('chats');
    if (savedChats) {
      setChats(JSON.parse(savedChats));
    }
  }, []);

  useEffect(() => {
    localStorage.setItem('chats', JSON.stringify(chats));
  }, [chats]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chats, activeChatId]);
  
  const handleNewChat = useCallback(() => {
    const newChat = {
      id: uuidv4(),
      title: 'New Chat',
      messages: [],
      timestamp: new Date().toISOString(),
    };
    setChats(prev => [newChat, ...prev]);
    setActiveChatId(newChat.id);
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
    if (!message.trim()) return;

    let currentChatId = activeChatId;
    if (!currentChatId) {
      const newChat = {
        id: uuidv4(),
        title: message.substring(0, 30), // Use the first 30 chars of the message as the title
        messages: [],
        timestamp: new Date().toISOString(),
      };
      setChats(prev => [newChat, ...prev]);
      setActiveChatId(newChat.id);
      currentChatId = newChat.id;
    }

    const userMessage = {
      id: uuidv4(),
      content: message,
      role: 'user',
      timestamp: new Date().toISOString(),
    };
    
    setChats(prev => prev.map(chat =>
      chat.id === currentChatId
        ? { ...chat, messages: [...chat.messages, userMessage] }
        : chat
    ));
    setIsLoading(true);

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
      setIsLoading(false);
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
      />
      
      <main className={`flex-1 flex flex-col transition-all duration-300 ease-in-out ${isSidebarCollapsed ? 'ml-16' : 'ml-64'}`}>
        {currentPage === 'chat' ? (
          <ChatInterface
            key={activeChatId} // Force re-mount on chat change
            messages={activeChat ? activeChat.messages : []}
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
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
    </div>
  );
}

export default App;
