from flask import Flask, request
import time
import pandas as pd
import uuid
from datetime import datetime
import json

import requests

df = pd.DataFrame(columns=["time", "heartrate"])

app = Flask(__name__)

broker = "mqtt-broker"
port = 1883


@app.route("/", methods=["PUT"])
def index():
    if request.json:
        received_date = time.time()
        data_string = request.json["data"]
        data_split = data_string.split(":", 1)

        attribute = data_split[0]
        value = int(data_split[-1])

        if attribute == "heartRate":
            data = {
                "id": str(uuid.uuid4()),
                "value": value,
                "timestamp": datetime.now().isoformat(),
                "topic": "heartrate",
            }
            requests.post("http://analysis-module:5000/data", json=data)

    return ""


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port="3476")
