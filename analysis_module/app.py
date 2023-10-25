from flask import Flask, request
from flask_cors import CORS
import json
from modality import Modality
from producer import Producer
from datetime import datetime, timedelta
from further_handlers import handle_expression, find_spikes
import pandas as pd
import sched, time
import requests
import time
import logging

log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)

ANALYSIS_INTERVAL = 0.1  # seconds
ROBOT_CONTROLLER_URL = "http://robot-controller:5000"
LINKEDIN_ROUTE = "http://linkedin-scraping:5000/linkedInScore"
EXPRESSION_ANALYZER_BASE_URL = "http://expression-processor:5000"

USE_LINKEDIN = False # Ob das Tool LinkedIn nutzen soll für die Initialisierung oder nicht

PRODUCERS = [
    Producer(
        "pupil",
        analysis_interval=0.5,
        threshold=0.001,
        handler="_handle_trend",
        output_modalities={"speed": 1.0, "smoothness": 1.0, "rotation": 1.0},
    ),
    Producer(
        "operator/distance",
        analysis_interval=1,
        threshold=5,
        handler="_handle_trend",
        output_modalities={"speed": 1.2, "proxemics": 1.2},
    ),
    Producer(
        "expression",
        analysis_interval=3,
        threshold=-2,
        handler=handle_expression,
        output_modalities={"episodic_behaviour": 1.0},
    ),
    Producer(
        "heartrate",
        analysis_interval=10,
        threshold=0.1,
        handler=find_spikes,
        output_modalities={
            "speed": -1.0,
            "smoothness": -1.0,
            "rotation": -1.0,
        },  # negative weight to reverse slope analysis
    ),
    Producer(
        "blinks",
        analysis_interval=300,
        threshold=0.1,
        handler="_handle_trend",
        output_modalities={
            "episodic_behaviour": -1.0,
            "rotation": -1.0,
        },  # negative weight to reverse slope analysis
    ),
]
PRODUCER_MAP = {producer.subscription_topic: producer for producer in PRODUCERS}

MODALITIES = [
    Modality(
        "speed",
        threshold=0.3,
        base_url=ROBOT_CONTROLLER_URL,
        increase_path="/increase_speed",
        decrease_path="/decrease_speed",
        cooldown_duration=0.5,
    ),
    Modality(
        "proxemics",
        threshold=0.2,
        base_url=ROBOT_CONTROLLER_URL,
        increase_path="/increase_proxemics",
        decrease_path="/decrease_proxemics",
        cooldown_duration=0.5,
    ),
    Modality(
        "smoothness",
        threshold=0.1,
        base_url=ROBOT_CONTROLLER_URL,
        increase_path="/add_smoothness",
        decrease_path="/remove_smoothness",
        cooldown_duration=10,
    ),
    Modality(
        "rotation",
        threshold=0.1,
        base_url=ROBOT_CONTROLLER_URL,
        increase_path="/add_rotations",
        decrease_path="/remove_rotations",
        cooldown_duration=10,
    ),
    Modality(
        "episodic_behaviour",
        threshold=0.3,
        base_url=ROBOT_CONTROLLER_URL,
        increase_path="/episodic_behaviour",
        cooldown_duration=300,
    ),
]
MODALITIES_MAP = {modality.name: modality for modality in MODALITIES}

df = pd.DataFrame(
    columns=["output_modality", "value"], index=pd.DatetimeIndex(name="time", data=[])
)
last_analysed_data = {}

# Default start values to be used with experience
PROXEMICS_MULTIPLIER = (
    2.3  # results in: 1, 1, 2, 3, 4 # TODO have something like 3,4,5,5,5
)
SPEED_MULTIPLIER = 2.5  # results in: 2, 3, 5, 7, 9
SMOOTHNESS_THRESHOLD = 3  # TODO handle that only smoothness or rotation is set
ROTATION_THRESHOLD = 2

app = Flask(__name__)
CORS(app)
analysis_cooldown = datetime.now() + timedelta(seconds=ANALYSIS_INTERVAL)


def get_influences():
    modalities = {modality.name: {} for modality in MODALITIES}
    for producer in PRODUCERS:
        for modality, value in producer._modalities.items():
            if modality in modalities:
                modalities[modality][producer.subscription_topic] = value
    return modalities


def analyse_signals():
    modalities = {modality.name: 0 for modality in MODALITIES}
    analysed_data = {producer.subscription_topic: {} for producer in PRODUCERS}
    for producer in PRODUCERS:
        singleOutputs = producer.handle()
        analysed_data[producer.subscription_topic] = producer._data.to_json()
        for modality, value in singleOutputs.items():
            if modality in modalities:
                modalities[modality] += value

    print(modalities, flush=True)

    publish_data = False
    for modality_name, value in modalities.items():
        modality = MODALITIES_MAP.get(modality_name, None)
        if not modality:
            continue

        if value > modality.threshold:
            publish_data = True
            modality.increase()
        elif value < -modality.threshold:
            publish_data = True
            modality.decrease()
        else:
            modality.neutral()

    if publish_data:
        global last_analysed_data
        last_analysed_data = analysed_data


def get_linkedIn_estimate(operator: str):
    response = requests.get(LINKEDIN_ROUTE, json={"operator": operator})
    print(response.json())
    return response.json()["score"]


def post_bootstrapped_params(params: dict):
    requests.post(ROBOT_CONTROLLER_URL + "/initialize_robot_params", json=params)


def calculate_params(experience: int):
    if experience == 0:
        raise Exception("Operator did not receive a value from LinkedIn")
    params = {
        "speed": round(SPEED_MULTIPLIER * experience),
        "proxemics": round(PROXEMICS_MULTIPLIER * experience),
        "smoothness": experience > SMOOTHNESS_THRESHOLD,
        "rotation": experience > ROTATION_THRESHOLD,
    }
    return params


def init_params_no_linkedIn():
    # Wenn LinkedIn Komponente nicht genutzt wird, werden diese Standardwerte genutzt
    params = {
        "speed": 5,
        "proxemics": 5,
        "smoothness": 5,
    }
    return params


def bootstrap_parameters():
    if USE_LINKEDIN:
        while True:
            time.sleep(1)
            try:
                response = requests.get(EXPRESSION_ANALYZER_BASE_URL + "/operator_details")
                if response.status_code == 201:
                    res = response.json()
                    gender = res.get("gender", None)
                    race = res.get("race", None)
                    age = res.get("age", None)
                    break
            except Exception as e:
                print(e)

        operator = "kayerikjenss"  # TODO get operator name from facial anaylsis module
        print(gender, age, race, flush=True)
        experience = get_linkedIn_estimate(operator)
        print(experience, flush=True)
        params = calculate_params(experience)
    else: 
        params = init_params_no_linkedIn()
    post_bootstrapped_params(params)


def _set_cooldown():
    global analysis_cooldown
    now = datetime.now()
    analysis_cooldown = now + timedelta(seconds=ANALYSIS_INTERVAL)


@app.route("/data", methods=["GET", "POST"])
def data():
    if request.method == "GET":
        global last_analysed_data
        last_analysed_data["influences"] = get_influences()
        print(last_analysed_data, flush=True)
        return last_analysed_data

    if request.json:
        data = request.json
        producer = PRODUCER_MAP.get(data["topic"], None)
        if producer:
            # append data to producer df and handle the data
            del data["topic"]
            producer.add_data(data)
            # value = producer.handle(data)

            # # append handled data to global df
            # global df
            # df = pd.concat([df, value]) if df is not None else value

            global analysis_cooldown
            if analysis_cooldown < datetime.now():
                _set_cooldown()
                analyse_signals()
                return {
                    "response": "Data received and handled. Analysis performed.",
                }, 202

            return {
                "response": "Data received and handled.",
            }, 200
    return {"response": "Could not associate the incoming data with any producer."}


@app.route("/producers", methods=["GET", "POST"])
def producers():
    if request.method == "GET":
        return {
            "producers": [
                {
                    "subscription_topic": p.subscription_topic,
                    "analysis_interval": p._analysis_interval,
                    "threshold": p._threshold,
                    "output_modalities": p._modalities,
                }
                for p in PRODUCERS
            ]
        }
    elif request.method == "POST":
        data = request.json
        subscription_topic = data["subscription_topic"]
        producer = PRODUCER_MAP.get(subscription_topic, None)
        if producer:
            # only update the values that are in the request
            if "analysis_interval" in data:
                producer._analysis_interval = data["analysis_interval"]
            if "threshold" in data:
                producer._threshold = data["threshold"]
            if "output_modalities" in data:
                producer._modalities = data["output_modalities"]
            return {"response": "Producer updated."}, 200
        else:
            return {"response": "Producer not found."}, 404


@app.route("/modalities", methods=["GET", "POST"])
def modalities():
    if request.method == "GET":
        return {
            "modalities": [
                {
                    "name": m.name,
                    "threshold": m.threshold,
                    "cooldown_duration": m.cooldown_duration,
                }
                for m in MODALITIES
            ]
        }
    elif request.method == "POST":
        data = request.json
        name = data["name"]
        modality = MODALITIES_MAP.get(name, None)
        if modality:
            # only update the values that are in the request
            if "threshold" in data:
                modality.threshold = data["threshold"]
            if "cooldown_duration" in data:
                modality.cooldown_duration = data["cooldown_duration"]
            return {"response": "Modality updated."}, 200
        else:
            return {"response": "Modality not found."}, 404


if __name__ == "__main__":
    bootstrap_parameters()
    app.run(debug=True, host="0.0.0.0", port="5000")
