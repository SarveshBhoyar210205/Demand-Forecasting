from flask import Flask, jsonify, request
import pandas as pd
import joblib
import os
import datetime
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/predict": {"origins": "http://localhost:3000"}})

# Google Drive file links
MODEL_URL = "https://drive.google.com/uc?export=download&id=12v42hELSYSM5NAt10m-qPrvfTw1Qf6VR"
FEATURES_URL = "https://drive.google.com/uc?export=download&id=1griXJTzjdASVfdRXXiUHQU9K9UUnRm_F"

# Local paths
MODEL_PATH = "best_demand_forecast_model.pkl"
FEATURES_PATH = "feature_names.pkl"

# Function to download model if not present
def download_file(url, save_path):
    if not os.path.exists(save_path):
        print(f"Downloading {save_path}...")
        response = requests.get(url, stream=True)
        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        print(f"✅ {save_path} downloaded successfully!")

# Ensure the model and feature names exist
download_file(MODEL_URL, MODEL_PATH)
download_file(FEATURES_URL, FEATURES_PATH)

# Load the model and features
model = joblib.load(MODEL_PATH)
expected_features = joblib.load(FEATURES_PATH)
print("✅ Model and features loaded successfully!")

@app.route('/predict', methods=['GET'])
def predict():
    if model is None:
        return jsonify({"error": "Model not found. Check the download link!"}), 500

    store_id = request.args.get('store_id')
    sku_id = request.args.get('sku_id')
    date_str = request.args.get('date')
    current_stock = request.args.get('current_stock')

    if not store_id or not sku_id or current_stock is None:
        return jsonify({"error": "Please provide store_id, sku_id, and current_stock"}), 400

    try:
        current_stock = int(current_stock)
    except ValueError:
        return jsonify({"error": "Invalid current_stock value. It must be an integer."}), 400

    if not date_str:
        today = datetime.date.today()
        next_week = today + datetime.timedelta(days=7)
        date_str = next_week.strftime('%Y-%m-%d')

    day, month, year = map(int, date_str.split('-'))

    input_data = pd.DataFrame([{"day": day, "month": month, "year": year}])

    for feature in expected_features:
        if feature.startswith("store_"):
            input_data[feature] = 1 if feature == f"store_{store_id}" else 0
        elif feature.startswith("sku_"):
            input_data[feature] = 1 if feature == f"sku_{sku_id}" else 0
        elif feature not in input_data.columns:
            input_data[feature] = 0

    input_data = input_data[expected_features]

    try:
        predicted_sales = model.predict(input_data)[0]
        predicted_sales = round(predicted_sales, 2)

        if current_stock < predicted_sales:
            recommended_restock = round(predicted_sales - current_stock)
        else:
            recommended_restock = "Sufficient stock"

        return jsonify({
            "store_id": store_id,
            "sku_id": sku_id,
            "predicted_sales": predicted_sales,
            "current_stock": current_stock,
            "recommended_restock": recommended_restock
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
