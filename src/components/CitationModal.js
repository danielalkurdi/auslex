import React, { useState, useEffect, useRef, useCallback } from 'react';
import { X, ExternalLink, Copy, Check, Loader2, AlertCircle, Search, Globe } from 'lucide-react';
import PropTypes from 'prop-types';
import { useAustLII } from '../services/austliiService';

/**
 * CitationModal - Displays legal provision content in a modal overlay
 * 
 * Features:
 * - Fetches and displays provision content from legal databases
 * - Shows metadata (act name, section, last amended date)
 * - Copy citation functionality
 * - Link to full act/regulation
 * - Loading and error states
 * - Positioned near clicked citation
 */
const CitationModal = ({ 
  citation, 
  isOpen, 
  onClose, 
  position = { top: 0, left: 0 }
}) => {
  const [austliiUrl, setAustliiUrl] = useState(null);
  const [urlOptions, setUrlOptions] = useState([]);
  const [selectedUrlIndex, setSelectedUrlIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [iframeError, setIframeError] = useState(false);
  const [copiedCitation, setCopiedCitation] = useState(false);
  const modalRef = useRef(null);
  const iframeRef = useRef(null);
  const { getUrlOptions } = useAustLII();

  // Load AustLII URL when modal opens
  useEffect(() => {
    if (isOpen && citation) {
      loadAustliiUrl();
    }
  }, [isOpen, citation, loadAustliiUrl]);

  // Close modal on escape key
  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen, onClose]);

  // Click outside to close
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (modalRef.current && !modalRef.current.contains(event.target)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen, onClose]);

  /**
   * Load AustLII URL for citation
   */
  const loadAustliiUrl = useCallback(() => {
    setIsLoading(true);
    setIframeError(false);

    try {
      const options = getUrlOptions(citation);
      setUrlOptions(options);
      setSelectedUrlIndex(0);
      setAustliiUrl(options[0]);
      
      console.log('Constructed AustLII URL:', options[0].url);
    } catch (err) {
      console.error('Error constructing AustLII URL:', err);
      setIframeError(true);
    } finally {
      setIsLoading(false);
    }
  }, [citation, getUrlOptions]);

  /**
   * Handle iframe load events
   */
  const handleIframeLoad = () => {
    setIsLoading(false);
    setIframeError(false);
  };

  /**
   * Handle iframe error events  
   */
  const handleIframeError = () => {
    setIsLoading(false);
    setIframeError(true);
  };

  /**
   * Try alternative URL option
   */
  const tryAlternativeUrl = (index) => {
    if (urlOptions[index]) {
      setSelectedUrlIndex(index);
      setAustliiUrl(urlOptions[index]);
      setIframeError(false);
      setIsLoading(true);
    }
  };

  /**
   * Copy citation to clipboard
   */
  const handleCopyCitation = async () => {
    try {
      await navigator.clipboard.writeText(citation.fullCitation);
      setCopiedCitation(true);
      setTimeout(() => setCopiedCitation(false), 2000);
    } catch (err) {
      console.error('Failed to copy citation:', err);
    }
  };

  /**
   * Calculate modal position to avoid viewport edges
   */
  const calculateModalPosition = () => {
    const isMobile = window.innerWidth < 768;
    const modalWidth = isMobile ? window.innerWidth - 20 : 700;
    const modalHeight = isMobile ? window.innerHeight - 40 : 550;
    const padding = isMobile ? 10 : 20;

    // Start with centered position by default
    let left = (window.innerWidth - modalWidth) / 2;
    let top = (window.innerHeight - modalHeight) / 2;

    // If position is provided, try to position near the clicked element
    if (position && position.left && position.top) {
      left = position.left;
      top = position.top + 30; // Offset below the clicked element

      // Adjust if modal would go off right edge
      if (left + modalWidth > window.innerWidth - padding) {
        left = window.innerWidth - modalWidth - padding;
      }

      // Adjust if modal would go off left edge
      if (left < padding) {
        left = padding;
      }

      // Adjust if modal would go off bottom edge
      if (top + modalHeight > window.innerHeight - padding) {
        // Try positioning above the element
        top = position.top - modalHeight - 10;
        
        // If still off screen, center vertically
        if (top < padding) {
          top = (window.innerHeight - modalHeight) / 2;
        }
      }
    }

    // Ensure minimum padding from edges
    left = Math.max(padding, Math.min(left, window.innerWidth - modalWidth - padding));
    top = Math.max(padding, Math.min(top, window.innerHeight - modalHeight - padding));

    return { left, top };
  };

  if (!isOpen || !citation) {
    return null;
  }

  const modalPosition = calculateModalPosition();

  return (
    <div className="fixed inset-0 bg-black/20 backdrop-blur-sm z-50 overflow-hidden">
      <div
        ref={modalRef}
        className="fixed bg-background-secondary border border-border-subtle rounded-lg shadow-2xl overflow-hidden animate-fade-in z-50"
        style={{
          left: window.innerWidth < 768 ? '10px' : `${modalPosition.left}px`,
          top: window.innerWidth < 768 ? '20px' : `${modalPosition.top}px`,
          width: window.innerWidth < 768 ? 'calc(100vw - 20px)' : 'min(700px, calc(100vw - 40px))',
          height: window.innerWidth < 768 ? 'calc(100vh - 40px)' : 'min(550px, calc(100vh - 40px))',
          maxWidth: 'calc(100vw - 20px)',
          maxHeight: 'calc(100vh - 40px)',
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        {/* Header */}
        <div className="flex items-start justify-between p-3 sm:p-4 border-b border-border-subtle bg-background-primary/50 flex-shrink-0">
          <div className="flex-1 min-w-0">
            <h3 className="text-base sm:text-lg font-semibold text-text-primary truncate">
              {citation.actName}
              {citation.year && (
                <span className="text-text-secondary ml-1 sm:ml-2">{citation.year}</span>
              )}
            </h3>
            <div className="flex items-center gap-2 sm:gap-4 mt-1 text-xs sm:text-sm text-text-secondary">
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 bg-accent rounded-full"></span>
                {citation.jurisdictionFull}
              </span>
              {citation.provisionType && citation.provision && (
                <span className="font-mono bg-border-subtle px-2 py-0.5 rounded">
                  {citation.provisionType} {citation.provision.raw}
                </span>
              )}
            </div>
          </div>
          
          <div className="flex items-center gap-2 ml-2 sm:ml-4">
            <button
              onClick={handleCopyCitation}
              className="p-2 text-text-secondary hover:text-text-primary hover:bg-border-subtle rounded transition-colors"
              title="Copy citation"
            >
              {copiedCitation ? (
                <Check className="w-4 h-4 text-status-success" />
              ) : (
                <Copy className="w-4 h-4" />
              )}
            </button>
            <button
              onClick={onClose}
              className="p-2 text-text-secondary hover:text-text-primary hover:bg-border-subtle rounded transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex flex-col flex-1 overflow-hidden">
          {/* Alternative URLs toolbar */}
          {urlOptions.length > 1 && (
            <div className="px-4 py-2 bg-background-primary/30 border-b border-border-subtle">
              <div className="flex items-center gap-2 text-sm">
                <span className="text-text-placeholder">Try alternative:</span>
                {urlOptions.map((option, index) => (
                  <button
                    key={index}
                    onClick={() => tryAlternativeUrl(index)}
                    className={`px-2 py-1 rounded text-xs transition-colors ${
                      selectedUrlIndex === index
                        ? 'bg-accent text-background-primary'
                        : 'bg-border-subtle text-text-secondary hover:bg-border-secondary'
                    }`}
                  >
                    {option.type === 'search' ? 'Search' : `Option ${index + 1}`}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Loading state */}
          {isLoading && (
            <div className="flex items-center justify-center py-8">
              <div className="flex items-center gap-3 text-text-secondary">
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Loading AustLII content...</span>
              </div>
            </div>
          )}

          {/* Error state */}
          {iframeError && austliiUrl && (
            <div className="p-4 m-4 bg-status-warning/10 border border-status-warning/20 rounded-lg">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-status-warning flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-medium text-status-warning mb-2">
                    Unable to load AustLII content
                  </h4>
                  <p className="text-sm text-text-secondary mb-3">
                    The content could not be displayed in the preview window. This may be due to:
                  </p>
                  <ul className="text-xs text-text-placeholder space-y-1 mb-3">
                    <li>• The provision may not exist at this URL</li>
                    <li>• AustLII may have changed their URL structure</li>
                    <li>• Network connectivity issues</li>
                  </ul>
                  
                  <div className="flex flex-wrap gap-2">
                    <a
                      href={austliiUrl.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 px-3 py-1.5 text-xs text-accent hover:text-accent-focus bg-accent/10 hover:bg-accent/20 rounded transition-colors"
                    >
                      <ExternalLink className="w-3 h-3" />
                      Open in AustLII
                    </a>
                    
                    {austliiUrl.fallbackSearch && (
                      <a
                        href={austliiUrl.fallbackSearch}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 px-3 py-1.5 text-xs text-text-secondary hover:text-text-primary bg-background-primary hover:bg-border-subtle rounded transition-colors"
                      >
                        <Search className="w-3 h-3" />
                        Search AustLII
                      </a>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* AustLII iframe */}
          {austliiUrl && !iframeError && (
            <div className="flex-1 relative overflow-auto">
              <iframe
                ref={iframeRef}
                src={austliiUrl.url}
                className="w-full h-full border-none bg-white"
                title={`AustLII - ${citation.fullCitation}`}
                onLoad={handleIframeLoad}
                onError={handleIframeError}
                sandbox="allow-same-origin allow-scripts allow-popups allow-forms"
              />
              
              {/* Loading overlay */}
              {isLoading && (
                <div className="absolute inset-0 bg-background-primary/50 flex items-center justify-center">
                  <div className="flex items-center gap-2 text-text-secondary">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Loading...</span>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        {austliiUrl && (
          <div className="border-t border-border-subtle p-3 sm:p-4 bg-background-primary/30 flex-shrink-0">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2 text-xs text-text-placeholder">
                  <Globe className="w-4 h-4" />
                  Source: AustLII
                </div>
                {austliiUrl.type === 'search' && (
                  <div className="flex items-center gap-1 text-xs text-status-warning">
                    <Search className="w-3 h-3" />
                    Search result
                  </div>
                )}
              </div>
              
              <div className="flex items-center gap-2">
                <a
                  href={austliiUrl.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 px-3 py-1.5 text-xs text-accent hover:text-accent-focus bg-accent/10 hover:bg-accent/20 rounded transition-colors"
                >
                  <ExternalLink className="w-3 h-3" />
                  Open in AustLII
                </a>
                <span className="text-xs text-text-placeholder">
                  {citation.fullCitation}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

CitationModal.propTypes = {
  citation: PropTypes.shape({
    id: PropTypes.string.isRequired,
    type: PropTypes.string.isRequired,
    actName: PropTypes.string.isRequired,
    year: PropTypes.string,
    jurisdiction: PropTypes.string.isRequired,
    jurisdictionFull: PropTypes.string.isRequired,
    provisionType: PropTypes.string,
    provision: PropTypes.object,
    fullCitation: PropTypes.string.isRequired,
    originalText: PropTypes.string.isRequired,
    // Additional fields for case citations
    plaintiff: PropTypes.string,
    defendant: PropTypes.string,
    court: PropTypes.string,
    caseNumber: PropTypes.string
  }),
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  position: PropTypes.shape({
    top: PropTypes.number,
    left: PropTypes.number
  })
};

export default CitationModal;