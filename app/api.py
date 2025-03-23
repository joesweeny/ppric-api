from flask import Flask, request, jsonify
import os
from pymongo import MongoClient
import json
from openai import OpenAI
from flask_cors import CORS
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
import pickle


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})


mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
db = client.get_default_database()
collection = db["fingerprints"]


MODEL_PATH = "rf_regressor_model.pkl"
with open(MODEL_PATH, 'rb') as f:
    rf_model = pickle.load(f)


openai_client = OpenAI(
    api_key=os.getenv("GROK_API_KEY"),
    base_url="https://api.x.ai/v1"
)


FEATURE_COLUMNS = [
    "headless", "cookiesEnabled", "pageLoadTime",
    "event_mousemove", "event_keydown", "event_scroll", "event_copy",
    "ip_is_datacenter", "screen_width", "screen_height",
    "screen_devicePixelRatio", "viewport_innerWidth", "viewport_innerHeight",
    "battery_level", "battery_charging", "battery_chargingTime",
    "hardware_cpuCores", "hardware_deviceMemory"
]


le_dict = {}


for col in ["headless", "cookiesEnabled", "event_mousemove", "event_keydown",
            "event_scroll", "event_copy", "ip_is_datacenter", "battery_charging"]:
    le_dict[col] = LabelEncoder()
    le_dict[col].fit([0, 1])


@app.route('/limit-increase', methods=['POST'])
def limit_increase():
    try:
        data = request.get_json()
        if not data or "userId" not in data:
            return jsonify({"status": "error", "message": "userId is required"}), 400

        user_id = data["userId"]
        user_records = list(collection.find({"userId": user_id}))
        if not user_records:
            return jsonify({"status": "error", "message": "No data found for this user"}), 404


        records_data = []
        for record in user_records:
            flat_record = {
                "headless": record["headless"],
                "cookiesEnabled": record["cookiesEnabled"],
                "pageLoadTime": record["pageLoadTime"],
                "event_mousemove": record["events"]["mousemove"],
                "event_keydown": record["events"]["keydown"],
                "event_scroll": record["events"]["scroll"],
                "event_copy": record["events"]["copy"],
                "ip_is_datacenter": record["ipDetails"]["is_datacenter"],
                "screen_width": record["screen"]["width"],
                "screen_height": record["screen"]["height"],
                "screen_devicePixelRatio": record["screen"]["devicePixelRatio"],
                "viewport_innerWidth": record["viewport"]["innerWidth"],
                "viewport_innerHeight": record["viewport"]["innerHeight"],
                "battery_level": record["battery"]["level"],
                "battery_charging": record["battery"]["charging"],
                "battery_chargingTime": record["battery"]["chargingTime"],
                "hardware_cpuCores": record["hardware"]["cpuCores"],
                "hardware_deviceMemory": record["hardware"]["deviceMemory"]
            }
            records_data.append(flat_record)


        df = pd.DataFrame(records_data)
        for col in le_dict.keys():
            df[col] = le_dict[col].transform(df[col])


        scores = rf_model.predict(df[FEATURE_COLUMNS])
        avg_score = int(np.mean(scores))


        user_data_str = "\n".join([str(record) for record in user_records])


        prompt = f"""
        You are an expert in spotting gambling patterns, talking to your customer services colleagues. 
        I’ve already calculated a score for this user: {avg_score} (0 means a sharp, pro bettor; 100 means a casual, everyday punter).
        Based on this score and the user data below, explain in a simple, human-friendly way why this user got this score. 
        Keep it short, clear, and easy to read, avoiding overly techy terms or long lists.
        Your explanation will help a customer service rep decide next steps for this user.

        Sharp bettors (closer to 0) tend to:
        - Hide their tracks (e.g., headless browsers, no cookies)
        - Load pages super fast (under 200ms)
        - Use powerful gear (lots of CPU cores and memory)
        - Barely interact (few clicks or scrolls)
        - Stick to the same setup consistently
        - Use datacenter IPs (like pros hiding their location)

        Casual punters (closer to 100) tend to:
        - Browse normally (no hiding, cookies on)
        - Load pages at average speed (over 300ms)
        - Use regular home computers
        - Click and scroll a lot
        - Change setups often
        - Use home internet

        User Data:
        {user_data_str}

        Give your answer as a reason that is no longer than 4 to 5 sentences.
        """

        response = openai_client.chat.completions.create(
            model="grok-2",
            messages=[
                {"role": "system", "content": "You are Grok, a gambling behavior analyst."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7,
        )

        return jsonify({
            "status": "success",
            "data": {
                "score": avg_score,
                "reason": response.choices[0].message.content
            }
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": f"Error processing limit increase: {str(e)}"}), 500


@app.route('/user-activity', methods=['POST'])
def get_user_activity():
    try:
        data = request.get_json()
        if not data or "userId" not in data:
            return jsonify({"status": "error", "message": "userId is required"}), 400

        user_id = data["userId"]
        user_records = list(collection.find({"userId": user_id}))

        if not user_records:
            return jsonify({"status": "success", "data": []}), 200

        activity_list = []
        for record in user_records:
            record.pop('_id', None)
            activity_list.append(record)

        return jsonify({
            "status": "success",
            "data": activity_list
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": f"Error fetching user activity: {str(e)}"}), 500


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
