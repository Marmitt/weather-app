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

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/weather")
def get_weather():
    city = request.args.get("city", "Sydney")
    lat, lon = get_coordinates(city)
    if not lat or not lon:
        return jsonify({"error": "City not found"}), 404

    weather_url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        f"&current_weather=true&daily=temperature_2m_max,temperature_2m_min&timezone=auto"
    )
    weather_res = requests.get(weather_url)
    weather_data = weather_res.json()

    return jsonify({
        "city": city,
        "lat": lat,
        "lon": lon,
        "current": weather_data.get("current_weather"),
        "daily": weather_data.get("daily")
    })

if __name__ == "__main__":
    app.run(debug=True)
