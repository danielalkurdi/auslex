import React, { useState, useCallback } from 'react';
import { X } from 'lucide-react';
import PropTypes from 'prop-types';

const Slider = React.memo(({ label, value, min, max, step, onChange, description }) => (
  <div>
    <label className="block text-sm font-medium text-text-secondary mb-2">
      {label}: <span className="font-semibold text-text-primary">{value}</span>
    </label>
    <input
      type="range"
      min={min} max={max} step={step}
      value={value}
      onChange={onChange}
      className="w-full h-1.5 bg-background-primary rounded-full appearance-none cursor-pointer accent-accent-focus"
      aria-describedby={description ? `${label.toLowerCase().replace(/\s+/g, '-')}-desc` : undefined}
    />
    {description && (
      <p id={`${label.toLowerCase().replace(/\s+/g, '-')}-desc`} className="text-sm text-text-placeholder mt-2">
        {description}
      </p>
    )}
  </div>
));

Slider.propTypes = {
  label: PropTypes.string.isRequired,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
  min: PropTypes.string.isRequired,
  max: PropTypes.string.isRequired,
  step: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  description: PropTypes.string
};

Slider.displayName = 'Slider';

const SettingsPanel = React.memo(({ settings, onSettingsChange, onClose }) => {
  const [localSettings, setLocalSettings] = useState(settings);
  const [hasChanges, setHasChanges] = useState(false);

  const handleChange = useCallback((key, value) => {
    setLocalSettings(prev => ({ ...prev, [key]: value }));
    setHasChanges(true);
  }, []);

  const handleSave = useCallback(() => {
    onSettingsChange(localSettings);
    setHasChanges(false);
    onClose();
  }, [localSettings, onSettingsChange, onClose]);

  const handleClose = useCallback(() => {
    const confirmClose = hasChanges && window.confirm ? 
      window.confirm('You have unsaved changes that will be lost. Are you sure?') : 
      !hasChanges;
    
    if (!hasChanges || confirmClose) {
      onClose();
    }
  }, [hasChanges, onClose]);
  

  return (
    <div className="fixed inset-0 bg-background-primary/80 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
      <div 
        className="bg-background-secondary rounded shadow-soft max-w-md w-full max-h-[90vh] overflow-y-auto border-1 border-border-subtle"
        role="dialog"
        aria-modal="true"
        aria-labelledby="settings-title"
      >
        <div className="p-8">
          <div className="flex items-start justify-between mb-8">
            <div>
              <h2 id="settings-title" className="h2">Settings</h2>
              <p className="text-text-secondary mt-1">Configure model parameters</p>
            </div>
            <button
              onClick={handleClose}
              className="p-1 text-text-placeholder hover:text-text-primary rounded-full transition-colors"
              aria-label="Close settings"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="space-y-8">
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-2">API Endpoint</label>
              <input
                type="url"
                value={localSettings.apiEndpoint}
                onChange={(e) => handleChange('apiEndpoint', e.target.value)}
                className="w-full bg-background-primary border-1 border-border-subtle rounded p-2 text-text-primary
                           placeholder-text-placeholder focus:border-accent-focus transition-colors duration-150"
                placeholder="http://localhost:8000"
                aria-describedby="api-endpoint-desc"
              />
              <p id="api-endpoint-desc" className="text-xs text-text-placeholder mt-1">
                The URL of your API endpoint
              </p>
            </div>

            <Slider
              label="Max Tokens" value={localSettings.maxTokens}
              min="512" max="4096" step="256"
              onChange={(e) => handleChange('maxTokens', parseInt(e.target.value))}
              description="Maximum length of the model's response."
            />
            
            <Slider
              label="Temperature" value={localSettings.temperature}
              min="0" max="2" step="0.1"
              onChange={(e) => handleChange('temperature', parseFloat(e.target.value))}
              description="Controls creativity. Lower is more predictable."
            />

            <Slider
              label="Top P" value={localSettings.topP}
              min="0.1" max="1" step="0.1"
              onChange={(e) => handleChange('topP', parseFloat(e.target.value))}
              description="Controls diversity of token selection."
            />
          </div>

          <div className="flex justify-end gap-3 mt-10 pt-6 border-t-1 border-border-subtle">
            <button
              onClick={handleClose}
              className="py-2 px-4 rounded text-center font-medium transition-colors
                         border-1 border-border-subtle text-text-secondary
                         hover:border-border-secondary hover:text-text-primary"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={!hasChanges}
              className="py-2 px-4 rounded text-center font-medium transition-colors
                         bg-background-secondary border-1 border-accent text-accent
                         hover:bg-accent hover:text-background-secondary
                         disabled:border-disabled-bg disabled:text-disabled-text disabled:cursor-not-allowed"
            >
              Save Changes
            </button>
          </div>
        </div>
      </div>
    </div>
  );
});

SettingsPanel.propTypes = {
  settings: PropTypes.shape({
    apiEndpoint: PropTypes.string.isRequired,
    maxTokens: PropTypes.number.isRequired,
    temperature: PropTypes.number.isRequired,
    topP: PropTypes.number.isRequired
  }).isRequired,
  onSettingsChange: PropTypes.func.isRequired,
  onClose: PropTypes.func.isRequired
};

SettingsPanel.displayName = 'SettingsPanel';

export default SettingsPanel;
