import React, { useState, useEffect } from 'react';
import { fetchDiseases, fetchDiseasePredictions, predictDisease, fetchFarms } from '../api';
import DiseaseList from '../components/DiseaseList';
import './Diseases.css';

const Diseases = () => {
  const [diseases, setDiseases] = useState([]);
  const [predictions, setPredictions] = useState([]);
  const [farms, setFarms] = useState([]);
  const [selectedFarm, setSelectedFarm] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    if (selectedFarm) {
      loadPredictions();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedFarm]);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      const [diseasesData, farmsData] = await Promise.all([
        fetchDiseases(),
        fetchFarms()
      ]);
      setDiseases(diseasesData);
      setFarms(farmsData);
      if (farmsData.length > 0) {
        setSelectedFarm(farmsData[0].id);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadPredictions = async () => {
    if (!selectedFarm) return;
    try {
      const predictionsData = await fetchDiseasePredictions(selectedFarm, null, 50);
      setPredictions(predictionsData);
    } catch (err) {
      console.error('Failed to load predictions:', err);
    }
  };

  const handlePredict = async (disease) => {
    if (!selectedFarm) {
      alert('Please select a farm first');
      return;
    }

    try {
      setGenerating(true);
      await predictDisease(selectedFarm, disease.name, 'mixed', 7);
      await loadPredictions();
      alert(`Prediction generated for ${disease.name}`);
    } catch (err) {
      alert(`Failed to generate prediction: ${err.message}`);
    } finally {
      setGenerating(false);
    }
  };

  const handleViewDetails = (disease, prediction) => {
    window.location.href = `/disease-forecasts?farm=${selectedFarm}&disease=${encodeURIComponent(disease.name)}`;
  };

  const handleGenerateAll = async () => {
    if (!selectedFarm) {
      alert('Please select a farm first');
      return;
    }

    if (!window.confirm('Generate predictions for all diseases? This may take a moment.')) {
      return;
    }

    try {
      setGenerating(true);
      for (const disease of diseases) {
        await predictDisease(selectedFarm, disease.name, 'mixed', 7);
      }
      await loadPredictions();
      alert('All predictions generated successfully!');
    } catch (err) {
      alert(`Failed to generate predictions: ${err.message}`);
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="diseases-page">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading diseases...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="diseases-page">
        <div className="error-container">
          <h2>Error</h2>
          <p>{error}</p>
          <button onClick={loadInitialData}>Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="diseases-page">
      <div className="diseases-header">
        <div>
          <h1>Disease Predictions</h1>
          <p>Monitor and predict crop diseases across your farms</p>
        </div>
        <button 
          className="btn btn--generate"
          onClick={handleGenerateAll}
          disabled={generating || !selectedFarm}
        >
          {generating ? 'Generating...' : '🔄 Generate All Predictions'}
        </button>
      </div>

      <div className="diseases-controls">
        <div className="farm-selector">
          <label>Select Farm:</label>
          <select 
            value={selectedFarm || ''} 
            onChange={(e) => setSelectedFarm(parseInt(e.target.value))}
            disabled={farms.length === 0}
          >
            {farms.length === 0 && <option>No farms available</option>}
            {farms.map(farm => (
              <option key={farm.id} value={farm.id}>
                {farm.name} - {farm.location}
              </option>
            ))}
          </select>
        </div>

        <div className="diseases-stats">
          <div className="stat">
            <div className="stat-value">{diseases.length}</div>
            <div className="stat-label">Diseases Tracked</div>
          </div>
          <div className="stat">
            <div className="stat-value">{predictions.length}</div>
            <div className="stat-label">Predictions</div>
          </div>
          <div className="stat">
            <div className="stat-value">
              {predictions.filter(p => p.risk_level === 'high' || p.risk_level === 'severe').length}
            </div>
            <div className="stat-label">High Risk</div>
          </div>
        </div>
      </div>

      <DiseaseList
        farmId={selectedFarm}
        diseases={diseases}
        predictions={predictions}
        onPredict={handlePredict}
        onViewDetails={handleViewDetails}
        loading={generating}
      />
    </div>
  );
};

export default Diseases;
