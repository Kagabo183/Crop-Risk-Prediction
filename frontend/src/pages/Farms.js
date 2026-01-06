import React, { useEffect, useState } from 'react';
import { fetchFarms } from '../api';
import '../styles/common.css';

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

	if (loading) {
		return (
			<div className="page-container">
				<div className="loading-state">Loading farms...</div>
			</div>
		);
	}

	if (error) {
		return (
			<div className="page-container">
				<div className="error-state">Error: {error}</div>
			</div>
		);
	}

	return (
		<div className="page-container">
			<div className="page-header">
				<h1>🏠 Farm Management</h1>
				<p>Monitor and manage all registered farms in the system</p>
			</div>

			<div className="data-table-container">
				<table className="data-table">
					<thead>
						<tr>
							<th>Farm Name</th>
							<th>Location</th>
							<th>Area (ha)</th>
							<th>Owner ID</th>
							<th>Status</th>
						</tr>
					</thead>
					<tbody>
						{farms.length === 0 ? (
							<tr>
								<td colSpan={5}>
									<div className="empty-state">
										<div className="empty-state-icon">🌾</div>
										<div className="empty-state-text">No farms found</div>
									</div>
								</td>
							</tr>
						) : (
							farms.map(farm => (
								<tr key={farm.id}>
									<td>{farm.name || '-'}</td>
									<td>{farm.location || '-'}</td>
									<td>{farm.area != null ? farm.area : '-'}</td>
									<td>{farm.owner_id || '-'}</td>
									<td>
										<span className="badge badge-success">Active</span>
									</td>
								</tr>
							))
						)}
					</tbody>
				</table>
			</div>
		</div>
	);
};

export default Farms;
