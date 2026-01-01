import React from 'react';
import '../components/Dashboard.css';

const Dashboard = () => (
  <div className="dashboard-content">
    <h2>Overview</h2>
    <div className="dashboard-widgets">
      <div className="widget">Farms: --</div>
      <div className="widget">Predictions: --</div>
      <div className="widget">Alerts: --</div>
    </div>
  </div>
);

export default Dashboard;
