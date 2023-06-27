import requests
import zmq
import msgpack
import json
import time
import datetime
import csv
import uuid
import pandas as pd

EYE_INDEX_MAPPING = {
    0: "right",
    1: "left",
}
CONFIDENCE_TRHESHOLD = 0.6
WRITE_TO_CSV = False

# PUPILLABS CONNECTION DETAILS
IP = "localhost"
PORT = 50020

ANALYSER_BASE_URL = "http://localhost:5006"


def approximate_timestamp(pupil_timestamp, offset):
    pupiltime_in_systemtime = pupil_timestamp + offset
    return datetime.datetime.fromtimestamp(pupiltime_in_systemtime)


def write_to_csv(data, filename="pupil.csv"):
    with open(filename, mode="a", newline="") as f:
        csv_writer = csv.writer(
            f, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
        )
        csv_writer.writerow(data.values())


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
subscriber.subscribe("blinks")


last_pupil_data = {}
last_blink = {"timestamp": datetime.datetime.now()}
BLINK_OFFSET = 0.5  # seconds that must be between two blinks
blinks = pd.DataFrame(
    columns=["value"], index=pd.DatetimeIndex(name="timestamp", data=[])
)
last_timestamp = datetime.datetime.now()


def handle_pupils(payload):
    global last_pupil_data
    message = msgpack.loads(payload)
    confidence = message[b"confidence"]

    if confidence < CONFIDENCE_TRHESHOLD:
        return

    id = message[b"id"]
    eye = EYE_INDEX_MAPPING[id]
    diameter = message[b"diameter_3d"]

    timestamp = approximate_timestamp(message[b"timestamp"], time_offset)

    if last_pupil_data:
        if last_pupil_data["eye"] == eye:
            last_pupil_data = {
                "eye": eye,
                "diameter": diameter,
            }
            return
        else:
            data = {
                "id": str(uuid.uuid4()),
                "value": (last_pupil_data["diameter"] + diameter) / 2,
                "timestamp": timestamp.isoformat(),
                "topic": "pupil",
            }
    else:
        last_pupil_data = {
            "eye": eye,
            "diameter": diameter,
        }
        return

    if WRITE_TO_CSV:
        write_to_csv(data)

    requests.post(ANALYSER_BASE_URL + "/data", json=data)


def handle_blinks(payload):
    global blinks
    message = msgpack.loads(payload)
    timestamp = approximate_timestamp(message[b"timestamp"], time_offset)
    last_blink = {
        "value": 1,
        "timestamp": timestamp,
    }
    new_df = pd.DataFrame.from_dict([last_blink])
    new_df.set_index(
        pd.DatetimeIndex(data=new_df["timestamp"], name="timestamp"),
        inplace=True,
    )
    new_df.drop(columns=["timestamp"], inplace=True)

    if len(blinks.tail(1).index):
        if blinks.tail(1).index.to_pydatetime() < timestamp - datetime.timedelta(
            seconds=BLINK_OFFSET
        ):
            blinks = pd.concat([blinks, new_df])

            if len(blinks.index) > 15:
                df = blinks.groupby(pd.Grouper(freq="1min")).sum()
                last_index = df.tail(1).index.to_pydatetime()[0]

                # check if new minute has started
                global last_timestamp
                if last_index > last_timestamp:
                    # from df get the value column from the second to last row
                    value = int(df.tail(2).head(1)["value"].values[0])
                    data = {
                        "id": str(uuid.uuid4()),
                        "value": value,
                        "timestamp": last_timestamp.isoformat(),
                        "topic": "blinks",
                    }
                    last_timestamp = last_index
                    try:
                        requests.post(ANALYSER_BASE_URL + "/data", json=data)
                    except Exception as e:
                        print(e)

    else:
        blinks = new_df


while True:
    topic, payload = subscriber.recv_multipart()

    if topic == b"blinks":
        handle_blinks(payload)
    else:
        handle_pupils(payload)
