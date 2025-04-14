from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

def get_coordinates(city):
    geo_url = f"https://nominatim.openstreetmap.org/search?city={city}&format=json&limit=1"
    geo_res = requests.get(geo_url, headers={"User-Agent": "weather-app"})
    data = geo_res.json()
    if not data:
        return None, None
    return data[0]["lat"], data[0]["lon"]

def get_weather_description(code):
    mapping = {
        0: "Clear sky ☀️",
        1: "Mainly clear 🌤️",
        2: "Partly cloudy ⛅",
        3: "Overcast ☁️",
        45: "Fog 🌫️",
        48: "Depositing rime fog 🌫️❄️",
        51: "Light drizzle 🌦️",
        61: "Light rain 🌧️",
        71: "Snow fall ❄️",
        80: "Rain showers 🌦️",
        95: "Thunderstorm ⛈️"
    }
    return mapping.get(code, "Unknown")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/weather")
def get_weather():
    city = request.args.get("city", "Sydney")
    print(f"City requested: {city}")

    lat, lon = get_coordinates(city)
    print(f"Coordinates: {lat}, {lon}")

    if not lat or not lon:
        print("Invalid city")
        return jsonify({"error": "City not found"}), 404

    try:
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            f"&current_weather=true"
            f"&daily=temperature_2m_max,temperature_2m_min"
            f"&hourly=relativehumidity_2m,apparent_temperature"
            f"&timezone=auto"
        )
        weather_res = requests.get(weather_url)
        weather_data = weather_res.json()
        print("RAW Open-Meteo response:", weather_data)

        current = weather_data.get("current_weather")
        daily = weather_data.get("daily")
        hourly = weather_data.get("hourly")

        if not current or not daily or not hourly:
            print("Missing expected weather data.")
            return jsonify({"error": "No current weather data available"}), 500

        # Extract closest humidity and apparent temperature using current time
        current_time = current["time"]
        try:
            index = hourly["time"].index(current_time)
            relative_humidity = hourly["relativehumidity_2m"][index]
            apparent_temp = hourly["apparent_temperature"][index]
        except ValueError:
            relative_humidity = "-"
            apparent_temp = current.get("temperature")

        weather_code = current.get("weathercode", -1)
        description = get_weather_description(weather_code)

        return jsonify({
            "city": city,
            "lat": lat,
            "lon": lon,
            "current": {
                **current,
                "relativehumidity_2m": relative_humidity,
                "apparent_temperature": apparent_temp
            },
            "condition": description,
            "daily": daily
        })

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run()
