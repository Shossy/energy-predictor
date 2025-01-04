import React, { useState } from "react";
import axios from "axios";
import { LocalizationProvider } from '@mui/x-date-pickers';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { DatePicker } from "@mui/x-date-pickers/DatePicker";
import { Button } from "@mui/material";

const App: React.FC = () => {
    const [startDate, setStartDate] = useState<Date | null>(null);
    const [endDate, setEndDate] = useState<Date | null>(null);
    const [predictions, setPredictions] = useState<number[]>([]);

    const handlePredict = async () => {
        if (!startDate || !endDate) {
            alert("Please select both start and end dates.");
            return;
        }

        if (startDate > endDate) {
          alert("End date cannot be earlier than Start Date");
          return;
        }

        try {
            const response = await axios.post("http://127.0.0.1:5000/predict", {
                dates: { start: startDate.toISOString(), end: endDate.toISOString() },
            });
            setPredictions(response.data.predictions);
        } catch (error) {
            console.error("Error fetching predictions:", error);
            alert("Failed to fetch predictions.");
        }
    };

    return (
        <div style={{ padding: "2rem" }}>
            <h1>Energy Prediction</h1>
            <div>
            <LocalizationProvider dateAdapter={AdapterDayjs}>
              <DatePicker
                label="Pick a date"
                value={startDate}
                onChange={(newValue) => setStartDate(newValue)}
              />
            </LocalizationProvider>
            <LocalizationProvider dateAdapter={AdapterDayjs}>
              <DatePicker
                label="Pick a date"
                value={endDate}
                onChange={(newValue) => setEndDate(newValue)}
              />
            </LocalizationProvider>
            </div>
            <br></br>
            <Button variant="contained" color="primary" onClick={handlePredict}>
                Predict
            </Button>
            <div>
                <h2>Predictions:</h2>
                {predictions.map((value, index) => (
                    <div key={index}>Day {index + 1}: {value} kWh</div>
                ))}
            </div>
        </div>
    );
};

export default App;
