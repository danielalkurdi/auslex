import React, { useMemo, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import PropTypes from 'prop-types';
import { renderableText } from '../utils/citationParser';
import CitationModal from './CitationModal';
import { ExternalLink, FileText, Scale } from 'lucide-react';

/**
 * MarkdownWithCitations - A component that renders markdown content while preserving
 * legal citation functionality. This component processes markdown first, then applies
 * citation detection and styling to text content.
 */
const MarkdownWithCitations = ({ 
  content, 
  className = '', 
  citationStyle = 'link',
  isUser = false,
  isError = false 
}) => {
  const [activeModal, setActiveModal] = React.useState(null);
  const [modalPosition, setModalPosition] = React.useState({ top: 0, left: 0 });

  /**
   * Handle citation click
   */
  const handleCitationClick = useCallback((citation, event) => {
    event.preventDefault();
    const rect = event.target.getBoundingClientRect();
    setModalPosition({
      top: rect.bottom + window.scrollY,
      left: rect.left + window.scrollX
    });
    setActiveModal(citation);
  }, []);

  /**
   * Handle modal close
   */
  const handleModalClose = useCallback(() => {
    setActiveModal(null);
  }, []);

  /**
   * Get citation icon based on type
   */
  const getCitationIcon = useCallback((type) => {
    switch (type) {
      case 'legislation':
        return <FileText className="w-3 h-3" />;
      case 'regulation':
        return <FileText className="w-3 h-3" />;
      case 'case':
        return <Scale className="w-3 h-3" />;
      default:
        return <ExternalLink className="w-3 h-3" />;
    }
  }, []);

  /**
   * Get citation styling classes
   */
  const getCitationClasses = useCallback((citation) => {
    const baseClasses = 'transition-all duration-200 cursor-pointer';
    
    const typeColors = {
      legislation: 'text-blue-600 hover:text-blue-700 border-blue-200 hover:border-blue-300',
      regulation: 'text-green-600 hover:text-green-700 border-green-200 hover:border-green-300', 
      case: 'text-purple-600 hover:text-purple-700 border-purple-200 hover:border-purple-300',
      unknown: 'text-accent hover:text-accent-focus border-accent/30 hover:border-accent/50'
    };
    
    const colors = typeColors[citation.type] || typeColors.unknown;

    switch (citationStyle) {
      case 'button':
        return `${baseClasses} ${colors} bg-transparent hover:bg-current/5 px-1 py-0.5 rounded border border-dashed font-medium`;
      case 'highlight':
        return `${baseClasses} ${colors} bg-current/5 hover:bg-current/10 px-1 rounded font-medium`;
      case 'link':
      default:
        return `${baseClasses} ${colors} underline decoration-dashed underline-offset-2 hover:decoration-solid font-medium`;
    }
  }, [citationStyle]);

  /**
   * Process text content for citations
   */
  const processTextWithCitations = useCallback((text) => {
    if (isUser || isError || typeof text !== 'string') {
      return text;
    }

    const chunks = renderableText(text);
    
    return chunks.map((chunk, index) => {
      if (chunk.type === 'citation') {
        const citation = chunk.citation;
        return (
          <span
            key={`citation-${index}-${citation.id}`}
            className={getCitationClasses(citation)}
            onClick={(e) => handleCitationClick(citation, e)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                handleCitationClick(citation, e);
              }
            }}
            tabIndex={0}
            role="button"
            aria-label={`Open details for ${citation.fullCitation}`}
            title={`${citation.fullCitation} - Click to view details`}
          >
            <span className="inline-flex items-center gap-1">
              {citationStyle === 'button' && getCitationIcon(citation.type)}
              {chunk.content}
            </span>
          </span>
        );
      } else {
        return chunk.content;
      }
    });
  }, [isUser, isError, citationStyle, getCitationClasses, handleCitationClick, getCitationIcon]);

  /**
   * Custom markdown components that handle citations
   */
  const markdownComponents = useMemo(() => ({
    p: ({ node, children, ...props }) => {
      // For assistant messages, process text content for citations
      if (!isUser && !isError) {
        // Extract text content from children
        const textContent = React.Children.toArray(children)
          .map(child => typeof child === 'string' ? child : '')
          .join('');
        
        // If this paragraph contains only text, process it for citations
        if (textContent.trim() && React.Children.count(children) === 1 && typeof children === 'string') {
          return (
            <p className="mb-2 sm:mb-3 last:mb-0" {...props}>
              {processTextWithCitations(textContent)}
            </p>
          );
        }
      }
      
      return <p className="mb-2 sm:mb-3 last:mb-0" {...props}>{children}</p>;
    },
    
    h1: ({ node, children, ...props }) => (
      <h1 className="text-lg sm:text-xl font-semibold mb-2 sm:mb-3 text-text-primary" {...props}>
        {children}
      </h1>
    ),
    
    h2: ({ node, children, ...props }) => (
      <h2 className="text-base sm:text-lg font-semibold mb-2 text-text-primary" {...props}>
        {children}
      </h2>
    ),
    
    h3: ({ node, children, ...props }) => (
      <h3 className="text-sm sm:text-base font-semibold mb-2 text-text-primary" {...props}>
        {children}
      </h3>
    ),
    
    h4: ({ node, children, ...props }) => (
      <h4 className="text-sm font-semibold mb-2 text-text-primary" {...props}>
        {children}
      </h4>
    ),
    
    ul: ({ node, ...props }) => (
      <ul className="list-disc pl-4 mb-2 sm:mb-3 space-y-1" {...props} />
    ),
    
    ol: ({ node, ...props }) => (
      <ol className="list-decimal pl-4 mb-2 sm:mb-3 space-y-1" {...props} />
    ),
    
    li: ({ node, ...props }) => (
      <li className="text-text-secondary" {...props} />
    ),
    
    a: ({ node, children, ...props }) => (
      <a className="text-accent hover:underline" {...props}>
        {children}
      </a>
    ),
    
    code: ({ node, inline, ...props }) => 
      inline ? (
        <code className="bg-border-subtle/20 text-text-primary px-1 sm:px-1.5 py-0.5 rounded text-sm sm:text-base" {...props} />
      ) : (
        <pre className="bg-border-subtle/20 p-2 sm:p-3 rounded overflow-x-auto text-sm sm:text-base my-2 sm:my-3" {...props} />
      ),
    
    pre: ({ node, ...props }) => <div {...props} />,
    
    strong: ({ node, ...props }) => (
      <strong className="font-semibold text-text-primary" {...props} />
    ),
    
    em: ({ node, ...props }) => (
      <em className="italic" {...props} />
    ),
    
    blockquote: ({ node, ...props }) => (
      <blockquote className="border-l-4 border-border-subtle pl-4 my-2 sm:my-3 text-text-secondary/90" {...props} />
    )
  }), [isUser, isError, citationStyle, processTextWithCitations]);

  return (
    <div className={className}>
      <ReactMarkdown components={markdownComponents} remarkPlugins={[remarkGfm]}>
        {content}
      </ReactMarkdown>
      
      {/* Citation Modal */}
      {activeModal && (
        <CitationModal
          citation={activeModal}
          isOpen={!!activeModal}
          onClose={handleModalClose}
          position={modalPosition}
        />
      )}
    </div>
  );
};

MarkdownWithCitations.propTypes = {
  content: PropTypes.string.isRequired,
  className: PropTypes.string,
  citationStyle: PropTypes.oneOf(['link', 'button', 'highlight']),
  isUser: PropTypes.bool,
  isError: PropTypes.bool
};

export default MarkdownWithCitations;