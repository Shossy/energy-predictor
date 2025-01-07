import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { PredictionDdata } from './prediction.model';

// Register required Chart.js components
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

interface Props {
  data: PredictionDdata[];
}

const EnergyPredictionGraph: React.FC<Props> = ({ data }) => {
  const chartData = {
    labels: data.map((point) => point.datetime),
    datasets: [
      {
        label: 'Predicted Energy (mWh)',
        data: data.map((point) => point.predicted_energy),
        borderColor: 'rgba(75, 192, 192, 1)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        tension: 0.3, // Smooth curves
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      tooltip: {
        enabled: true,
      },
    },
    scales: {
      x: {
        type: 'category', // Use category scale
        title: {
          display: true,
          text: 'Datetime',
        },
      },
      y: {
        title: {
          display: true,
          text: 'Energy (kWh)',
        },
      },
    },
  };

  return (
    <div>
      <h2>Energy Predictions</h2>
      <Line data={chartData} options={options} />
    </div>
  );
};

export default EnergyPredictionGraph;
