import React, { useEffect, useRef, useState } from 'react';

const GOOGLE_MAPS_API_KEY = 'AIzaSyAa3_gwS8sCKhxT5SnuyK-CHcz0SBLCViM';

function loadGoogleMaps(apiKey) {
  return new Promise((resolve, reject) => {
    // Check if already loaded
    if (window.google && window.google.maps) {
      return resolve(window.google.maps);
    }
    
    const id = 'google-maps-script';
    const existingScript = document.getElementById(id);
    
    if (existingScript) {
      // Script already loading, wait for it
      const checkLoaded = setInterval(() => {
        if (window.google && window.google.maps) {
          clearInterval(checkLoaded);
          resolve(window.google.maps);
        }
      }, 100);
      setTimeout(() => {
        clearInterval(checkLoaded);
        reject(new Error('Google Maps loading timeout'));
      }, 10000);
      return;
    }
    
    // Create and load script
    const script = document.createElement('script');
    script.id = id;
    script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}`;
    script.async = true;
    script.defer = true;
    script.onload = () => {
      if (window.google && window.google.maps) {
        resolve(window.google.maps);
      } else {
        reject(new Error('Google Maps failed to load'));
      }
    };
    script.onerror = (error) => reject(error);
    document.head.appendChild(script);
  });
}

const MapPanel = ({ farms = [], predictions = [], selectedFarmId, onSelectFarm, filters = {} }) => {
  const mapRef = useRef(null);
  const mapInstance = useRef(null);
  const markersRef = useRef({});
  const polygonsRef = useRef({});
  const infoWindowRef = useRef(null);
  const [stressCompare, setStressCompare] = useState(false);
  const [viewMode, setViewMode] = useState('markers'); // 'markers' or 'satellite'
  const [satelliteData, setSatelliteData] = useState([]);

  useEffect(() => {
    let mounted = true;
    loadGoogleMaps(GOOGLE_MAPS_API_KEY).then((maps) => {
      if (!mounted) return;
      if (!mapRef.current) return;
      // Rwanda center coordinates
      mapInstance.current = new maps.Map(mapRef.current, {
        center: { lat: -1.9403, lng: 29.8739 },
        zoom: 8,
        gestureHandling: 'greedy',
        mapTypeControl: true,
        mapTypeControlOptions: {
          style: maps.MapTypeControlStyle?.HORIZONTAL_BAR || 0,
          position: maps.ControlPosition?.TOP_RIGHT || 2
        }
      });
      infoWindowRef.current = new maps.InfoWindow();
      renderMarkers();
    }).catch((err) => {
      console.error('Google Maps load error:', err);
      // Fallback: initialize without map controls if Maps API fails
    });
    
    // Fetch satellite data with error handling
    fetch('http://localhost:8000/api/v1/farm-satellite/')
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(data => {
        if (mounted) setSatelliteData(data);
      })
      .catch(err => {
        console.error('Error fetching satellite data:', err.message);
        // Don't break the app if satellite data fails
      });
    
    return () => { mounted = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    // Re-render markers or polygons based on view mode
    if (viewMode === 'markers') {
      clearPolygons();
      renderMarkers();
    } else {
      clearMarkers();
      renderSatellitePolygons();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [farms, predictions, filters, stressCompare, viewMode, satelliteData]);

  useEffect(() => {
    // Highlight selected marker
    if (!selectedFarmId || !markersRef.current) return;
    Object.entries(markersRef.current).forEach(([fid, marker]) => {
      if (parseInt(fid, 10) === parseInt(selectedFarmId, 10)) {
        marker.setAnimation(window.google.maps.Animation.BOUNCE);
        marker.setZIndex(9999);
        setTimeout(() => marker.setAnimation(null), 2000);
        if (mapInstance.current) {
          mapInstance.current.panTo(marker.getPosition());
          mapInstance.current.setZoom(12);
        }
      } else {
        marker.setAnimation(null);
        marker.setZIndex(1);
      }
    });
  }, [selectedFarmId]);

  function riskToColor(risk) {
    if (risk >= 60) return '#e53e3e';
    if (risk >= 30) return '#dd6b20';
    return '#38a169';
  }

  function ndviToColor(ndvi) {
    if (ndvi == null) return '#9ca3af'; // gray for unknown
    if (ndvi >= 0.6) return '#10b981'; // green - healthy
    if (ndvi >= 0.3) return '#f59e0b'; // amber - moderate
    return '#ef4444'; // red - stressed
  }

  function clearMarkers() {
    Object.values(markersRef.current).forEach(m => m.setMap(null));
    markersRef.current = {};
  }

  function clearPolygons() {
    Object.values(polygonsRef.current).forEach(p => p.setMap(null));
    polygonsRef.current = {};
  }

  function markerScaleForRisk(risk) {
    const r = Math.max(0, Math.min(100, risk || 0));
    return 6 + Math.round((r / 100) * 8);
  }

  function getPredictionForFarm(farmId) {
    return predictions.find(p => parseInt(p.farm_id, 10) === parseInt(farmId, 10));
  }

  function renderMarkers() {
    if (!window.google || !window.google.maps || !mapInstance.current) return;
    const maps = window.google.maps;
    clearMarkers();

    const avgRisk = predictions.length ? (predictions.reduce((s, p) => s + (p.risk_score || 0), 0) / predictions.length) : 0;
    const bounds = new maps.LatLngBounds();
    let hasMarkers = false;

    farms.forEach(f => {
      if (!f.latitude || !f.longitude) return;
      const pred = getPredictionForFarm(f.id) || {};
      if (filters.riskLevel) {
        const level = filters.riskLevel;
        const r = pred.risk_score || 0;
        if (level === 'Critical' && r < 60) return;
        if (level === 'Warning' && (r < 30 || r >= 60)) return;
        if (level === 'Stable' && r >= 30) return;
      }
      const color = riskToColor(pred.risk_score || 0);
      const scale = markerScaleForRisk(pred.risk_score || 0);

      const isAboveAvg = stressCompare && pred.risk_score != null && pred.risk_score > avgRisk;
      const position = { lat: f.latitude, lng: f.longitude };
      const marker = new maps.Marker({
        position,
        map: mapInstance.current,
        title: f.name || `Farm ${f.id}`,
        icon: {
          path: maps.SymbolPath.CIRCLE,
          scale: isAboveAvg ? Math.max(scale, 12) : scale,
          fillColor: color,
          fillOpacity: 0.95,
          strokeWeight: isAboveAvg ? 2 : 1,
          strokeColor: isAboveAvg ? '#000000' : '#ffffff'
        }
      });

      marker.addListener('click', () => {
        const content = buildInfoWindowContent(f, pred);
        infoWindowRef.current.setContent(content);
        infoWindowRef.current.open(mapInstance.current, marker);
        if (onSelectFarm) onSelectFarm(f.id);
      });

      markersRef.current[f.id] = marker;
      bounds.extend(position);
      hasMarkers = true;
    });

    if (hasMarkers && farms.length > 0) {
      mapInstance.current.fitBounds(bounds);
      maps.event.addListenerOnce(mapInstance.current, 'idle', () => {
        const zoom = mapInstance.current.getZoom();
        if (zoom > 12) mapInstance.current.setZoom(12);
      });
    }
  }

  function renderSatellitePolygons() {
    if (!window.google || !window.google.maps || !mapInstance.current) return;
    if (satelliteData.length === 0) return;
    
    const maps = window.google.maps;
    clearPolygons();
    
    const bounds = new maps.LatLngBounds();
    let hasPolygons = false;

    satelliteData.forEach(farm => {
      if (!farm.latitude || !farm.longitude) return;
      
      const pred = getPredictionForFarm(farm.id) || {};
      if (filters.riskLevel) {
        const level = filters.riskLevel;
        const r = pred.risk_score || 0;
        if (level === 'Critical' && r < 60) return;
        if (level === 'Warning' && (r < 30 || r >= 60)) return;
        if (level === 'Stable' && r >= 30) return;
      }

      // Create approximate polygon based on farm area
      const area = farm.area || 10;
      const sideLengthMeters = Math.sqrt(area * 10000);
      const latOffset = (sideLengthMeters / 111320) / 2;
      const lngOffset = (sideLengthMeters / (111320 * Math.cos(farm.latitude * Math.PI / 180))) / 2;

      const polygonCoords = [
        { lat: farm.latitude - latOffset, lng: farm.longitude - lngOffset },
        { lat: farm.latitude - latOffset, lng: farm.longitude + lngOffset },
        { lat: farm.latitude + latOffset, lng: farm.longitude + lngOffset },
        { lat: farm.latitude + latOffset, lng: farm.longitude - lngOffset }
      ];

      const color = ndviToColor(farm.ndvi);
      const polygon = new maps.Polygon({
        paths: polygonCoords,
        strokeColor: color,
        strokeOpacity: 0.8,
        strokeWeight: 2,
        fillColor: color,
        fillOpacity: 0.5,
        map: mapInstance.current
      });

      polygon.addListener('click', (e) => {
        const content = buildSatelliteInfoWindowContent(farm, pred);
        infoWindowRef.current.setContent(content);
        infoWindowRef.current.setPosition(e.latLng);
        infoWindowRef.current.open(mapInstance.current);
        if (onSelectFarm) onSelectFarm(farm.id);
      });

      polygonsRef.current[farm.id] = polygon;
      bounds.extend({ lat: farm.latitude, lng: farm.longitude });
      hasPolygons = true;
    });

    if (hasPolygons) {
      mapInstance.current.fitBounds(bounds);
      maps.event.addListenerOnce(mapInstance.current, 'idle', () => {
        const zoom = mapInstance.current.getZoom();
        if (zoom > 12) mapInstance.current.setZoom(12);
      });
    }
  }

  function buildInfoWindowContent(farm, pred) {
    const name = farm.name || `Farm #${farm.id}`;
    const loc = `${farm.latitude?.toFixed(4) || '-'}, ${farm.longitude?.toFixed(4) || '-'}`;
    const area = farm.area_ha ? `${farm.area_ha} ha` : '-';
    const risk = pred?.risk_score ? `${pred.risk_score.toFixed(1)}%` : 'N/A';
    const yieldLoss = pred?.yield_loss ? `${pred.yield_loss.toFixed(1)}%` : 'N/A';
    const confidence = pred?.confidence_score ? `${pred.confidence_score.toFixed(0)}%` : 'N/A';
    const drivers = pred?.risk_drivers ? Object.keys(pred.risk_drivers).map(k => `<div>${k}</div>`).join('') : '-';
    const recs = pred?.recommendations ? pred.recommendations.slice(0,3).map(r => `<div><strong>${r.urgency}</strong>: ${r.action}</div>`).join('') : '-';

    const mapsLink = `https://www.google.com/maps/search/?api=1&query=${farm.latitude},${farm.longitude}`;
    return `
      <div style="min-width:240px">
        <div style="font-weight:700;margin-bottom:6px">${name}</div>
        <div style="font-size:13px;color:#444;margin-bottom:6px">Location: ${loc}</div>
        <div style="font-size:13px;color:#444;margin-bottom:6px">Area: ${area}</div>
        <div style="font-size:13px;color:#444;margin-bottom:6px">Risk Score: ${risk}</div>
        <div style="font-size:13px;color:#444;margin-bottom:6px">Yield Loss: ${yieldLoss}</div>
        <div style="font-size:13px;color:#444;margin-bottom:6px">Top Drivers: ${drivers}</div>
        <div style="font-size:13px;color:#444;margin-bottom:6px">Confidence: ${confidence}</div>
        <div style="font-size:13px;color:#444;margin-top:8px">Actions: ${recs}</div>
        <div style="margin-top:8px;font-size:13px"><a target="_blank" rel="noopener noreferrer" href="${mapsLink}">Open in Google Maps</a></div>
      </div>
    `;
  }

  function buildSatelliteInfoWindowContent(farm, pred) {
    const name = farm.name || `Farm #${farm.id}`;
    const loc = `${farm.latitude?.toFixed(4) || '-'}, ${farm.longitude?.toFixed(4) || '-'}`;
    const area = farm.area ? `${farm.area} ha` : '-';
    const ndvi = farm.ndvi != null ? farm.ndvi.toFixed(3) : 'N/A';
    const ndviDate = farm.ndvi_date || 'N/A';
    const imageType = farm.image_type || '-';
    const ndviStatus = farm.ndvi_status || 'unknown';
    const statusColors = { healthy: '#10b981', moderate: '#f59e0b', stressed: '#ef4444', unknown: '#9ca3af' };
    const statusColor = statusColors[ndviStatus];
    
    // Data source indicator
    const dataSource = farm.data_source || 'simulated';
    const isRealData = dataSource === 'real';
    const sourceLabel = isRealData ? 'REAL SENTINEL-2' : 'SIMULATED';
    const sourceColor = isRealData ? '#059669' : '#6b7280';
    const tile = farm.tile || '';
    const cloudCover = farm.cloud_cover != null ? `${(farm.cloud_cover * 100).toFixed(1)}%` : '';
    
    const risk = pred?.risk_score ? `${pred.risk_score.toFixed(1)}%` : 'N/A';
    const yieldLoss = pred?.yield_loss ? `${pred.yield_loss.toFixed(1)}%` : 'N/A';
    
    const mapsLink = `https://www.google.com/maps/search/?api=1&query=${farm.latitude},${farm.longitude}`;
    return `
      <div style="min-width:260px">
        <div style="font-weight:700;margin-bottom:8px;color:#1f2937">${name}</div>
        <div style="display:inline-block;padding:2px 8px;background:${isRealData ? '#d1fae5' : '#f3f4f6'};color:${sourceColor};border-radius:4px;font-size:11px;font-weight:600;margin-bottom:8px">${sourceLabel}</div>
        <div style="font-size:13px;color:#444;margin-bottom:6px">${loc}</div>
        <div style="font-size:13px;color:#444;margin-bottom:6px">Area: ${area}</div>
        <div style="padding:8px;background:#f9fafb;border-radius:6px;margin:8px 0">
          <div style="font-size:12px;color:#6b7280;margin-bottom:4px">SATELLITE DATA</div>
          <div style="font-size:14px;font-weight:600;color:${statusColor};margin-bottom:4px">NDVI: ${ndvi}</div>
          <div style="font-size:12px;color:#6b7280">Status: <span style="color:${statusColor};font-weight:600">${ndviStatus.toUpperCase()}</span></div>
          <div style="font-size:12px;color:#6b7280">Date: ${ndviDate}</div>
          <div style="font-size:12px;color:#6b7280">Type: ${imageType}</div>
          ${tile ? `<div style="font-size:12px;color:#6b7280">Tile: ${tile}</div>` : ''}
          ${cloudCover ? `<div style="font-size:12px;color:#6b7280">Cloud Cover: ${cloudCover}</div>` : ''}
        </div>
        <div style="font-size:13px;color:#444;margin-bottom:4px">Risk Score: ${risk}</div>
        <div style="font-size:13px;color:#444;margin-bottom:8px">Yield Loss: ${yieldLoss}</div>
        <div style="margin-top:8px;font-size:13px"><a target="_blank" rel="noopener noreferrer" href="${mapsLink}">Open in Google Maps</a></div>
      </div>
    `;
  }

  function computeCounts() {
    const counts = { Stable: 0, Warning: 0, Critical: 0 };
    const dataSource = viewMode === 'satellite' ? satelliteData : farms;
    
    dataSource.forEach(f => {
      const p = getPredictionForFarm(f.id) || {};
      const r = p.risk_score || 0;
      if (r >= 60) counts.Critical += 1;
      else if (r >= 30) counts.Warning += 1;
      else counts.Stable += 1;
    });
    return counts;
  }

  function renderLegend() {
    const counts = computeCounts();
    const isMarkerView = viewMode === 'markers';
    
    const items = isMarkerView ? [
      { key: 'Stable', color: '#38a169', icon: '●', label: 'Stable' },
      { key: 'Warning', color: '#dd6b20', icon: '●', label: 'Warning' },
      { key: 'Critical', color: '#e53e3e', icon: '●', label: 'Critical' }
    ] : [
      { key: 'Healthy', color: '#10b981', icon: '■', label: 'Healthy (NDVI ≥0.6)' },
      { key: 'Moderate', color: '#f59e0b', icon: '■', label: 'Moderate (0.3-0.6)' },
      { key: 'Stressed', color: '#ef4444', icon: '■', label: 'Stressed (<0.3)' }
    ];
    
    return (
      <>
        <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 8, color: '#1f2937' }}>
          {isMarkerView ? 'Risk Level' : 'Vegetation Health (NDVI)'}
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {items.map(it => (
            <div key={it.key} onClick={() => { 
              if (isMarkerView && typeof filters.onChange === 'function') {
                filters.onChange({ ...filters, riskLevel: filters.riskLevel === it.key ? '' : it.key }); 
              }
            }} style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: 8, 
              cursor: isMarkerView ? 'pointer' : 'default', 
              padding: '4px 8px', 
              borderRadius: 4, 
              background: (isMarkerView && filters.riskLevel === it.key) ? '#f1f5f9' : 'transparent', 
              transition: 'background 0.15s' 
            }}>
              <div style={{ fontSize: 16, color: it.color, lineHeight: 1 }}>{it.icon}</div>
              <div style={{ fontSize: 11, color: '#1f2937', fontWeight: 500 }}>{it.label}</div>
              {isMarkerView && <div style={{ fontSize: 11, color: '#6b7280', fontWeight: 600 }}>({counts[it.key]})</div>}
            </div>
          ))}
        </div>
      </>
    );
  }

  return (
    <div style={{ width: '100%', height: '100%', minHeight: 400, borderRadius: 8, overflow: 'hidden' }}>
      <div style={{ height: '48px', display: 'flex', alignItems: 'center', padding: '8px 12px', gap: 8, background: '#fff', borderBottom: '1px solid #eee' }}>
        <div style={{ fontSize: 13, fontWeight: 600 }}>Farm Risk Map</div>
        <div style={{ marginLeft: 12, display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '4px 12px', background: '#f8fafc', borderRadius: 6 }}>
            <button 
              onClick={() => setViewMode('markers')} 
              style={{ 
                fontSize: 12, 
                padding: '4px 12px', 
                border: 'none', 
                borderRadius: 4, 
                cursor: 'pointer',
                background: viewMode === 'markers' ? '#3b82f6' : 'transparent',
                color: viewMode === 'markers' ? '#fff' : '#64748b',
                fontWeight: viewMode === 'markers' ? 600 : 400
              }}
            >
              Risk Points
            </button>
            <button 
              onClick={() => setViewMode('satellite')} 
              style={{ 
                fontSize: 12, 
                padding: '4px 12px', 
                border: 'none', 
                borderRadius: 4, 
                cursor: 'pointer',
                background: viewMode === 'satellite' ? '#3b82f6' : 'transparent',
                color: viewMode === 'satellite' ? '#fff' : '#64748b',
                fontWeight: viewMode === 'satellite' ? 600 : 400
              }}
            >
              Satellite View
            </button>
          </div>
          {viewMode === 'satellite' && satelliteData.length > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11 }}>
              <span style={{ padding: '2px 8px', background: '#d1fae5', color: '#059669', borderRadius: 4, fontWeight: 600 }}>
                Real: {satelliteData.filter(f => f.data_source === 'real').length}
              </span>
              <span style={{ padding: '2px 8px', background: '#f3f4f6', color: '#6b7280', borderRadius: 4, fontWeight: 600 }}>
                Simulated: {satelliteData.filter(f => f.data_source !== 'real').length}
              </span>
            </div>
          )}
          {viewMode === 'markers' && (
            <label style={{ fontSize: 13, color: '#4a5568' }}>
              <input type="checkbox" checked={stressCompare} onChange={(e) => setStressCompare(e.target.checked)} style={{ marginRight: 6 }} />
              Stress Comparison
            </label>
          )}
        </div>
      </div>
      <div style={{ position: 'relative', width: '100%', height: 'calc(100% - 48px)' }}>
        <div ref={mapRef} style={{ width: '100%', height: '100%' }} />
        <div style={{ position: 'absolute', top: 10, right: 10, background: 'white', padding: '12px 16px', borderRadius: 8, boxShadow: '0 2px 8px rgba(0,0,0,0.15)', zIndex: 1000 }}>
          {renderLegend()}
        </div>
      </div>
    </div>
  );
};

export default MapPanel;
