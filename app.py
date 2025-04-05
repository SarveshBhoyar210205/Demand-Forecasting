from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)

# ✅ Enable CORS for frontend access
CORS(app, resources={r"/*": {"origins": "*"}})

# ✅ Google APIs
GOOGLE_MAPS_API_KEY = "AIzaSyCrTX-gRHbf-ZQ_k5Ji61IqrQENwJ7RUfA"
ROUTES_API_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"
AIR_QUALITY_API_URL = "https://airquality.googleapis.com/v1/currentConditions:lookup"

### 🚀 1️⃣ GET ALTERNATIVE ROUTES
@app.route("/get-alternative-routes", methods=["POST"])
def get_alternative_routes():
    data = request.json
    origin = data.get("origin")
    destination = data.get("destination")
    
    if not origin or not destination:
        return jsonify({"success": False, "error": "Missing origin or destination"}), 400

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
        "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.polyline,routes.legs"
    }

    body = {
        "origin": {
            "location": {
                "latLng": {
                    "latitude": origin["latitude"],
                    "longitude": origin["longitude"]
                }
            }
        },
        "destination": {
            "location": {
                "latLng": {
                    "latitude": destination["latitude"],
                    "longitude": destination["longitude"]
                }
            }
        },
        "travelMode": "DRIVE",
        "computeAlternativeRoutes": True,
        "routingPreference": "TRAFFIC_AWARE_OPTIMAL"
    }

    try:
        response = requests.post(ROUTES_API_URL, json=body, headers=headers)
        
        # Debugging: Log the API response
        print("API Response: ", response.json())  # Print the entire response to check

        if response.status_code == 200:
            routes = response.json().get("routes", [])
            if routes:
                return jsonify({"success": True, "routes": routes})
            else:
                return jsonify({"success": False, "error": "No valid routes found"}), 404
        else:
            return jsonify({"success": False, "error": response.text}), response.status_code

    except Exception as e:
        print("Error occurred while fetching routes: ", e)  # Log the error
        return jsonify({"success": False, "error": str(e)}), 500


### 🌍 2️⃣ GET AIR QUALITY FROM GOOGLE API
@app.route("/get-air-quality", methods=["POST"])
def get_air_quality():
    data = request.json
    route_points = data.get("route_points")

    if not route_points:
        return jsonify({"success": False, "error": "No route points provided"}), 400

    aqi_values = []

    for point in route_points:
        lat, lng = point["lat"], point["lng"]
        
        # ✅ Fetch AQI using Google Air Quality API
        try:
            response = requests.get(f"{AIR_QUALITY_API_URL}?key={GOOGLE_MAPS_API_KEY}&location.latitude={lat}&location.longitude={lng}")
            
            # Debugging: Log the API response
            print("Air Quality API Response: ", response.json())  # Log AQI response
            
            if response.status_code == 200:
                aqi_data = response.json()
                if "indexes" in aqi_data and len(aqi_data["indexes"]) > 0:
                    aqi = aqi_data["indexes"][0]["aqi"]
                    aqi_values.append(aqi)
        except Exception as e:
            print(f"Error fetching AQI for point {lat}, {lng}: {e}")
            continue

    if aqi_values:
        avg_aqi = sum(aqi_values) / len(aqi_values)
        return jsonify({"success": True, "average_aqi": avg_aqi, "aqi_values": aqi_values})
    else:
        return jsonify({"success": False, "error": "No AQI data found"}), 404


### ✅ ALLOW CORS FOR OPTIONS REQUESTS
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response


if __name__ == "__main__":
    app.run(debug=True)
