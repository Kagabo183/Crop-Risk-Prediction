import React, { useState, useEffect, useCallback } from 'react';
import { fetchFarms, fetchPredictions, fetchAlerts, fetchDiseases, fetchDiseasePredictions } from '../api';
import RiskIndicator from '../components/RiskIndicator';
import '../components/Dashboard.css';

const API_BASE = 'http://localhost:8000/api/v1';

const Dashboard = () => {
  const [stats, setStats] = useState({
    farms: 0,
    predictions: 0,
    alerts: 0,
    diseases: 0,
    highRiskDiseases: 0,
    realSatelliteData: 0
  });
  const [topRiskDiseases, setTopRiskDiseases] = useState([]);
  const [realSatelliteFarms, setRealSatelliteFarms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // New state for multi-level analysis
  const [analysisView, setAnalysisView] = useState('province'); // 'province', 'district', 'farm'
  const [provinceData, setProvinceData] = useState([]);
  const [districtData, setDistrictData] = useState([]);
  const [farmData, setFarmData] = useState([]);
  const [selectedProvince, setSelectedProvince] = useState(null);
  const [selectedDistrict, setSelectedDistrict] = useState(null);
  const [pipelineStatus, setPipelineStatus] = useState(null);
  const [fetching, setFetching] = useState(false);

  const loadAnalyticsData = useCallback(async () => {
    try {
      // Load province analytics
      const provResp = await fetch(`${API_BASE}/pipeline/predictions/by-province`);
      const provData = await provResp.json();
      setProvinceData(Array.isArray(provData) ? provData : []);
      
      // Load district analytics
      const distResp = await fetch(`${API_BASE}/pipeline/predictions/by-district`);
      const distData = await distResp.json();
      setDistrictData(Array.isArray(distData) ? distData : []);
      
      // Load farm analytics
      const farmResp = await fetch(`${API_BASE}/pipeline/predictions/by-farm`);
      const farmDataResp = await farmResp.json();
      setFarmData(Array.isArray(farmDataResp) ? farmDataResp : []);
      
      // Load pipeline status
      const statusResp = await fetch(`${API_BASE}/pipeline/status`);
      const statusData = await statusResp.json();
      setPipelineStatus(statusData);
      
    } catch (err) {
      console.error('Analytics load error:', err);
    }
  }, []);

  const loadDashboardData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      console.log('🔄 Loading dashboard data...');
      
      const timeout = (ms) => new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Request timeout')), ms)
      );
      
      const fetchWithTimeout = (promise, ms = 10000) => 
        Promise.race([promise, timeout(ms)]);

      const [farmsData, predictionsData, alertsData, diseasesData, diseasePredsData, satelliteData] = await Promise.all([
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
        }),
        fetchWithTimeout(fetch(`${API_BASE}/farm-satellite/`).then(r => r.json())).catch(err => {
          console.error('❌ Satellite data error:', err.message);
          return [];
        })
      ]);

      // Filter only real Sentinel-2 data
      const realData = Array.isArray(satelliteData) ? satelliteData.filter(f => f.data_source === 'real') : [];
      setRealSatelliteFarms(realData);

      console.log('✅ Data loaded:', {
        farms: farmsData?.length,
        predictions: predictionsData?.length,
        alerts: alertsData?.length,
        diseases: diseasesData?.length,
        diseasePredictions: diseasePredsData?.length,
        realSatelliteData: realData?.length
      });

      const highRisk = Array.isArray(diseasePredsData) ? diseasePredsData.filter(p => 
        p.risk_level === 'high' || p.risk_level === 'severe' || p.risk_level === 'critical'
      ) : [];

      const sorted = Array.isArray(diseasePredsData) ? [...diseasePredsData].sort((a, b) => (b.risk_score || 0) - (a.risk_score || 0)) : [];
      const top3 = sorted.slice(0, 3);

      setStats({
        farms: Array.isArray(farmsData) ? farmsData.length : 0,
        predictions: Array.isArray(predictionsData) ? predictionsData.length : 0,
        alerts: Array.isArray(alertsData) ? alertsData.length : 0,
        diseases: Array.isArray(diseasesData) ? diseasesData.length : 0,
        highRiskDiseases: highRisk.length,
        realSatelliteData: realData.length
      });

      setTopRiskDiseases(top3);
      
      // Load analytics data
      await loadAnalyticsData();
      
      setLoading(false);
    } catch (err) {
      console.error('❌ Failed to load dashboard data:', err);
      setError(err.message || 'Failed to load data');
      setStats({
        farms: 0,
        predictions: 0,
        alerts: 0,
        diseases: 0,
        highRiskDiseases: 0,
        realSatelliteData: 0
      });
      setLoading(false);
    }
  }, [loadAnalyticsData]);

  const handleFetchData = async () => {
    setFetching(true);
    try {
      const response = await fetch(`${API_BASE}/pipeline/fetch-data`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const result = await response.json();
      console.log('Fetch data result:', result);
      
      // Poll for status updates
      const pollStatus = setInterval(async () => {
        const statusResp = await fetch(`${API_BASE}/pipeline/status`);
        const statusData = await statusResp.json();
        setPipelineStatus(statusData);
        
        if (!statusData.is_running) {
          clearInterval(pollStatus);
          setFetching(false);
          loadDashboardData(); // Reload data
        }
      }, 3000);
      
    } catch (err) {
      console.error('Fetch data error:', err);
      setFetching(false);
    }
  };

  const handleApplyExistingTiles = async () => {
    setFetching(true);
    try {
      const response = await fetch(`${API_BASE}/pipeline/apply-existing-tiles`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const result = await response.json();
      console.log('Apply tiles result:', result);
      await loadDashboardData();
    } catch (err) {
      console.error('Apply tiles error:', err);
    }
    setFetching(false);
  };

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  const getFilteredDistrictData = () => {
    if (!selectedProvince) return districtData;
    return districtData.filter(d => d.province === selectedProvince);
  };

  const getFilteredFarmData = () => {
    let filtered = farmData;
    if (selectedProvince) {
      filtered = filtered.filter(f => f.province === selectedProvince);
    }
    if (selectedDistrict) {
      filtered = filtered.filter(f => f.district && f.district.includes(selectedDistrict));
    }
    return filtered;
  };

  const getRiskColor = (riskLevel) => {
    switch (riskLevel) {
      case 'low': return '#10b981';
      case 'moderate': return '#f59e0b';
      case 'high': return '#ef4444';
      case 'critical': return '#7f1d1d';
      default: return '#6b7280';
    }
  };

  const getRiskBg = (riskLevel) => {
    switch (riskLevel) {
      case 'low': return '#d1fae5';
      case 'moderate': return '#fef3c7';
      case 'high': return '#fee2e2';
      case 'critical': return '#fecaca';
      default: return '#f3f4f6';
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-icon">⏳</div>
        <div style={{ fontSize: '18px', color: '#6b7280' }}>Loading dashboard data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <div className="error-icon">⚠️</div>
        <div style={{ fontSize: '24px', color: '#ef4444', marginBottom: '8px', fontWeight: 'bold' }}>Error Loading Dashboard</div>
        <div style={{ fontSize: '16px', color: '#6b7280', marginBottom: '24px' }}>{error}</div>
        <button 
          onClick={loadDashboardData}
          className="btn-primary"
        >
          🔄 Retry
        </button>
      </div>
    );
  }

  return (
    <div className="dashboard-content">
      <div className="dashboard-header-container">
        <div>
          <h1 className="dashboard-title">Crop Risk Dashboard</h1>
          <p className="dashboard-subtitle">Monitor farm health, satellite data, and risk analysis</p>
        </div>
        <div className="dashboard-controls">
          <button
            onClick={handleApplyExistingTiles}
            disabled={fetching}
            className="btn-secondary"
          >
            🔄 Apply Existing Data
          </button>
          <button
            onClick={handleFetchData}
            disabled={fetching}
            className="btn-primary"
          >
            {fetching ? (
              <>⏳ Fetching...</>
            ) : (
              <>🛰️ Fetch Satellite Data</>
            )}
          </button>
        </div>
      </div>

      {/* Pipeline Status Banner */}
      {pipelineStatus && (
        <div className="pipeline-status">
          <div className="pipeline-info">
            <strong>{pipelineStatus.is_running ? '⏳ Pipeline Running' : '✅ Pipeline Ready'}</strong>
            {pipelineStatus.last_run && (
              <span style={{ marginLeft: '16px', color: '#6b7280', fontSize: '13px' }}>
                Last run: {new Date(pipelineStatus.last_run).toLocaleString()}
              </span>
            )}
          </div>
          <div style={{ fontSize: '13px' }}>
            {pipelineStatus.summary && (
              <>
                <span style={{ marginRight: '16px' }}>📊 Avg NDVI: <strong>{pipelineStatus.summary.average_ndvi?.toFixed(4)}</strong></span>
                <span>🏥 Status: <strong style={{ color: getRiskColor(pipelineStatus.summary.overall_risk) }}>{pipelineStatus.summary.overall_health?.toUpperCase()}</strong></span>
              </>
            )}
          </div>
        </div>
      )}
      
      {/* Stats Widgets */}
      <div className="dashboard-widgets">
        <div className="widget">
          <div className="widget-icon">🌾</div>
          <div className="widget-content">
            <div className="widget-value">{stats.farms}</div>
            <div className="widget-label">Monitored Farms</div>
            <div className="widget-sublabel">Active monitoring</div>
          </div>
        </div>

        <div className="widget">
          <div className="widget-icon">🗺️</div>
          <div className="widget-content">
            <div className="widget-value">{provinceData.length}</div>
            <div className="widget-label">Provinces</div>
            <div className="widget-sublabel">Coverage areas</div>
          </div>
        </div>

        <div className="widget">
          <div className="widget-icon">📍</div>
          <div className="widget-content">
            <div className="widget-value">{districtData.length}</div>
            <div className="widget-label">Districts</div>
            <div className="widget-sublabel">Monitored regions</div>
          </div>
        </div>

        <div className="widget">
          <div className="widget-icon">🛰️</div>
          <div className="widget-content">
            <div className="widget-value">{stats.realSatelliteData}</div>
            <div className="widget-label">Real Satellite Data</div>
            <div className="widget-sublabel">Sentinel-2 imagery</div>
          </div>
        </div>

        <div className="widget widget--alert">
          <div className="widget-icon" style={{ background: '#fee2e2', color: '#ef4444' }}>⚠️</div>
          <div className="widget-content">
            <div className="widget-value" style={{ color: '#ef4444' }}>{stats.highRiskDiseases}</div>
            <div className="widget-label">High Risk Areas</div>
          </div>
        </div>
      </div>

      {/* Multi-Level Analysis Section */}
      <div className="dashboard-section">
        <div className="section-header">
          <h3 className="section-title">📊 Multi-Level Risk Analysis</h3>
          <div className="view-tabs">
            <button
              onClick={() => { setAnalysisView('province'); setSelectedProvince(null); setSelectedDistrict(null); }}
              className={`view-tab ${analysisView === 'province' ? 'active' : ''}`}
            >
              By Province
            </button>
            <button
              onClick={() => { setAnalysisView('district'); setSelectedDistrict(null); }}
              className={`view-tab ${analysisView === 'district' ? 'active' : ''}`}
            >
              By District
            </button>
            <button
              onClick={() => setAnalysisView('farm')}
              className={`view-tab ${analysisView === 'farm' ? 'active' : ''}`}
            >
              By Farm
            </button>
          </div>
        </div>

        {/* Breadcrumb / Filters */}
        {(selectedProvince || selectedDistrict) && (
          <div className="filter-tags">
            <span className="filter-label">Filtering:</span>
            {selectedProvince && (
              <span
                onClick={() => { setSelectedProvince(null); setSelectedDistrict(null); }}
                className="filter-tag"
              >
                {selectedProvince} ✕
              </span>
            )}
            {selectedDistrict && (
              <span
                onClick={() => setSelectedDistrict(null)}
                className="filter-tag"
              >
                {selectedDistrict} ✕
              </span>
            )}
          </div>
        )}

        {/* Province View */}
        {analysisView === 'province' && (
          <div className="risk-cards-grid">
            {provinceData.map((prov, idx) => (
              <div
                key={idx}
                className="risk-card"
                style={{
                  borderLeft: `4px solid ${getRiskColor(prov.risk_level)}`
                }}
                onClick={() => { setSelectedProvince(prov.province); setAnalysisView('district'); }}
              >
                <div className="risk-card-header">
                  <span className="risk-badge" style={{ background: getRiskBg(prov.risk_level), color: getRiskColor(prov.risk_level) }}>
                    {prov.province?.charAt(0)}
                  </span>
                  <span className="risk-badge" style={{
                    background: getRiskBg(prov.risk_level),
                    color: getRiskColor(prov.risk_level)
                  }}>
                    {prov.risk_level?.toUpperCase()}
                  </span>
                </div>
                <div className="risk-card-body">
                  <h4 className="risk-card-title">{prov.province} Province</h4>
                  <div className="risk-stat">
                    <span className="risk-stat-label">Farms:</span>
                    <span className="risk-stat-value">{prov.farm_count}</span>
                  </div>
                  <div className="risk-stat">
                    <span className="risk-stat-label">Avg NDVI:</span>
                    <span className="risk-stat-value" style={{ color: getRiskColor(prov.risk_level) }}>
                      {prov.avg_ndvi?.toFixed(4)}
                    </span>
                  </div>
                  <div className="risk-stat">
                    <span className="risk-stat-label">Risk Score:</span>
                    <span className="risk-stat-value" style={{ color: getRiskColor(prov.risk_level) }}>
                      {prov.risk_score?.toFixed(1)}%
                    </span>
                  </div>
                  <div className="risk-recommendation">
                    💡 {prov.recommendation}
                  </div>
                </div>
                <div className="risk-card-footer">
                  <span>Click to view districts →</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* District View */}
        {analysisView === 'district' && (
          <div className="risk-cards-grid">
            {getFilteredDistrictData().map((dist, idx) => (
              <div
                key={idx}
                className="risk-card"
                style={{
                  borderLeft: `4px solid ${getRiskColor(dist.risk_level)}`
                }}
                onClick={() => { setSelectedDistrict(dist.district?.split(',')[0]); setAnalysisView('farm'); }}
              >
                <div className="risk-card-header">
                  <span className="risk-badge" style={{ background: getRiskBg(dist.risk_level), color: getRiskColor(dist.risk_level) }}>
                    📍
                  </span>
                  <span className="risk-badge" style={{
                    background: getRiskBg(dist.risk_level),
                    color: getRiskColor(dist.risk_level)
                  }}>
                    {dist.risk_level?.toUpperCase()}
                  </span>
                </div>
                <div className="risk-card-body">
                  <h4 className="risk-card-title">{dist.district?.split(',')[0]}</h4>
                  <div style={{ fontSize: '13px', color: '#6b7280', marginBottom: '8px' }}>{dist.province} Province</div>
                  <div className="risk-stat">
                    <span className="risk-stat-label">Farms:</span>
                    <span className="risk-stat-value">{dist.farm_count}</span>
                  </div>
                  <div className="risk-stat">
                    <span className="risk-stat-label">Avg NDVI:</span>
                    <span className="risk-stat-value" style={{ color: getRiskColor(dist.risk_level) }}>
                      {dist.avg_ndvi?.toFixed(4)}
                    </span>
                  </div>
                  <div className="risk-stat">
                    <span className="risk-stat-label">Risk Score:</span>
                    <span className="risk-stat-value" style={{ color: getRiskColor(dist.risk_level) }}>
                      {dist.risk_score?.toFixed(1)}%
                    </span>
                  </div>
                  <div className="risk-stat">
                    <span className="risk-stat-label">Time to Impact:</span>
                    <span className="risk-stat-value">{dist.time_to_impact}</span>
                  </div>
                </div>
                <div className="risk-card-footer">
                  <span>Click to view farms →</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Farm View */}
        {analysisView === 'farm' && (
          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Farm</th>
                  <th>District</th>
                  <th>Province</th>
                  <th style={{ textAlign: 'center' }}>NDVI</th>
                  <th style={{ textAlign: 'center' }}>Risk Score</th>
                  <th style={{ textAlign: 'center' }}>Status</th>
                  <th>Recommendation</th>
                </tr>
              </thead>
              <tbody>
                {getFilteredFarmData().slice(0, 20).map((farm, idx) => (
                  <tr key={idx}>
                    <td>
                      <strong>{farm.farm_name}</strong>
                      <div style={{ fontSize: '11px', color: '#6b7280' }}>ID: {farm.farm_id}</div>
                    </td>
                    <td>{farm.district?.split(',')[0]}</td>
                    <td>{farm.province}</td>
                    <td style={{ textAlign: 'center' }}>
                      <span className="table-status-badge" style={{ 
                        background: getRiskBg(farm.risk_level),
                        color: getRiskColor(farm.risk_level)
                      }}>
                        {farm.ndvi?.toFixed(4)}
                      </span>
                    </td>
                    <td style={{ textAlign: 'center' }}>
                      <span style={{ color: getRiskColor(farm.risk_level), fontWeight: 600 }}>
                        {farm.risk_score?.toFixed(1)}%
                      </span>
                    </td>
                    <td style={{ textAlign: 'center' }}>
                      <span className="table-status-badge" style={{
                        background: getRiskBg(farm.risk_level),
                        color: getRiskColor(farm.risk_level)
                      }}>
                        {farm.health_status?.toUpperCase()}
                      </span>
                    </td>
                    <td style={{ fontSize: '13px', color: '#6b7280' }}>
                      {farm.recommendation}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {getFilteredFarmData().length > 20 && (
              <div style={{ textAlign: 'center', padding: '16px', color: '#6b7280' }}>
                Showing 20 of {getFilteredFarmData().length} farms. <a href="/farms" style={{ color: '#3b82f6' }}>View all farms →</a>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Real Satellite Data Section */}
      {realSatelliteFarms.length > 0 && (
        <div className="dashboard-section">
          <div className="section-header">
            <h3 className="section-title">🛰️ Real Sentinel-2 Satellite Data</h3>
            <div style={{ fontSize: '14px', color: '#059669', background: '#d1fae5', padding: '6px 12px', borderRadius: '20px', fontWeight: 600 }}>
              ✅ {realSatelliteFarms.length} farms monitored
            </div>
          </div>
          
          <div className="risk-cards-grid">
            {realSatelliteFarms.slice(0, 6).map((farm, idx) => (
              <div key={idx} className="risk-card" style={{ borderLeft: '4px solid #059669' }}>
                <div className="risk-card-header">
                  <span className="risk-badge" style={{ background: '#d1fae5', color: '#059669' }}>🛰️</span>
                  <span className="risk-badge" style={{ background: '#d1fae5', color: '#059669' }}>REAL DATA</span>
                </div>
                <div className="risk-card-body">
                  <h4 className="risk-card-title">{farm.name || `Farm #${farm.id}`}</h4>
                  <div className="risk-stat">
                    <span className="risk-stat-label">NDVI Value:</span>
                    <span className="risk-stat-value" style={{ color: farm.ndvi >= 0.3 ? '#059669' : '#ef4444' }}>{farm.ndvi?.toFixed(4) || 'N/A'}</span>
                  </div>
                  <div className="risk-stat">
                    <span className="risk-stat-label">Status:</span>
                    <span className="risk-stat-value" style={{ 
                      color: farm.ndvi_status === 'healthy' ? '#059669' : farm.ndvi_status === 'moderate' ? '#f59e0b' : '#ef4444'
                    }}>{farm.ndvi_status?.toUpperCase() || 'N/A'}</span>
                  </div>
                  <div className="risk-stat">
                    <span className="risk-stat-label">Location:</span>
                    <span className="risk-stat-value">{farm.location || 'N/A'}</span>
                  </div>
                  {farm.tile && (
                    <div className="risk-stat">
                      <span className="risk-stat-label">Tile:</span>
                      <span className="risk-stat-value">{farm.tile}</span>
                    </div>
                  )}
                  <div style={{ fontSize: '11px', color: '#6b7280', marginTop: '12px' }}>
                    📅 {farm.ndvi_date || 'N/A'}
                  </div>
                </div>
              </div>
            ))}
          </div>
          {realSatelliteFarms.length > 6 && (
            <div style={{ textAlign: 'center', marginTop: '24px' }}>
              <a href="/farms" className="btn-secondary" style={{ textDecoration: 'none' }}>View all {realSatelliteFarms.length} farms with real data →</a>
            </div>
          )}
        </div>
      )}

      {topRiskDiseases.length > 0 && (
        <div className="dashboard-section">
          <div className="section-header">
            <h3 className="section-title">🔴 Top Disease Risks</h3>
          </div>
          <div className="risk-cards-grid">
            {topRiskDiseases.map((pred, idx) => (
              <div key={idx} className="risk-card">
                <div className="risk-card-header">
                  <span className="risk-badge" style={{ background: '#fee2e2', color: '#ef4444' }}>#{idx + 1}</span>
                  <RiskIndicator 
                    riskScore={pred.risk_score}
                    riskLevel={pred.risk_level}
                    size="small"
                  />
                </div>
                <div className="risk-card-body">
                  <h4 className="risk-card-title">Farm ID: {pred.farm_id}</h4>
                  <div className="risk-stat">
                    <span className="risk-stat-label">Infection Risk:</span>
                    <span className="risk-stat-value">{Math.round(pred.infection_probability * 100)}%</span>
                  </div>
                  {pred.recommended_actions && pred.recommended_actions.length > 0 && (
                    <div className="risk-recommendation">
                      ⚡ {pred.recommended_actions[0]}
                    </div>
                  )}
                </div>
                <div className="risk-card-footer">
                  <a href={`/disease-forecasts?farm=${pred.farm_id}`} style={{ textDecoration: 'none', color: 'inherit' }}>View Forecast →</a>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="dashboard-section">
        <div className="section-header">
          <h3 className="section-title">Quick Actions</h3>
        </div>
        <div className="quick-actions-grid">
          <a href="/satellite-images" className="action-card">
            <span className="action-icon">🛰️</span>
            <span className="action-label">Satellite Images</span>
          </a>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
