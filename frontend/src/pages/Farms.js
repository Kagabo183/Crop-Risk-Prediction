import React, { useEffect, useState } from 'react';
import { fetchFarms, updateFarm } from '../api';
import '../styles/common.css';

const Farms = () => {
	const [farms, setFarms] = useState([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState(null);
	const [savingId, setSavingId] = useState(null);

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
				<h1>Farm Management</h1>
				<p>Monitor and manage all registered farms in the system</p>
			</div>

			<div className="data-table-container">
				<table className="data-table">
					<thead>
						<tr>
							<th>Farm Name</th>
							<th>Location</th>
							<th>Crop Type</th>
							<th>Area (ha)</th>
							<th>Owner ID</th>
							<th>Status</th>
							<th>Actions</th>
						</tr>
					</thead>
					<tbody>
						{farms.length === 0 ? (
							<tr>
								<td colSpan={7}>
									<div className="empty-state">
										<div className="empty-state-text">No farms found</div>
									</div>
								</td>
							</tr>
						) : (
							farms.map(farm => (
								<tr key={farm.id}>
									<td>{farm.name || '-'}</td>
									<td>{farm.location || '-'}</td>
									<td>{farm.crop_type || '-'}</td>
									<td>{farm.area != null ? farm.area : '-'}</td>
									<td>{farm.owner_id || '-'}</td>
									<td>
										<span className="badge badge-success">Active</span>
									</td>
									<td>
										<button
											className="btn"
											disabled={savingId === farm.id}
											onClick={async () => {
												const next = window.prompt('Set crop type for this farm (e.g., potato, maize, tomato):', farm.crop_type || '');
												if (next == null) return;
												const trimmed = String(next).trim();
												try {
													setSavingId(farm.id);
													const updated = await updateFarm(farm.id, { crop_type: trimmed || null });
													setFarms((prev) => prev.map((f) => (f.id === farm.id ? updated : f)));
												} catch (e) {
													alert(e?.message || 'Failed to update farm');
												} finally {
													setSavingId(null);
												}
											}}
										>
											{savingId === farm.id ? 'Saving…' : 'Set crop'}
										</button>
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
