import React, { useState, useRef } from 'react';
import { Search, FileText, Users, Brain, CheckCircle, AlertCircle, Clock } from 'lucide-react';

const AdvancedResearch = ({ onClose }) => {
  const [query, setQuery] = useState('');
  const [selectedJurisdictions, setSelectedJurisdictions] = useState(['federal']);
  const [selectedLegalAreas, setSelectedLegalAreas] = useState([]);
  const [includePrecedents, setIncludePrecedents] = useState(true);
  const [includeCommentary, setIncludeCommentary] = useState(true);
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.7);
  const [isResearching, setIsResearching] = useState(false);
  const [researchResults, setResearchResults] = useState(null);
  const [activeTab, setActiveTab] = useState('analysis');

  const jurisdictions = [
    { value: 'federal', label: 'Federal' },
    { value: 'nsw', label: 'New South Wales' },
    { value: 'vic', label: 'Victoria' },
    { value: 'qld', label: 'Queensland' },
    { value: 'sa', label: 'South Australia' },
    { value: 'wa', label: 'Western Australia' },
    { value: 'tas', label: 'Tasmania' },
    { value: 'nt', label: 'Northern Territory' },
    { value: 'act', label: 'Australian Capital Territory' }
  ];

  const legalAreas = [
    { value: 'contract', label: 'Contract Law' },
    { value: 'tort', label: 'Tort Law' },
    { value: 'criminal', label: 'Criminal Law' },
    { value: 'constitutional', label: 'Constitutional Law' },
    { value: 'administrative', label: 'Administrative Law' },
    { value: 'employment', label: 'Employment Law' },
    { value: 'migration', label: 'Migration Law' },
    { value: 'corporate', label: 'Corporate Law' },
    { value: 'family', label: 'Family Law' },
    { value: 'property', label: 'Property Law' },
    { value: 'intellectual_property', label: 'Intellectual Property' },
    { value: 'tax', label: 'Tax Law' },
    { value: 'environmental', label: 'Environmental Law' }
  ];

  const handleJurisdictionChange = (jurisdiction) => {
    setSelectedJurisdictions(prev => 
      prev.includes(jurisdiction)
        ? prev.filter(j => j !== jurisdiction)
        : [...prev, jurisdiction]
    );
  };

  const handleLegalAreaChange = (area) => {
    setSelectedLegalAreas(prev =>
      prev.includes(area)
        ? prev.filter(a => a !== area)
        : [...prev, area]
    );
  };

  const handleAdvancedResearch = async () => {
    if (!query.trim()) return;

    setIsResearching(true);
    
    try {
      const response = await fetch('/api/research/advanced', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query,
          jurisdictions: selectedJurisdictions,
          legal_areas: selectedLegalAreas,
          include_precedents: includePrecedents,
          include_commentary: includeCommentary,
          confidence_threshold: confidenceThreshold
        })
      });

      if (!response.ok) {
        throw new Error('Research request failed');
      }

      const results = await response.json();
      setResearchResults(results);
      setActiveTab('analysis');
    } catch (error) {
      console.error('Advanced research error:', error);
      // Handle error appropriately
    } finally {
      setIsResearching(false);
    }
  };

  const getConfidenceColor = (level) => {
    switch (level) {
      case 'high': return 'text-green-600';
      case 'medium': return 'text-yellow-600';
      case 'low': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getConfidenceIcon = (level) => {
    switch (level) {
      case 'high': return <CheckCircle className="w-4 h-4" />;
      case 'medium': return <AlertCircle className="w-4 h-4" />;
      case 'low': return <AlertCircle className="w-4 h-4" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-background-primary rounded-lg shadow-2xl w-full max-w-6xl h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border-primary">
          <div className="flex items-center space-x-3">
            <Brain className="w-6 h-6 text-accent-gold" />
            <h2 className="text-xl font-semibold">Advanced Legal Research</h2>
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
          {/* Research Configuration */}
          <div className="w-1/3 p-6 border-r border-border-primary overflow-y-auto">
            <div className="space-y-6">
              {/* Query Input */}
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  Research Query
                </label>
                <textarea
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Enter your legal research question..."
                  className="w-full h-24 px-3 py-2 bg-background-secondary border border-border-primary rounded-md text-text-primary placeholder-text-muted resize-none"
                />
              </div>

              {/* Jurisdictions */}
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  Jurisdictions
                </label>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {jurisdictions.map(jurisdiction => (
                    <label key={jurisdiction.value} className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={selectedJurisdictions.includes(jurisdiction.value)}
                        onChange={() => handleJurisdictionChange(jurisdiction.value)}
                        className="rounded border-border-primary text-accent-gold focus:ring-accent-gold/20"
                      />
                      <span className="text-sm text-text-primary">{jurisdiction.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Legal Areas */}
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  Legal Areas (Optional)
                </label>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {legalAreas.map(area => (
                    <label key={area.value} className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={selectedLegalAreas.includes(area.value)}
                        onChange={() => handleLegalAreaChange(area.value)}
                        className="rounded border-border-primary text-accent-gold focus:ring-accent-gold/20"
                      />
                      <span className="text-sm text-text-primary">{area.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Research Options */}
              <div className="space-y-3">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={includePrecedents}
                    onChange={(e) => setIncludePrecedents(e.target.checked)}
                    className="rounded border-border-primary text-accent-gold focus:ring-accent-gold/20"
                  />
                  <span className="text-sm text-text-primary">Include Precedent Analysis</span>
                </label>

                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={includeCommentary}
                    onChange={(e) => setIncludeCommentary(e.target.checked)}
                    className="rounded border-border-primary text-accent-gold focus:ring-accent-gold/20"
                  />
                  <span className="text-sm text-text-primary">Include Scholarly Commentary</span>
                </label>
              </div>

              {/* Confidence Threshold */}
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  Confidence Threshold: {Math.round(confidenceThreshold * 100)}%
                </label>
                <input
                  type="range"
                  min="0.3"
                  max="0.95"
                  step="0.05"
                  value={confidenceThreshold}
                  onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
                  className="w-full"
                />
              </div>

              {/* Research Button */}
              <button
                onClick={handleAdvancedResearch}
                disabled={isResearching || !query.trim()}
                className="w-full bg-accent-gold text-surface-dark font-medium py-2 px-4 rounded-md hover:bg-accent-gold/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
              >
                {isResearching ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-surface-dark border-t-transparent"></div>
                    <span>Researching...</span>
                  </>
                ) : (
                  <>
                    <Search className="w-4 h-4" />
                    <span>Start Research</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Research Results */}
          <div className="flex-1 flex flex-col">
            {researchResults ? (
              <>
                {/* Results Header */}
                <div className="p-6 border-b border-border-primary">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-medium">Research Results</h3>
                    <div className={`flex items-center space-x-2 ${getConfidenceColor(researchResults.confidence_assessment?.overall_confidence)}`}>
                      {getConfidenceIcon(researchResults.confidence_assessment?.overall_confidence)}
                      <span className="text-sm font-medium capitalize">
                        {researchResults.confidence_assessment?.overall_confidence} Confidence
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex space-x-1 mt-4">
                    {['analysis', 'components', 'metadata'].map(tab => (
                      <button
                        key={tab}
                        onClick={() => setActiveTab(tab)}
                        className={`px-4 py-2 text-sm rounded-md transition-colors ${
                          activeTab === tab
                            ? 'bg-accent-gold text-surface-dark'
                            : 'text-text-secondary hover:text-text-primary hover:bg-background-secondary'
                        }`}
                      >
                        {tab === 'analysis' ? 'Comprehensive Analysis' :
                         tab === 'components' ? 'Research Components' : 'Metadata'}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Results Content */}
                <div className="flex-1 p-6 overflow-y-auto">
                  {activeTab === 'analysis' && (
                    <div className="prose prose-invert max-w-none">
                      <div className="whitespace-pre-wrap text-text-primary">
                        {researchResults.comprehensive_analysis}
                      </div>
                    </div>
                  )}
                  
                  {activeTab === 'components' && (
                    <div className="space-y-6">
                      {researchResults.research_components?.map((component, index) => (
                        <div key={index} className="bg-background-secondary p-4 rounded-lg">
                          <h4 className="font-medium text-text-primary mb-2 capitalize">
                            {component.type?.replace(/_/g, ' ')}
                          </h4>
                          <div className="text-text-primary whitespace-pre-wrap">
                            {component.content}
                          </div>
                          {component.timestamp && (
                            <div className="text-text-muted text-xs mt-2">
                              Generated: {new Date(component.timestamp).toLocaleString()}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                  
                  {activeTab === 'metadata' && (
                    <div className="bg-background-secondary p-4 rounded-lg">
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="text-text-secondary">Jurisdictions:</span>
                          <div className="text-text-primary">
                            {researchResults.research_metadata?.jurisdictions_covered?.join(', ')}
                          </div>
                        </div>
                        <div>
                          <span className="text-text-secondary">Legal Areas:</span>
                          <div className="text-text-primary">
                            {researchResults.research_metadata?.legal_areas?.join(', ') || 'General'}
                          </div>
                        </div>
                        <div>
                          <span className="text-text-secondary">Components Analyzed:</span>
                          <div className="text-text-primary">
                            {researchResults.research_metadata?.components_analyzed}
                          </div>
                        </div>
                        <div>
                          <span className="text-text-secondary">Data Completeness:</span>
                          <div className="text-text-primary">
                            {Math.round((researchResults.confidence_assessment?.data_completeness || 0) * 100)}%
                          </div>
                        </div>
                      </div>
                      
                      {researchResults.confidence_assessment?.reliability_factors && (
                        <div className="mt-4">
                          <span className="text-text-secondary text-sm">Reliability Factors:</span>
                          <ul className="text-text-primary text-sm mt-1 space-y-1">
                            {researchResults.confidence_assessment.reliability_factors.map((factor, index) => (
                              <li key={index} className="flex items-start space-x-2">
                                <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                                <span>{factor}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center text-text-secondary">
                <div className="text-center">
                  <Brain className="w-16 h-16 mx-auto mb-4 text-accent-gold/50" />
                  <p className="text-lg">Configure your research parameters and click "Start Research"</p>
                  <p className="text-sm mt-2">Advanced AI analysis across multiple legal dimensions</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdvancedResearch;