
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
