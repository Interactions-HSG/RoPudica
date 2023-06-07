import zmq
import msgpack
import paho.mqtt.client as mqtt
import json
import time
import datetime
import csv
import uuid

EYE_INDEX_MAPPING = {
    0: "right",
    1: "left",
}
CONFIDENCE_TRHESHOLD = 0.6
WRITE_TO_CSV = False

# PUPILLABS CONNECTION DETAILS
IP = "localhost"
PORT = 50020

# MQTT CONNECTION DETAILS
BROKER = "localhost"
MQTT_PORT = 1883
MQTT_ACTIVE = True
DEBUG_MQTT = True


def on_publish(client, userdata, result):
    print("data published \n")
    pass


def approximate_timestamp(pupil_timestamp, offset):
    pupiltime_in_systemtime = pupil_timestamp + offset
    return datetime.datetime.fromtimestamp(pupiltime_in_systemtime)


def write_to_csv(data, filename="pupil.csv"):
    with open(filename, mode="a", newline="") as f:
        csv_writer = csv.writer(
            f, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
        )
        csv_writer.writerow(data.values())


# MQTT
if MQTT_ACTIVE:
    client = mqtt.Client(protocol=mqtt.MQTTv5)
    if DEBUG_MQTT:
        client.on_publish = on_publish
    client.connect(BROKER, MQTT_PORT)

# ZMQ
ctx = zmq.Context()
pupil_remote = ctx.socket(zmq.REQ)
pupil_remote.connect(f"tcp://{IP}:{PORT}")

pupil_remote.send_string("t")
pupil_start_time = pupil_remote.recv_string()
system_start_time = time.time()
time_offset = system_start_time - float(pupil_start_time)

# Request 'SUB_PORT' for reading data
pupil_remote.send_string("SUB_PORT")
sub_port = pupil_remote.recv_string()

subscriber = ctx.socket(zmq.SUB)
subscriber.connect(f"tcp://{IP}:{sub_port}")
subscriber.subscribe("pupil.0.3d")
subscriber.subscribe("pupil.1.3d")

last = {}
while True:
    topic, payload = subscriber.recv_multipart()
    message = msgpack.loads(payload)
    confidence = message[b"confidence"]

    if confidence < CONFIDENCE_TRHESHOLD:
        continue

    id = message[b"id"]
    eye = EYE_INDEX_MAPPING[id]
    diameter = message[b"diameter_3d"]

    timestamp = approximate_timestamp(message[b"timestamp"], time_offset)

    if last:
        if last["eye"] == eye:
            last = {
                "eye": eye,
                "diameter": diameter,
            }
            continue
        else:
            data = {
                "id": str(uuid.uuid4()),
                "value": (last["diameter"] + diameter) / 2,
                "timestamp": timestamp.isoformat(),
            }
    else:
        last = {
            "eye": eye,
            "diameter": diameter,
        }
        continue

    # print(data)
    if WRITE_TO_CSV:
        write_to_csv(data)
    if MQTT_ACTIVE:
        client.publish("pupil", json.dumps(data))
