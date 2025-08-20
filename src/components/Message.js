import React from 'react';
import PropTypes from 'prop-types';
import MarkdownWithCitations from './MarkdownWithCitations';

const Message = React.memo(({ message }) => {
  const isUser = message.role === 'user';
  const isError = message.isError;

  return (
    <div className={`w-full flex ${isUser ? 'justify-end' : 'justify-start'} animate-fade-in`}>
      <div className={`
        max-w-[90%] sm:max-w-[80%] font-sans text-sm sm:text-base leading-relaxed
        ${isUser 
          ? 'text-text-primary text-right' 
          : 'text-text-secondary text-left'
        }
        ${isError ? 'text-status-warning' : ''}
      `}>
        <MarkdownWithCitations 
          content={message.content}
          citationStyle="link"
          isUser={isUser}
          isError={isError}
          className=""
        />
        {isError && (
          <p className="text-sm sm:text-base mt-2 text-status-warning opacity-80">
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
