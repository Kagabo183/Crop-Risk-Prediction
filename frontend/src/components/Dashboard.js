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
          
          setAnalytics({
            avgRisk: avgRisk.toFixed(1),
            avgYieldLoss: avgYieldLoss.toFixed(1),
            highRisk,
            mediumRisk,
            lowRisk,
            criticalDiseaseRisk,
            riskPercentage: ((highRisk / preds.length) * 100).toFixed(1)
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
                  <th style={{padding: 12, textAlign: 'left', fontSize: 12, fontWeight: 600, color: '#4a5568'}}>FARM ID</th>
                  <th style={{padding: 12, textAlign: 'left', fontSize: 12, fontWeight: 600, color: '#4a5568'}}>DATE</th>
                  <th style={{padding: 12, textAlign: 'left', fontSize: 12, fontWeight: 600, color: '#4a5568'}}>RISK LEVEL</th>
                  <th style={{padding: 12, textAlign: 'right', fontSize: 12, fontWeight: 600, color: '#4a5568'}}>RISK SCORE</th>
                  <th style={{padding: 12, textAlign: 'right', fontSize: 12, fontWeight: 600, color: '#4a5568'}}>YIELD LOSS</th>
                  <th style={{padding: 12, textAlign: 'left', fontSize: 12, fontWeight: 600, color: '#4a5568'}}>DISEASE</th>
                </tr>
              </thead>
              <tbody>
                {recentPredictions.length === 0 && (
                  <tr><td colSpan={6} style={{padding: 24, textAlign: 'center', color: '#a0aec0'}}>No risk assessments available.</td></tr>
                )}
                {recentPredictions.map((pred, idx) => {
                  const badge = getRiskBadge(pred.risk_score);
                  return (
                    <tr key={pred.id} style={{borderBottom: '1px solid #f7fafc', background: idx % 2 === 0 ? '#fff' : '#fafafa'}}>
                      <td style={{padding: 12, fontWeight: 600}}>#{pred.farm_id}</td>
                      <td style={{padding: 12, fontSize: 13}}>{formatDate(pred.predicted_at)}</td>
                      <td style={{padding: 12}}>
                        <span style={{
                          padding: '4px 12px',
                          borderRadius: 12,
                          fontSize: 11,
                          fontWeight: 'bold',
                          background: badge.bg,
                          color: badge.color
                        }}>
                          {badge.label}
                        </span>
                      </td>
                      <td style={{padding: 12, textAlign: 'right', fontWeight: 600, color: badge.color}}>{pred.risk_score.toFixed(1)}%</td>
                      <td style={{padding: 12, textAlign: 'right', color: '#4a5568'}}>{pred.yield_loss ? pred.yield_loss.toFixed(1) + '%' : '-'}</td>
                      <td style={{padding: 12, fontSize: 13}}>{pred.disease_risk || '-'}</td>
                    </tr>
                  );
                })}
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
        <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8, color: '#7c2d12' }}>\ud83d\udccb Recommended Actions</h3>
        <ul style={{ margin: 0, paddingLeft: 20, color: '#744210' }}>
          {analytics && analytics.highRisk > 0 && (
            <li style={{ marginBottom: 8 }}>
              <strong>{analytics.highRisk} farms</strong> are at high risk - immediate intervention recommended
            </li>
          )}
          {analytics && analytics.criticalDiseaseRisk > 0 && (
            <li style={{ marginBottom: 8 }}>
              <strong>{analytics.criticalDiseaseRisk} farms</strong> showing critical disease indicators - deploy field agents
            </li>
          )}
          {analytics && analytics.avgYieldLoss > 10 && (
            <li style={{ marginBottom: 8 }}>
              Average projected yield loss of <strong>{analytics.avgYieldLoss}%</strong> - consider national support programs
            </li>
          )}
          <li>Monitor satellite imagery for vegetation health changes across all districts</li>
        </ul>
      </div>
    </div>
  );
};

export default Dashboard;
