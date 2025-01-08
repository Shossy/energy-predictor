from datetime import datetime, timezone, timedelta

import numpy as np
import pytz
import openmeteo_requests
from openmeteo_sdk.Variable import Variable
import pandas as pd


def get_weather_data(data):
    dates = data['dates']
    coords = data['location']
    print(coords)
    timezone_client = data['timezone']
    tz = pytz.timezone(timezone_client)

    start_date = datetime.strptime(dates['start'], '%Y-%m-%dT%H:%M:%S').date()
    end_date = datetime.strptime(dates['end'], '%Y-%m-%dT%H:%M:%S').date()

    gmt_now = datetime.now(tz).date()

    if data['mode'] == 'wind':
        if (gmt_now - end_date).days > 10:
            return wind_data_archive(start_date - timedelta(days=1), end_date, timezone_client, coords)
        elif (gmt_now - start_date - timedelta(days=1)).days > 10 and end_date < gmt_now:
            prev_data = wind_data_archive(start_date - timedelta(days=1), gmt_now - timedelta(days=11), timezone_client,
                                          coords)
            forecast_data = make_wind_forecast(16, 10, timezone_client, coords)
            result = pd.concat([prev_data, forecast_data])
            result = result[result.index < pd.to_datetime(end_date + timedelta(days=1)).tz_localize(tz)]
            result = result[result.index >= pd.to_datetime(start_date - timedelta(days=1)).tz_localize(tz)]
            return result
        else:
            result = make_wind_forecast(16, 10, timezone_client, coords)
            result = result[result.index < pd.to_datetime(end_date + timedelta(days=1)).tz_localize(tz)]
            result = result[result.index >= pd.to_datetime(start_date - timedelta(days=1)).tz_localize(tz)]
            return result
    else:
        if (gmt_now - end_date).days > 10:
            return solar_data_archive(start_date - timedelta(days=1), end_date, timezone_client, coords)
        elif (gmt_now - start_date - timedelta(days=1)).days > 10 and end_date < gmt_now:
            prev_data = solar_data_archive(start_date - timedelta(days=1), gmt_now - timedelta(days=11),
                                           timezone_client, coords)
            forecast_data = make_solar_forecast(16, 10, timezone_client, coords)
            result = pd.concat([prev_data, forecast_data])
            result = result[result.index < pd.to_datetime(end_date + timedelta(days=1)).tz_localize(tz)]
            result = result[result.index >= pd.to_datetime(start_date - timedelta(days=1)).tz_localize(tz)]
            return result
        else:
            result = make_solar_forecast(16, 10, timezone_client, coords)
            result = result[result.index < pd.to_datetime(end_date + timedelta(days=1)).tz_localize(tz)]
            result = result[result.index >= pd.to_datetime(start_date - timedelta(days=1)).tz_localize(tz)]
            return result


def wind_data_archive(start_date, end_date, timezone_client, coords):
    om = openmeteo_requests.Client()
    params = {
        "latitude": coords['latitude'],
        "longitude": coords['longitude'],
        "start_date": start_date,
        "end_date": end_date,
        "timezone": timezone_client,
        "hourly": ["temperature_2m", "wind_speed_100m", "relative_humidity_2m", "dewpoint_2m", "wind_direction_100m",
                   "wind_gusts_10m"],
    }

    responses = om.weather_api("https://historical-forecast-api.open-meteo.com/v1/forecast", params=params)
    return process_wind_response(responses, timezone_client)


def make_wind_forecast(days_into_future, days_into_past, timezone_client, coords):
    om = openmeteo_requests.Client()
    params = {
        "latitude": coords['latitude'],
        "longitude": coords['longitude'],
        "past_days": days_into_past,
        "forecast_days": days_into_future,
        "timezone": timezone_client,
        "hourly": ["temperature_2m", "wind_speed_100m", "relative_humidity_2m", "dewpoint_2m", "wind_direction_100m",
                   "wind_gusts_10m"],
    }

    responses = om.weather_api("https://api.open-meteo.com/v1/forecast", params=params)
    return process_wind_response(responses, timezone_client)


def solar_data_archive(start_date, end_date, timezone_client, coords):
    om = openmeteo_requests.Client()
    params = {
        "latitude": coords['latitude'],
        "longitude": coords['longitude'],
        "start_date": start_date,
        "end_date": end_date,
        "timezone": timezone_client,
        "hourly": ["temperature_2m", "wind_speed_100m", "relative_humidity_2m", "visibility", "cloud_cover"],
        "temperature_unit": "fahrenheit"
    }

    responses = om.weather_api("https://historical-forecast-api.open-meteo.com/v1/forecast", params=params)
    return process_solar_response(responses, timezone_client, coords['latitude'])


def make_solar_forecast(days_into_future, days_into_past, timezone_client, coords):
    om = openmeteo_requests.Client()
    params = {
        "latitude": coords['latitude'],
        "longitude": coords['longitude'],
        "past_days": days_into_past,
        "forecast_days": days_into_future,
        "timezone": timezone_client,
        "hourly": ["temperature_2m", "wind_speed_100m", "relative_humidity_2m", "visibility", "cloud_cover"],
        "temperature_unit": "fahrenheit"
    }

    responses = om.weather_api("https://api.open-meteo.com/v1/forecast", params=params)
    return process_solar_response(responses, timezone_client, coords['latitude'])


def process_wind_response(responses, timezone_client):
    response = responses[0]

    hourly = response.Hourly()

    hourly_variables = list(map(lambda i: hourly.Variables(i), range(0, hourly.VariablesLength())))

    hourly_temperature_2m = next(
        filter(lambda x: x.Variable() == Variable.temperature and x.Altitude() == 2, hourly_variables)).ValuesAsNumpy()
    hourly_wind_speed_100m = next(
        filter(lambda x: x.Variable() == Variable.wind_speed and x.Altitude() == 100, hourly_variables)).ValuesAsNumpy()

    hourly_relative_humidity_2m = next(
        filter(lambda x: x.Variable() == Variable.relative_humidity, hourly_variables)).ValuesAsNumpy()
    hourly_dew_point_2m = next(filter(lambda x: x.Variable() == Variable.dew_point, hourly_variables)).ValuesAsNumpy()
    hourly_wind_direction_100m = next(
        filter(lambda x: x.Variable() == Variable.wind_direction and x.Altitude() == 100,
               hourly_variables)).ValuesAsNumpy()
    hourly_wind_gusts_10m = next(
        filter(lambda x: x.Variable() == Variable.wind_gusts and x.Altitude() == 10, hourly_variables)).ValuesAsNumpy()

    hourly_data = {"Time": pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s"),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s"),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left"
    ), "temperature_2m": hourly_temperature_2m, "relativehumidity_2m": hourly_relative_humidity_2m,
        "dewpoint_2m": hourly_dew_point_2m, "windspeed_100m": hourly_wind_speed_100m,
        "winddirection_100m": hourly_wind_direction_100m, "windgusts_10m": hourly_wind_gusts_10m}

    hourly_dataframe_pd = pd.DataFrame(data=hourly_data)

    hourly_dataframe_pd['Time'] = pd.to_datetime(hourly_dataframe_pd['Time'])

    tz = pytz.timezone(timezone_client)
    hourly_dataframe_pd['Time'] = hourly_dataframe_pd['Time'].dt.tz_localize('UTC').dt.tz_convert(tz)
    hourly_dataframe_pd.set_index('Time', inplace=True)
    return hourly_dataframe_pd


def process_solar_response(responses, timezone_client, latitude):
    response = responses[0]

    hourly = response.Hourly()

    hourly_variables = list(map(lambda i: hourly.Variables(i), range(0, hourly.VariablesLength())))

    hourly_temperature_2m = next(
        filter(lambda x: x.Variable() == Variable.temperature and x.Altitude() == 2, hourly_variables)).ValuesAsNumpy()
    hourly_wind_speed_100m = next(
        filter(lambda x: x.Variable() == Variable.wind_speed and x.Altitude() == 100, hourly_variables)).ValuesAsNumpy()

    hourly_relative_humidity_2m = next(
        filter(lambda x: x.Variable() == Variable.relative_humidity, hourly_variables)).ValuesAsNumpy()
    hourly_visibility = next(filter(lambda x: x.Variable() == Variable.visibility, hourly_variables)).ValuesAsNumpy()
    hourly_cloud_cover_total = next(
        filter(lambda x: x.Variable() == Variable.cloud_cover, hourly_variables)).ValuesAsNumpy()

    hourly_data = {"Time": pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s"),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s"),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left"
    ), "Average Temperature (Day)": hourly_temperature_2m, "Relative Humidity": hourly_relative_humidity_2m,
        "Average Wind Speed (Period)": hourly_wind_speed_100m,
        "Visibility": hourly_visibility, "Sky Cover": hourly_cloud_cover_total}

    hourly_dataframe_pd = pd.DataFrame(data=hourly_data)

    hourly_dataframe_pd['Time'] = pd.to_datetime(hourly_dataframe_pd['Time'])

    tz = pytz.timezone(timezone_client)
    hourly_dataframe_pd['Time'] = hourly_dataframe_pd['Time'].dt.tz_localize('UTC').dt.tz_convert(tz)
    hourly_dataframe_pd.set_index('Time', inplace=True)

    group_size = 3
    hourly_dataframe_pd = (
        hourly_dataframe_pd.groupby(np.arange(len(hourly_dataframe_pd)) // group_size)
        .mean()
        .set_index(hourly_dataframe_pd.index[::group_size])  # Set index to the first timestamp of each group
    )

    print(hourly_dataframe_pd)
    hourly_dataframe_pd['Sky Cover'] = pd.cut(hourly_dataframe_pd['Sky Cover'], bins=4, labels=[1, 2, 3, 4])
    hourly_dataframe_pd['Visibility'] = pd.cut(hourly_dataframe_pd['Visibility'], bins=10, labels=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

    hourly_dataframe_pd = update_in_chunks(hourly_dataframe_pd, 'Average Temperature (Day)', 8)

    noon_distance = calculate_distance_to_solar_noon_with_datetime(hourly_dataframe_pd.index, latitude)
    hourly_dataframe_pd['Distance to Solar Noon'] = noon_distance

    hourly_dataframe_pd = hourly_dataframe_pd[[
        'Distance to Solar Noon', 'Average Temperature (Day)',
        'Average Wind Speed (Period)', 'Relative Humidity',
        'Sky Cover', 'Visibility'
    ]]
    return hourly_dataframe_pd


def update_in_chunks(df, column, chunk_size):
    # Loop through the DataFrame in chunks of the specified size
    for i in range(0, len(df), chunk_size):
        # Get the subset of the dataframe
        chunk = df.iloc[i:i + chunk_size]

        # Calculate the mean of the specified column for this chunk
        mean_value = chunk[column].mean()

        # Set all values in the chunk to the calculated mean
        df.loc[chunk.index, column] = mean_value

    return df


def calculate_distance_to_solar_noon_with_datetime(dates, longitude):
    """
    Recalculate the distance to solar noon for a DataFrame with a datetime index.

    Args:
        df (pd.DataFrame): Input DataFrame with a datetime index.
        longitude (float): Longitude of the location (degrees, positive for East, negative for West).

    Returns:
        pd.DataFrame: Updated DataFrame with recalculated 'Distance to Solar Noon'.
    """

    def calculate_eot(day_of_year):
        """Calculate the Equation of Time (EOT) in minutes."""
        B = 2 * np.pi * (day_of_year - 81) / 365
        eot = 7.5 * np.sin(B) - 9.87 * np.sin(2 * B) - 1.914 * np.cos(B) + 0.020 * np.cos(2 * B)
        return eot

    def calculate_solar_noon(eot, longitude):
        """Calculate solar noon local time in hours (24-hour format)."""
        solar_noon = 12 + (longitude / 15) - (eot / 60)  # Convert EOT to hours
        return solar_noon

    def calculate_distance(hour, solar_noon):
        """Calculate normalized distance to solar noon."""
        hour_angle = 15 * (hour - solar_noon)
        return abs(hour_angle) / 180  # Normalize to [0, 1]

    distances = []
    for timestamp in dates:
        # Extract day of year and hour from the datetime index
        day_of_year = timestamp.timetuple().tm_yday
        hour = timestamp.hour + timestamp.minute / 60  # Convert to decimal hours

        # Calculate EOT and solar noon
        eot = calculate_eot(day_of_year)
        solar_noon = calculate_solar_noon(eot, longitude)

        # Calculate normalized distance to solar noon
        distance = calculate_distance(hour, solar_noon)
        distances.append(distance)

    # Add the recalculated distance to the DataFrame
    return distances
