import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { Send, Loader2 } from 'lucide-react';
import Message from './Message';
import PropTypes from 'prop-types';

const welcomeMessages = [
  "Ready when you are.",
  "Ask me anything about Australian law.",
  "How can I help you today?",
  "What legal question is on your mind?",
  "Please enter your legal query below.",
];

const InputArea = React.memo(({ inputMessage, setInputMessage, handleSubmit, handleKeyDown, isLoading, textareaRef }) => (
  <div className="bg-background-primary pt-4 pb-6 sticky bottom-0">
    <div className="w-full max-w-3xl mx-auto">
      <div className="relative" onKeyDown={handleKeyDown}>
        <div className="flex items-center gap-2 bg-background-secondary rounded-full p-3 border-1 border-border-subtle focus-within:border-border-secondary transition-colors duration-200">
          <textarea
            ref={textareaRef}
            onInput={(e) => setInputMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything..."
            className="flex-1 w-full bg-transparent border-none outline-none resize-none appearance-none text-text-primary placeholder-text-placeholder focus:outline-none focus-visible:outline-none"
            autoFocus
            rows="1"
            disabled={isLoading}
            style={{ maxHeight: '200px' }}
            aria-label="Type your legal question"
          />
          <button
            onClick={handleSubmit}
            className="w-10 h-10 flex-shrink-0 rounded-full flex items-center justify-center transition-colors duration-150
                       bg-gray-700 text-white
                       hover:bg-gray-600
                       disabled:bg-disabled-bg disabled:text-disabled-text disabled:cursor-not-allowed"
            disabled={!inputMessage.trim() || isLoading}
            aria-label={isLoading ? 'Processing...' : 'Send message'}
          >
            {isLoading ? <Loader2 className="w-5 h-5 animate-slow-spin" /> : <Send className="w-5 h-5" />}
          </button>
        </div>
      </div>
    </div>
  </div>
));

InputArea.propTypes = {
  inputMessage: PropTypes.string.isRequired,
  setInputMessage: PropTypes.func.isRequired,
  handleSubmit: PropTypes.func.isRequired,
  handleKeyDown: PropTypes.func.isRequired,
  isLoading: PropTypes.bool.isRequired,
  textareaRef: PropTypes.object.isRequired
};

InputArea.displayName = 'InputArea';

const ChatInterface = React.memo(({ messages, onSendMessage, isLoading, messagesEndRef }) => {
  const [inputMessage, setInputMessage] = useState('');
  const [welcomeMessage, setWelcomeMessage] = useState('');
  const textareaRef = useRef(null);

  const welcomeMessageMemo = useMemo(() => {
    if (messages.length === 0) {
      return welcomeMessages[Math.floor(Math.random() * welcomeMessages.length)];
    }
    return '';
  }, [messages.length]);

  useEffect(() => {
    setWelcomeMessage(welcomeMessageMemo);
  }, [welcomeMessageMemo]);



  const handleSubmit = useCallback((e) => {
    e.preventDefault();
    if (inputMessage.trim() && !isLoading) {
      onSendMessage(inputMessage);
      setInputMessage('');
      if (textareaRef.current) {
        textareaRef.current.value = '';
      }
    }
  }, [inputMessage, isLoading, onSendMessage]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  }, [handleSubmit]);


  return (
    <div className="h-full flex flex-col bg-background-primary">
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center p-6">
            <h1 className="text-3xl font-semibold text-text-primary">{welcomeMessage}</h1>
          </div>
        ) : (
          <div className="space-y-10 py-8 max-w-3xl mx-auto w-full px-6">
            {messages.map((message, index) => (
              <Message key={`${message.id}-${index}`} message={message} />
            ))}
            {isLoading && (
              <div className="flex items-center gap-3 px-1 animate-fade-in">
                <Loader2 className="w-5 h-5 text-text-placeholder animate-slow-spin" />
                <span className="text-text-placeholder text-sm">AusLex is thinking...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>
      
      <InputArea 
        inputMessage={inputMessage}
        setInputMessage={setInputMessage}
        handleSubmit={handleSubmit}
        handleKeyDown={handleKeyDown}
        isLoading={isLoading}
        textareaRef={textareaRef}
      />
    </div>
  );
});

ChatInterface.propTypes = {
  messages: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      content: PropTypes.string.isRequired,
      role: PropTypes.oneOf(['user', 'assistant']).isRequired,
      timestamp: PropTypes.string.isRequired,
      isError: PropTypes.bool
    })
  ).isRequired,
  onSendMessage: PropTypes.func.isRequired,
  isLoading: PropTypes.bool.isRequired,
  messagesEndRef: PropTypes.object.isRequired
};

ChatInterface.displayName = 'ChatInterface';

export default ChatInterface;
