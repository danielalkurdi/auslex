import React, { useMemo } from 'react';
import { User, Bot } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import PropTypes from 'prop-types';

const Message = React.memo(({ message }) => {
  const isUser = message.role === 'user';
  const isError = message.isError;

  const Icon = isUser ? User : Bot;
  const authorName = isUser ? "You" : "AusLex";
  
  const containerClasses = `flex items-start gap-4 ${isUser ? 'justify-end' : 'justify-start'}`;
  const bubbleClasses = `bg-background-secondary border-1 rounded p-4 w-auto max-w-full
    ${isUser ? 'border-border-secondary/30' : 'border-border-subtle'}`;
  const errorClasses = isError ? '!border-status-warning/50' : '';

  const markdownStyles = useMemo(() => ({
    p: ({node, ...props}) => <p className="mb-4 last:mb-0" {...props} />,
    // eslint-disable-next-line jsx-a11y/heading-has-content
    h1: ({node, ...props}) => <h1 className="h1 mb-4 border-b border-border-subtle pb-2" {...props} />,
    // eslint-disable-next-line jsx-a11y/heading-has-content
    h2: ({node, ...props}) => <h2 className="h2 mb-3" {...props} />,
    // eslint-disable-next-line jsx-a11y/heading-has-content
    h3: ({node, ...props}) => <h3 className="h3 mb-2" {...props} />,
    ul: ({node, ...props}) => <ul className="list-disc pl-5 mb-4 space-y-2" {...props} />,
    ol: ({node, ...props}) => <ol className="list-decimal pl-5 mb-4 space-y-2" {...props} />,
    // eslint-disable-next-line jsx-a11y/anchor-has-content
    a: ({node, ...props}) => <a className="text-accent hover:underline" {...props} />,
    code: ({node, inline, ...props}) => 
      inline ? 
      <code className="bg-background-primary text-text-secondary px-1 py-0.5 rounded" {...props} /> :
      <pre className="bg-background-primary p-3 rounded overflow-x-auto text-sm" {...props} />,
    pre: ({node, ...props}) => <div {...props} />
  }), []);

  const authorBlock = useMemo(() => (
    <div className="flex items-center gap-3">
      <div 
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${isUser ? 'bg-background-secondary border-1 border-border-secondary/30' : 'bg-background-secondary border-1 border-border-subtle'}`}
        role="img"
        aria-label={`${authorName} avatar`}
      >
        <Icon className={`w-4 h-4 ${isUser ? 'text-text-secondary' : 'text-accent-focus'}`} />
      </div>
      <span className="font-semibold text-text-primary text-base">{authorName}</span>
    </div>
  ), [isUser, authorName]);

  const messageBlock = useMemo(() => (
     <div className={`${bubbleClasses} ${errorClasses} ${isUser ? 'mr-12' : 'ml-12'} mt-2`}>
        <div className={isUser ? 'font-sans' : 'font-serif'}>
          <ReactMarkdown components={markdownStyles} remarkPlugins={[remarkGfm]}>
            {message.content}
          </ReactMarkdown>
        </div>
        {isError && (
          <p className="text-sm mt-3 text-status-warning">
            There was an issue processing this request. Please try again.
          </p>
        )}
      </div>
  ), [bubbleClasses, errorClasses, isUser, markdownStyles, message.content, isError]);

  return (
    <div className={`${containerClasses} animate-fade-in`}>
      {isUser ? (
        <>
          {messageBlock}
          {authorBlock}
        </>
      ) : (
        <>
          {authorBlock}
          {messageBlock}
        </>
      )}
    </div>
  );
});

Message.propTypes = {
  message: PropTypes.shape({
    id: PropTypes.string.isRequired,
    content: PropTypes.string.isRequired,
    role: PropTypes.oneOf(['user', 'assistant']).isRequired,
    timestamp: PropTypes.string.isRequired,
    isError: PropTypes.bool
  }).isRequired
};

Message.displayName = 'Message';

export default Message;
