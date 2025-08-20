import React, { useState, useRef } from 'react';
import { FileText, Download, Share2, Clock, CheckCircle, AlertTriangle } from 'lucide-react';

const LegalMemoGenerator = ({ onClose }) => {
  const [query, setQuery] = useState('');
  const [clientContext, setClientContext] = useState('');
  const [memoType, setMemoType] = useState('comprehensive');
  const [targetAudience, setTargetAudience] = useState('legal_professional');
  const [isGenerating, setIsGenerating] = useState(false);
  const [memoResult, setMemoResult] = useState(null);
  const [previewMode, setPreviewMode] = useState('formatted');

  const memoTypes = [
    { value: 'brief', label: 'Brief Analysis', description: 'Concise summary with key points' },
    { value: 'comprehensive', label: 'Comprehensive', description: 'Full analysis with detailed reasoning' },
    { value: 'advisory', label: 'Advisory Opinion', description: 'Formal legal advice with recommendations' }
  ];

  const audienceTypes = [
    { value: 'client', label: 'Client', description: 'Non-lawyer friendly language' },
    { value: 'legal_professional', label: 'Legal Professional', description: 'Technical legal terminology' },
    { value: 'academic', label: 'Academic', description: 'Scholarly analysis and theory' }
  ];

  const handleGenerateMemo = async () => {
    if (!query.trim()) return;

    setIsGenerating(true);
    
    try {
      const response = await fetch('/api/research/memo', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query,
          client_context: clientContext,
          memo_type: memoType,
          target_audience: targetAudience
        })
      });

      if (!response.ok) {
        throw new Error('Memo generation failed');
      }

      const result = await response.json();
      setMemoResult(result);
      setPreviewMode('formatted');
    } catch (error) {
      console.error('Legal memo generation error:', error);
      // Handle error appropriately
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownload = () => {
    if (!memoResult) return;

    const content = `
# Legal Memorandum

**Generated:** ${new Date().toLocaleDateString()}
**Type:** ${memoTypes.find(t => t.value === memoType)?.label}
**Audience:** ${audienceTypes.find(a => a.value === targetAudience)?.label}

## Executive Summary
${memoResult.executive_summary}

---

${memoResult.memo_content}

---

## Key Findings
${memoResult.key_findings.map((finding, index) => `${index + 1}. ${finding}`).join('\n')}

## Recommendations
${memoResult.recommendations.map((rec, index) => `${index + 1}. ${rec}`).join('\n')}

---

*This memorandum was generated using AusLex AI and contains ${memoResult.citations_count} legal citations. Confidence level: ${memoResult.confidence_level.toUpperCase()}*

*This information is for educational purposes only and does not constitute legal advice.*
    `;

    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `legal-memo-${Date.now()}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getConfidenceColor = (level) => {
    switch (level?.toLowerCase()) {
      case 'high': return 'text-green-600';
      case 'medium': return 'text-yellow-600';
      case 'low': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getConfidenceIcon = (level) => {
    switch (level?.toLowerCase()) {
      case 'high': return <CheckCircle className="w-4 h-4" />;
      case 'medium': return <AlertTriangle className="w-4 h-4" />;
      case 'low': return <AlertTriangle className="w-4 h-4" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-background-primary rounded-lg shadow-2xl w-full max-w-7xl h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border-primary">
          <div className="flex items-center space-x-3">
            <FileText className="w-6 h-6 text-accent-gold" />
            <h2 className="text-xl font-semibold">Legal Memorandum Generator</h2>
          </div>
          <button
            onClick={onClose}
            className="text-text-secondary hover:text-text-primary transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="flex-1 flex overflow-hidden">
          {/* Configuration Panel */}
          <div className="w-1/3 p-6 border-r border-border-primary overflow-y-auto">
            <div className="space-y-6">
              {/* Legal Issue */}
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  Legal Issue or Question
                </label>
                <textarea
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Describe the legal issue that requires analysis..."
                  className="w-full h-32 px-3 py-2 bg-background-secondary border border-border-primary rounded-md text-text-primary placeholder-text-muted resize-none"
                />
              </div>

              {/* Client Context */}
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  Client Context (Optional)
                </label>
                <textarea
                  value={clientContext}
                  onChange={(e) => setClientContext(e.target.value)}
                  placeholder="Provide relevant background about the client situation..."
                  className="w-full h-20 px-3 py-2 bg-background-secondary border border-border-primary rounded-md text-text-primary placeholder-text-muted resize-none"
                />
              </div>

              {/* Memo Type */}
              <div>
                <label className="block text-sm font-medium text-text-primary mb-3">
                  Memorandum Type
                </label>
                <div className="space-y-3">
                  {memoTypes.map(type => (
                    <label key={type.value} className="flex items-start space-x-3 cursor-pointer">
                      <input
                        type="radio"
                        name="memoType"
                        value={type.value}
                        checked={memoType === type.value}
                        onChange={(e) => setMemoType(e.target.value)}
                        className="mt-1 text-accent-gold focus:ring-accent-gold/20"
                      />
                      <div className="flex-1">
                        <div className="text-sm font-medium text-text-primary">{type.label}</div>
                        <div className="text-xs text-text-muted">{type.description}</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              {/* Target Audience */}
              <div>
                <label className="block text-sm font-medium text-text-primary mb-3">
                  Target Audience
                </label>
                <div className="space-y-3">
                  {audienceTypes.map(audience => (
                    <label key={audience.value} className="flex items-start space-x-3 cursor-pointer">
                      <input
                        type="radio"
                        name="targetAudience"
                        value={audience.value}
                        checked={targetAudience === audience.value}
                        onChange={(e) => setTargetAudience(e.target.value)}
                        className="mt-1 text-accent-gold focus:ring-accent-gold/20"
                      />
                      <div className="flex-1">
                        <div className="text-sm font-medium text-text-primary">{audience.label}</div>
                        <div className="text-xs text-text-muted">{audience.description}</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              {/* Generate Button */}
              <button
                onClick={handleGenerateMemo}
                disabled={isGenerating || !query.trim()}
                className="w-full bg-accent-gold text-surface-dark font-medium py-3 px-4 rounded-md hover:bg-accent-gold/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
              >
                {isGenerating ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-surface-dark border-t-transparent"></div>
                    <span>Generating Memorandum...</span>
                  </>
                ) : (
                  <>
                    <FileText className="w-4 h-4" />
                    <span>Generate Memorandum</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Preview Panel */}
          <div className="flex-1 flex flex-col">
            {memoResult ? (
              <>
                {/* Preview Header */}
                <div className="p-6 border-b border-border-primary">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-medium">Generated Memorandum</h3>
                    <div className="flex items-center space-x-3">
                      <div className={`flex items-center space-x-2 ${getConfidenceColor(memoResult.confidence_level)}`}>
                        {getConfidenceIcon(memoResult.confidence_level)}
                        <span className="text-sm font-medium capitalize">
                          {memoResult.confidence_level} Confidence
                        </span>
                      </div>
                      <div className="flex space-x-2">
                        <button
                          onClick={handleDownload}
                          className="px-3 py-2 bg-accent-gold text-surface-dark rounded-md hover:bg-accent-gold/90 flex items-center space-x-2"
                        >
                          <Download className="w-4 h-4" />
                          <span>Download</span>
                        </button>
                        <button className="px-3 py-2 border border-border-primary rounded-md hover:bg-background-secondary flex items-center space-x-2">
                          <Share2 className="w-4 h-4" />
                          <span>Share</span>
                        </button>
                      </div>
                    </div>
                  </div>
                  
                  {/* Stats */}
                  <div className="flex space-x-6 text-sm text-text-secondary">
                    <div>Citations: {memoResult.citations_count}</div>
                    <div>Type: {memoTypes.find(t => t.value === memoType)?.label}</div>
                    <div>Audience: {audienceTypes.find(a => a.value === targetAudience)?.label}</div>
                  </div>
                  
                  <div className="flex space-x-1 mt-4">
                    {['formatted', 'summary', 'findings'].map(mode => (
                      <button
                        key={mode}
                        onClick={() => setPreviewMode(mode)}
                        className={`px-4 py-2 text-sm rounded-md transition-colors capitalize ${
                          previewMode === mode
                            ? 'bg-accent-gold text-surface-dark'
                            : 'text-text-secondary hover:text-text-primary hover:bg-background-secondary'
                        }`}
                      >
                        {mode === 'formatted' ? 'Full Memo' : mode}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Preview Content */}
                <div className="flex-1 p-6 overflow-y-auto">
                  {previewMode === 'formatted' && (
                    <div className="prose prose-invert max-w-none">
                      <div className="mb-6 p-4 bg-background-secondary rounded-lg">
                        <h4 className="text-lg font-medium mb-2 text-accent-gold">Executive Summary</h4>
                        <p className="text-text-primary">{memoResult.executive_summary}</p>
                      </div>
                      <div className="whitespace-pre-wrap text-text-primary">
                        {memoResult.memo_content}
                      </div>
                    </div>
                  )}
                  
                  {previewMode === 'summary' && (
                    <div className="space-y-6">
                      <div>
                        <h4 className="text-lg font-medium mb-3 text-accent-gold">Executive Summary</h4>
                        <p className="text-text-primary whitespace-pre-wrap">
                          {memoResult.executive_summary}
                        </p>
                      </div>
                      
                      <div>
                        <h4 className="text-lg font-medium mb-3 text-accent-gold">Key Recommendations</h4>
                        <ul className="space-y-2">
                          {memoResult.recommendations.map((rec, index) => (
                            <li key={index} className="flex items-start space-x-3">
                              <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                              <span className="text-text-primary">{rec}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  )}
                  
                  {previewMode === 'findings' && (
                    <div>
                      <h4 className="text-lg font-medium mb-4 text-accent-gold">Key Findings</h4>
                      <div className="space-y-4">
                        {memoResult.key_findings.map((finding, index) => (
                          <div key={index} className="p-4 bg-background-secondary rounded-lg">
                            <div className="flex items-start space-x-3">
                              <div className="w-6 h-6 bg-accent-gold/20 rounded-full flex items-center justify-center flex-shrink-0">
                                <span className="text-sm font-medium text-accent-gold">{index + 1}</span>
                              </div>
                              <p className="text-text-primary">{finding}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center text-text-secondary">
                <div className="text-center">
                  <FileText className="w-16 h-16 mx-auto mb-4 text-accent-gold/50" />
                  <p className="text-lg mb-2">Configure your memorandum parameters</p>
                  <p className="text-sm">Enter your legal issue and click "Generate Memorandum"</p>
                  <div className="mt-6 text-sm text-text-muted">
                    <p className="mb-2">Features:</p>
                    <ul className="space-y-1">
                      <li>• Professional legal memorandum format</li>
                      <li>• Audience-appropriate language</li>
                      <li>• Executive summary and recommendations</li>
                      <li>• Confidence indicators and citations</li>
                      <li>• Export to various formats</li>
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LegalMemoGenerator;