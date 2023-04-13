from flask import Flask, request
import paho.mqtt.client as mqtt
import time
import pandas as pd

df = pd.DataFrame(columns=['time', 'heartrate'])

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
        received_date = time.time()
        data_string = request.json['data']
        data_split = data_string.split(':', 1)
        
        attribute = data_split[0]
        value = int(data_split[-1])
        
        if attribute == 'heartRate':
            if len(df) > 3: # only calculate if we have at least 3 values in df
                last_60_seconds = df[df['time'] > received_date - 60]
                mean = last_60_seconds['heartrate'].mean()
                std_dev = last_60_seconds['heartrate'].std()
                
                distance = (mean - value) / std_dev
                client.publish("heartrate/deviation", distance)


            df.loc[len(df)] = [received_date, value]

        client.publish("heartrate/debug/"+attribute, value)
    return ''

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port='3476')