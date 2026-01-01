import React, { useEffect, useState } from 'react';
import { fetchSatelliteImageCount, fetchFarms, fetchPredictions, fetchAlerts } from '../api';
import './Dashboard.css';

const Dashboard = () => {
  const [satelliteCount, setSatelliteCount] = useState('--');
  const [farmCount, setFarmCount] = useState('--');
  const [predictionCount, setPredictionCount] = useState('--');
  const [alertCount, setAlertCount] = useState('--');
  const [recentPredictions, setRecentPredictions] = useState([]);
  const [recentAlerts, setRecentAlerts] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [intelligenceMetrics, setIntelligenceMetrics] = useState(null);

  useEffect(() => {
    fetchSatelliteImageCount()
      .then(count => setSatelliteCount(count))
      .catch(() => setSatelliteCount('Error'));
    fetchFarms()
      .then(farms => setFarmCount(farms.length))
      .catch(() => setFarmCount('Error'));
    fetchPredictions()
      .then(preds => {
        console.log('Predictions:', preds);
        setPredictionCount(preds.length);
        setRecentPredictions(preds.slice(-10).reverse());
        
        // Calculate analytics for national-level insights
        if (preds.length > 0) {
          const avgRisk = preds.reduce((sum, p) => sum + p.risk_score, 0) / preds.length;
          const avgYieldLoss = preds.reduce((sum, p) => sum + (p.yield_loss || 0), 0) / preds.length;
          const highRisk = preds.filter(p => p.risk_score >= 60).length;
          const mediumRisk = preds.filter(p => p.risk_score >= 30 && p.risk_score < 60).length;
          const lowRisk = preds.filter(p => p.risk_score < 30).length;
          const criticalDiseaseRisk = preds.filter(p => p.disease_risk === 'Critical' || p.disease_risk === 'High').length;
          
          // Advanced intelligence metrics
          const immediate = preds.filter(p => p.time_to_impact === '< 7 days').length;
          const shortTerm = preds.filter(p => p.time_to_impact === '7-14 days').length;
          const mediumTerm = preds.filter(p => p.time_to_impact === '14-30 days').length;
          const stable = preds.filter(p => p.time_to_impact === '> 30 days (Stable)').length;
          
          const avgConfidence = preds.reduce((sum, p) => sum + (p.confidence_score || 0), 0) / preds.length;
          const highConfidence = preds.filter(p => p.confidence_level === 'High').length;
          
          const totalEconomicLoss = preds.reduce((sum, p) => sum + (p.impact_metrics?.economic_loss_usd || 0), 0);
          const totalYieldLoss = preds.reduce((sum, p) => sum + (p.impact_metrics?.yield_loss_tons || 0), 0);
          const totalMealsLost = preds.reduce((sum, p) => sum + (p.impact_metrics?.meals_lost || 0), 0);
          
          // Top risk drivers across all predictions
          const driverCounts = {};
          preds.forEach(p => {
            if (p.risk_drivers) {
              Object.keys(p.risk_drivers).forEach(driver => {
                driverCounts[driver] = (driverCounts[driver] || 0) + 1;
              });
            }
          });
          const topDrivers = Object.entries(driverCounts)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 3);
          
          setAnalytics({
            avgRisk: avgRisk.toFixed(1),
            avgYieldLoss: avgYieldLoss.toFixed(1),
            highRisk,
            mediumRisk,
            lowRisk,
            criticalDiseaseRisk,
            riskPercentage: ((highRisk / preds.length) * 100).toFixed(1)
          });
          
          setIntelligenceMetrics({
            immediate,
            shortTerm,
            mediumTerm,
            stable,
            avgConfidence: avgConfidence.toFixed(1),
            highConfidence,
            totalEconomicLoss: totalEconomicLoss.toFixed(0),
            totalYieldLoss: totalYieldLoss.toFixed(1),
            totalMealsLost: totalMealsLost.toFixed(0),
            topDrivers
          });
        }
      })
      .catch((err) => {
        console.error('Prediction fetch error:', err);
        setPredictionCount('Error');
        setRecentPredictions([]);
      });
    fetchAlerts()
      .then(alerts => {
        setAlertCount(alerts.length);
        setRecentAlerts(alerts.slice(-10).reverse());
      })
      .catch(() => {
        setAlertCount('Error');
        setRecentAlerts([]);
      });
  }, []);

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
    } catch {
      return dateStr;
    }
  };

  const getRiskBadge = (risk) => {
    if (risk >= 60) return { bg: '#fed7d7', color: '#c53030', label: 'HIGH' };
    if (risk >= 30) return { bg: '#feebc8', color: '#c05621', label: 'MEDIUM' };
    return { bg: '#c6f6d5', color: '#22543d', label: 'LOW' };
  };

  const getTimeToImpactBadge = (timeToImpact) => {
    if (!timeToImpact) return null;
    if (timeToImpact === '< 7 days') return { bg: '#fed7d7', color: '#c53030', icon: '🚨', label: '< 7d' };
    if (timeToImpact === '7-14 days') return { bg: '#feebc8', color: '#c05621', icon: '⚠️', label: '7-14d' };
    if (timeToImpact === '14-30 days') return { bg: '#fefcbf', color: '#744210', icon: '⏰', label: '14-30d' };
    return { bg: '#c6f6d5', color: '#22543d', icon: '✅', label: 'Stable' };
  };

  const getConfidenceBadge = (confidence) => {
    if (confidence === 'High') return { bg: '#c6f6d5', color: '#22543d', label: 'High' };
    if (confidence === 'Medium') return { bg: '#fefcbf', color: '#744210', label: 'Medium' };
    return { bg: '#fed7d7', color: '#c53030', label: 'Low' };
  };

  const formatDriverName = (driver) => {
    const names = {
      'rainfall_deficit': 'Rainfall Deficit',
      'heat_stress_days': 'Heat Stress',
      'ndvi_trend': 'Vegetation Decline',
      'ndvi_anomaly': 'Abnormal Vegetation'
    };
    return names[driver] || driver;
  };

  return (
    <div className="dashboard-content">
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ marginBottom: 8, fontSize: 28, fontWeight: 600 }}>National Crop Risk Assessment Dashboard</h2>
        <p style={{ color: '#718096', fontSize: 14 }}>Real-time agricultural risk monitoring and decision support system for Rwanda</p>
      </div>

      {/* Key Metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginBottom: 32 }}>
        <div style={{ background: '#fff', padding: 20, borderRadius: 8, boxShadow: '0 2px 8px rgba(0,0,0,0.06)', borderLeft: '4px solid #3182ce' }}>
          <div style={{ fontSize: 12, color: '#718096', fontWeight: 600, marginBottom: 4 }}>MONITORED FARMS</div>
          <div style={{ fontSize: 32, fontWeight: 'bold', color: '#2d3748' }}>{farmCount}</div>
        </div>
        <div style={{ background: '#fff', padding: 20, borderRadius: 8, boxShadow: '0 2px 8px rgba(0,0,0,0.06)', borderLeft: '4px solid #48bb78' }}>
          <div style={{ fontSize: 12, color: '#718096', fontWeight: 600, marginBottom: 4 }}>RISK ASSESSMENTS</div>
          <div style={{ fontSize: 32, fontWeight: 'bold', color: '#2d3748' }}>{predictionCount}</div>
        </div>
        <div style={{ background: '#fff', padding: 20, borderRadius: 8, boxShadow: '0 2px 8px rgba(0,0,0,0.06)', borderLeft: '4px solid #ed8936' }}>
          <div style={{ fontSize: 12, color: '#718096', fontWeight: 600, marginBottom: 4 }}>ACTIVE ALERTS</div>
          <div style={{ fontSize: 32, fontWeight: 'bold', color: '#2d3748' }}>{alertCount}</div>
        </div>
        <div style={{ background: '#fff', padding: 20, borderRadius: 8, boxShadow: '0 2px 8px rgba(0,0,0,0.06)', borderLeft: '4px solid #805ad5' }}>
          <div style={{ fontSize: 12, color: '#718096', fontWeight: 600, marginBottom: 4 }}>SATELLITE IMAGES</div>
          <div style={{ fontSize: 32, fontWeight: 'bold', color: '#2d3748' }}>{satelliteCount}</div>
        </div>
      </div>

      {/* National Risk Analytics */}
      {analytics && (
        <div style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', padding: 24, borderRadius: 12, marginBottom: 32, color: '#fff' }}>
          <h3 style={{ marginBottom: 16, fontSize: 18, fontWeight: 600 }}>📊 National Risk Analytics</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 16 }}>
            <div>
              <div style={{ fontSize: 12, opacity: 0.9, marginBottom: 4 }}>Avg Risk Score</div>
              <div style={{ fontSize: 28, fontWeight: 'bold' }}>{analytics.avgRisk}%</div>
            </div>
            <div>
              <div style={{ fontSize: 12, opacity: 0.9, marginBottom: 4 }}>Avg Yield Loss</div>
              <div style={{ fontSize: 28, fontWeight: 'bold' }}>{analytics.avgYieldLoss}%</div>
            </div>
            <div>
              <div style={{ fontSize: 12, opacity: 0.9, marginBottom: 4 }}>High Risk Farms</div>
              <div style={{ fontSize: 28, fontWeight: 'bold' }}>{analytics.highRisk} ({analytics.riskPercentage}%)</div>
            </div>
            <div>
              <div style={{ fontSize: 12, opacity: 0.9, marginBottom: 4 }}>Disease Threats</div>
              <div style={{ fontSize: 28, fontWeight: 'bold' }}>{analytics.criticalDiseaseRisk}</div>
            </div>
          </div>
        </div>
      )}

      {/* Advanced Intelligence Metrics */}
      {intelligenceMetrics && (
        <div style={{ marginBottom: 32, display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 16 }}>
          {/* Time to Impact Distribution */}
          <div style={{ background: '#fff', padding: 20, borderRadius: 12, boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, color: '#2d3748' }}>⏱️ Time to Impact</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 13, color: '#4a5568' }}>🚨 Immediate (&lt; 7 days)</span>
                <span style={{ fontSize: 18, fontWeight: 'bold', color: '#c53030' }}>{intelligenceMetrics.immediate}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 13, color: '#4a5568' }}>⚠️ Short-term (7-14 days)</span>
                <span style={{ fontSize: 18, fontWeight: 'bold', color: '#c05621' }}>{intelligenceMetrics.shortTerm}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 13, color: '#4a5568' }}>⏰ Medium-term (14-30 days)</span>
                <span style={{ fontSize: 18, fontWeight: 'bold', color: '#744210' }}>{intelligenceMetrics.mediumTerm}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 13, color: '#4a5568' }}>✅ Stable (&gt; 30 days)</span>
                <span style={{ fontSize: 18, fontWeight: 'bold', color: '#22543d' }}>{intelligenceMetrics.stable}</span>
              </div>
            </div>
          </div>

          {/* Prediction Confidence */}
          <div style={{ background: '#fff', padding: 20, borderRadius: 12, boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, color: '#2d3748' }}>🎯 Prediction Confidence</h3>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 48, fontWeight: 'bold', color: '#3182ce' }}>{intelligenceMetrics.avgConfidence}%</div>
              <div style={{ fontSize: 13, color: '#718096', marginBottom: 16 }}>Average Confidence Score</div>
              <div style={{ padding: '8px 16px', background: '#ebf8ff', borderRadius: 8, display: 'inline-block' }}>
                <span style={{ fontSize: 13, color: '#2c5282', fontWeight: 600 }}>
                  {intelligenceMetrics.highConfidence} High Confidence Predictions
                </span>
              </div>
            </div>
          </div>

          {/* Impact Metrics */}
          <div style={{ background: '#fff', padding: 20, borderRadius: 12, boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, color: '#2d3748' }}>💰 National Impact</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <div style={{ fontSize: 11, color: '#718096', marginBottom: 4 }}>Economic Loss</div>
                <div style={{ fontSize: 20, fontWeight: 'bold', color: '#c53030' }}>
                  ${parseInt(intelligenceMetrics.totalEconomicLoss).toLocaleString()}
                </div>
              </div>
              <div>
                <div style={{ fontSize: 11, color: '#718096', marginBottom: 4 }}>Yield Loss (tons)</div>
                <div style={{ fontSize: 20, fontWeight: 'bold', color: '#c05621' }}>
                  {parseFloat(intelligenceMetrics.totalYieldLoss).toLocaleString()} tons
                </div>
              </div>
              <div>
                <div style={{ fontSize: 11, color: '#718096', marginBottom: 4 }}>Food Security Impact</div>
                <div style={{ fontSize: 20, fontWeight: 'bold', color: '#744210' }}>
                  {parseInt(intelligenceMetrics.totalMealsLost).toLocaleString()} meals
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Top Risk Drivers */}
      {intelligenceMetrics && intelligenceMetrics.topDrivers.length > 0 && (
        <div style={{ background: '#fff', padding: 24, borderRadius: 12, marginBottom: 32, boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
          <h3 style={{ marginBottom: 16, fontSize: 18, fontWeight: 600 }}>🔍 Most Common Risk Drivers Nationwide</h3>
          <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
            {intelligenceMetrics.topDrivers.map(([driver, count]) => (
              <div key={driver} style={{ 
                flex: '1 1 200px',
                padding: '16px 20px',
                background: 'linear-gradient(135deg, #f6f8fa 0%, #edf2f7 100%)',
                borderRadius: 8,
                borderLeft: '4px solid #3182ce'
              }}>
                <div style={{ fontSize: 13, color: '#718096', marginBottom: 4 }}>
                  {formatDriverName(driver)}
                </div>
                <div style={{ fontSize: 24, fontWeight: 'bold', color: '#2d3748' }}>
                  {count} <span style={{ fontSize: 14, fontWeight: 'normal', color: '#718096' }}>farms affected</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Risk Distribution */}
      {analytics && (
        <div style={{ background: '#fff', padding: 24, borderRadius: 12, marginBottom: 32, boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
          <h3 style={{ marginBottom: 16, fontSize: 18, fontWeight: 600 }}>Risk Distribution Across Monitored Farms</h3>
          <div style={{ display: 'flex', gap: 16, alignItems: 'flex-end', height: 200 }}>
            <div style={{ flex: 1, textAlign: 'center' }}>
              <div style={{ 
                background: '#c6f6d5', 
                height: `${(analytics.lowRisk / predictionCount) * 200}px`, 
                borderRadius: '8px 8px 0 0',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 'bold',
                fontSize: 24,
                color: '#22543d',
                minHeight: 40
              }}>
                {analytics.lowRisk}
              </div>
              <div style={{ marginTop: 8, fontSize: 12, fontWeight: 600, color: '#22543d' }}>LOW RISK</div>
              <div style={{ fontSize: 11, color: '#718096' }}>&lt; 30%</div>
            </div>
            <div style={{ flex: 1, textAlign: 'center' }}>
              <div style={{ 
                background: '#feebc8', 
                height: `${(analytics.mediumRisk / predictionCount) * 200}px`, 
                borderRadius: '8px 8px 0 0',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 'bold',
                fontSize: 24,
                color: '#c05621',
                minHeight: 40
              }}>
                {analytics.mediumRisk}
              </div>
              <div style={{ marginTop: 8, fontSize: 12, fontWeight: 600, color: '#c05621' }}>MEDIUM RISK</div>
              <div style={{ fontSize: 11, color: '#718096' }}>30-60%</div>
            </div>
            <div style={{ flex: 1, textAlign: 'center' }}>
              <div style={{ 
                background: '#fed7d7', 
                height: `${(analytics.highRisk / predictionCount) * 200}px`, 
                borderRadius: '8px 8px 0 0',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 'bold',
                fontSize: 24,
                color: '#c53030',
                minHeight: 40
              }}>
                {analytics.highRisk}
              </div>
              <div style={{ marginTop: 8, fontSize: 12, fontWeight: 600, color: '#c53030' }}>HIGH RISK</div>
              <div style={{ fontSize: 11, color: '#718096' }}>&gt; 60%</div>
            </div>
          </div>
        </div>
      )}

      <div style={{marginTop: 32, display: 'flex', gap: 24, flexWrap: 'wrap'}}>
        <div style={{flex: 2, minWidth: 400}}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h3 style={{ fontSize: 18, fontWeight: 600 }}>Recent Risk Assessments</h3>
            <span style={{ fontSize: 12, color: '#718096' }}>Last 10 predictions</span>
          </div>
          <div style={{ background: '#fff', borderRadius: 12, boxShadow: '0 2px 12px rgba(0,0,0,0.08)', overflow: 'hidden' }}>
            <table style={{width: '100%', borderCollapse: 'collapse'}}>
              <thead>
                <tr style={{background: '#f7fafc', borderBottom: '2px solid #e2e8f0'}}>
                  <th style={{padding: 12, textAlign: 'left', fontSize: 12, fontWeight: 600, color: '#4a5568'}}>FARM</th>
                  <th style={{padding: 12, textAlign: 'left', fontSize: 12, fontWeight: 600, color: '#4a5568'}}>RISK</th>
                  <th style={{padding: 12, textAlign: 'left', fontSize: 12, fontWeight: 600, color: '#4a5568'}}>TIME</th>
                  <th style={{padding: 12, textAlign: 'left', fontSize: 12, fontWeight: 600, color: '#4a5568'}}>CONF.</th>
                  <th style={{padding: 12, textAlign: 'left', fontSize: 12, fontWeight: 600, color: '#4a5568'}}>DRIVERS</th>
                </tr>
              </thead>
              <tbody>
                {recentPredictions.length === 0 && (
                  <tr><td colSpan={5} style={{padding: 24, textAlign: 'center', color: '#a0aec0'}}>No risk assessments available.</td></tr>
                )}
                {recentPredictions.map((pred, idx) => {
                  const badge = getRiskBadge(pred.risk_score);
                  const timeBadge = getTimeToImpactBadge(pred.time_to_impact);
                  const confBadge = getConfidenceBadge(pred.confidence_level);
                  const topDriver = pred.risk_drivers ? Object.entries(pred.risk_drivers)
                    .sort((a, b) => b[1] - a[1])[0] : null;
                  
                  return (
                    <tr 
                      key={pred.id} 
                      style={{
                        borderBottom: '1px solid #f7fafc', 
                        background: idx % 2 === 0 ? '#fff' : '#fafafa',
                        cursor: 'pointer'
                      }}
                      onClick={() => {
                        // Expand to show details
                        const row = document.getElementById(`detail-${pred.id}`);
                        if (row) row.style.display = row.style.display === 'none' ? 'table-row' : 'none';
                      }}
                    >
                      <td style={{padding: 12, fontWeight: 600}}>
                        <div>#{pred.farm_id}</div>
                        <div style={{ fontSize: 10, color: '#718096' }}>{formatDate(pred.predicted_at)}</div>
                      </td>
                      <td style={{padding: 12}}>
                        <div style={{ marginBottom: 4 }}>
                          <span style={{
                            padding: '4px 12px',
                            borderRadius: 12,
                            fontSize: 11,
                            fontWeight: 'bold',
                            background: badge.bg,
                            color: badge.color
                          }}>
                            {pred.risk_score.toFixed(1)}%
                          </span>
                        </div>
                        <div style={{ fontSize: 10, color: '#718096' }}>
                          Yield: {pred.yield_loss ? pred.yield_loss.toFixed(1) + '%' : '-'}
                        </div>
                      </td>
                      <td style={{padding: 12}}>
                        {timeBadge && (
                          <span style={{
                            padding: '4px 8px',
                            borderRadius: 8,
                            fontSize: 10,
                            fontWeight: 'bold',
                            background: timeBadge.bg,
                            color: timeBadge.color,
                            whiteSpace: 'nowrap'
                          }}>
                            {timeBadge.icon} {timeBadge.label}
                          </span>
                        )}
                      </td>
                      <td style={{padding: 12}}>
                        {confBadge && (
                          <div>
                            <span style={{
                              padding: '3px 8px',
                              borderRadius: 6,
                              fontSize: 10,
                              fontWeight: 'bold',
                              background: confBadge.bg,
                              color: confBadge.color
                            }}>
                              {confBadge.label}
                            </span>
                            <div style={{ fontSize: 10, color: '#718096', marginTop: 2 }}>
                              {pred.confidence_score?.toFixed(0)}%
                            </div>
                          </div>
                        )}
                      </td>
                      <td style={{padding: 12, fontSize: 11, color: '#4a5568'}}>
                        {topDriver ? (
                          <div>
                            <div style={{ fontWeight: 600 }}>{formatDriverName(topDriver[0])}</div>
                            <div style={{ fontSize: 10, color: '#718096' }}>{topDriver[1].toFixed(0)}% contribution</div>
                          </div>
                        ) : '-'}
                      </td>
                    </tr>
                  );
                })}
                {recentPredictions.map((pred) => (
                  <tr 
                    key={`detail-${pred.id}`}
                    id={`detail-${pred.id}`}
                    style={{ display: 'none', background: '#f7fafc' }}
                  >
                    <td colSpan={5} style={{ padding: 16 }}>
                      <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
                        {/* Risk Explanation */}
                        <div style={{ flex: '1 1 300px' }}>
                          <div style={{ fontSize: 12, fontWeight: 600, color: '#4a5568', marginBottom: 8 }}>
                            📋 Risk Explanation
                          </div>
                          <div style={{ fontSize: 13, color: '#2d3748', lineHeight: 1.5 }}>
                            {pred.risk_explanation || 'No explanation available'}
                          </div>
                        </div>
                        
                        {/* Recommendations */}
                        {pred.recommendations && pred.recommendations.length > 0 && (
                          <div style={{ flex: '1 1 300px' }}>
                            <div style={{ fontSize: 12, fontWeight: 600, color: '#4a5568', marginBottom: 8 }}>
                              💡 Recommendations
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                              {pred.recommendations.slice(0, 2).map((rec, idx) => (
                                <div 
                                  key={idx}
                                  style={{ 
                                    padding: 8,
                                    background: rec.urgency === 'Immediate' ? '#fff5f5' : '#fffaf0',
                                    borderLeft: `3px solid ${rec.urgency === 'Immediate' ? '#e53e3e' : '#ed8936'}`,
                                    borderRadius: 4,
                                    fontSize: 12
                                  }}
                                >
                                  <div style={{ fontWeight: 600, marginBottom: 2 }}>
                                    {rec.urgency}: {rec.action}
                                  </div>
                                  <div style={{ fontSize: 10, color: '#718096' }}>
                                    {rec.timeframe} • {rec.priority} Priority
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                        
                        {/* Impact Metrics */}
                        {pred.impact_metrics && (
                          <div style={{ flex: '1 1 200px' }}>
                            <div style={{ fontSize: 12, fontWeight: 600, color: '#4a5568', marginBottom: 8 }}>
                              📊 Impact Metrics
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 12 }}>
                              <div>
                                💰 Economic: <strong>${pred.impact_metrics.economic_loss_usd?.toFixed(0)}</strong>
                              </div>
                              <div>
                                🌾 Yield Loss: <strong>{pred.impact_metrics.yield_loss_tons?.toFixed(1)} tons</strong>
                              </div>
                              <div>
                                🍚 Meals Lost: <strong>{pred.impact_metrics.meals_lost?.toFixed(0)}</strong>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        <div style={{flex: 1, minWidth: 300}}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h3 style={{ fontSize: 18, fontWeight: 600 }}>Priority Alerts</h3>
            <span style={{ fontSize: 12, color: '#718096' }}>Real-time</span>
          </div>
          <div style={{ background: '#fff', borderRadius: 12, boxShadow: '0 2px 12px rgba(0,0,0,0.08)', maxHeight: 600, overflowY: 'auto' }}>
            {recentAlerts.length === 0 && (
              <div style={{ padding: 24, textAlign: 'center', color: '#a0aec0' }}>No alerts available.</div>
            )}
            {recentAlerts.map((alert, idx) => {
              let bgColor = '#ebf8ff', borderColor = '#3182ce', icon = '\u2139\ufe0f';
              if (alert.level === 'warning') {
                bgColor = '#fffaf0';
                borderColor = '#ed8936';
                icon = '\u26a0\ufe0f';
              } else if (alert.level === 'critical') {
                bgColor = '#fff5f5';
                borderColor = '#e53e3e';
                icon = '\u26d4';
              }
              return (
                <div key={alert.id} style={{
                  padding: 16,
                  borderBottom: idx < recentAlerts.length - 1 ? '1px solid #f7fafc' : 'none',
                  borderLeft: `4px solid ${borderColor}`,
                  background: bgColor
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 4 }}>
                    <span style={{ fontWeight: 600, fontSize: 13 }}>{icon} Farm #{alert.farm_id}</span>
                    <span style={{ fontSize: 11, color: '#718096' }}>{formatDate(alert.created_at)}</span>
                  </div>
                  <div style={{ fontSize: 13, color: '#4a5568', lineHeight: 1.5 }}>{alert.message}</div>
                  <div style={{ marginTop: 8 }}>
                    <span style={{
                      padding: '2px 8px',
                      borderRadius: 8,
                      fontSize: 10,
                      fontWeight: 'bold',
                      textTransform: 'uppercase',
                      background: borderColor,
                      color: '#fff'
                    }}>
                      {alert.level}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Action Items */}
      <div style={{ marginTop: 32, background: '#fffaf0', borderLeft: '4px solid #dd6b20', padding: 20, borderRadius: 8 }}>
        <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8, color: '#7c2d12' }}>📋 Recommended Actions</h3>
        <ul style={{ margin: 0, paddingLeft: 20, color: '#744210' }}>
          {intelligenceMetrics && intelligenceMetrics.immediate > 0 && (
            <li style={{ marginBottom: 8 }}>
              <strong>🚨 URGENT:</strong> {intelligenceMetrics.immediate} farms require immediate intervention (impact expected within 7 days)
            </li>
          )}
          {intelligenceMetrics && intelligenceMetrics.shortTerm > 0 && (
            <li style={{ marginBottom: 8 }}>
              <strong>⚠️ HIGH PRIORITY:</strong> {intelligenceMetrics.shortTerm} farms at risk in 7-14 days - prepare field deployment
            </li>
          )}
          {analytics && analytics.highRisk > 0 && (
            <li style={{ marginBottom: 8 }}>
              <strong>{analytics.highRisk} farms</strong> are at high risk - immediate intervention recommended
            </li>
          )}
          {intelligenceMetrics && parseFloat(intelligenceMetrics.totalEconomicLoss) > 50000 && (
            <li style={{ marginBottom: 8 }}>
              Projected economic loss of <strong>${parseInt(intelligenceMetrics.totalEconomicLoss).toLocaleString()}</strong> - consider emergency agricultural support programs
            </li>
          )}
          {intelligenceMetrics && intelligenceMetrics.topDrivers.length > 0 && (
            <li style={{ marginBottom: 8 }}>
              Primary threat: <strong>{formatDriverName(intelligenceMetrics.topDrivers[0][0])}</strong> affecting {intelligenceMetrics.topDrivers[0][1]} farms - deploy targeted interventions
            </li>
          )}
          <li>Monitor satellite imagery for vegetation health changes across all districts</li>
        </ul>
      </div>
    </div>
  );
};

export default Dashboard;
