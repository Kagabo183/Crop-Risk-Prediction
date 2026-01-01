

import React, { useEffect, useState } from 'react';
import { fetchUsers } from '../api';

const Users = () => {
	const [users, setUsers] = useState([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState(null);

	useEffect(() => {
		fetchUsers()
			.then(data => {
				setUsers(data);
				setLoading(false);
			})
			.catch(err => {
				setError(err.message);
				setLoading(false);
			});
	}, []);

	return (
		<div style={{ padding: 32 }}>
			<h2>Users</h2>
			{loading && <p>Loading...</p>}
			{error && <p style={{ color: 'red' }}>Error: {error}</p>}
			{!loading && !error && (
				<table style={{width: '100%', background: '#fff', borderRadius: 8, boxShadow: '0 2px 8px rgba(0,0,0,0.04)', borderCollapse: 'collapse'}}>
					<thead>
						<tr style={{background: '#f7fafc'}}>
							<th style={{padding: 8, textAlign: 'left'}}>ID</th>
							<th style={{padding: 8, textAlign: 'left'}}>Email</th>
						</tr>
					</thead>
					<tbody>
						{users.length === 0 && (
							<tr><td colSpan={2} style={{padding: 8}}>No users found.</td></tr>
						)}
						{users.map(user => (
							<tr key={user.id}>
								<td style={{padding: 8}}>{user.id}</td>
								<td style={{padding: 8}}>{user.email}</td>
							</tr>
						))}
					</tbody>
				</table>
			)}
		</div>
	);
};

export default Users;
