from flask import Flask, request
import json
from modality import Modality
from producer import Producer
from datetime import datetime, timedelta
from further_handlers import handle_expression
import pandas as pd
import sched, time
import requests
import time

ANALYSIS_INTERVAL = 10  # seconds
ROBOT_CONTROLLER_URL = "http://robot-controller:5000"
LINKEDIN_ROUTE = "http://linkedin-scraping:5000/linkedInScore"
EXPRESSION_ANALYZER_BASE_URL = "http://expression-processor:5000"

PRODUCERS = [
    Producer(
        "pupil",
        analysis_interval=0.5,
        threshold=0.001,
        handler="_handle_trend",
        output_modalities=["speed", "smoothness", "rotation"],
        weight=1.0,
    ),
    Producer(
        "operator/distance",
        analysis_interval=0.5,
        threshold=0.001,
        handler="_handle_trend",
        output_modalities=["speed", "proxemics"],
        weight=1.0,
    ),
    Producer(
        "expression",
        analysis_interval=3,
        threshold=-2,
        handler=handle_expression,
        output_modalities=["episodic_behaviour"],
        weight=1.0,
    ),
    Producer(
        "heartrate",
        analysis_interval=60,
        threshold=0.1,
        handler="_handle_trend",
        output_modalities=["speed", "smoothness", "rotation"],
        weight=1.0,
    ),
    Producer(
        "blinks",
        analysis_interval=300,
        threshold=0.1,
        handler="_handle_trend",
        output_modalities=["episodic_behaviour", "rotation"],
        weight=-1.0,  # negative weight to reverse slope analysis
    ),
]
PRODUCER_MAP = {producer.subscription_topic: producer for producer in PRODUCERS}

MODALITIES = [
    Modality(
        "speed",
        threshold=0.1,
        base_url=ROBOT_CONTROLLER_URL,
        increase_path="/increase_speed",
        decrease_path="/decrease_speed",
        cooldown_duration=20,
    ),
    Modality(
        "proxemics",
        threshold=0.1,
        base_url=ROBOT_CONTROLLER_URL,
        increase_path="/increase_proxemics",
        decrease_path="/decrease_proxemics",
        cooldown_duration=20,
    ),
    Modality(
        "smoothness",
        threshold=0.1,
        base_url=ROBOT_CONTROLLER_URL,
        increase_path="/add_smoothness",
        decrease_path="/remove_smoothness",
        cooldown_duration=20,
    ),
    Modality(
        "rotation",
        threshold=0.1,
        base_url=ROBOT_CONTROLLER_URL,
        increase_path="/add_rotations",
        decrease_path="/remove_rotations",
        cooldown_duration=20,
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

# Default start values to be used with experience
PROXEMICS_MULTIPLIER = 0.7  # results in: 1, 1, 2, 3, 4
SPEED_MULTIPLIER = 1.7  # results in: 2, 3, 5, 7, 9
SMOOTHNESS_THRESHOLD = 3
ROTATION_THRESHOLD = 2

app = Flask(__name__)
analysis_cooldown = datetime.now() + timedelta(seconds=ANALYSIS_INTERVAL)


def analyse_signals():
    global df
    analysis_interval = df.last(pd.Timedelta(seconds=ANALYSIS_INTERVAL))
    grouped = (
        analysis_interval[["output_modality", "value"]]
        .groupby("output_modality")
        .mean()
    )

    print(grouped, flush=True)
    for index, row in grouped.iterrows():
        modality = MODALITIES_MAP.get(index, None)
        if not modality:
            continue
        if row["value"] > modality.threshold:
            modality.increase()
        elif row["value"] < -modality.threshold:
            modality.decrease()
        else:
            modality.neutral()


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


def bootstrap_parameters():
    while True:
        time.sleep(1)
        try:
            response = requests.get(EXPRESSION_ANALYZER_BASE_URL + "/operator_details")
            if response.status_code == 200:
                res = response.json()
                gender = res.get("gender", None)
                if gender is not None:
                    race = res.get("race", None)
                    age = res.get("age", None)
                    break
        except Exception as e:
            print(e)

    operator = "lukashueller"  # TODO get operator name from facial anaylsis module
    print(gender, age, race, flush=True)
    experience = get_linkedIn_estimate(operator)
    print(experience, flush=True)
    params = calculate_params(experience)
    post_bootstrapped_params(params)


def _set_cooldown():
    global analysis_cooldown
    now = datetime.now()
    analysis_cooldown = now + timedelta(seconds=ANALYSIS_INTERVAL)


@app.route("/data", methods=["POST"])
def deliver_data():
    if request.json:
        data = request.json
        producer = PRODUCER_MAP.get(data["topic"], None)
        if producer:
            # append data to producer df and handle the data
            del data["topic"]
            value = producer.handle(data)

            # append handled data to global df
            global df
            df = pd.concat([df, value]) if df is not None else value

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


if __name__ == "__main__":
    bootstrap_parameters()
    app.run(debug=True, host="0.0.0.0", port="5000")
