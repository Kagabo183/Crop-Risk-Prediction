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

  useEffect(() => {
    fetchSatelliteImageCount()
      .then(count => setSatelliteCount(count))
      .catch(() => setSatelliteCount('Error'));
    fetchFarms()
      .then(farms => setFarmCount(farms.length))
      .catch(() => setFarmCount('Error'));
    fetchPredictions()
      .then(preds => {
        setPredictionCount(preds.length);
        setRecentPredictions(preds.slice(-5).reverse());
      })
      .catch(() => {
        setPredictionCount('Error');
        setRecentPredictions([]);
      });
    fetchAlerts()
      .then(alerts => {
        setAlertCount(alerts.length);
        setRecentAlerts(alerts.slice(-5).reverse());
      })
      .catch(() => {
        setAlertCount('Error');
        setRecentAlerts([]);
      });
  }, []);

  return (
    <div className="dashboard-content">
      <h2>Overview</h2>
      <div className="dashboard-widgets">
        <div className="widget">Farms: {farmCount}</div>
        <div className="widget">Predictions: {predictionCount}</div>
        <div className="widget">Alerts: {alertCount}</div>
        <div className="widget">Satellite Images: {satelliteCount}</div>
      </div>

      <div style={{marginTop: 40, display: 'flex', gap: 40, flexWrap: 'wrap'}}>
        <div style={{flex: 2, minWidth: 320}}>
          <h3>Recent Predictions</h3>
          <table style={{width: '100%', background: '#fff', borderRadius: 8, boxShadow: '0 2px 8px rgba(0,0,0,0.04)', borderCollapse: 'collapse'}}>
            <thead>
              <tr style={{background: '#f7fafc'}}>
                <th style={{padding: 8, textAlign: 'left'}}>Farm</th>
                <th style={{padding: 8, textAlign: 'left'}}>Date</th>
                <th style={{padding: 8, textAlign: 'left'}}>Risk</th>
                <th style={{padding: 8, textAlign: 'left'}}>Yield Loss %</th>
                <th style={{padding: 8, textAlign: 'left'}}>Disease Risk</th>
              </tr>
            </thead>
            <tbody>
              {recentPredictions.length === 0 && (
                <tr><td colSpan={5} style={{padding: 8}}>No predictions found.</td></tr>
              )}
              {recentPredictions.map(pred => (
                <tr key={pred.id}>
                  <td style={{padding: 8}}>{pred.farm_id || '-'}</td>
                  <td style={{padding: 8}}>{pred.date || '-'}</td>
                  <td style={{padding: 8}}>{pred.risk_score != null ? pred.risk_score : '-'}</td>
                  <td style={{padding: 8}}>{pred.yield_loss_percent != null ? pred.yield_loss_percent : '-'}</td>
                  <td style={{padding: 8}}>{pred.disease_risk_level || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div style={{flex: 1, minWidth: 240}}>
          <h3>Latest Alerts</h3>
          <ul style={{background: '#fff', borderRadius: 8, boxShadow: '0 2px 8px rgba(0,0,0,0.04)', padding: 16, listStyle: 'none'}}>
            {recentAlerts.length === 0 && <li>No alerts found.</li>}
            {recentAlerts.map(alert => (
              <li key={alert.id} style={{marginBottom: 12}}>
                <strong>{alert.level || 'Alert'}:</strong> {alert.message || '-'}<br/>
                <span style={{fontSize: 12, color: '#888'}}>{alert.created_at || ''}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
