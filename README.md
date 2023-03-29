# RoPudica

This repository is part of my Master Thesis at teh university of St. Gallen.
There are multiple components, that make up the architecture and this is edited and extended as the project comes to be.

## heartrate_processor

Taking in data from an Apple Watch and processing it. Build the docker image with `docker build --tag heartrate-flask-docker .` so that it can be used by the docker compose file.

## posture_processor

Using a Intel RealSense camera to reason on the operators pose

_How to run from within the processor directory:_

```bash
python3.9 -m venv posture
source posture/bin/activate
pip install -r requirements.txt
#run the script with sudo privilege
sudo python3 posture_test.py
```

## mosquitto

A MQTT broker used for debugging at the moment in combination with a Grafana dashboard.

_Mosquitto auth:_

- username = mosquittoUser
- pw = MosquittoPassword
- _also allows anonymous connections_

_Grafana auth:_

- username = admin
- pw = admin
