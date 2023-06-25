import json
import paho.mqtt.client as mqtt
from modality import Modality
from producer import Producer
from datetime import datetime, timedelta
import pandas as pd
import sched, time
import requests

ANALYSIS_INTERVAL = 3  # seconds
ROBOT_CONTROLLER_URL = "http://localhost:5001"

PRODUCERS = [
    Producer(
        "pupil",
        analysis_interval=0.5,
        threshold=0.001,
        handler="_handle_trend",
        output_modalities=["speed"],
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

df = pd.DataFrame(columns=["time", "output_modality", "value"])

MQTT_BROKER = "localhost"
MQTT_PORT = 1883

# Default start values to be used with experience
PROXEMICS_MULTIPLIER = 0.7  # results in: 1, 1, 2, 3, 4
SPEED_MULTIPLIER = 1.7  # results in: 2, 3, 5, 7, 9
SMOOTHNESS_THRESHOLD = 3
ROTATION_THRESHOLD = 2


def analyse_signals(scheduler):
    global df
    scheduler.enter(ANALYSIS_INTERVAL, 1, analyse_signals, (scheduler,))

    analysis_interval = df.last(pd.Timedelta(seconds=ANALYSIS_INTERVAL))
    grouped = (
        analysis_interval[["output_modality", "value"]]
        .groupby("output_modality")
        .mean()
    )

    print(grouped)
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


def on_message(client, userdata, msg):
    global df
    producer = PRODUCER_MAP.get(msg.topic)
    if producer:
        value = producer.handle(json.loads(msg.payload))
        # print(value)
        df = pd.concat([df, value]) if df is not None else value


def connect_mqtt():
    client = mqtt.Client(protocol=mqtt.MQTTv5)
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT)
    return client


def get_linkedIn_estimate(operator: str):
    response = requests.post(
        "http://localhost:5000/linkedInScore", json={"operator:": operator}
    )
    return response.json()["score"]


def post_bootstrapped_params(params: dict):
    response = requests.post(
        ROBOT_CONTROLLER_URL + "/initialize_robot_params", json=params
    )
    return response.json()


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
    operator = "Kay Erik Jenss"  # TODO get operator name from facial anaylsis module

    experience = get_linkedIn_estimate(operator)
    post_bootstrapped_params(calculate_params(experience))


def run():
    client = connect_mqtt()
    bootstrap_parameters()

    for producer in PRODUCERS:
        client.subscribe(producer.subscription_topic)
    client.loop_start()

    my_scheduler = sched.scheduler(time.time, time.sleep)
    my_scheduler.enter(ANALYSIS_INTERVAL, 1, analyse_signals, (my_scheduler,))
    my_scheduler.run()


if __name__ == "__main__":
    run()
