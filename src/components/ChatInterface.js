import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { Send, Loader2, Square } from 'lucide-react';
import Message from './Message';
import PropTypes from 'prop-types';

// Typewriter Animation Component
const TypewriterText = ({ messages, className }) => {
  const [currentText, setCurrentText] = useState('');
  const [isTypingComplete, setIsTypingComplete] = useState(false);
  const [showCursor, setShowCursor] = useState(true);
  const typeSpeedRef = useRef(120);

  useEffect(() => {
    if (isTypingComplete) return; // Don't continue typing if complete
    
    const typewriterEffect = () => {
      const targetMessage = messages[0]; // Only use the first message
      
      if (currentText.length < targetMessage.length) {
        // Typing forward
        setCurrentText(targetMessage.substring(0, currentText.length + 1));
      } else {
        // Message complete, stop typing
        setIsTypingComplete(true);
      }
    };

    const timer = setTimeout(typewriterEffect, typeSpeedRef.current);
    return () => clearTimeout(timer);
  }, [currentText, isTypingComplete, messages]);

  useEffect(() => {
    // Cursor blinking effect (continues forever)
    const cursorTimer = setInterval(() => {
      setShowCursor(prev => !prev);
    }, 400);
    
    return () => clearInterval(cursorTimer);
  }, []);

  return (
    <div className="console-container">
      <h1 className={`${className} text-white`}>
        {currentText}
        <span 
          className={`console-underscore ${showCursor ? 'opacity-100' : 'opacity-0'} transition-opacity duration-100`}
        >
          _
        </span>
      </h1>
    </div>
  );
};

// Enhanced welcome message system
const getContextualInfo = () => {
  const timeOfDay = new Date().getHours();
  const dayOfWeek = new Date().getDay();
  const isWeekend = dayOfWeek === 0 || dayOfWeek === 6;
  const userAgent = navigator.userAgent;
  const isMobile = /Mobile|Android|iPhone|iPad/i.test(userAgent);
  const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  const isAustralianTZ = timeZone.includes('Australia');
  
  return { timeOfDay, isWeekend, isMobile, isAustralianTZ };
};

const generateWelcomeMessages = () => {
  const { timeOfDay, isWeekend, isMobile, isAustralianTZ } = getContextualInfo();
  
  const timeGreetings = [
    timeOfDay < 12 ? "Good morning" : timeOfDay < 17 ? "Good afternoon" : "Good evening",
    timeOfDay < 6 ? "Working late" : timeOfDay > 22 ? "Burning the midnight oil" : null
  ].filter(Boolean);

  const contextualMessages = [
    // Time-based messages
    isWeekend ? "Weekend legal research?" : null,
    timeOfDay > 22 || timeOfDay < 6 ? "Legal questions don't keep business hours" : null,
    
    // Location-based messages  
    isAustralianTZ ? "Your Australian legal AI assistant is ready" : "Australian law from anywhere in the world",
    
    // Device-based messages
    isMobile ? "Mobile-friendly legal guidance at your fingertips" : null,
    
    // General encouraging messages
    "Every legal question deserves a thorough answer",
    "Australian law made accessible",
    "Ready to explore Australian legal frameworks",
    "Your digital legal research companion",
    "Where legal expertise meets modern AI",
    "Legal clarity in an often complex system",
  ].filter(Boolean);

  // Create multiple messages for typewriter rotation
  const messages = [];
  
  // Add greeting + message combinations
  if (timeGreetings.length > 0) {
    const greeting = timeGreetings[0];
    const randomMessage = contextualMessages[Math.floor(Math.random() * contextualMessages.length)];
    messages.push(`${greeting}! ${randomMessage}`);
  }
  
  // Add 2-3 more standalone contextual messages
  const shuffled = [...contextualMessages].sort(() => 0.5 - Math.random());
  messages.push(...shuffled.slice(0, 2));
  
  return messages.length > 0 ? messages : ["Ready to help with Australian law"];
};

const InputArea = React.memo(({ inputMessage, setInputMessage, handleSubmit, handleKeyDown, isLoading, textareaRef, isFloating = false }) => (
  <div className={isFloating ? "w-full" : "bg-background-primary pt-4 pb-4 sm:pb-6 sticky bottom-0"}>
    <div className={isFloating ? "w-full" : "w-full max-w-3xl mx-auto px-3 sm:px-4"}>
      <div className="relative" onKeyDown={handleKeyDown}>
        <div className={`
          flex items-center gap-2 sm:gap-3 bg-background-secondary rounded-full px-3 sm:px-5 py-3 sm:py-4 border-1 border-border-subtle focus-within:border-border-secondary transition-colors duration-200
          ${isFloating ? 'shadow-lg' : ''}
        `}>
          <textarea
            ref={textareaRef}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything..."
            className="flex-1 w-full bg-transparent border-none outline-none resize-none appearance-none text-sm sm:text-base text-text-primary placeholder-text-placeholder focus:outline-none focus-visible:outline-none"
            autoFocus
            rows="1"
            disabled={isLoading}
            style={{ maxHeight: '200px' }}
            aria-label="Type your legal question"
          />
          <button
            onClick={handleSubmit}
            className="w-8 h-8 sm:w-10 sm:h-10 flex-shrink-0 rounded-full flex items-center justify-center transition-colors duration-150
                       bg-gray-700 text-white
                       hover:bg-gray-600
                       disabled:bg-disabled-bg disabled:text-disabled-text disabled:cursor-not-allowed"
            disabled={!inputMessage.trim() || isLoading}
            aria-label={isLoading ? 'Processing...' : 'Send message'}
          >
            {isLoading ? <Loader2 className="w-4 h-4 sm:w-5 sm:h-5 animate-slow-spin" /> : <Send className="w-4 h-4 sm:w-5 sm:h-5" />}
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
  textareaRef: PropTypes.object.isRequired,
  isFloating: PropTypes.bool
};

InputArea.displayName = 'InputArea';

const jurisdictions = ['Cth','NSW','VIC','QLD','WA','SA','TAS','NT','ACT','HCA','FCA','FCCA','FCAAFC','NSWCA'];

const ChatInterface = React.memo(({ messages, onSendMessage, isLoading, messagesEndRef, jurisdiction, setJurisdiction, asAt, setAsAt }) => {
  const [inputMessage, setInputMessage] = useState('');
  const textareaRef = useRef(null);
  const [streaming, setStreaming] = useState(true);
  const [controller, setController] = useState(null);
  const [liveSnippets, setLiveSnippets] = useState([]);


  const welcomeMessages = useMemo(() => {
    if (messages.length === 0) {
      return generateWelcomeMessages();
    }
    return [];
  }, [messages.length]);



  const handleSubmit = useCallback((e) => {
    e.preventDefault();
    if (inputMessage.trim() && !isLoading) {
      if (streaming && window?.ReadableStream) {
        const abort = new AbortController();
        setController(abort);
        const base = process.env.REACT_APP_API_ENDPOINT || 'http://localhost:8787';
        const url = new URL(base + '/api/ask');
        url.searchParams.set('stream', '1');
        fetch(url.toString(), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: inputMessage, jurisdiction: jurisdiction || undefined, asAt: asAt || undefined }),
          signal: abort.signal
        }).then(async (resp) => {
          if (!resp.ok) throw new Error('stream failed');
          const reader = resp.body.getReader();
          const decoder = new TextDecoder();
          let buffer = '';
          let provisional = '';
          setLiveSnippets([]);
          while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const events = buffer.split('\n\n');
            buffer = events.pop() || '';
            for (const evt of events) {
              const lines = evt.split('\n');
              const type = (lines.find(l=>l.startsWith('event:'))||'').replace('event:','').trim();
              const dataLine = (lines.find(l=>l.startsWith('data:'))||'');
              const dataRaw = dataLine.slice(6);
              try {
                const data = JSON.parse(dataRaw);
                if (type === 'snippets') setLiveSnippets(data);
                if (type === 'delta' && data.proseFragment) provisional += data.proseFragment;
                if (type === 'done') onSendMessage(inputMessage);
              } catch {}
            }
          }
        }).catch(() => {}).finally(() => setController(null));
      } else {
        onSendMessage(inputMessage);
      }
      setInputMessage('');
    }
  }, [inputMessage, isLoading, onSendMessage, streaming, jurisdiction, asAt]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  }, [handleSubmit]);


  return (
    <div className="h-full flex flex-col bg-background-primary">
      <div className="w-full max-w-4xl mx-auto px-3 sm:px-4 pt-4">
        <div className="flex flex-wrap gap-3 items-end mb-2">
          <div>
            <label className="block text-xs text-text-secondary mb-1">Jurisdiction</label>
            <select value={jurisdiction} onChange={e=>setJurisdiction(e.target.value)} className="bg-background-secondary border-1 border-border-subtle rounded px-2 py-1">
              <option value="">All</option>
              {jurisdictions.map(j => <option key={j} value={j}>{j}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-text-secondary mb-1">As at</label>
            <input type="date" value={asAt} onChange={e=>setAsAt(e.target.value)} className="bg-background-secondary border-1 border-border-subtle rounded px-2 py-1" />
          </div>
          {asAt && (
            <span className="text-xs px-2 py-1 bg-yellow-100 text-yellow-800 rounded">time-travel</span>
          )}
        </div>
      </div>
      {messages.length === 0 ? (
        // Empty state with centered input
        <div className="h-full flex flex-col items-center justify-center p-4 sm:p-6 relative">
          {welcomeMessages.length > 0 && (
            <TypewriterText 
              messages={welcomeMessages} 
              className="text-xl sm:text-2xl md:text-3xl font-semibold mb-6 sm:mb-8 min-h-[3rem] px-4"
            />
          )}
          <div className="w-full max-w-2xl px-4">
            <InputArea 
              inputMessage={inputMessage}
              setInputMessage={setInputMessage}
              handleSubmit={handleSubmit}
              handleKeyDown={handleKeyDown}
              isLoading={isLoading}
              textareaRef={textareaRef}
              isFloating={true}
            />
          </div>
        </div>
      ) : (
        // Chat state with messages and bottom input
        <>
          <div className="flex-1 overflow-y-auto">
            <div className="space-y-4 py-4 sm:py-6 max-w-4xl mx-auto w-full px-3 sm:px-4">
              {liveSnippets.length > 0 && (
                <div className="p-2 bg-background-secondary rounded border-1 border-border-subtle">
                  <div className="text-xs text-text-secondary mb-1">Likely sources</div>
                  <ul className="text-sm list-disc pl-5">
                    {liveSnippets.map(s => (
                      <li key={s.id}><a className="text-accent underline" href={s.url} target="_blank" rel="noreferrer">{s.title} {s.provision || s.paragraph || ''}</a></li>
                    ))}
                  </ul>
                </div>
              )}
              {messages.map((message) => (
                <Message key={message.id} message={message} />
               ))}
              {isLoading && (
                <div className="flex justify-start animate-fade-in">
                  <div className="flex items-center gap-2 text-text-placeholder text-base">
                    <Loader2 className="w-4 h-4 animate-slow-spin" />
                    <span>AusLex is thinking...</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>
          
          <InputArea 
            inputMessage={inputMessage}
            setInputMessage={setInputMessage}
            handleSubmit={handleSubmit}
            handleKeyDown={handleKeyDown}
            isLoading={isLoading}
            textareaRef={textareaRef}
            isFloating={false}
          />
          <div className="w-full max-w-4xl mx-auto px-3 sm:px-4 pb-3 flex items-center gap-3">
            <label className="text-xs flex items-center gap-2"><input type="checkbox" checked={streaming} onChange={e=>setStreaming(e.target.checked)} /> Stream answers</label>
            {controller && (
              <button className="text-xs px-2 py-1 rounded bg-red-600 text-white flex items-center gap-1" onClick={()=>{ controller.abort(); setController(null); }}><Square className="w-3 h-3"/> Cancel</button>
            )}
          </div>
        </>
      )}
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
