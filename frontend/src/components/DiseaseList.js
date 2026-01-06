import React, { useState } from 'react';
import DiseaseCard from './DiseaseCard';
import './DiseaseList.css';

const DiseaseList = ({ farmId, diseases, predictions, onPredict, onViewDetails, loading }) => {
  const [filter, setFilter] = useState('all');
  const [sortBy, setSortBy] = useState('risk');
  const [searchTerm, setSearchTerm] = useState('');

  const getPredictionForDisease = (diseaseId) => {
    return predictions?.find(p => p.disease_id === diseaseId);
  };

  const filterDiseases = () => {
    let filtered = diseases || [];

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(d => 
        d.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        d.scientific_name?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Risk level filter
    if (filter !== 'all') {
      filtered = filtered.filter(d => {
        const pred = getPredictionForDisease(d.id);
        return pred?.risk_level?.toLowerCase() === filter;
      });
    }

    // Sort
    if (sortBy === 'risk') {
      filtered.sort((a, b) => {
        const predA = getPredictionForDisease(a.id);
        const predB = getPredictionForDisease(b.id);
        return (predB?.risk_score || 0) - (predA?.risk_score || 0);
      });
    } else if (sortBy === 'name') {
      filtered.sort((a, b) => a.name.localeCompare(b.name));
    } else if (sortBy === 'type') {
      filtered.sort((a, b) => a.pathogen_type.localeCompare(b.pathogen_type));
    }

    return filtered;
  };

  const filteredDiseases = filterDiseases();

  const getFilterCounts = () => {
    const counts = {
      all: diseases?.length || 0,
      severe: 0,
      high: 0,
      moderate: 0,
      low: 0
    };

    diseases?.forEach(d => {
      const pred = getPredictionForDisease(d.id);
      const level = pred?.risk_level?.toLowerCase();
      if (level && counts.hasOwnProperty(level)) {
        counts[level]++;
      }
    });

    return counts;
  };

  const counts = getFilterCounts();

  if (loading) {
    return (
      <div className="disease-list__loading">
        <div className="spinner"></div>
        <p>Loading diseases...</p>
      </div>
    );
  }

  if (!diseases || diseases.length === 0) {
    return (
      <div className="disease-list__empty">
        <p>No diseases found. Initialize the disease catalog.</p>
      </div>
    );
  }

  return (
    <div className="disease-list">
      <div className="disease-list__controls">
        <div className="disease-list__search">
          <input
            type="text"
            placeholder="Search diseases..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
        </div>

        <div className="disease-list__filters">
          <button 
            className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >
            All ({counts.all})
          </button>
          <button 
            className={`filter-btn ${filter === 'severe' ? 'active' : ''}`}
            onClick={() => setFilter('severe')}
          >
            🔴 Severe ({counts.severe})
          </button>
          <button 
            className={`filter-btn ${filter === 'high' ? 'active' : ''}`}
            onClick={() => setFilter('high')}
          >
            🟠 High ({counts.high})
          </button>
          <button 
            className={`filter-btn ${filter === 'moderate' ? 'active' : ''}`}
            onClick={() => setFilter('moderate')}
          >
            🟡 Moderate ({counts.moderate})
          </button>
          <button 
            className={`filter-btn ${filter === 'low' ? 'active' : ''}`}
            onClick={() => setFilter('low')}
          >
            🟢 Low ({counts.low})
          </button>
        </div>

        <div className="disease-list__sort">
          <label>Sort by:</label>
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
            <option value="risk">Risk Level</option>
            <option value="name">Name</option>
            <option value="type">Type</option>
          </select>
        </div>
      </div>

      {filteredDiseases.length === 0 ? (
        <div className="disease-list__empty">
          <p>No diseases match your filters.</p>
        </div>
      ) : (
        <div className="disease-list__grid">
          {filteredDiseases.map(disease => (
            <DiseaseCard
              key={disease.id}
              disease={disease}
              prediction={getPredictionForDisease(disease.id)}
              onPredict={onPredict}
              onViewDetails={onViewDetails}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default DiseaseList;
