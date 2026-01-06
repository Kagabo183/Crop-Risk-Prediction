import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { fetchDailyForecast, fetchWeeklyForecast, fetchFarms, fetchDiseases } from '../api';
import RiskIndicator from '../components/RiskIndicator';
import './DiseaseForecasts.css';

const DiseaseForecasts = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [farms, setFarms] = useState([]);
  const [diseases, setDiseases] = useState([]);
  const [selectedFarm, setSelectedFarm] = useState(null);
  const [selectedDisease, setSelectedDisease] = useState('');
  const [dailyForecast, setDailyForecast] = useState([]);
  const [weeklyForecast, setWeeklyForecast] = useState(null);
  const [loading, setLoading] = useState(true);
  const [forecastDays, setForecastDays] = useState(7);

  useEffect(() => {
    loadInitialData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (selectedFarm && selectedDisease) {
      loadForecasts();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedFarm, selectedDisease, forecastDays]);

  const loadInitialData = async () => {
    try {
      const [farmsData, diseasesData] = await Promise.all([
        fetchFarms(),
        fetchDiseases()
      ]);
      setFarms(farmsData);
      setDiseases(diseasesData);

      // Set from URL params or defaults
      const farmParam = searchParams.get('farm');
      const diseaseParam = searchParams.get('disease');
      
      if (farmParam) {
        setSelectedFarm(parseInt(farmParam));
      } else if (farmsData.length > 0) {
        setSelectedFarm(farmsData[0].id);
      }

      if (diseaseParam) {
        setSelectedDisease(diseaseParam);
      } else if (diseasesData.length > 0) {
        setSelectedDisease(diseasesData[0].name);
      }

      setLoading(false);
    } catch (err) {
      console.error('Failed to load initial data:', err);
      setLoading(false);
    }
  };

  const loadForecasts = async () => {
    if (!selectedFarm || !selectedDisease) return;

    try {
      const [daily, weekly] = await Promise.all([
        fetchDailyForecast(selectedFarm, selectedDisease, forecastDays),
        fetchWeeklyForecast(selectedFarm, selectedDisease)
      ]);
      setDailyForecast(daily);
      setWeeklyForecast(weekly);
    } catch (err) {
      console.error('Failed to load forecasts:', err);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', weekday: 'short' });
  };

  const handleFarmChange = (farmId) => {
    setSelectedFarm(farmId);
    setSearchParams({ farm: farmId, disease: selectedDisease });
  };

  const handleDiseaseChange = (diseaseName) => {
    setSelectedDisease(diseaseName);
    setSearchParams({ farm: selectedFarm, disease: diseaseName });
  };

  if (loading) {
    return (
      <div className="forecasts-page">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading forecasts...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="forecasts-page">
      <div className="forecasts-header">
        <h1>Disease Forecasts</h1>
        <p>Daily and weekly disease risk predictions</p>
      </div>

      <div className="forecasts-controls">
        <div className="control-group">
          <label>Farm:</label>
          <select value={selectedFarm || ''} onChange={(e) => handleFarmChange(parseInt(e.target.value))}>
            {farms.map(farm => (
              <option key={farm.id} value={farm.id}>
                {farm.name} - {farm.location}
              </option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label>Disease:</label>
          <select value={selectedDisease} onChange={(e) => handleDiseaseChange(e.target.value)}>
            {diseases.map(disease => (
              <option key={disease.id} value={disease.name}>
                {disease.name}
              </option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label>Forecast Days:</label>
          <select value={forecastDays} onChange={(e) => setForecastDays(parseInt(e.target.value))}>
            <option value="3">3 Days</option>
            <option value="7">7 Days</option>
            <option value="14">14 Days</option>
          </select>
        </div>
      </div>

      {weeklyForecast && (
        <div className="weekly-forecast-card">
          <h2>📅 Weekly Summary</h2>
          <div className="weekly-content">
            <div className="weekly-risk">
              <RiskIndicator 
                riskScore={weeklyForecast.average_risk_score}
                riskLevel={weeklyForecast.risk_level}
                size="large"
              />
            </div>
            <div className="weekly-details">
              <div className="weekly-stat">
                <span className="label">Peak Risk Day:</span>
                <span className="value">🔴 {formatDate(weeklyForecast.peak_risk_day)}</span>
              </div>
              <div className="weekly-stat">
                <span className="label">High Risk Days:</span>
                <span className="value">{weeklyForecast.high_risk_days_count} days</span>
              </div>
              <div className="weekly-stat">
                <span className="label">Confidence:</span>
                <span className="value">{Math.round(weeklyForecast.forecast_confidence * 100)}%</span>
              </div>
            </div>
          </div>

          {weeklyForecast.strategic_recommendations && weeklyForecast.strategic_recommendations.length > 0 && (
            <div className="weekly-recommendations">
              <h3>Strategic Recommendations</h3>
              <ul>
                {weeklyForecast.strategic_recommendations.map((rec, idx) => (
                  <li key={idx}>{rec}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <div className="daily-forecast-section">
        <h2>📊 Daily Forecast</h2>
        {dailyForecast.length === 0 ? (
          <div className="no-data">
            <p>No forecast data available. Generate predictions first.</p>
          </div>
        ) : (
          <div className="daily-forecast-grid">
            {dailyForecast.map((day, idx) => (
              <div key={idx} className="daily-forecast-card">
                <div className="day-header">
                  <div className="day-date">{formatDate(day.forecast_date)}</div>
                  {day.is_critical_day && <span className="critical-badge">⚡ Critical</span>}
                </div>

                <RiskIndicator 
                  riskScore={day.risk_score}
                  riskLevel={day.risk_level}
                  size="small"
                />

                <div className="day-stats">
                  <div className="day-stat">
                    <span className="icon">🦠</span>
                    <span className="value">{Math.round(day.infection_probability * 100)}%</span>
                    <span className="label">Infection Risk</span>
                  </div>
                  <div className="day-stat">
                    <span className="icon">📈</span>
                    <span className="value">{Math.round(day.forecast_confidence * 100)}%</span>
                    <span className="label">Confidence</span>
                  </div>
                </div>

                {day.recommended_actions && day.recommended_actions.length > 0 && (
                  <div className="day-actions">
                    <ul>
                      {day.recommended_actions.slice(0, 2).map((action, i) => (
                        <li key={i}>{action}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default DiseaseForecasts;
