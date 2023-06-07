import json
import paho.mqtt.client as mqtt
from modality import Modality
from producer import Producer
from datetime import datetime, timedelta
import pandas as pd
import sched, time

ANALYSIS_INTERVAL = 3  # seconds
ROBOT_CONTROLLER_URL = "http://localhost:5000"

PRODUCERS = [
    Producer(
        "pupil",
        analysis_interval=0.5,
        threshold=0.001,
        handler="_handle_trend",
        output_modalities=["speed"],
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
    ),
    Modality(
        "proxemics",
        threshold=0.1,
        base_url=ROBOT_CONTROLLER_URL,
        increase_path="/increase_proxemics",
        decrease_path="/decrease_proxemics",
    ),
]
MODALITIES_MAP = {modality.name: modality for modality in MODALITIES}

df = pd.DataFrame(columns=["time", "output_modality", "value"])

MQTT_BROKER = "localhost"
MQTT_PORT = 1883


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


def run():
    my_scheduler = sched.scheduler(time.time, time.sleep)
    client = connect_mqtt()

    for producer in PRODUCERS:
        client.subscribe(producer.subscription_topic)
    client.loop_start()

    my_scheduler.enter(ANALYSIS_INTERVAL, 1, analyse_signals, (my_scheduler,))
    my_scheduler.run()


if __name__ == "__main__":
    run()
