import React, { useMemo, useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { fetchDailyForecast, fetchWeeklyForecast, fetchFarms, fetchDiseases, fetchRemoteSensingDiagnostics, createDisease, predictDisease, submitDiseaseObservation, fetchFarmObservations } from '../api';
import RiskIndicator from '../components/RiskIndicator';
import './DiseaseForecasts.css';

const DiseaseForecasts = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [farms, setFarms] = useState([]);
  const [diseases, setDiseases] = useState([]);
  const [selectedFarm, setSelectedFarm] = useState(null);
  const [selectedDisease, setSelectedDisease] = useState('');
  const [dailyForecast, setDailyForecast] = useState([]);
  const [weeklyForecast, setWeeklyForecast] = useState(null);
  const [loading, setLoading] = useState(true);
  const [forecastLoading, setForecastLoading] = useState(false);
  const [initError, setInitError] = useState(null);
  const [forecastError, setForecastError] = useState(null);
  const [notice, setNotice] = useState(null);
  const [forecastDays, setForecastDays] = useState(7);
  const [cropType, setCropType] = useState('potato');
  const [isGenerating, setIsGenerating] = useState(false);
  const [seedBusy, setSeedBusy] = useState(false);
  const [diagnostics, setDiagnostics] = useState(null);
  const [diagnosticsError, setDiagnosticsError] = useState(null);
  const [observations, setObservations] = useState([]);
  const [obsLoading, setObsLoading] = useState(false);
  const [obsError, setObsError] = useState(null);
  const [obsDate, setObsDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [obsPresent, setObsPresent] = useState(true);
  const [obsSeverity, setObsSeverity] = useState('moderate');
  const [obsNotes, setObsNotes] = useState('');
  const [obsSaving, setObsSaving] = useState(false);

  // Auto-forecast (innovation mode): generate once per selection key, no loops.
  const AUTO_FORECAST = true;
  const lastAutoKeyRef = useRef('');

  // Auto-seed disease catalog if empty (so the page is never "blank").
  const AUTO_SEED_DISEASES = true;

  useEffect(() => {
    loadInitialData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (selectedFarm && selectedDisease) {
      loadForecasts();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedFarm, selectedDisease, forecastDays]);

  const loadObservations = async () => {
    if (!selectedFarm) return;
    try {
      setObsLoading(true);
      setObsError(null);
      const data = await fetchFarmObservations(selectedFarm, 20);
      setObservations(Array.isArray(data) ? data : []);
    } catch (e) {
      setObsError(e?.message || 'Failed to load observations');
      setObservations([]);
    } finally {
      setObsLoading(false);
    }
  };

  useEffect(() => {
    if (!loading && selectedFarm) {
      loadObservations();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, selectedFarm]);

  // Pull Sentinel/NDVI diagnostics and auto-pick the top ranked disease risk.
  useEffect(() => {
    let alive = true;
    const run = async () => {
      if (!selectedFarm || loading) return;
      try {
        setDiagnosticsError(null);
        const d = await fetchRemoteSensingDiagnostics(selectedFarm, 30, 3);
        if (!alive) return;
        setDiagnostics(d);

        const top = Array.isArray(d?.top_disease_risks) ? d.top_disease_risks[0] : null;
        const topDiseaseName = top?.disease;

        // If diseases exist and top disease is present, auto-select it.
        if (topDiseaseName && Array.isArray(diseases) && diseases.some((x) => x?.name === topDiseaseName)) {
          if (selectedDisease !== topDiseaseName) {
            setSelectedDisease(topDiseaseName);
            setSearchParams({ farm: selectedFarm, disease: topDiseaseName });
          }
        }
      } catch (e) {
        if (!alive) return;
        setDiagnosticsError(e?.message || 'Failed to load Sentinel diagnostics.');
        setDiagnostics(null);
      }
    };
    run();
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedFarm, loading, diseases]);

  const loadInitialData = async () => {
    try {
      setInitError(null);
      const [farmsData, diseasesDataRaw] = await Promise.all([fetchFarms(), fetchDiseases()]);

      const cleanDiseasesInitial = (Array.isArray(diseasesDataRaw) ? diseasesDataRaw : []).filter(
        (d) => d && typeof d.name === 'string' && d.name.trim().length > 0
      );

      let diseasesData = cleanDiseasesInitial;
      const alreadySeeded = localStorage.getItem('disease_defaults_seeded') === '1';
      if (AUTO_SEED_DISEASES && !alreadySeeded && diseasesData.length === 0) {
        setNotice('Setting up disease catalog…');
        const defaults = [
          {
            name: 'Late Blight',
            description: 'A major disease that thrives in cool, wet conditions.',
            crop_type: 'Potato',
            scientific_name: 'Phytophthora infestans',
            symptoms: ['Water-soaked leaf spots', 'White growth under leaves', 'Rapid plant collapse'],
            favorable_conditions: ['High humidity', 'Frequent rainfall', 'Cool temperatures'],
            prevention_methods: ['Resistant varieties', 'Crop rotation', 'Preventive fungicide schedule'],
          },
          {
            name: 'Powdery Mildew',
            description: 'Common fungal disease that forms white powdery patches on leaves.',
            crop_type: 'Tomato',
            scientific_name: 'Oidium spp.',
            symptoms: ['White powdery spots', 'Leaf yellowing', 'Reduced vigor'],
            favorable_conditions: ['Warm days', 'Cool nights', 'High relative humidity'],
            prevention_methods: ['Improve airflow', 'Avoid overhead watering', 'Sulfur-based control'],
          },
          {
            name: 'Bacterial Spot',
            description: 'Bacterial disease causing dark lesions on leaves and fruit.',
            crop_type: 'Tomato',
            scientific_name: 'Xanthomonas spp.',
            symptoms: ['Small dark leaf spots', 'Defoliation', 'Fruit blemishes'],
            favorable_conditions: ['Warm temperatures', 'Rain splash', 'High humidity'],
            prevention_methods: ['Clean seed/seedlings', 'Copper sprays', 'Field sanitation'],
          },
        ];

        for (const disease of defaults) {
          try {
            await createDisease(disease);
          } catch (e) {
            const msg = String(e?.message || e);
            if (!/already exists|duplicate|unique/i.test(msg)) {
              // If seeding fails for reasons other than duplicates, stop attempting.
              break;
            }
          }
        }

        try {
          const seeded = await fetchDiseases();
          diseasesData = (Array.isArray(seeded) ? seeded : []).filter(
            (d) => d && typeof d.name === 'string' && d.name.trim().length > 0
          );
          if (diseasesData.length > 0) {
            localStorage.setItem('disease_defaults_seeded', '1');
            setNotice('Disease catalog ready. Auto-forecast will run…');
          }
        } catch {
          // Ignore: the page will remain in empty state with a manual seed option.
        }
      }

      setFarms(farmsData);
      setDiseases(diseasesData);

      // Set from URL params or defaults
      const farmParam = searchParams.get('farm');
      const diseaseParam = searchParams.get('disease');
      
      if (farmParam) {
        setSelectedFarm(parseInt(farmParam));
      } else if (farmsData.length > 0) {
        setSelectedFarm(farmsData[0].id);
      }

      if (diseaseParam && diseasesData.some((d) => d.name === diseaseParam)) {
        setSelectedDisease(diseaseParam);
      } else if (diseasesData.length > 0) {
        setSelectedDisease(diseasesData[0].name);
      } else {
        setSelectedDisease('');
      }

      setLoading(false);
    } catch (err) {
      console.error('Failed to load initial data:', err);
      setInitError(err?.message || 'Failed to load farms/diseases.');
      setLoading(false);
    }
  };

  // Prevent "blank" disease selection: always select the first valid disease.
  useEffect(() => {
    if (!Array.isArray(diseases) || diseases.length === 0) return;
    if (selectedDisease && diseases.some((d) => d.name === selectedDisease)) return;
    setSelectedDisease(diseases[0].name);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [diseases]);

  const loadForecasts = async () => {
    if (!selectedFarm || !selectedDisease) return;

    try {
      setForecastLoading(true);
      setForecastError(null);
      setNotice(null);
      const [daily, weekly] = await Promise.all([
        fetchDailyForecast(selectedFarm, selectedDisease, forecastDays),
        fetchWeeklyForecast(selectedFarm, selectedDisease)
      ]);
      setDailyForecast(Array.isArray(daily) ? daily : []);
      setWeeklyForecast(weekly || null);
    } catch (err) {
      console.error('Failed to load forecasts:', err);
      setForecastError(err?.message || 'Failed to load forecast data.');
      setDailyForecast([]);
      setWeeklyForecast(null);
    } finally {
      setForecastLoading(false);
    }
  };

  const formatDate = (value) => {
    if (!value) return '-';
    const date = value instanceof Date ? value : new Date(value);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', weekday: 'short' });
  };

  const getRiskTone = (riskLevel) => {
    const level = (riskLevel || '').toLowerCase();
    if (level === 'critical' || level === 'severe') return 'critical';
    if (level === 'high') return 'high';
    if (level === 'moderate' || level === 'medium') return 'moderate';
    return 'low';
  };

  const insights = useMemo(() => {
    const forecast = Array.isArray(dailyForecast) ? dailyForecast : [];
    if (!forecast.length) {
      return null;
    }

    const peak = forecast.reduce((acc, item) => (item.risk_score > acc.risk_score ? item : acc), forecast[0]);
    const actionableDays = forecast.filter((d) => Boolean(d.actionable)).length;
    const avgRisk = forecast.reduce((sum, item) => sum + (Number(item.risk_score) || 0), 0) / forecast.length;
    const avgConfidence = forecast.reduce((sum, item) => sum + (Number(item.confidence) || 0), 0) / forecast.length;

    const highestHumidityDay = forecast.reduce((acc, item) => {
      const humidity = Number(item?.weather?.humidity);
      const current = Number(acc?.weather?.humidity);
      if (!Number.isFinite(humidity)) return acc;
      if (!Number.isFinite(current)) return item;
      return humidity > current ? item : acc;
    }, forecast[0]);

    return {
      peak,
      actionableDays,
      avgRisk,
      avgConfidence,
      highestHumidityDay,
    };
  }, [dailyForecast]);

  const selectedFarmLabel = useMemo(() => {
    const match = farms.find((f) => f.id === selectedFarm);
    if (!match) return '';
    const parts = [match.name, match.location].filter(Boolean);
    return parts.join(' — ');
  }, [farms, selectedFarm]);

  const diseaseNameById = useMemo(() => {
    const m = new Map();
    for (const d of Array.isArray(diseases) ? diseases : []) {
      if (d && typeof d.id === 'number' && typeof d.name === 'string') {
        m.set(d.id, d.name);
      }
    }
    return m;
  }, [diseases]);

  const handleGenerateForecast = async () => {
    if (!selectedFarm || !selectedDisease) return;
    try {
      setIsGenerating(true);
      setForecastError(null);
      setNotice(null);
      const response = await predictDisease(selectedFarm, selectedDisease, cropType, forecastDays);
      const forecast = response?.forecast;
      if (forecast) {
        setWeeklyForecast(forecast);
        if (Array.isArray(forecast.daily_forecasts)) {
          setDailyForecast(forecast.daily_forecasts);
        } else {
          await loadForecasts();
        }
        setNotice('Forecast generated from latest weather inputs.');
      } else {
        await loadForecasts();
        setNotice('Prediction generated. Loading forecast data…');
      }
    } catch (err) {
      console.error('Failed to generate forecast:', err);
      setForecastError(err?.message || 'Failed to generate forecast.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSubmitObservation = async () => {
    if (!selectedFarm) return;
    if (!selectedDisease) {
      setObsError('Select a disease first.');
      return;
    }
    try {
      setObsSaving(true);
      setObsError(null);
      await submitDiseaseObservation({
        farmId: selectedFarm,
        diseaseName: selectedDisease,
        diseasePresent: obsPresent,
        diseaseSeverity: obsPresent ? obsSeverity : null,
        observationDate: obsDate,
        notes: obsNotes,
      });
      setObsNotes('');
      await loadObservations();
      setNotice('Observation saved. This improves model quality over time.');
    } catch (e) {
      setObsError(e?.message || 'Failed to submit observation');
    } finally {
      setObsSaving(false);
    }
  };

  // Auto-generate forecast if none exists yet for the selected farm+disease.
  useEffect(() => {
    if (!AUTO_FORECAST) return;
    if (loading) return;
    if (initError) return;
    if (!selectedFarm || !selectedDisease) return;
    if (forecastLoading || isGenerating) return;

    const hasAnyForecast = (Array.isArray(dailyForecast) && dailyForecast.length > 0) || Boolean(weeklyForecast);
    if (hasAnyForecast) return;

    const key = `${selectedFarm}::${selectedDisease}::${cropType}::${forecastDays}`;
    if (lastAutoKeyRef.current === key) return;

    // Mark before calling so a backend error doesn't loop forever.
    lastAutoKeyRef.current = key;
    setNotice('Auto-forecast is running…');
    handleGenerateForecast();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [AUTO_FORECAST, loading, initError, selectedFarm, selectedDisease, cropType, forecastDays, forecastLoading, isGenerating, dailyForecast, weeklyForecast]);

  const handleSeedDiseases = async () => {
    try {
      setSeedBusy(true);
      setForecastError(null);
      setNotice(null);

      const defaults = [
        {
          name: 'Late Blight',
          description: 'A major disease that thrives in cool, wet conditions.',
          crop_type: 'Potato',
          scientific_name: 'Phytophthora infestans',
          symptoms: ['Water-soaked leaf spots', 'White growth under leaves', 'Rapid plant collapse'],
          favorable_conditions: ['High humidity', 'Frequent rainfall', 'Cool temperatures'],
          prevention_methods: ['Resistant varieties', 'Crop rotation', 'Preventive fungicide schedule'],
        },
        {
          name: 'Powdery Mildew',
          description: 'Common fungal disease that forms white powdery patches on leaves.',
          crop_type: 'Tomato',
          scientific_name: 'Oidium spp.',
          symptoms: ['White powdery spots', 'Leaf yellowing', 'Reduced vigor'],
          favorable_conditions: ['Warm days', 'Cool nights', 'High relative humidity'],
          prevention_methods: ['Improve airflow', 'Avoid overhead watering', 'Sulfur-based control'],
        },
        {
          name: 'Bacterial Spot',
          description: 'Bacterial disease causing dark lesions on leaves and fruit.',
          crop_type: 'Tomato',
          scientific_name: 'Xanthomonas spp.',
          symptoms: ['Small dark leaf spots', 'Defoliation', 'Fruit blemishes'],
          favorable_conditions: ['Warm temperatures', 'Rain splash', 'High humidity'],
          prevention_methods: ['Clean seed/seedlings', 'Copper sprays', 'Field sanitation'],
        },
      ];

      for (const disease of defaults) {
        try {
          await createDisease(disease);
        } catch (e) {
          // If backend rejects duplicates, ignore and keep going.
          const msg = String(e?.message || e);
          if (!/already exists|duplicate|unique/i.test(msg)) throw e;
        }
      }

      const diseasesData = await fetchDiseases();
      const cleanDiseases = (Array.isArray(diseasesData) ? diseasesData : []).filter(
        (d) => d && typeof d.name === 'string' && d.name.trim().length > 0
      );
      setDiseases(cleanDiseases);
      if (!selectedDisease && diseasesData.length > 0) {
        setSelectedDisease(cleanDiseases[0]?.name || '');
      }
      setNotice('Seeded common diseases. You can now generate forecasts.');
    } catch (err) {
      setForecastError(err?.message || 'Failed to seed diseases.');
    } finally {
      setSeedBusy(false);
    }
  };

  const handleFarmChange = (farmId) => {
    setSelectedFarm(farmId);
    setSearchParams({ farm: farmId, disease: selectedDisease });
  };

  const handleDiseaseChange = (diseaseName) => {
    setSelectedDisease(diseaseName);
    setSearchParams({ farm: selectedFarm, disease: diseaseName });
  };

  if (loading) {
    return (
      <div className="forecasts-page">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading forecasts...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="forecasts-page">
      <div className="forecasts-header">
        <div className="df-title-row">
          <h1>Disease Forecasts</h1>
          <span className="df-build-stamp">UI Build: 2026-01-10</span>
        </div>
        <p>Daily and weekly disease risk predictions with actionable insights</p>
      </div>

      <div className="forecast-explainer">
        <div className="forecast-explainer__title">What are we forecasting?</div>
        <div className="forecast-explainer__body">
          <p>
            This page forecasts <strong>disease risk</strong> (not yield). For a selected farm and disease, we estimate how likely an
            outbreak becomes over the next few days based on forecast weather and farm context.
          </p>
          <ul>
            <li><strong>Daily Risk Score (0–100):</strong> how risky each day looks for that disease.</li>
            <li><strong>Risk Level:</strong> Low / Moderate / High / Critical (derived from the score).</li>
            <li><strong>Confidence:</strong> how reliable the estimate is (usually higher for near-term days).</li>
            <li><strong>Actionable Days:</strong> days where risk crosses an action threshold (e.g., scouting/spraying).</li>
          </ul>
          <p className="forecast-explainer__hint">
            To forecast, you need at least one farm <em>and</em> at least one disease saved in the system.
          </p>
        </div>
      </div>

      <div className="sentinel-panel">
        <div className="sentinel-panel__title">Sentinel AI (Automatic)</div>
        {diagnosticsError ? (
          <div className="sentinel-panel__error">{diagnosticsError}</div>
        ) : diagnostics ? (
          <div className="sentinel-panel__grid">
            <div className="sentinel-metric">
              <div className="sentinel-label">Crop cover</div>
              <div className="sentinel-value">{String(diagnostics.cover_class || 'unknown').replace(/_/g, ' ')}</div>
              <div className="sentinel-meta">From NDVI (vegetation signal)</div>
            </div>
            <div className="sentinel-metric">
              <div className="sentinel-label">Stress score</div>
              <div className="sentinel-value">{Math.round((diagnostics.stress_score || 0) * 100)}%</div>
              <div className="sentinel-meta">Trend + anomaly + NDVI level</div>
            </div>
            <div className="sentinel-metric">
              <div className="sentinel-label">Latest NDVI</div>
              <div className="sentinel-value">{diagnostics?.ndvi?.current ?? '—'}</div>
              <div className="sentinel-meta">Points: {diagnostics?.ndvi?.points ?? 0}</div>
            </div>
            <div className="sentinel-metric">
              <div className="sentinel-label">Farm crop type</div>
              <div className="sentinel-value">{diagnostics?.farm_crop_type || '—'}</div>
              <div className="sentinel-meta">Saved on the farm profile</div>
            </div>
            <div className="sentinel-metric sentinel-metric--wide">
              <div className="sentinel-label">Top likely diseases (ranked)</div>
              {Array.isArray(diagnostics.top_disease_risks) && diagnostics.top_disease_risks.length > 0 ? (
                <div className="sentinel-chips">
                  {diagnostics.top_disease_risks.map((x, i) => (
                    <span key={i} className="sentinel-chip">
                      {x.disease}: {Math.round(x.risk_score)}
                    </span>
                  ))}
                </div>
              ) : (
                <div className="sentinel-meta">No diseases in the catalog yet (seed defaults to enable ranking).</div>
              )}
              {Array.isArray(diagnostics.drivers) && diagnostics.drivers.length > 0 && (
                <div className="sentinel-meta">Signals: {diagnostics.drivers.join(' • ')}</div>
              )}
            </div>
          </div>
        ) : (
          <div className="sentinel-panel__loading">Loading Sentinel diagnostics…</div>
        )}
      </div>

      {(initError || forecastError || notice) && (
        <div className={`forecast-banner ${initError || forecastError ? 'is-error' : 'is-info'}`}>
          <div className="forecast-banner__title">
            {initError ? 'Setup issue' : forecastError ? 'Forecast issue' : 'Update'}
          </div>
          <div className="forecast-banner__body">
            {initError || forecastError || notice}
          </div>
          <div className="forecast-banner__actions">
            <button
              type="button"
              className="forecast-btn is-secondary"
              onClick={() => {
                setLoading(true);
                loadInitialData();
              }}
            >
              Retry
            </button>
            {selectedFarm && selectedDisease && (
              <button
                type="button"
                className="forecast-btn is-primary"
                onClick={() => loadForecasts()}
                disabled={forecastLoading}
              >
                {forecastLoading ? 'Refreshing…' : 'Refresh'}
              </button>
            )}
          </div>
        </div>
      )}

      <div className="forecasts-controls">
        <div className="control-group">
          <label>Farm:</label>
          <select value={selectedFarm || ''} onChange={(e) => handleFarmChange(parseInt(e.target.value))}>
            {farms.map(farm => (
              <option key={farm.id} value={farm.id}>
                {farm.name} - {farm.location}
              </option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label>Disease:</label>
          <select value={selectedDisease || ''} onChange={(e) => handleDiseaseChange(e.target.value)} disabled={diseases.length === 0}>
            {diseases.map(disease => (
              <option key={disease.id} value={disease.name}>
                {disease.name}
              </option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label>Crop:</label>
          <select value={cropType} onChange={(e) => setCropType(e.target.value)}>
            <option value="potato">Potato</option>
            <option value="tomato">Tomato</option>
            <option value="wheat">Wheat</option>
            <option value="maize">Maize</option>
          </select>
        </div>

        <div className="control-group">
          <label>Forecast Days:</label>
          <select value={forecastDays} onChange={(e) => setForecastDays(parseInt(e.target.value))}>
            <option value="3">3 Days</option>
            <option value="7">7 Days</option>
            <option value="14">14 Days</option>
          </select>
        </div>

        <div className="control-group forecasts-actions">
          <button
            type="button"
            className="forecast-btn is-primary"
            onClick={handleGenerateForecast}
            disabled={!selectedFarm || !selectedDisease || isGenerating}
            title="Creates a prediction in the backend and returns a fresh forecast"
          >
            {isGenerating ? 'Generating…' : 'Generate Risk Forecast'}
          </button>
        </div>
      </div>

      {(farms.length === 0 || diseases.length === 0) && (
        <div className="empty-state">
          <h2>Nothing to forecast yet</h2>
          <p>
            {farms.length === 0 && 'No farms found. Add farms (with coordinates) to generate forecasts. '}
            {diseases.length === 0 && 'No diseases found. Add diseases (or seed defaults) to start forecasting. '}
          </p>

          {diseases.length === 0 && (
            <div className="empty-state__actions">
              <button
                type="button"
                className="forecast-btn is-primary"
                onClick={handleSeedDiseases}
                disabled={seedBusy}
              >
                {seedBusy ? 'Seeding…' : 'Seed common diseases'}
              </button>
              <button
                type="button"
                className="forecast-btn is-secondary"
                onClick={() => {
                  setLoading(true);
                  loadInitialData();
                }}
                disabled={seedBusy}
              >
                Refresh lists
              </button>
            </div>
          )}
        </div>
      )}

      {selectedFarm && selectedDisease && (
        <div className="context-strip">
          <div className="context-strip__title">Current selection</div>
          <div className="context-strip__meta">
            <span><strong>Farm:</strong> {selectedFarmLabel || `Farm #${selectedFarm}`}</span>
            <span><strong>Disease:</strong> {selectedDisease}</span>
            <span><strong>Horizon:</strong> {forecastDays} days</span>
          </div>
        </div>
      )}

      {selectedFarm && selectedDisease && (
        <div className="obs-panel">
          <div className="obs-panel__title">Ground truth (field observation)</div>
          <div className="obs-panel__subtitle">
            Record what you actually see in the field. This helps validate and improve predictions.
          </div>

          <div className="obs-panel__grid">
            <div className="obs-field">
              <label>Date</label>
              <input type="date" value={obsDate} onChange={(e) => setObsDate(e.target.value)} />
            </div>

            <div className="obs-field">
              <label>Disease present?</label>
              <select value={obsPresent ? 'yes' : 'no'} onChange={(e) => setObsPresent(e.target.value === 'yes')}>
                <option value="yes">Yes</option>
                <option value="no">No</option>
              </select>
            </div>

            <div className="obs-field">
              <label>Severity</label>
              <select value={obsSeverity} onChange={(e) => setObsSeverity(e.target.value)} disabled={!obsPresent}>
                <option value="low">Low</option>
                <option value="moderate">Moderate</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>

            <div className="obs-field obs-field--wide">
              <label>Notes</label>
              <input
                type="text"
                value={obsNotes}
                onChange={(e) => setObsNotes(e.target.value)}
                placeholder="Symptoms, where you saw it, photos taken, etc."
              />
            </div>

            <div className="obs-actions">
              <button type="button" className="forecast-btn is-primary" onClick={handleSubmitObservation} disabled={obsSaving}>
                {obsSaving ? 'Saving…' : 'Save observation'}
              </button>
              <button type="button" className="forecast-btn is-secondary" onClick={loadObservations} disabled={obsLoading || obsSaving}>
                {obsLoading ? 'Loading…' : 'Refresh history'}
              </button>
            </div>
          </div>

          {obsError && <div className="obs-panel__error">{obsError}</div>}

          <div className="obs-panel__history">
            <div className="obs-panel__history-title">Recent observations</div>
            {obsLoading ? (
              <div className="obs-panel__muted">Loading…</div>
            ) : observations.length === 0 ? (
              <div className="obs-panel__muted">No observations yet for this farm.</div>
            ) : (
              <div className="obs-list">
                {observations.slice(0, 8).map((o) => {
                  const diseaseLabel = o?.disease_id ? (diseaseNameById.get(o.disease_id) || `Disease #${o.disease_id}`) : 'Unspecified';
                  return (
                    <div key={o.id} className="obs-item">
                      <div className="obs-item__main">
                        <div className="obs-item__title">{diseaseLabel}</div>
                        <div className="obs-item__meta">
                          {o?.observation_date || '—'} • {o?.disease_present ? 'present' : 'not present'}
                          {o?.disease_severity ? ` • ${o.disease_severity}` : ''}
                        </div>
                      </div>
                      {o?.notes && <div className="obs-item__notes">{o.notes}</div>}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}

      {weeklyForecast && (
        <div className="weekly-forecast-card">
          <h2>📅 Weekly Summary</h2>
          <div className="weekly-content">
            <div className="weekly-risk">
              <RiskIndicator 
                riskScore={weeklyForecast.average_risk_score}
                riskLevel={weeklyForecast.weekly_risk_level}
                size="large"
              />
            </div>
            <div className="weekly-details">
              <div className="weekly-stat">
                <span className="label">Peak Risk Day:</span>
                <span className="value">🔴 {formatDate(weeklyForecast.peak_risk_day)}</span>
              </div>
              <div className="weekly-stat">
                <span className="label">Actionable Days (≥ 60):</span>
                <span className="value">{weeklyForecast.critical_action_days} days</span>
              </div>
              <div className="weekly-stat">
                <span className="label">Peak Risk Score:</span>
                <span className="value">{Math.round(weeklyForecast.peak_risk_score)} / 100</span>
              </div>
            </div>
          </div>

          {weeklyForecast.recommended_strategy && (
            <div className="weekly-recommendations">
              <h3>Recommended Strategy</h3>
              <p className="weekly-strategy">{weeklyForecast.recommended_strategy}</p>
            </div>
          )}
        </div>
      )}

      {insights && (
        <div className="insights-section">
          <h2>🔎 Insights</h2>
          <div className="insights-grid">
            <div className={`insight-card tone-${getRiskTone(weeklyForecast?.weekly_risk_level || insights?.peak?.risk_level)}`}>
              <div className="insight-label">Average Risk</div>
              <div className="insight-value">{Math.round(insights.avgRisk)} / 100</div>
              <div className="insight-meta">Based on {dailyForecast.length} day(s) forecast</div>
            </div>
            <div className="insight-card">
              <div className="insight-label">Peak Risk</div>
              <div className="insight-value">{Math.round(insights.peak.risk_score)} / 100</div>
              <div className="insight-meta">{formatDate(insights.peak.date)}</div>
            </div>
            <div className="insight-card">
              <div className="insight-label">Action Days</div>
              <div className="insight-value">{insights.actionableDays}</div>
              <div className="insight-meta">Days where risk ≥ 60</div>
            </div>
            <div className="insight-card">
              <div className="insight-label">Forecast Confidence</div>
              <div className="insight-value">{Math.round(insights.avgConfidence * 100)}%</div>
              <div className="insight-meta">Higher for near-term days</div>
            </div>
          </div>
        </div>
      )}

      <div className="daily-forecast-section">
        <h2>📊 Daily Forecast</h2>
        {forecastLoading ? (
          <div className="loading-inline">Loading forecast data…</div>
        ) : dailyForecast.length === 0 ? (
          <div className="no-data">
            <p>No forecast data available yet.</p>
            <button type="button" className="forecast-btn is-primary" onClick={handleGenerateForecast} disabled={isGenerating}>
              {isGenerating ? 'Generating…' : 'Generate Risk Forecast Now'}
            </button>
          </div>
        ) : (
          <div className="daily-forecast-grid">
            {dailyForecast.map((day, idx) => (
              <div key={idx} className="daily-forecast-card">
                <div className="day-header">
                  <div className="day-date">{formatDate(day.date)}</div>
                    {day.actionable && <span className="critical-badge">Action</span>}
                </div>

                <RiskIndicator 
                  riskScore={day.risk_score}
                  riskLevel={day.risk_level}
                  size="small"
                />

                <div className="day-stats">
                  <div className="day-stat">
                    <span className="value">{Math.round((day.risk_score / 100) * 100)}%</span>
                    <span className="label">Risk (derived)</span>
                  </div>
                  <div className="day-stat">
                    <span className="value">{Math.round((day.confidence || 0) * 100)}%</span>
                    <span className="label">Confidence</span>
                  </div>
                </div>

                {day.weather && (
                  <div className="day-weather">
                    <span className="weather-chip">Temp: {day.weather.temperature ?? '--'}°C</span>
                    <span className="weather-chip">Humidity: {day.weather.humidity ?? '--'}%</span>
                    <span className="weather-chip">Rainfall: {day.weather.rainfall ?? '--'} mm</span>
                    <span className="weather-chip">Leaf wetness: {day.weather.leaf_wetness ?? '--'}</span>
                  </div>
                )}

                {weeklyForecast?.recommended_strategy && idx === 0 && (
                  <div className="day-actions">
                    <div className="day-actions__title">Recommended strategy</div>
                    <div className="day-actions__text">{weeklyForecast.recommended_strategy}</div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default DiseaseForecasts;
