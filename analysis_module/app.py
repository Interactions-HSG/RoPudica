import json
import paho.mqtt.client as mqtt
from modality import Modality
from producer import Producer
import pandas as pd
import sched, time

ANALYSIS_INTERVAL = 3  # seconds

PRODUCERS = []
PRODUCER_MAP = {producer.subscription_topic: producer for producer in PRODUCERS}

MODLITIES = []
MODALITIES_MAP = {modality.name: modality for modality in MODLITIES}
MODALITY_THRESHOLD = 0.5

df = pd.DataFrame(columns=["time", "output_modality", "value"])

MQTT_BROKER = "mqtt-broker"
MQTT_PORT = 1883


def analyse_signals(scheduler):
    scheduler.enter(ANALYSIS_INTERVAL, 1, analyse_signals, (scheduler,))

    analysis_interval = df[df["time"] > time.time() - ANALYSIS_INTERVAL]
    grouped = analysis_interval.groupby("output_modality").sum()

    for index, row in grouped.iterrows():
        modality = MODALITIES_MAP[index]
        if row["value"] > MODALITY_THRESHOLD:
            modality.increase()
        elif row["value"] < -MODALITY_THRESHOLD:
            modality.decrease()
        else:
            modality.neutral()


def on_message(client, userdata, msg):
    producer = PRODUCER_MAP.get(msg.topic)
    if producer:
        value = producer.handle(json.loads(msg.payload))
        df = pd.concat([df, value], ignore_index=True)


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
