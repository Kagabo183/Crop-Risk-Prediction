

import React, { useEffect, useState } from 'react';
import { fetchFarms } from '../api';

const Farms = () => {
	const [farms, setFarms] = useState([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState(null);

	useEffect(() => {
		fetchFarms()
			.then(data => {
				setFarms(data);
				setLoading(false);
			})
			.catch(err => {
				setError(err.message);
				setLoading(false);
			});
	}, []);

	return (
		<div style={{ padding: 32 }}>
			<h2>Farms</h2>
			{loading && <p>Loading...</p>}
			{error && <p style={{ color: 'red' }}>Error: {error}</p>}
			{!loading && !error && (
				<table style={{width: '100%', background: '#fff', borderRadius: 8, boxShadow: '0 2px 8px rgba(0,0,0,0.04)', borderCollapse: 'collapse'}}>
					<thead>
						<tr style={{background: '#f7fafc'}}>
							<th style={{padding: 8, textAlign: 'left'}}>Name</th>
							<th style={{padding: 8, textAlign: 'left'}}>Location</th>
							<th style={{padding: 8, textAlign: 'left'}}>Area (ha)</th>
							<th style={{padding: 8, textAlign: 'left'}}>Owner</th>
						</tr>
					</thead>
					<tbody>
						{farms.length === 0 && (
							<tr><td colSpan={4} style={{padding: 8}}>No farms found.</td></tr>
						)}
						{farms.map(farm => (
							<tr key={farm.id}>
								<td style={{padding: 8}}>{farm.name || '-'}</td>
								<td style={{padding: 8}}>{farm.location || '-'}</td>
								<td style={{padding: 8}}>{farm.area != null ? farm.area : '-'}</td>
								<td style={{padding: 8}}>{farm.owner_id || '-'}</td>
							</tr>
						))}
					</tbody>
				</table>
			)}
		</div>
	);
};

export default Farms;
