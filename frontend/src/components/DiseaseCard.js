import React from 'react';
import RiskIndicator from './RiskIndicator';
import './DiseaseCard.css';

const DiseaseCard = ({ disease, prediction, onPredict, onViewDetails }) => {
  const formatDate = (dateString) => {
    if (!dateString) return '--';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const getTreatmentUrgency = (actions) => {
    if (!actions || actions.length === 0) return null;
    const firstAction = actions[0];
    if (firstAction.includes('immediately') || firstAction.includes('urgent')) {
      return { level: 'immediate', color: '#ef4444' };
    }
    if (firstAction.includes('24') || firstAction.includes('48')) {
      return { level: 'soon', color: '#f97316' };
    }
    if (firstAction.includes('days') || firstAction.includes('week')) {
      return { level: 'scheduled', color: '#f59e0b' };
    }
    return { level: 'monitor', color: '#10b981' };
  };

  const urgency = prediction ? getTreatmentUrgency(prediction.recommended_actions) : null;

  return (
    <div className="disease-card">
      <div className="disease-card__header">
        <div className="disease-card__title">
          <h3>{disease.name}</h3>
          <p className="disease-card__scientific">{disease.scientific_name}</p>
        </div>
        {prediction && (
          <RiskIndicator 
            riskScore={prediction.risk_score} 
            riskLevel={prediction.risk_level}
            size="medium"
          />
        )}
      </div>

      <div className="disease-card__body">
        <div className="disease-card__info">
          <div className="disease-card__info-item">
            <span className="label">Type:</span>
            <span className="value">{disease.pathogen_type}</span>
          </div>
          <div className="disease-card__info-item">
            <span className="label">Crops:</span>
            <span className="value">{disease.affected_crops?.join(', ') || 'Various'}</span>
          </div>
          {prediction && (
            <>
              <div className="disease-card__info-item">
                <span className="label">Infection Risk:</span>
                <span className="value">{Math.round(prediction.infection_probability * 100)}%</span>
              </div>
              <div className="disease-card__info-item">
                <span className="label">Symptom Onset:</span>
                <span className="value">{prediction.days_to_symptom_onset || '--'} days</span>
              </div>
              <div className="disease-card__info-item">
                <span className="label">Last Updated:</span>
                <span className="value">{formatDate(prediction.prediction_date)}</span>
              </div>
            </>
          )}
        </div>

        {prediction && prediction.recommended_actions && prediction.recommended_actions.length > 0 && (
          <div className="disease-card__actions">
            <h4>
              {urgency && (
                <span style={{ color: urgency.color }}>
                  {urgency.level.toUpperCase()}
                </span>
              )}
              {!urgency && 'Recommended Actions'}
            </h4>
            <ul>
              {prediction.recommended_actions.slice(0, 3).map((action, idx) => (
                <li key={idx}>{action}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div className="disease-card__footer">
        {onPredict && (
          <button 
            className="btn btn--secondary"
            onClick={() => onPredict(disease)}
          >
            Generate Prediction
          </button>
        )}
        {onViewDetails && prediction && (
          <button 
            className="btn btn--primary"
            onClick={() => onViewDetails(disease, prediction)}
          >
            View Forecast
          </button>
        )}
      </div>
    </div>
  );
};

export default DiseaseCard;
