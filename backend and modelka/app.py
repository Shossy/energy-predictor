from datetime import datetime, timedelta

import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import tensorflow as tf
import joblib
from openmeteo_service import get_weather_data

app = Flask(__name__)
CORS(app)

model_wind = tf.keras.models.load_model("best_lstm_model.keras", safe_mode=False)
model_solar = tf.keras.models.load_model("solar_model.h5", safe_mode=False)

scaler_wind = joblib.load("minmax_scaler_wind.pkl")
scaler_solar = joblib.load("minmax_scaler.pkl")


class Prediction:
    def __init__(self, date, energy):
        self.datetime = date  # No trailing comma
        self.energy = energy  # No trailing comma

    def to_dict(self):
        return {
            "datetime": self.datetime,
            "predicted_energy": self.energy
        }

@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    weather = get_weather_data(data)
    if data['mode'] == 'wind':
        index = weather.index
        columns = weather.columns
        scaled_weather = scaler_wind.transform(weather)
        scaled_weather = pd.DataFrame(scaled_weather)
        scaled_weather.index = index
        scaled_weather.columns = columns
        input_data = create_lag(pd.DataFrame(scaled_weather))
        predictions = model_wind.predict(input_data)
        freq = 'H'
    else:
        index = weather.index
        columns = weather.columns
        scaled_weather = scaler_solar.transform(weather)
        scaled_weather = pd.DataFrame(scaled_weather)
        scaled_weather.index = index
        scaled_weather.columns = columns
        input_data = create_lag(scaled_weather, 8)
        predictions = model_solar.predict(input_data)
        freq = '3H'
    response = create_response(predictions, data['dates'], freq)
    return jsonify(response)

def create_lag(X, time_steps=24):
    X_lag = []
    for i in range(len(X) - time_steps):
        v = X.iloc[i:(i + time_steps)].values
        X_lag.append(v)
    return np.array(X_lag)

def create_response(predictions, dates, freq):
    # Generate hourly intervals
    start = datetime.strptime(dates['start'], '%Y-%m-%dT%H:%M:%S')
    end = datetime.strptime(dates['end'], '%Y-%m-%dT%H:%M:%S')
    datetimes = pd.date_range(start=start, end=end + timedelta(days=1), freq=freq)
    # Convert to list of strings
    datetime_list = datetimes.strftime('%Y-%m-%d %H:%M:%S').tolist()
    response = [Prediction(date, float(energy[0])).to_dict() for date, energy in zip(datetime_list, predictions)]
    return response

if __name__ == "__main__":
    app.run(debug=True)
