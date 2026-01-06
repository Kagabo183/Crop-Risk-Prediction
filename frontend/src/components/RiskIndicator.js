import React from 'react';
import './RiskIndicator.css';

const RiskIndicator = ({ riskScore, riskLevel, size = 'medium' }) => {
  const getRiskColor = (level) => {
    const colors = {
      'low': '#10b981',
      'moderate': '#f59e0b',
      'high': '#f97316',
      'severe': '#ef4444',
      'critical': '#dc2626'
    };
    return colors[level?.toLowerCase()] || '#6b7280';
  };

  const getRiskIcon = (level) => {
    const icons = {
      'low': '🟢',
      'moderate': '🟡',
      'high': '🟠',
      'severe': '🔴',
      'critical': '🔴'
    };
    return icons[level?.toLowerCase()] || '⚪';
  };

  const sizeClass = `risk-indicator--${size}`;

  return (
    <div 
      className={`risk-indicator ${sizeClass}`}
      style={{ borderColor: getRiskColor(riskLevel) }}
    >
      <div className="risk-indicator__icon">
        {getRiskIcon(riskLevel)}
      </div>
      <div className="risk-indicator__content">
        <div 
          className="risk-indicator__score"
          style={{ color: getRiskColor(riskLevel) }}
        >
          {riskScore !== null && riskScore !== undefined ? Math.round(riskScore) : '--'}
        </div>
        <div className="risk-indicator__level">
          {riskLevel || 'Unknown'}
        </div>
      </div>
    </div>
  );
};

export default RiskIndicator;
