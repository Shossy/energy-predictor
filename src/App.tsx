import React, { useState } from "react";
import axios from "axios";
import { LocalizationProvider } from '@mui/x-date-pickers';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { DatePicker } from "@mui/x-date-pickers/DatePicker";
import { Button, TextField } from "@mui/material";
import dayjs, { Dayjs } from "dayjs";
import { PredictionDdata } from "./prediction.model";
import EnergyPredictionGraph from "./Chart";

const App: React.FC = () => {
    const [startDate, setStartDate] = useState<Dayjs | null>(null);
    const [endDate, setEndDate] = useState<Dayjs | null>(null);
    const [latitude, setLatitude] = useState<string>("");
    const [longitude, setLongitude] = useState<string>("");
    const [predictions, setPredictions] = useState<PredictionDdata[]>([]);

    const handlePredict = async () => {
        if (!startDate || !endDate) {
            alert("Please select both start and end dates.");
            return;
        }

        if (!latitude || !longitude) {
            alert("Please enter both latitude and longitude.");
            return;
        }

        const lat = parseFloat(latitude);
        const lon = parseFloat(longitude);

        if (isNaN(lat) || isNaN(lon)) {
            alert("Latitude and Longitude must be numbers.");
            return;
        }

        if (lat < -90 || lat > 90) {
            alert("Latitude must be between -90 and 90.");
            return;
        }

        if (lon < -180 || lon > 180) {
            alert("Longitude must be between -180 and 180.");
            return;
        }

        if (startDate > endDate) {
            alert("End date cannot be earlier than Start Date");
            return;
        }

        const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        const startDateFormatted = dayjs(startDate).format("YYYY-MM-DDTHH:mm:ss");
        const endDateFormatted = dayjs(endDate).format("YYYY-MM-DDTHH:mm:ss");

        try {
            const response = await axios.post("http://127.0.0.1:5000/predict", {
                dates: { start: startDateFormatted, end: endDateFormatted },
                location: { latitude: lat, longitude: lon },
                mode: 'solar',
                timezone,
            });
            setPredictions(response.data);
            console.log(predictions);
        } catch (error) {
            console.error("Error fetching predictions:", error);
            alert("Failed to fetch predictions.");
        }
    };

    const totalEnergy = predictions.reduce((sum, prediction) => sum + prediction.predicted_energy, 0);

    const maxEndDate = dayjs().add(15, "days");

    const exportToCSV = () => {
      if (predictions.length === 0) {
          alert("No predictions available to export.");
          return;
      }

      // Convert predictions to CSV format
      const headers = ["Datetime", "Predicted Energy (kWh)"];
      const csvRows = [
          headers.join(","), // Header row
          ...predictions.map(prediction => `${prediction.datetime},${prediction.predicted_energy}`), // Data rows
      ];
      const csvContent = csvRows.join("\n");

      // Create a Blob and download link
      const blob = new Blob([csvContent], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "predictions.csv";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
  };

    return (
        <div style={{ padding: "2rem" }}>
            <h1>Energy Prediction</h1>
            <div>
                <LocalizationProvider dateAdapter={AdapterDayjs}>
                    <DatePicker
                        label="Start Date"
                        value={startDate}
                        onChange={(newValue) => setStartDate(newValue)}
                        maxDate={maxEndDate}
                    />
                </LocalizationProvider>
                <LocalizationProvider dateAdapter={AdapterDayjs}>
                    <DatePicker
                        label="End Date"
                        value={endDate}
                        onChange={(newValue) => setEndDate(newValue)}
                        maxDate={maxEndDate}
                    />
                </LocalizationProvider>
            </div>
            <br />
            <div>
                <TextField
                    label="Latitude"
                    variant="outlined"
                    value={latitude}
                    onChange={(e) => setLatitude(e.target.value)}
                    
                    style={{ marginRight: "1rem" }}
                />
                <TextField
                    label="Longitude"
                    variant="outlined"
                    value={longitude}
                    onChange={(e) => setLongitude(e.target.value)}
                    
                />
            </div>
            <br />
            <Button variant="contained" color="primary" style={{ marginRight: "1rem" }} onClick={handlePredict}>
                Predict
            </Button>
            <Button variant="contained" color="secondary" onClick={exportToCSV}>
                Export to CSV
            </Button>
            <div>
                <h2>Total energy outcome:</h2>
                <div>{totalEnergy} mWh</div>
            </div>
            {predictions.length > 0 ? <EnergyPredictionGraph data={predictions} /> : ''}
        </div>
    );
};

export default App;
