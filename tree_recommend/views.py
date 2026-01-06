
import requests
from django.shortcuts import render
from .data import load_tree_data
from datetime import datetime
import json
import os


CACHE_FILE = os.path.join(os.path.dirname(__file__), "tree_recommend_cache.json")

def fetch_geocoding(place):
    #  Geoapify
    GEOAPIFY_KEY = os.getenv("GEOAPIFY_API_KEY")
    geo_url = f"https://api.geoapify.com/v1/geocode/search?text={place}&apiKey={GEOAPIFY_KEY}"
    try:
        resp = requests.get(geo_url, timeout=5).json()
        features = resp.get("features", [{}])
        if features and "properties" in features[0]:
            props = features[0]["properties"]
            return props.get("lat"), props.get("lon"), props.get("city") or props.get("town") or props.get("village") or place
    except:
        pass
    
    # Nominatim
    try:
        osm_url = f"https://nominatim.openstreetmap.org/search?format=json&q={place}"
        resp = requests.get(osm_url, headers={'User-Agent': 'GreenCoinApp'}, timeout=5).json()
        if resp:
            return float(resp[0]["lat"]), float(resp[0]["lon"]), place
    except:
        pass

    return None, None, place


def fetch_weather(lat, lon):
    temps = []
    humidity = []

    # OpenWeatherMap
    try:
        OPENWEATHER_KEY = os.getenv("OPENWEATHER_API_KEY")
        url1 = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_KEY}&units=metric"
        resp1 = requests.get(url1, timeout=5).json()
        temps.append(resp1.get("main", {}).get("temp", 0))
        humidity.append(resp1.get("main", {}).get("humidity", 0))
    except:
        pass

    # WeatherAPI
    try:
        WEATHER_KEY = os.getenv("WEATHER_API_KEY")
        url2 = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_KEY}&q={lat},{lon}"
        resp2 = requests.get(url2, timeout=5).json()
        temps.append(resp2.get("current", {}).get("temp_c", 0))
        humidity.append(resp2.get("current", {}).get("humidity", 0))
    except:
        pass

    if temps and humidity:
        return sum(temps)/len(temps), sum(humidity)/len(humidity)
    return 0, 0


def fetch_pollution(lat, lon):
    pm2_5_list = []

    # OpenWeatherMap
    try:
        OPENWEATHER_KEY = os.getenv("OPENWEATHER_API_KEY")
        url1 = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={OPENWEATHER_KEY}"
        resp1 = requests.get(url1, timeout=5).json()
        components = resp1.get("list", [{}])[0].get("components", {})
        pm2_5_list.append(components.get("pm2_5", 0))
    except:
        pass

    # OpenAQ
    try:
        url2 = f"https://api.openaq.org/v2/latest?coordinates={lat},{lon}&radius=10000&limit=1"
        resp2 = requests.get(url2, timeout=5).json()
        measurements = resp2.get("results", [{}])[0].get("measurements", [])
        for m in measurements:
            if m.get("parameter") == "pm25":
                pm2_5_list.append(m.get("value", 0))
    except:
        pass

    if pm2_5_list:
        return sum(pm2_5_list)/len(pm2_5_list)
    return 0


def recommend_trees(request):
    result = None
    tree_data = load_tree_data()

    if request.method == "POST":
        place = request.POST.get("place")

       
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r") as f:
                cache = json.load(f)
            if place in cache:
                return render(request, "tree_recommend/form.html", {"result": cache[place]})
        else:
            cache = {}

        # Geocoding
        lat, lon, city_name = fetch_geocoding(place)
        if lat is None or lon is None:
            result = {"error": "City not found. Please enter a valid place name."}
            return render(request, "tree_recommend/form.html", {"result": result})

        # Weather
        temp, humidity = fetch_weather(lat, lon)

        # Pollution (PM2.5)
        pm2_5 = fetch_pollution(lat, lon)

        # Current Month
        current_month = datetime.now().strftime("%B")

        # Filter JSON data dynamically
        recommended_trees = []
        for item in tree_data:
            if "months" in item and current_month not in item["months"]:
                continue
            if "temp_min" in item and temp < item["temp_min"]:
                continue
            if "temp_max" in item and temp > item["temp_max"]:
                continue
            if "humidity_min" in item and humidity < item["humidity_min"]:
                continue
            if "humidity_max" in item and humidity > item["humidity_max"]:
                continue
            if "aqi_min" in item and pm2_5 < item["aqi_min"]:
                continue
            if "aqi_max" in item and pm2_5 > item["aqi_max"]:
                continue
            recommended_trees.extend(item.get("trees", []))

        recommended_trees = list(set(recommended_trees))

        # CO2 & Trees Calculation (demo values)
        co = pm2_5  
        annual_co2_kg = co * 7.8
        population = 10000
        total_co2 = annual_co2_kg * population
        trees_needed = round(total_co2 / 21)

        result = {
            "city": city_name,
            "aqi": round(pm2_5, 2),
            "co2": round(co, 2),
            "temp": round(temp, 2),
            "humidity": round(humidity, 2),
            "trees_needed": trees_needed,
            "recommended_trees": recommended_trees
        }

        
        cache[place] = result
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f)

    return render(request, "tree_recommend/form.html", {"result": result})
