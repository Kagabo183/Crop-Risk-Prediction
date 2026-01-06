import React, { useState, useEffect } from 'react';
import { fetchDataStatus, triggerDataFetch } from '../api';
import './DataStatus.css';

function DataStatus() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [fetching, setFetching] = useState(false);
  const [message, setMessage] = useState('');

  const loadStatus = async () => {
    setLoading(true);
    try {
      const data = await fetchDataStatus();
      setStatus(data);
    } catch (error) {
      console.error('Failed to load data status:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStatus();
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleFetchData = async () => {
    setFetching(true);
    setMessage('');
    try {
      const result = await triggerDataFetch();
      setMessage(result.message);
      // Reload status after 5 seconds
      setTimeout(loadStatus, 5000);
    } catch (error) {
      setMessage('Failed to trigger data fetch: ' + error.message);
    } finally {
      setFetching(false);
    }
  };

  if (loading) {
    return <div className="data-status-loading">Loading data status...</div>;
  }

  if (!status) {
    return <div className="data-status-error">Failed to load data status</div>;
  }

  return (
    <div className="data-status">
      <div className="data-status-header">
        <h2>📊 Data Status</h2>
        <button 
          className="fetch-button" 
          onClick={handleFetchData} 
          disabled={fetching}
        >
          {fetching ? '🔄 Fetching...' : '🔄 Fetch Latest Data'}
        </button>
      </div>

      {message && <div className="status-message">{message}</div>}

      <div className="status-cards">
        {/* Satellite Data Card */}
        <div className={`status-card ${status.satellite_data.up_to_date ? 'up-to-date' : 'outdated'}`}>
          <h3>🛰️ Satellite Data</h3>
          <div className="card-content">
            <div className="stat">
              <span className="label">Total Images:</span>
              <span className="value">{status.satellite_data.count.toLocaleString()}</span>
            </div>
            <div className="stat">
              <span className="label">Latest Date:</span>
              <span className="value">{status.satellite_data.latest_date}</span>
            </div>
            <div className="stat">
              <span className="label">Status:</span>
              <span className={`badge ${status.satellite_data.up_to_date ? 'success' : 'warning'}`}>
                {status.satellite_data.up_to_date 
                  ? '✅ Up to Date' 
                  : `⚠️ ${status.satellite_data.days_behind} days behind`}
              </span>
            </div>
            <div className="date-range">
              <small>{status.satellite_data.earliest_date} to {status.satellite_data.latest_date}</small>
            </div>
          </div>
        </div>

        {/* Weather Data Card */}
        <div className={`status-card ${status.weather_data.up_to_date ? 'up-to-date' : 'outdated'}`}>
          <h3>🌦️ Weather Data</h3>
          <div className="card-content">
            <div className="stat">
              <span className="label">Total Records:</span>
              <span className="value">{status.weather_data.count.toLocaleString()}</span>
            </div>
            <div className="stat">
              <span className="label">Latest Date:</span>
              <span className="value">{status.weather_data.latest_date}</span>
            </div>
            <div className="stat">
              <span className="label">Status:</span>
              <span className={`badge ${status.weather_data.up_to_date ? 'success' : 'warning'}`}>
                {status.weather_data.up_to_date 
                  ? '✅ Up to Date' 
                  : `⚠️ ${status.weather_data.days_behind} days behind`}
              </span>
            </div>
            <div className="date-range">
              <small>{status.weather_data.earliest_date} to {status.weather_data.latest_date}</small>
            </div>
          </div>
        </div>

        {/* Predictions Card */}
        <div className="status-card predictions">
          <h3>🎯 Predictions</h3>
          <div className="card-content">
            <div className="stat">
              <span className="label">Total Predictions:</span>
              <span className="value">{status.predictions.count.toLocaleString()}</span>
            </div>
            <div className="stat">
              <span className="label">Latest:</span>
              <span className="value">
                {new Date(status.predictions.latest).toLocaleString()}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="current-date">
        <small>Current System Date: {status.current_date}</small>
      </div>
    </div>
  );
}

export default DataStatus;
