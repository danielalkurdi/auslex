import React, { useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import PropTypes from 'prop-types';
import CitationText from './CitationText';

const Message = React.memo(({ message }) => {
  const isUser = message.role === 'user';
  const isError = message.isError;

  const markdownStyles = useMemo(() => ({
    p: ({node, ...props}) => <p className="mb-3 last:mb-0" {...props} />,
    // eslint-disable-next-line jsx-a11y/heading-has-content
    h1: ({node, ...props}) => <h1 className="text-xl font-semibold mb-3 text-text-primary" {...props} />,
    // eslint-disable-next-line jsx-a11y/heading-has-content
    h2: ({node, ...props}) => <h2 className="text-lg font-semibold mb-2 text-text-primary" {...props} />,
    // eslint-disable-next-line jsx-a11y/heading-has-content
    h3: ({node, ...props}) => <h3 className="text-base font-semibold mb-2 text-text-primary" {...props} />,
    ul: ({node, ...props}) => <ul className="list-disc pl-4 mb-3 space-y-1" {...props} />,
    ol: ({node, ...props}) => <ol className="list-decimal pl-4 mb-3 space-y-1" {...props} />,
    // eslint-disable-next-line jsx-a11y/anchor-has-content
    a: ({node, ...props}) => <a className="text-accent hover:underline" {...props} />,
    code: ({node, inline, ...props}) => 
      inline ? 
      <code className="bg-border-subtle/20 text-text-primary px-1.5 py-0.5 rounded text-base" {...props} /> :
      <pre className="bg-border-subtle/20 p-3 rounded overflow-x-auto text-base my-3" {...props} />,
    pre: ({node, ...props}) => <div {...props} />
  }), []);

  return (
    <div className={`w-full flex ${isUser ? 'justify-end' : 'justify-start'} animate-fade-in`}>
      <div className={`
        max-w-[80%] font-sans text-base leading-relaxed
        ${isUser 
          ? 'text-text-primary text-right' 
          : 'text-text-secondary text-left'
        }
        ${isError ? 'text-status-warning' : ''}
      `}>
        {isUser || isError ? (
          // For user messages and errors, use regular markdown
          <ReactMarkdown components={markdownStyles} remarkPlugins={[remarkGfm]}>
            {message.content}
          </ReactMarkdown>
        ) : (
          // For assistant messages, use CitationText to handle legal citations
          <CitationText
            text={message.content}
            citationStyle="link"
            className="prose prose-sm max-w-none"
          />
        )}
        {isError && (
          <p className="text-base mt-2 text-status-warning opacity-80">
            There was an issue processing this request. Please try again.
          </p>
        )}
      </div>
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
