import React, { useEffect, useState } from 'react';
import { fetchSatelliteImages, fetchNDVIMeans, triggerScan, getTaskStatus } from '../api';

const SatelliteImages = () => {
  const [images, setImages] = useState([]);
  const [ndviData, setNdviData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [scanStatus, setScanStatus] = useState(null);
  const [viewMode, setViewMode] = useState('table'); // 'table' or 'ndvi'

  const loadData = () => {
    setLoading(true);
    Promise.all([
      fetchSatelliteImages(1000),
      fetchNDVIMeans(1000)
    ])
      .then(([imgData, ndviData]) => {
        setImages(imgData);
        setNdviData(ndviData);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleScan = async () => {
    setScanning(true);
    setScanStatus('Triggering scan...');
    try {
      const result = await triggerScan();
      setScanStatus(`Scan started! Task ID: ${result.task_id}`);
      // Reload data after a few seconds
      setTimeout(() => {
        loadData();
        setScanning(false);
        setScanStatus('Scan complete. Data refreshed.');
      }, 5000);
    } catch (err) {
      setScanStatus(`Error: ${err.message}`);
      setScanning(false);
    }
  };

  return (
    <div style={{ padding: 32 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h2>Satellite Images & NDVI Processing</h2>
        <div style={{ display: 'flex', gap: 12 }}>
          <button
            onClick={() => setViewMode('table')}
            style={{
              padding: '8px 16px',
              background: viewMode === 'table' ? '#3182ce' : '#e2e8f0',
              color: viewMode === 'table' ? '#fff' : '#2d3748',
              border: 'none',
              borderRadius: 6,
              cursor: 'pointer'
            }}
          >
            All Images
          </button>
          <button
            onClick={() => setViewMode('ndvi')}
            style={{
              padding: '8px 16px',
              background: viewMode === 'ndvi' ? '#3182ce' : '#e2e8f0',
              color: viewMode === 'ndvi' ? '#fff' : '#2d3748',
              border: 'none',
              borderRadius: 6,
              cursor: 'pointer'
            }}
          >
            NDVI Data
          </button>
          <button
            onClick={handleScan}
            disabled={scanning}
            style={{
              padding: '8px 16px',
              background: scanning ? '#cbd5e0' : '#48bb78',
              color: '#fff',
              border: 'none',
              borderRadius: 6,
              cursor: scanning ? 'not-allowed' : 'pointer',
              fontWeight: 'bold'
            }}
          >
            {scanning ? '⏳ Scanning...' : '🔄 Scan & Process'}
          </button>
        </div>
      </div>

      {scanStatus && (
        <div style={{
          padding: 12,
          background: scanStatus.includes('Error') ? '#fed7d7' : '#c6f6d5',
          color: scanStatus.includes('Error') ? '#c53030' : '#22543d',
          borderRadius: 6,
          marginBottom: 16
        }}>
          {scanStatus}
        </div>
      )}

      {loading && <p>Loading...</p>}
      {error && <p style={{ color: 'red' }}>Error: {error}</p>}

      {!loading && !error && viewMode === 'table' && (
        <div>
          <p style={{ marginBottom: 12, color: '#718096' }}>Total Images: {images.length}</p>
          <table style={{width: '100%', background: '#fff', borderRadius: 8, boxShadow: '0 2px 8px rgba(0,0,0,0.04)', borderCollapse: 'collapse'}}>
            <thead>
              <tr style={{background: '#f7fafc'}}>
                <th style={{padding: 8, textAlign: 'left'}}>Date</th>
                <th style={{padding: 8, textAlign: 'left'}}>Region</th>
                <th style={{padding: 8, textAlign: 'left'}}>Type</th>
                <th style={{padding: 8, textAlign: 'left'}}>Mean NDVI</th>
                <th style={{padding: 8, textAlign: 'left'}}>Cloud Cover (%)</th>
                <th style={{padding: 8, textAlign: 'left'}}>File</th>
              </tr>
            </thead>
            <tbody>
              {images.length === 0 && (
                <tr><td colSpan={6} style={{padding: 8}}>No images found.</td></tr>
              )}
              {images.map(img => (
                <tr key={img.id}>
                  <td style={{padding: 8}}>{img.date || '-'}</td>
                  <td style={{padding: 8}}>{img.region || '-'}</td>
                  <td style={{padding: 8}}>{img.image_type || '-'}</td>
                  <td style={{padding: 8}}>
                    {img.extra_metadata && img.extra_metadata.mean_ndvi != null ? (
                      <span style={{
                        padding: '2px 8px',
                        borderRadius: 4,
                        background: img.extra_metadata.mean_ndvi > 0.6 ? '#c6f6d5' :
                                    img.extra_metadata.mean_ndvi > 0.3 ? '#feebc8' : '#fed7d7',
                        color: img.extra_metadata.mean_ndvi > 0.6 ? '#22543d' :
                               img.extra_metadata.mean_ndvi > 0.3 ? '#7c2d12' : '#c53030'
                      }}>
                        {img.extra_metadata.mean_ndvi.toFixed(3)}
                      </span>
                    ) : '-'}
                  </td>
                  <td style={{padding: 8}}>{img.extra_metadata && img.extra_metadata.cloud_cover != null ? img.extra_metadata.cloud_cover : '-'}</td>
                  <td style={{padding: 8}}>
                    {img.file_path ? (
                      <a
                        href={`http://localhost:8000/api/v1/satellite-images/download/${img.id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ color: '#3182ce', textDecoration: 'underline' }}
                      >
                        Download
                      </a>
                    ) : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!loading && !error && viewMode === 'ndvi' && (
        <div>
          <p style={{ marginBottom: 12, color: '#718096' }}>NDVI Processed Images: {ndviData.length}</p>
          <div style={{ marginBottom: 24, background: '#fff', padding: 16, borderRadius: 8, boxShadow: '0 2px 8px rgba(0,0,0,0.04)' }}>
            <h3 style={{ marginBottom: 12 }}>NDVI Statistics</h3>
            {ndviData.length > 0 ? (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
                <div>
                  <div style={{ fontSize: 14, color: '#718096' }}>Average NDVI</div>
                  <div style={{ fontSize: 24, fontWeight: 'bold', color: '#2d3748' }}>
                    {(ndviData.reduce((sum, d) => sum + d.mean_ndvi, 0) / ndviData.length).toFixed(3)}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: 14, color: '#718096' }}>Max NDVI</div>
                  <div style={{ fontSize: 24, fontWeight: 'bold', color: '#38a169' }}>
                    {Math.max(...ndviData.map(d => d.mean_ndvi)).toFixed(3)}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: 14, color: '#718096' }}>Min NDVI</div>
                  <div style={{ fontSize: 24, fontWeight: 'bold', color: '#e53e3e' }}>
                    {Math.min(...ndviData.map(d => d.mean_ndvi)).toFixed(3)}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: 14, color: '#718096' }}>Healthy (>0.6)</div>
                  <div style={{ fontSize: 24, fontWeight: 'bold', color: '#38a169' }}>
                    {ndviData.filter(d => d.mean_ndvi > 0.6).length}
                  </div>
                </div>
              </div>
            ) : <p>No NDVI data available</p>}
          </div>

          <table style={{width: '100%', background: '#fff', borderRadius: 8, boxShadow: '0 2px 8px rgba(0,0,0,0.04)', borderCollapse: 'collapse'}}>
            <thead>
              <tr style={{background: '#f7fafc'}}>
                <th style={{padding: 8, textAlign: 'left'}}>Date</th>
                <th style={{padding: 8, textAlign: 'left'}}>Region</th>
                <th style={{padding: 8, textAlign: 'left'}}>Mean NDVI</th>
                <th style={{padding: 8, textAlign: 'left'}}>Vegetation Health</th>
                <th style={{padding: 8, textAlign: 'left'}}>File</th>
              </tr>
            </thead>
            <tbody>
              {ndviData.length === 0 && (
                <tr><td colSpan={5} style={{padding: 8}}>No NDVI data found. Click "Scan & Process" to start processing.</td></tr>
              )}
              {ndviData.map((item, idx) => {
                const health = item.mean_ndvi > 0.6 ? 'Healthy' :
                               item.mean_ndvi > 0.3 ? 'Moderate' : 'Poor';
                return (
                  <tr key={idx}>
                    <td style={{padding: 8}}>{item.date || '-'}</td>
                    <td style={{padding: 8}}>{item.region || '-'}</td>
                    <td style={{padding: 8}}>
                      <span style={{
                        padding: '4px 12px',
                        borderRadius: 4,
                        fontWeight: 'bold',
                        background: item.mean_ndvi > 0.6 ? '#c6f6d5' :
                                    item.mean_ndvi > 0.3 ? '#feebc8' : '#fed7d7',
                        color: item.mean_ndvi > 0.6 ? '#22543d' :
                               item.mean_ndvi > 0.3 ? '#7c2d12' : '#c53030'
                      }}>
                        {item.mean_ndvi.toFixed(3)}
                      </span>
                    </td>
                    <td style={{padding: 8}}>{health}</td>
                    <td style={{padding: 8}}>
                      <a
                        href={`http://localhost:8000/api/v1/satellite-images/download/${item.id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ color: '#3182ce', textDecoration: 'underline' }}
                      >
                        Download
                      </a>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default SatelliteImages;
