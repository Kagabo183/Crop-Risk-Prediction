
import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Dashboard from '../components/Dashboard';
import Farms from '../pages/Farms';
import Predictions from '../pages/Predictions';
import Alerts from '../pages/Alerts';
import Users from '../pages/Users';
import SatelliteImages from '../pages/SatelliteImages';
import Diseases from '../pages/Diseases';
import DiseaseForecasts from '../pages/DiseaseForecasts';
import './MainContent.css';

const MainContent = () => (
  <main className="main-content">
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/farms" element={<Farms />} />
      <Route path="/predictions" element={<Predictions />} />
      <Route path="/diseases" element={<Diseases />} />
      <Route path="/disease-forecasts" element={<DiseaseForecasts />} />
      <Route path="/alerts" element={<Alerts />} />
      <Route path="/users" element={<Users />} />
      <Route path="/satellite-images" element={<SatelliteImages />} />
    </Routes>
  </main>
);

export default MainContent;
