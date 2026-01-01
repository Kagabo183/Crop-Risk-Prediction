

import React, { useEffect, useState } from 'react';
import { fetchAlerts } from '../api';

const Alerts = () => {
	const [alerts, setAlerts] = useState([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState(null);

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

	return (
		<div style={{ padding: 32 }}>
			<h2>Alerts</h2>
			{loading && <p>Loading...</p>}
			{error && <p style={{ color: 'red' }}>Error: {error}</p>}
			{!loading && !error && (
				<table style={{width: '100%', background: '#fff', borderRadius: 8, boxShadow: '0 2px 8px rgba(0,0,0,0.04)', borderCollapse: 'collapse'}}>
					<thead>
						<tr style={{background: '#f7fafc'}}>
							<th style={{padding: 8, textAlign: 'left'}}>Level</th>
							<th style={{padding: 8, textAlign: 'left'}}>Message</th>
							<th style={{padding: 8, textAlign: 'left'}}>Farm</th>
							<th style={{padding: 8, textAlign: 'left'}}>Date</th>
						</tr>
					</thead>
					<tbody>
						{alerts.length === 0 && (
							<tr><td colSpan={4} style={{padding: 8}}>No alerts found.</td></tr>
						)}
						{alerts.map(alert => (
							<tr key={alert.id}>
								<td style={{padding: 8}}>{alert.level || '-'}</td>
								<td style={{padding: 8}}>{alert.message || '-'}</td>
								<td style={{padding: 8}}>{alert.farm_id || '-'}</td>
								<td style={{padding: 8}}>{alert.created_at || '-'}</td>
							</tr>
						))}
					</tbody>
				</table>
			)}
		</div>
	);
};

export default Alerts;
