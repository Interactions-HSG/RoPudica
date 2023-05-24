import zmq
import msgpack
import paho.mqtt.client as mqtt
import json 
import time
import datetime
import csv

EYE_INDEX_MAPPING = {
    0: 'right',
    1: 'left',
}

# PUPILLABS CONNECTION DETAILS
IP = 'localhost'
PORT = 50020

# MQTT CONNECTION DETAILS
BROKER="localhost"
MQTT_PORT=1883
DEBUG_MQTT = False

def on_publish(client,userdata,result):
    print("data published \n")
    pass

def approximate_timestamp(pupil_timestamp, offset):
    pupiltime_in_systemtime = pupil_timestamp + offset
    return datetime.datetime.fromtimestamp(pupiltime_in_systemtime)

def write_to_csv(data):
    with open('pupil.csv', mode='a', newline='') as f:
        csv_writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow(data.values())

# MQTT
client= mqtt.Client(protocol=mqtt.MQTTv5)
if DEBUG_MQTT:
    client.on_publish = on_publish
client.connect(BROKER,MQTT_PORT)

# ZMQ
ctx = zmq.Context()
pupil_remote = ctx.socket(zmq.REQ)
pupil_remote.connect(f'tcp://{IP}:{PORT}')

pupil_remote.send_string('t')
pupil_start_time = pupil_remote.recv_string()
system_start_time = time.time()
time_offset = system_start_time - float(pupil_start_time)

# Request 'SUB_PORT' for reading data
pupil_remote.send_string('SUB_PORT')
sub_port = pupil_remote.recv_string()

subscriber = ctx.socket(zmq.SUB)
subscriber.connect(f'tcp://{IP}:{sub_port}')
subscriber.subscribe('pupil.0.2d')  
subscriber.subscribe('pupil.1.2d')  

while True:
    topic, payload = subscriber.recv_multipart()
    message = msgpack.loads(payload)
    
    id = message[b'id']
    eye = EYE_INDEX_MAPPING[id]
    diameter = message[b'diameter']
    confidence = message[b'confidence']
    timestamp = approximate_timestamp(message[b'timestamp'], time_offset)
    
    data = {
        'id': id,
        'eye': eye,
        'diameter': diameter,
        'confidence': confidence,
        'timestamp': timestamp.isoformat(),
    }
    
    write_to_csv(data)
    # client.publish("debug/pupil/"+eye, json.dumps(data))