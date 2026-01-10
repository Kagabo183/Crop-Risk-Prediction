

import React, { useEffect, useState } from 'react';
import { fetchAlerts } from '../api';

const Alerts = () => {
	const [alerts, setAlerts] = useState([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState(null);
	const [activeTab, setActiveTab] = useState('notifications'); // 'notifications' or 'alerts'

	useEffect(() => {
		fetchAlerts()
			.then(data => {
				setAlerts(data);
				setLoading(false);
			})
			.catch(err => {
				setError(err.message);
				setLoading(false);
			});
	}, []);

	// Filter logic: 
	// Notifications = info, system, or undefined/null levels
	// Alerts = warning, error, critical, high, moderate, low levels
	const filteredAlerts = alerts.filter(alert => {
		const lvl = (alert.level || 'info').toLowerCase();
		const isNotification = ['info', 'system', 'success'].includes(lvl);
		
		if (activeTab === 'notifications') {
			return isNotification;
		} else {
			return !isNotification;
		}
	});

	const tabStyle = (isActive) => ({
		padding: '12px 24px',
		cursor: 'pointer',
		fontWeight: 600,
		borderBottom: isActive ? '3px solid #3b82f6' : '3px solid transparent',
		color: isActive ? '#3b82f6' : '#6b7280',
		transition: 'all 0.2s ease'
	});

	return (
		<div style={{ padding: 32, maxWidth: '1200px', margin: '0 auto' }}>
			{/* Tab Header */}
			<div style={{ 
				display: 'flex', 
				gap: '16px', 
				marginBottom: '32px', 
				borderBottom: '1px solid #e5e7eb',
				paddingBottom: '0' 
			}}>
				<div 
					onClick={() => setActiveTab('notifications')}
					style={tabStyle(activeTab === 'notifications')}
				>
					Notifications
				</div>
				<div 
					onClick={() => setActiveTab('alerts')}
					style={tabStyle(activeTab === 'alerts')}
				>
					Risk Alerts
				</div>
			</div>

			<div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
				<h2 style={{ margin: 0, color: '#1f2937' }}>
					{activeTab === 'notifications' ? 'System Updates & Data Notifications' : 'Disease & Risk Alerts'}
				</h2>
			</div>

			{loading && (
				<div style={{ textAlign: 'center', padding: '40px', color: '#6b7280' }}>
					Loading...
				</div>
			)}
			
			{error && (
				<div style={{ padding: '16px', background: '#fee2e2', color: '#ef4444', borderRadius: '8px' }}>
					Error: {error}
				</div>
			)}

			{!loading && !error && (
				<div style={{ background: '#fff', borderRadius: '12px', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)', overflow: 'hidden' }}>
					<table style={{ width: '100%', borderCollapse: 'collapse' }}>
						<thead>
							<tr style={{ background: '#f9fafb', borderBottom: '1px solid #e5e7eb' }}>
								<th style={{ padding: '16px', textAlign: 'left', fontSize: '12px', textTransform: 'uppercase', color: '#6b7280', fontWeight: 600 }}>Level</th>
								<th style={{ padding: '16px', textAlign: 'left', fontSize: '12px', textTransform: 'uppercase', color: '#6b7280', fontWeight: 600 }}>Message</th>
								<th style={{ padding: '16px', textAlign: 'left', fontSize: '12px', textTransform: 'uppercase', color: '#6b7280', fontWeight: 600 }}>Related Farm</th>
								<th style={{ padding: '16px', textAlign: 'left', fontSize: '12px', textTransform: 'uppercase', color: '#6b7280', fontWeight: 600 }}>Date/Time</th>
							</tr>
						</thead>
						<tbody>
							{filteredAlerts.length === 0 && (
								<tr>
									<td colSpan={4} style={{ padding: '40px', textAlign: 'center', color: '#9ca3af' }}>
										No {activeTab} found
									</td>
								</tr>
							)}
							{filteredAlerts.map((alert, idx) => {
								let badgeColor = '#e5e7eb';
								let badgeText = '#374151';
								const lvl = (alert.level || 'info').toLowerCase();

								if (lvl === 'critical' || lvl === 'severe') {
									badgeColor = '#fee2e2';
									badgeText = '#dc2626';
								} else if (lvl === 'high' || lvl === 'warning') {
									badgeColor = '#ffedd5';
									badgeText = '#ea580c';
								} else if (lvl === 'moderate') {
									badgeColor = '#fef9c3';
									badgeText = '#ca8a04';
								} else if (lvl === 'info' || lvl === 'system') {
									badgeColor = '#dbeafe';
									badgeText = '#2563eb';
								} else if (lvl === 'success') {
									badgeColor = '#d1fae5';
									badgeText = '#059669';
								}

								return (
									<tr key={alert.id || idx} style={{ borderBottom: '1px solid #f3f4f6' }}>
										<td style={{ padding: '16px' }}>
											<span style={{
												padding: '4px 8px',
												borderRadius: '9999px',
												background: badgeColor,
												color: badgeText,
												fontSize: '12px',
												fontWeight: 600,
												textTransform: 'uppercase'
											}}>
												{alert.level || 'INFO'}
											</span>
										</td>
										<td style={{ padding: '16px', color: '#1f2937', fontWeight: 500 }}>
											{alert.message || '-'}
										</td>
										<td style={{ padding: '16px', color: '#6b7280' }}>
											{alert.farm_id ? (
												<span style={{ 
													padding: '2px 8px', 
													background: '#f3f4f6', 
													borderRadius: '4px',
													fontSize: '13px'
												}}>
													Farm #{alert.farm_id}
												</span>
											) : <span style={{ color: '#d1d5db' }}>-</span>}
										</td>
										<td style={{ padding: '16px', color: '#6b7280', fontSize: '14px' }}>
											{alert.created_at || '-'}
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

export default Alerts;
