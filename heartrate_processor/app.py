from flask import Flask, request
import paho.mqtt.client as mqtt

app = Flask(__name__)

broker="mqtt-broker"
port=1883

def on_publish(client,userdata,result):
    print("data published \n")
    pass

client= mqtt.Client(protocol=mqtt.MQTTv5)
client.on_publish = on_publish
client.connect(broker,port)

@app.route('/', methods = ['PUT'])
def index():
    if request.json:
        data_string = request.json['data']
        data_split = data_string.split(':', 1)
        
        attribute = data_split[0]
        value = data_split[-1]

        client.publish("debug/heartrate", value)
    return ''

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port='3476')