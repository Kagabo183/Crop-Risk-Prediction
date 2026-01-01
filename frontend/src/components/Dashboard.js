import React, { useEffect, useState } from 'react';
import { fetchSatelliteImageCount, fetchFarms, fetchPredictions, fetchAlerts } from '../api';
import MapPanel from './MapPanel';
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
  const [farmsList, setFarmsList] = useState([]);
  const [allPredictions, setAllPredictions] = useState([]);
  const [selectedFarmId, setSelectedFarmId] = useState(null);
  const [filters, setFilters] = useState({});
  const [expandedRows, setExpandedRows] = useState([]);

  useEffect(() => {
    fetchSatelliteImageCount()
      .then(count => setSatelliteCount(count))
      .catch(() => setSatelliteCount('Error'));
    fetchFarms()
      .then(farms => {
        setFarmCount(farms.length);
        setFarmsList(farms);
      })
      .catch(() => setFarmCount('Error'));
    fetchPredictions()
      .then(preds => {
        console.log('Predictions:', preds);
        setPredictionCount(preds.length);
        setAllPredictions(preds);
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

  const toggleRow = (predId) => {
    setExpandedRows(prev => {
      const copy = new Set(prev);
      if (copy.has(predId)) copy.delete(predId); else copy.add(predId);
      return Array.from(copy);
    });
  };

  const handleSelectFarm = (farmId) => {
    setSelectedFarmId(farmId);
    // Expand most recent prediction for this farm if exists
    const predsForFarm = allPredictions.filter(p => p.farm_id === farmId);
    if (predsForFarm.length > 0) {
      const latest = predsForFarm[predsForFarm.length - 1];
      setExpandedRows(prev => Array.from(new Set([...prev, latest.id])));
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
    <div className="dashboard-content" style={{ padding: '24px 32px', maxWidth: 1800, margin: '0 auto', background: '#f8fafc' }}>
      {/* Page Header */}
      <div style={{ marginBottom: 32, padding: '24px 0', borderBottom: '2px solid #e2e8f0' }}>
        <h1 style={{ margin: 0, marginBottom: 8, fontSize: 32, fontWeight: 700, color: '#1a202c' }}>
          🌾 National Crop Risk Assessment
        </h1>
        <p style={{ margin: 0, color: '#718096', fontSize: 15, fontWeight: 500 }}>
          Real-time agricultural risk monitoring and decision support system for Rwanda
        </p>
      </div>

      {/* Key Metrics - More compact and visual */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 20, marginBottom: 36 }}>
        <div style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', padding: '24px 20px', borderRadius: 12, boxShadow: '0 4px 12px rgba(102, 126, 234, 0.3)', position: 'relative', overflow: 'hidden' }}>
          <div style={{ position: 'absolute', top: -10, right: -10, fontSize: 80, opacity: 0.15 }}>🚜</div>
          <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.9)', fontWeight: 600, marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5 }}>Monitored Farms</div>
          <div style={{ fontSize: 40, fontWeight: 'bold', color: '#fff' }}>{farmCount}</div>
          <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.8)', marginTop: 4 }}>Active monitoring</div>
        </div>
        
        <div style={{ background: 'linear-gradient(135deg, #48bb78 0%, #38a169 100%)', padding: '24px 20px', borderRadius: 12, boxShadow: '0 4px 12px rgba(72, 187, 120, 0.3)', position: 'relative', overflow: 'hidden' }}>
          <div style={{ position: 'absolute', top: -10, right: -10, fontSize: 80, opacity: 0.15 }}>📊</div>
          <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.9)', fontWeight: 600, marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5 }}>Risk Assessments</div>
          <div style={{ fontSize: 40, fontWeight: 'bold', color: '#fff' }}>{predictionCount}</div>
          <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.8)', marginTop: 4 }}>Total predictions</div>
        </div>
        
        <div style={{ background: 'linear-gradient(135deg, #ed8936 0%, #dd6b20 100%)', padding: '24px 20px', borderRadius: 12, boxShadow: '0 4px 12px rgba(237, 137, 54, 0.3)', position: 'relative', overflow: 'hidden' }}>
          <div style={{ position: 'absolute', top: -10, right: -10, fontSize: 80, opacity: 0.15 }}>⚠️</div>
          <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.9)', fontWeight: 600, marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5 }}>Active Alerts</div>
          <div style={{ fontSize: 40, fontWeight: 'bold', color: '#fff' }}>{alertCount}</div>
          <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.8)', marginTop: 4 }}>Requiring attention</div>
        </div>
        
        <div style={{ background: 'linear-gradient(135deg, #3182ce 0%, #2c5282 100%)', padding: '24px 20px', borderRadius: 12, boxShadow: '0 4px 12px rgba(49, 130, 206, 0.3)', position: 'relative', overflow: 'hidden' }}>
          <div style={{ position: 'absolute', top: -10, right: -10, fontSize: 80, opacity: 0.15 }}>🛰️</div>
          <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.9)', fontWeight: 600, marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5 }}>Satellite Images</div>
          <div style={{ fontSize: 40, fontWeight: 'bold', color: '#fff' }}>{satelliteCount}</div>
          <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.8)', marginTop: 4 }}>Data points collected</div>
        </div>
      </div>

      {/* National Risk Analytics */}
      {analytics && (
        <div style={{ 
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 
          padding: 32, 
          borderRadius: 16, 
          marginBottom: 36, 
          color: '#fff',
          boxShadow: '0 10px 30px rgba(102, 126, 234, 0.3)',
          position: 'relative',
          overflow: 'hidden'
        }}>
          <div style={{ position: 'absolute', top: -50, right: -50, width: 200, height: 200, background: 'rgba(255,255,255,0.08)', borderRadius: '50%' }}></div>
          <div style={{ position: 'absolute', bottom: -30, left: -30, width: 150, height: 150, background: 'rgba(255,255,255,0.05)', borderRadius: '50%' }}></div>
          
          <div style={{ position: 'relative', zIndex: 1 }}>
            <h3 style={{ marginBottom: 20, fontSize: 24, fontWeight: 700, letterSpacing: -0.5 }}>📊 National Risk Analytics</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 20 }}>
              <div style={{ background: 'rgba(255,255,255,0.15)', padding: 20, borderRadius: 12, backdropFilter: 'blur(10px)' }}>
                <div style={{ fontSize: 13, opacity: 0.9, marginBottom: 8, fontWeight: 600 }}>Avg Risk Score</div>
                <div style={{ fontSize: 36, fontWeight: 'bold' }}>{analytics.avgRisk}%</div>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.15)', padding: 20, borderRadius: 12, backdropFilter: 'blur(10px)' }}>
                <div style={{ fontSize: 13, opacity: 0.9, marginBottom: 8, fontWeight: 600 }}>Avg Yield Loss</div>
                <div style={{ fontSize: 36, fontWeight: 'bold' }}>{analytics.avgYieldLoss}%</div>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.15)', padding: 20, borderRadius: 12, backdropFilter: 'blur(10px)' }}>
                <div style={{ fontSize: 13, opacity: 0.9, marginBottom: 8, fontWeight: 600 }}>High Risk Farms</div>
                <div style={{ fontSize: 36, fontWeight: 'bold' }}>{analytics.highRisk}</div>
                <div style={{ fontSize: 12, opacity: 0.8, marginTop: 4 }}>({analytics.riskPercentage}% of total)</div>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.15)', padding: 20, borderRadius: 12, backdropFilter: 'blur(10px)' }}>
                <div style={{ fontSize: 13, opacity: 0.9, marginBottom: 8, fontWeight: 600 }}>Disease Threats</div>
                <div style={{ fontSize: 36, fontWeight: 'bold' }}>{analytics.criticalDiseaseRisk}</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Advanced Intelligence Metrics */}
      {intelligenceMetrics && (
        <div style={{ marginBottom: 36, display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 20 }}>
          {/* Time to Impact Distribution */}
          <div style={{ background: '#fff', padding: 24, borderRadius: 16, boxShadow: '0 4px 16px rgba(0,0,0,0.08)', border: '1px solid #e2e8f0' }}>
            <h3 style={{ fontSize: 17, fontWeight: 700, marginBottom: 20, color: '#1a202c', display: 'flex', alignItems: 'center', gap: 8 }}>
              <span>⏱️</span> Time to Impact
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: 12, background: '#fee', borderRadius: 10, border: '1px solid #fecaca' }}>
                <span style={{ fontSize: 14, color: '#7f1d1d', fontWeight: 600 }}>🚨 Immediate (&lt; 7 days)</span>
                <span style={{ fontSize: 22, fontWeight: 'bold', color: '#c53030' }}>{intelligenceMetrics.immediate}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: 12, background: '#fef3c7', borderRadius: 10, border: '1px solid #fde68a' }}>
                <span style={{ fontSize: 14, color: '#78350f', fontWeight: 600 }}>⚠️ Short-term (7-14 days)</span>
                <span style={{ fontSize: 22, fontWeight: 'bold', color: '#c05621' }}>{intelligenceMetrics.shortTerm}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: 12, background: '#fef3e2', borderRadius: 10, border: '1px solid #fed7aa' }}>
                <span style={{ fontSize: 14, color: '#7c2d12', fontWeight: 600 }}>⏰ Medium-term (14-30 days)</span>
                <span style={{ fontSize: 22, fontWeight: 'bold', color: '#92400e' }}>{intelligenceMetrics.mediumTerm}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: 12, background: '#ecfdf5', borderRadius: 10, border: '1px solid #a7f3d0' }}>
                <span style={{ fontSize: 14, color: '#064e3b', fontWeight: 600 }}>✅ Stable (&gt; 30 days)</span>
                <span style={{ fontSize: 22, fontWeight: 'bold', color: '#22543d' }}>{intelligenceMetrics.stable}</span>
              </div>
            </div>
          </div>

          {/* Prediction Confidence */}
          <div style={{ background: '#fff', padding: 24, borderRadius: 16, boxShadow: '0 4px 16px rgba(0,0,0,0.08)', border: '1px solid #e2e8f0' }}>
            <h3 style={{ fontSize: 17, fontWeight: 700, marginBottom: 20, color: '#1a202c', display: 'flex', alignItems: 'center', gap: 8 }}>
              <span>🎯</span> Prediction Confidence
            </h3>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 56, fontWeight: 'bold', color: '#3182ce', marginBottom: 8 }}>{intelligenceMetrics.avgConfidence}%</div>
              <div style={{ fontSize: 14, color: '#718096', marginBottom: 20, fontWeight: 500 }}>Average Confidence Score</div>
              <div style={{ padding: '12px 20px', background: '#ebf8ff', borderRadius: 10, display: 'inline-block', border: '1px solid #bee3f8' }}>
                <span style={{ fontSize: 14, color: '#2c5282', fontWeight: 700 }}>
                  {intelligenceMetrics.highConfidence} High Confidence Predictions
                </span>
              </div>
            </div>
          </div>

          {/* Impact Metrics */}
          <div style={{ background: '#fff', padding: 24, borderRadius: 16, boxShadow: '0 4px 16px rgba(0,0,0,0.08)', border: '1px solid #e2e8f0' }}>
            <h3 style={{ fontSize: 17, fontWeight: 700, marginBottom: 20, color: '#1a202c', display: 'flex', alignItems: 'center', gap: 8 }}>
              <span>💰</span> National Impact
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div style={{ padding: 16, background: '#fef2f2', borderRadius: 10, border: '1px solid #fecaca' }}>
                <div style={{ fontSize: 12, color: '#7f1d1d', marginBottom: 6, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5 }}>Economic Loss</div>
                <div style={{ fontSize: 26, fontWeight: 'bold', color: '#c53030' }}>
                  ${parseInt(intelligenceMetrics.totalEconomicLoss).toLocaleString()}
                </div>
              </div>
              <div style={{ padding: 16, background: '#fff7ed', borderRadius: 10, border: '1px solid #fed7aa' }}>
                <div style={{ fontSize: 12, color: '#7c2d12', marginBottom: 6, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5 }}>Yield Loss</div>
                <div style={{ fontSize: 26, fontWeight: 'bold', color: '#c05621' }}>
                  {parseFloat(intelligenceMetrics.totalYieldLoss).toLocaleString()} tons
                </div>
              </div>
              <div style={{ padding: 16, background: '#fef3e2', borderRadius: 10, border: '1px solid #fde68a' }}>
                <div style={{ fontSize: 12, color: '#78350f', marginBottom: 6, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5 }}>Food Security Impact</div>
                <div style={{ fontSize: 26, fontWeight: 'bold', color: '#92400e' }}>
                  {parseInt(intelligenceMetrics.totalMealsLost).toLocaleString()} meals
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Top Risk Drivers */}
      {intelligenceMetrics && intelligenceMetrics.topDrivers.length > 0 && (
        <div style={{ background: '#fff', padding: 28, borderRadius: 16, marginBottom: 36, boxShadow: '0 4px 16px rgba(0,0,0,0.08)', border: '1px solid #e2e8f0' }}>
          <h3 style={{ marginBottom: 20, fontSize: 20, fontWeight: 700, color: '#1a202c', display: 'flex', alignItems: 'center', gap: 8 }}>
            <span>🔍</span> Most Common Risk Drivers Nationwide
          </h3>
          <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
            {intelligenceMetrics.topDrivers.map(([driver, count]) => (
              <div key={driver} style={{ 
                flex: '1 1 220px',
                padding: '20px 24px',
                background: 'linear-gradient(135deg, #f6f8fa 0%, #edf2f7 100%)',
                borderRadius: 12,
                borderLeft: '4px solid #3182ce',
                transition: 'all 0.2s',
                boxShadow: '0 2px 8px rgba(0,0,0,0.04)'
              }}>
                <div style={{ fontSize: 14, color: '#4a5568', marginBottom: 8, fontWeight: 600 }}>
                  {formatDriverName(driver)}
                </div>
                <div style={{ fontSize: 28, fontWeight: 'bold', color: '#2d3748' }}>
                  {count}
                </div>
                <div style={{ fontSize: 13, fontWeight: 500, color: '#718096', marginTop: 4 }}>farms affected</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Risk Distribution */}
      {analytics && (
        <div style={{ background: '#fff', padding: 28, borderRadius: 16, marginBottom: 36, boxShadow: '0 4px 16px rgba(0,0,0,0.08)', border: '1px solid #e2e8f0' }}>
          <h3 style={{ marginBottom: 24, fontSize: 20, fontWeight: 700, color: '#1a202c', display: 'flex', alignItems: 'center', gap: 8 }}>
            <span>📊</span> Risk Distribution Across Monitored Farms
          </h3>
          <div style={{ display: 'flex', gap: 24, alignItems: 'flex-end', height: 240 }}>
            <div style={{ flex: 1, textAlign: 'center' }}>
              <div style={{ 
                background: 'linear-gradient(to top, #48bb78, #68d391)', 
                height: `${Math.max((analytics.lowRisk / predictionCount) * 240, 50)}px`, 
                borderRadius: '12px 12px 0 0',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 'bold',
                fontSize: 32,
                color: '#fff',
                boxShadow: '0 4px 12px rgba(72, 187, 120, 0.3)',
                position: 'relative',
                overflow: 'hidden'
              }}>
                <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '40%', background: 'rgba(255,255,255,0.2)' }}></div>
                <span style={{ position: 'relative', zIndex: 1 }}>{analytics.lowRisk}</span>
              </div>
              <div style={{ marginTop: 12, fontSize: 13, fontWeight: 700, color: '#22543d', textTransform: 'uppercase', letterSpacing: 0.5 }}>Low Risk</div>
              <div style={{ fontSize: 12, color: '#718096', marginTop: 4, fontWeight: 500 }}>&lt; 30%</div>
            </div>
            <div style={{ flex: 1, textAlign: 'center' }}>
              <div style={{ 
                background: 'linear-gradient(to top, #ed8936, #f6ad55)', 
                height: `${Math.max((analytics.mediumRisk / predictionCount) * 240, 50)}px`, 
                borderRadius: '12px 12px 0 0',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 'bold',
                fontSize: 32,
                color: '#fff',
                boxShadow: '0 4px 12px rgba(237, 137, 54, 0.3)',
                position: 'relative',
                overflow: 'hidden'
              }}>
                <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '40%', background: 'rgba(255,255,255,0.2)' }}></div>
                <span style={{ position: 'relative', zIndex: 1 }}>{analytics.mediumRisk}</span>
              </div>
              <div style={{ marginTop: 12, fontSize: 13, fontWeight: 700, color: '#c05621', textTransform: 'uppercase', letterSpacing: 0.5 }}>Medium Risk</div>
              <div style={{ fontSize: 12, color: '#718096', marginTop: 4, fontWeight: 500 }}>30-60%</div>
            </div>
            <div style={{ flex: 1, textAlign: 'center' }}>
              <div style={{ 
                background: 'linear-gradient(to top, #e53e3e, #fc8181)', 
                height: `${Math.max((analytics.highRisk / predictionCount) * 240, 50)}px`, 
                borderRadius: '12px 12px 0 0',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 'bold',
                fontSize: 32,
                color: '#fff',
                boxShadow: '0 4px 12px rgba(229, 62, 62, 0.3)',
                position: 'relative',
                overflow: 'hidden'
              }}>
                <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '40%', background: 'rgba(255,255,255,0.2)' }}></div>
                <span style={{ position: 'relative', zIndex: 1 }}>{analytics.highRisk}</span>
              </div>
              <div style={{ marginTop: 12, fontSize: 13, fontWeight: 700, color: '#c53030', textTransform: 'uppercase', letterSpacing: 0.5 }}>High Risk</div>
              <div style={{ fontSize: 12, color: '#718096', marginTop: 4, fontWeight: 500 }}>&gt; 60%</div>
            </div>
          </div>
        </div>
      )}

      <div style={{marginTop: 0, display: 'flex', gap: 28, flexWrap: 'wrap'}}>
        <div style={{flex: 2, minWidth: 500}}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <h3 style={{ fontSize: 22, fontWeight: 700, color: '#1a202c', display: 'flex', alignItems: 'center', gap: 8 }}>
              <span>📋</span> Recent Risk Assessments
            </h3>
            <span style={{ fontSize: 13, color: '#718096', fontWeight: 500 }}>Last 10 predictions</span>
          </div>
          <div style={{ background: '#fff', borderRadius: 16, boxShadow: '0 4px 16px rgba(0,0,0,0.08)', overflow: 'hidden', border: '1px solid #e2e8f0' }}>
            <table style={{width: '100%', borderCollapse: 'collapse'}}>
              <thead>
                <tr style={{background: 'linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%)', borderBottom: '2px solid #cbd5e0'}}>
                  <th style={{padding: '16px 20px', textAlign: 'left', fontSize: 12, fontWeight: 700, color: '#2d3748', textTransform: 'uppercase', letterSpacing: 0.5}}>Farm</th>
                  <th style={{padding: '16px 20px', textAlign: 'left', fontSize: 12, fontWeight: 700, color: '#2d3748', textTransform: 'uppercase', letterSpacing: 0.5}}>Risk</th>
                  <th style={{padding: '16px 20px', textAlign: 'left', fontSize: 12, fontWeight: 700, color: '#2d3748', textTransform: 'uppercase', letterSpacing: 0.5}}>Time</th>
                  <th style={{padding: '16px 20px', textAlign: 'left', fontSize: 12, fontWeight: 700, color: '#2d3748', textTransform: 'uppercase', letterSpacing: 0.5}}>Conf.</th>
                  <th style={{padding: '16px 20px', textAlign: 'left', fontSize: 12, fontWeight: 700, color: '#2d3748', textTransform: 'uppercase', letterSpacing: 0.5}}>Drivers</th>
                </tr>
              </thead>
              <tbody>
                {recentPredictions.length === 0 && (
                  <tr><td colSpan={5} style={{padding: 32, textAlign: 'center', color: '#a0aec0', fontSize: 14}}>No risk assessments available.</td></tr>
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
                        borderBottom: '1px solid #edf2f7', 
                        background: idx % 2 === 0 ? '#fff' : '#f9fafb',
                        cursor: 'pointer',
                        transition: 'all 0.2s'
                      }}
                      onClick={() => {
                        // select farm and toggle details
                        setSelectedFarmId(pred.farm_id);
                        toggleRow(pred.id);
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.background = '#f0f4f8'}
                      onMouseLeave={(e) => e.currentTarget.style.background = idx % 2 === 0 ? '#fff' : '#f9fafb'}
                    >
                      <td style={{padding: '16px 20px', fontWeight: 600, fontSize: 14, color: '#2d3748', background: selectedFarmId === pred.farm_id ? '#fffbe6' : 'inherit' }}>
                        <div style={{ marginBottom: 4 }}>Farm #{pred.farm_id}</div>
                        <div style={{ fontSize: 11, color: '#a0aec0', fontWeight: 500 }}>{formatDate(pred.predicted_at)}</div>
                      </td>
                      <td style={{padding: '16px 20px'}}>
                        <span style={{
                          padding: '6px 14px',
                          borderRadius: 20,
                          fontSize: 12,
                          fontWeight: 700,
                          background: badge.bg,
                          color: badge.color,
                          display: 'inline-block'
                        }}>
                          {pred.risk_score.toFixed(1)}%
                        </span>
                        <div style={{ fontSize: 11, color: '#a0aec0', marginTop: 6, fontWeight: 500 }}>
                          Yield: {pred.yield_loss ? pred.yield_loss.toFixed(1) + '%' : '-'}
                        </div>
                      </td>
                      <td style={{padding: '16px 20px'}}>
                        {timeBadge && (
                          <span style={{
                            padding: '6px 12px',
                            borderRadius: 20,
                            fontSize: 11,
                            fontWeight: 700,
                            background: timeBadge.bg,
                            color: timeBadge.color,
                            whiteSpace: 'nowrap',
                            display: 'inline-block'
                          }}>
                            {timeBadge.icon} {timeBadge.label}
                          </span>
                        )}
                      </td>
                      <td style={{padding: '16px 20px'}}>
                        {confBadge && (
                          <div>
                            <span style={{
                              padding: '5px 12px',
                              borderRadius: 16,
                              fontSize: 11,
                              fontWeight: 700,
                              background: confBadge.bg,
                              color: confBadge.color,
                              display: 'inline-block'
                            }}>
                              {confBadge.label}
                            </span>
                            <div style={{ fontSize: 11, color: '#a0aec0', marginTop: 6, fontWeight: 500 }}>
                              {pred.confidence_score?.toFixed(0)}%
                            </div>
                          </div>
                        )}
                      </td>
                      <td style={{padding: '16px 20px', fontSize: 12, color: '#4a5568', fontWeight: 500}}>
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
                    style={{ display: expandedRows.includes(pred.id) ? 'table-row' : 'none', background: '#f7fafc' }}
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
        <div style={{flex: 1, minWidth: 380, display: 'flex', flexDirection: 'column', gap: 20}}>
          {/* Map Section */}
          <div style={{ background: '#fff', borderRadius: 16, overflow: 'hidden', boxShadow: '0 4px 16px rgba(0,0,0,0.08)', border: '1px solid #e2e8f0' }}>
            <div style={{ padding: '16px 20px', background: 'linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%)', borderBottom: '2px solid #cbd5e0' }}>
              <h3 style={{ fontSize: 18, fontWeight: 700, color: '#1a202c', margin: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
                <span>🗺️</span> Farm Locations
              </h3>
            </div>
            <div style={{ height: 420 }}>
              <MapPanel
                farms={farmsList}
                predictions={allPredictions}
                selectedFarmId={selectedFarmId}
                onSelectFarm={(id) => handleSelectFarm(id)}
                filters={{ ...filters, onChange: (f) => setFilters(f) }}
              />
            </div>
          </div>

          {/* Alerts Section */}
          <div style={{ background: '#fff', borderRadius: 16, boxShadow: '0 4px 16px rgba(0,0,0,0.08)', border: '1px solid #e2e8f0', overflow: 'hidden' }}>
            <div style={{ padding: '16px 20px', background: 'linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%)', borderBottom: '2px solid #cbd5e0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ fontSize: 18, fontWeight: 700, color: '#1a202c', margin: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
                <span>⚠️</span> Priority Alerts
              </h3>
              <span style={{ fontSize: 12, color: '#718096', fontWeight: 600, background: '#fff', padding: '4px 12px', borderRadius: 12 }}>Real-time</span>
            </div>
            <div style={{ maxHeight: 500, overflowY: 'auto' }}>
              {recentAlerts.length === 0 && (
                <div style={{ padding: 32, textAlign: 'center', color: '#a0aec0', fontSize: 14 }}>No alerts available.</div>
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
                  padding: 20,
                  borderBottom: idx < recentAlerts.length - 1 ? '1px solid #edf2f7' : 'none',
                  borderLeft: `4px solid ${borderColor}`,
                  background: bgColor,
                  transition: 'all 0.2s'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                    <span style={{ fontWeight: 700, fontSize: 14, color: '#2d3748' }}>{icon} Farm #{alert.farm_id}</span>
                    <span style={{ fontSize: 11, color: '#a0aec0', fontWeight: 500 }}>{formatDate(alert.created_at)}</span>
                  </div>
                  <div style={{ fontSize: 13, color: '#4a5568', lineHeight: 1.6, marginBottom: 10 }}>{alert.message}</div>
                  <span style={{
                    padding: '4px 12px',
                    borderRadius: 12,
                    fontSize: 11,
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    letterSpacing: 0.5,
                    background: borderColor,
                    color: '#fff',
                    display: 'inline-block'
                  }}>
                    {alert.level}
                  </span>
                </div>
              );
            })}
            </div>
          </div>
        </div>
      </div>

      {/* Action Items */}
      <div style={{ 
        marginTop: 36, 
        background: 'linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%)', 
        borderLeft: '6px solid #f59e0b', 
        padding: 28, 
        borderRadius: 16,
        boxShadow: '0 4px 16px rgba(245, 158, 11, 0.15)',
        border: '1px solid #fde68a'
      }}>
        <h3 style={{ fontSize: 20, fontWeight: 700, marginBottom: 16, color: '#78350f', display: 'flex', alignItems: 'center', gap: 8 }}>
          <span>📋</span> Recommended Actions
        </h3>
        <ul style={{ margin: 0, paddingLeft: 24, color: '#92400e', lineHeight: 1.8 }}>
          {intelligenceMetrics && intelligenceMetrics.immediate > 0 && (
            <li style={{ marginBottom: 12, fontSize: 14, fontWeight: 500 }}>
              <strong style={{ color: '#dc2626' }}>🚨 URGENT:</strong> {intelligenceMetrics.immediate} farms require immediate intervention (impact expected within 7 days)
            </li>
          )}
          {intelligenceMetrics && intelligenceMetrics.shortTerm > 0 && (
            <li style={{ marginBottom: 12, fontSize: 14, fontWeight: 500 }}>
              <strong style={{ color: '#ea580c' }}>⚠️ HIGH PRIORITY:</strong> {intelligenceMetrics.shortTerm} farms at risk in 7-14 days - prepare field deployment
            </li>
          )}
          {analytics && analytics.highRisk > 0 && (
            <li style={{ marginBottom: 12, fontSize: 14, fontWeight: 500 }}>
              <strong>{analytics.highRisk} farms</strong> are at high risk - immediate intervention recommended
            </li>
          )}
          {intelligenceMetrics && parseFloat(intelligenceMetrics.totalEconomicLoss) > 50000 && (
            <li style={{ marginBottom: 12, fontSize: 14, fontWeight: 500 }}>
              Projected economic loss of <strong>${parseInt(intelligenceMetrics.totalEconomicLoss).toLocaleString()}</strong> - consider emergency agricultural support programs
            </li>
          )}
          {intelligenceMetrics && intelligenceMetrics.topDrivers.length > 0 && (
            <li style={{ marginBottom: 12, fontSize: 14, fontWeight: 500 }}>
              Primary threat: <strong>{formatDriverName(intelligenceMetrics.topDrivers[0][0])}</strong> affecting {intelligenceMetrics.topDrivers[0][1]} farms - deploy targeted interventions
            </li>
          )}
          <li style={{ fontSize: 14, fontWeight: 500 }}>Monitor satellite imagery for vegetation health changes across all districts</li>
        </ul>
      </div>
    </div>
  );
};

export default Dashboard;
