
export async function fetchSatelliteImageCount() {
  const res = await fetch(`${API_BASE}/satellite-images/?source=db`);
  if (!res.ok) throw new Error('Failed to fetch satellite image count');
  const data = await res.json();
  return data.length || 0;
}

export async function fetchSatelliteImages(limit = 100) {
  const res = await fetch(`${API_BASE}/satellite-images/?source=db&limit=${limit}`);
  if (!res.ok) throw new Error('Failed to fetch satellite images');
  return res.json();
}

export async function fetchNDVIMeans(limit = 100) {
  const res = await fetch(`${API_BASE}/satellite-images/ndvi-means?source=db&limit=${limit}`);
  if (!res.ok) throw new Error('Failed to fetch NDVI means');
  return res.json();
}

export async function triggerScan() {
  const res = await fetch(`${API_BASE}/satellite-images/scan`, {
    method: 'POST',
    headers: { ...getAuthHeaders() }
  });
  if (!res.ok) throw new Error('Failed to trigger scan');
  return res.json();
}

export async function getTaskStatus(taskId) {
  const res = await fetch(`${API_BASE}/satellite-images/task/${taskId}`);
  if (!res.ok) throw new Error('Failed to fetch task status');
  return res.json();
}

// ========== Disease Prediction API ==========

export async function fetchDiseases() {
  const res = await fetch(`${API_BASE}/diseases/`, {
    headers: { ...getAuthHeaders() }
  });
  if (!res.ok) throw new Error('Failed to fetch diseases');
  return res.json();
}

export async function predictDisease(farmId, diseaseName, cropType, forecastDays = 7) {
  const res = await fetch(`${API_BASE}/diseases/predict`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders()
    },
    body: JSON.stringify({
      farm_id: farmId,
      disease_name: diseaseName,
      crop_type: cropType,
      forecast_days: forecastDays
    })
  });
  if (!res.ok) throw new Error('Failed to predict disease');
  return res.json();
}

export async function fetchDailyForecast(farmId, diseaseName, days = 7) {
  const params = new URLSearchParams({ days: days.toString() });
  if (diseaseName) params.append('disease_name', diseaseName);
  
  const res = await fetch(`${API_BASE}/diseases/forecast/daily/${farmId}?${params}`, {
    headers: { ...getAuthHeaders() }
  });
  if (!res.ok) throw new Error('Failed to fetch daily forecast');
  return res.json();
}

export async function fetchWeeklyForecast(farmId, diseaseName) {
  const params = new URLSearchParams();
  if (diseaseName) params.append('disease_name', diseaseName);
  
  const res = await fetch(`${API_BASE}/diseases/forecast/weekly/${farmId}?${params}`, {
    headers: { ...getAuthHeaders() }
  });
  if (!res.ok) throw new Error('Failed to fetch weekly forecast');
  return res.json();
}

export async function fetchDiseaseStatistics(farmId, diseaseName, days = 30) {
  const params = new URLSearchParams({ days: days.toString() });
  if (diseaseName) params.append('disease_name', diseaseName);
  
  const res = await fetch(`${API_BASE}/diseases/statistics/${farmId}?${params}`, {
    headers: { ...getAuthHeaders() }
  });
  if (!res.ok) throw new Error('Failed to fetch disease statistics');
  return res.json();
}

export async function fetchDiseasePredictions(farmId, diseaseName, limit = 10) {
  const params = new URLSearchParams({ limit: limit.toString() });
  if (farmId) params.append('farm_id', farmId);
  if (diseaseName) params.append('disease_name', diseaseName);
  
  const res = await fetch(`${API_BASE}/diseases/predictions/?${params}`, {
    headers: { ...getAuthHeaders() }
  });
  if (!res.ok) throw new Error('Failed to fetch disease predictions');
  return res.json();
}

export async function submitDiseaseObservation(farmId, diseaseName, severity, notes = '') {
  const res = await fetch(`${API_BASE}/diseases/observations`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders()
    },
    body: JSON.stringify({
      farm_id: farmId,
      disease_name: diseaseName,
      severity,
      notes
    })
  });
  if (!res.ok) throw new Error('Failed to submit observation');
  return res.json();
}
// Simple API utility for backend requests
const API_BASE = 'http://localhost:8000/api/v1';

function getAuthHeaders() {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function fetchFarms() {
  const res = await fetch(`${API_BASE}/farms/`, {
    headers: { ...getAuthHeaders() }
  });
  if (!res.ok) throw new Error('Failed to fetch farms');
  return res.json();
}

export async function fetchPredictions() {
  const res = await fetch(`${API_BASE}/predictions/`, {
    headers: { ...getAuthHeaders() }
  });
  if (!res.ok) throw new Error('Failed to fetch predictions');
  return res.json();
}

export async function fetchAlerts() {
  const res = await fetch(`${API_BASE}/alerts/`, {
    headers: { ...getAuthHeaders() }
  });
  if (!res.ok) throw new Error('Failed to fetch alerts');
  return res.json();
}

export async function fetchUsers() {
  const res = await fetch(`${API_BASE}/users/`, {
    headers: { ...getAuthHeaders() }
  });
  if (!res.ok) throw new Error('Failed to fetch users');
  return res.json();
}

// ========== Analytics API ==========

export async function fetchDashboardMetrics() {
  const res = await fetch(`${API_BASE}/analytics/dashboard-metrics`, {
    headers: { ...getAuthHeaders() }
  });
  if (!res.ok) throw new Error('Failed to fetch dashboard metrics');
  return res.json();
}

export async function fetchEnrichedPredictions() {
  const res = await fetch(`${API_BASE}/analytics/predictions-enriched`, {
    headers: { ...getAuthHeaders() }
  });
  if (!res.ok) throw new Error('Failed to fetch enriched predictions');
  return res.json();
}

// ========== Data Management API ==========

export async function fetchDataStatus() {
  const res = await fetch(`${API_BASE}/data/data-status`, {
    headers: { ...getAuthHeaders() }
  });
  if (!res.ok) throw new Error('Failed to fetch data status');
  return res.json();
}

export async function triggerDataFetch() {
  const res = await fetch(`${API_BASE}/data/fetch-data`, {
    method: 'POST',
    headers: { ...getAuthHeaders() }
  });
  if (!res.ok) throw new Error('Failed to trigger data fetch');
  return res.json();
}
