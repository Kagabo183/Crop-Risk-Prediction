import React, { useState, useEffect } from 'react';
import { fetchFarms, fetchPredictions, fetchAlerts, fetchDiseases, fetchDiseasePredictions } from '../api';
import RiskIndicator from '../components/RiskIndicator';
import '../components/Dashboard.css';

const Dashboard = () => {
  const [stats, setStats] = useState({
    farms: 0,
    predictions: 0,
    alerts: 0,
    diseases: 0,
    highRiskDiseases: 0
  });
  const [topRiskDiseases, setTopRiskDiseases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboardData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      console.log('🔄 Loading dashboard data...');
      
      // Add timeout to API calls
      const timeout = (ms) => new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Request timeout')), ms)
      );
      
      const fetchWithTimeout = (promise, ms = 10000) => 
        Promise.race([promise, timeout(ms)]);

      const [farmsData, predictionsData, alertsData, diseasesData, diseasePredsData] = await Promise.all([
        fetchWithTimeout(fetchFarms()).catch(err => { 
          console.error('❌ Farms error:', err.message); 
          return []; 
        }),
        fetchWithTimeout(fetchPredictions()).catch(err => { 
          console.error('❌ Predictions error:', err.message); 
          return []; 
        }),
        fetchWithTimeout(fetchAlerts()).catch(err => { 
          console.error('❌ Alerts error:', err.message); 
          return []; 
        }),
        fetchWithTimeout(fetchDiseases()).catch(err => { 
          console.error('❌ Diseases error:', err.message); 
          return []; 
        }),
        fetchWithTimeout(fetchDiseasePredictions(null, null, 100)).catch(err => { 
          console.error('❌ Disease predictions error:', err.message); 
          return []; 
        })
      ]);

      console.log('✅ Data loaded:', {
        farms: farmsData?.length,
        predictions: predictionsData?.length,
        alerts: alertsData?.length,
        diseases: diseasesData?.length,
        diseasePredictions: diseasePredsData?.length
      });

      const highRisk = Array.isArray(diseasePredsData) ? diseasePredsData.filter(p => 
        p.risk_level === 'high' || p.risk_level === 'severe' || p.risk_level === 'critical'
      ) : [];

      // Get top 3 highest risk diseases
      const sorted = Array.isArray(diseasePredsData) ? [...diseasePredsData].sort((a, b) => (b.risk_score || 0) - (a.risk_score || 0)) : [];
      const top3 = sorted.slice(0, 3);

      setStats({
        farms: Array.isArray(farmsData) ? farmsData.length : 0,
        predictions: Array.isArray(predictionsData) ? predictionsData.length : 0,
        alerts: Array.isArray(alertsData) ? alertsData.length : 0,
        diseases: Array.isArray(diseasesData) ? diseasesData.length : 0,
        highRiskDiseases: highRisk.length
      });

      setTopRiskDiseases(top3);
      setLoading(false);
    } catch (err) {
      console.error('❌ Failed to load dashboard data:', err);
      setError(err.message || 'Failed to load data');
      // Set default values on error
      setStats({
        farms: 0,
        predictions: 0,
        alerts: 0,
        diseases: 0,
        highRiskDiseases: 0
      });
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="dashboard-content">
        <h2>Overview</h2>
        <div style={{ textAlign: 'center', padding: '60px', fontSize: '18px', color: '#666' }}>
          <div style={{ fontSize: '48px', marginBottom: '20px' }}>⏳</div>
          <div>Loading dashboard data...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-content">
        <h2>Overview</h2>
        <div style={{ textAlign: 'center', padding: '60px' }}>
          <div style={{ fontSize: '48px', marginBottom: '20px', color: '#f44336' }}>⚠️</div>
          <div style={{ fontSize: '18px', color: '#f44336', marginBottom: '10px' }}>Error Loading Dashboard</div>
          <div style={{ fontSize: '14px', color: '#666', marginBottom: '30px' }}>{error}</div>
          <button 
            onClick={loadDashboardData}
            style={{
              padding: '12px 24px',
              fontSize: '16px',
              backgroundColor: '#4CAF50',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer'
            }}
          >
            🔄 Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-content">
      <h2>Overview</h2>
      
      <div className="dashboard-widgets">
        <div className="widget">
          <div className="widget-icon">🌾</div>
          <div className="widget-content">
            <div className="widget-value">{loading ? '...' : stats.farms}</div>
            <div className="widget-label">Monitored Farms</div>
            <div className="widget-sublabel">Active monitoring</div>
          </div>
        </div>

        <div className="widget">
          <div className="widget-icon">📊</div>
          <div className="widget-content">
            <div className="widget-value">{loading ? '...' : stats.predictions}</div>
            <div className="widget-label">Risk Assessments</div>
            <div className="widget-sublabel">Total predictions</div>
          </div>
        </div>

        <div className="widget">
          <div className="widget-icon">⚠️</div>
          <div className="widget-content">
            <div className="widget-value">{loading ? '...' : stats.alerts}</div>
            <div className="widget-label">Active Alerts</div>
            <div className="widget-sublabel">Requiring attention</div>
          </div>
        </div>

        <div className="widget">
          <div className="widget-icon">🛰️</div>
          <div className="widget-content">
            <div className="widget-value">{loading ? '...' : stats.predictions}</div>
            <div className="widget-label">Satellite Images</div>
            <div className="widget-sublabel">Data points</div>
          </div>
        </div>

        <div className="widget widget--alert">
          <div className="widget-icon">⚠️</div>
          <div className="widget-content">
            <div className="widget-value">{stats.highRiskDiseases}</div>
            <div className="widget-label">High Risk Diseases</div>
          </div>
        </div>
      </div>

      {topRiskDiseases.length > 0 && (
        <div className="dashboard-section">
          <h3>🔴 Top Disease Risks</h3>
          <div className="disease-risk-cards">
            {topRiskDiseases.map((pred, idx) => (
              <div key={idx} className="disease-risk-card">
                <div className="disease-risk-header">
                  <span className="disease-rank">#{idx + 1}</span>
                  <RiskIndicator 
                    riskScore={pred.risk_score}
                    riskLevel={pred.risk_level}
                    size="small"
                  />
                </div>
                <div className="disease-risk-body">
                  <h4>Farm ID: {pred.farm_id}</h4>
                  <div className="disease-risk-stat">
                    <span>Infection Risk:</span>
                    <span className="value">{Math.round(pred.infection_probability * 100)}%</span>
                  </div>
                  {pred.recommended_actions && pred.recommended_actions.length > 0 && (
                    <div className="disease-action">
                      ⚡ {pred.recommended_actions[0]}
                    </div>
                  )}
                </div>
                <div className="disease-risk-footer">
                  <a href={`/disease-forecasts?farm=${pred.farm_id}`}>View Forecast →</a>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="dashboard-section">
        <h3>Quick Actions</h3>
        <div className="quick-actions">
          <a href="/diseases" className="action-btn">
            <span className="action-icon">🦠</span>
            <span>Disease Predictions</span>
          </a>
          <a href="/disease-forecasts" className="action-btn">
            <span className="action-icon">📈</span>
            <span>View Forecasts</span>
          </a>
          <a href="/farms" className="action-btn">
            <span className="action-icon">🌾</span>
            <span>Manage Farms</span>
          </a>
          <a href="/alerts" className="action-btn">
            <span className="action-icon">🔔</span>
            <span>View Alerts</span>
          </a>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
