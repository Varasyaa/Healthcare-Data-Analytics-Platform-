// src/Dashboard.js
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Bar, Line } from 'react-chartjs-2';
import { useHistory } from 'react-router-dom';

function Dashboard() {
  const history = useHistory();
  const [visitsData, setVisitsData] = useState([]);
  const [avgLab, setAvgLab] = useState(null);
  const token = localStorage.getItem('token');

  useEffect(() => {
    if (!token) {
      history.push('/');
    }
    // Fetch visits per patient analytics
    axios.get('http://localhost:5000/api/analytics/visits-per-patient', {
      headers: { 'Authorization': `Bearer ${token}` }
    }).then(res => {
      setVisitsData(res.data);
    }).catch(err => console.error(err));

    // Fetch average lab result for a specific test type (e.g., "Glucose")
    axios.get('http://localhost:5000/api/analytics/average-lab-result/Glucose', {
      headers: { 'Authorization': `Bearer ${token}` }
    }).then(res => {
      setAvgLab(res.data.average_result);
    }).catch(err => console.error(err));
  }, [token, history]);

  // Prepare data for visits chart
  const visitsChartData = {
    labels: visitsData.map(d => d.patient),
    datasets: [{
      label: 'Number of Visits',
      data: visitsData.map(d => d.visit_count),
      backgroundColor: 'rgba(75,192,192,0.6)'
    }]
  };

  return (
    <div>
      <h2>Healthcare Analytics Dashboard</h2>
      <div>
        <h3>Visits per Patient</h3>
        <Bar data={visitsChartData} />
      </div>
      <div>
        <h3>Average Glucose Level</h3>
        <Line data={{
          labels: ['Average'],
          datasets: [{
            label: 'Glucose',
            data: [avgLab],
            backgroundColor: 'rgba(255,99,132,0.6)'
          }]
        }} />
      </div>
    </div>
  );
}

export default Dashboard;
