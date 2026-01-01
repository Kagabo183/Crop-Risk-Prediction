

import React, { useEffect, useState } from 'react';
import { fetchPredictions } from '../api';

const Predictions = () => {
	const [predictions, setPredictions] = useState([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState(null);

	useEffect(() => {
		fetchPredictions()
			.then(data => {
				setPredictions(data);
				setLoading(false);
			})
			.catch(err => {
				setError(err.message);
				setLoading(false);
			});
	}, []);

	return (
		<div style={{ padding: 32 }}>
			<h2>Predictions</h2>
			{loading && <p>Loading...</p>}
			{error && <p style={{ color: 'red' }}>Error: {error}</p>}
			{!loading && !error && (
				<table style={{width: '100%', background: '#fff', borderRadius: 8, boxShadow: '0 2px 8px rgba(0,0,0,0.04)', borderCollapse: 'collapse'}}>
					<thead>
						<tr style={{background: '#f7fafc'}}>
							<th style={{padding: 8, textAlign: 'left'}}>Farm</th>
							<th style={{padding: 8, textAlign: 'left'}}>Date</th>
							<th style={{padding: 8, textAlign: 'left'}}>Risk</th>
							<th style={{padding: 8, textAlign: 'left'}}>Yield Loss %</th>
							<th style={{padding: 8, textAlign: 'left'}}>Disease Risk</th>
							<th style={{padding: 8, textAlign: 'left'}}>Action</th>
						</tr>
					</thead>
					<tbody>
						{predictions.length === 0 && (
							<tr><td colSpan={6} style={{padding: 8}}>No predictions found.</td></tr>
						)}
						{predictions.map(pred => (
							<tr key={pred.id}>
								<td style={{padding: 8}}>{pred.farm_id || '-'}</td>
								<td style={{padding: 8}}>{pred.date || '-'}</td>
								<td style={{padding: 8}}>{pred.risk_score != null ? pred.risk_score : '-'}</td>
								<td style={{padding: 8}}>{pred.yield_loss_percent != null ? pred.yield_loss_percent : '-'}</td>
								<td style={{padding: 8}}>{pred.disease_risk_level || '-'}</td>
								<td style={{padding: 8}}><button style={{padding: '4px 12px', background: '#4fd1c5', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer'}}>Predict Risk</button></td>
							</tr>
						))}
					</tbody>
				</table>
			)}
		</div>
	);
};

export default Predictions;
