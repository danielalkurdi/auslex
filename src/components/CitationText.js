import React, { useState, useRef } from 'react';
import PropTypes from 'prop-types';
import { renderableText } from '../utils/citationParser';
import CitationModal from './CitationModal';
import { ExternalLink, FileText, Scale } from 'lucide-react';

/**
 * CitationText - Renders text with clickable legal citations
 * 
 * This component automatically detects legal citations in text and makes them
 * clickable. When clicked, citations open a modal with the provision content.
 * 
 * Features:
 * - Automatic citation detection and parsing
 * - Visual styling to distinguish citations from regular text
 * - Click handling with modal positioning
 * - Different styles for different citation types
 * - Keyboard navigation support
 */
const CitationText = ({ 
  text, 
  className = '', 
  citationStyle = 'link' // 'link', 'button', 'highlight'
}) => {
  const [activeModal, setActiveModal] = useState(null);
  const [modalPosition, setModalPosition] = useState({ top: 0, left: 0 });
  const citationRefs = useRef({});

  // Parse text into renderable chunks
  const chunks = renderableText(text);

  /**
   * Handle citation click
   * @param {Object} citation - The clicked citation object
   * @param {Event} event - The click event
   */
  const handleCitationClick = (citation, event) => {
    event.preventDefault();
    
    // Calculate modal position based on clicked element
    const rect = event.target.getBoundingClientRect();
    setModalPosition({
      top: rect.bottom + window.scrollY,
      left: rect.left + window.scrollX
    });
    
    setActiveModal(citation);
  };

  /**
   * Handle modal close
   */
  const handleModalClose = () => {
    setActiveModal(null);
  };

  /**
   * Get citation icon based on type
   * @param {string} type - Citation type
   * @returns {JSX.Element} Icon component
   */
  const getCitationIcon = (type) => {
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
  };

  /**
   * Get citation styling classes based on citation type and style preference
   * @param {Object} citation - Citation object
   * @returns {string} CSS classes
   */
  const getCitationClasses = (citation) => {
    const baseClasses = 'transition-all duration-200 cursor-pointer';
    
    // Type-based colors
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
  };

  /**
   * Render individual citation element
   * @param {Object} chunk - Citation chunk object
   * @param {number} index - Chunk index
   * @returns {JSX.Element} Citation element
   */
  const renderCitation = (chunk, index) => {
    const citation = chunk.citation;
    
    return (
      <span
        key={`citation-${index}-${citation.id}`}
        ref={el => citationRefs.current[citation.id] = el}
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
  };

  /**
   * Render text chunk
   * @param {Object} chunk - Text chunk object  
   * @param {number} index - Chunk index
   * @returns {JSX.Element} Text element
   */
  const renderText = (chunk, index) => {
    return (
      <span key={`text-${index}`}>
        {chunk.content}
      </span>
    );
  };

  return (
    <div className={className}>
      {/* Render text with citations */}
      <div className="leading-relaxed">
        {chunks.map((chunk, index) => {
          if (chunk.type === 'citation') {
            return renderCitation(chunk, index);
          } else {
            return renderText(chunk, index);
          }
        })}
      </div>

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

CitationText.propTypes = {
  text: PropTypes.string.isRequired,
  className: PropTypes.string,
  citationStyle: PropTypes.oneOf(['link', 'button', 'highlight'])
};


export default CitationText;