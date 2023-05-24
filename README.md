# RoPudica

This repository is part of my Master Thesis at teh university of St. Gallen.
There are multiple components, that make up the architecture and this is edited and extended as the project comes to be.

## heartrate_processor

Taking in data from an Apple Watch and processing it. Build the docker image with `docker build --tag heartrate-flask-docker .` so that it can be used by the docker compose file.

## linkedin_scraping

Receiving an operator name via HTTP and responds with LinkedIn information and a score on how experienced the operator might have been with industrial robots.  
It requires a _.env_ file in the _/linkedin_scraping_ directory which includes the attributes `LINKEDIN_USERNAME`, `LINKEDIN_PASSWORD` and `OPENAI_KEY`.

Example:

```http request
GET: http://localhost:5000/linkedInScore
BODY:
    {
        "operator": "Kay Erik Jenß"
    }
```

Build the docker image with `docker build --tag linkedin-scraping-flask-docker .` so that it can be used by the docker compose file. This does not use the slim pre-bruilt image, as it requires a pip dependency to be installed directly from git, which is not included in the slim image.

## posture_processor

Using a Intel RealSense camera to reason on the operators pose

_How to run from within the processor directory:_

```bash
python3.9 -m venv posture
source posture/bin/activate
pip install -r requirements.txt
#run the script with sudo privilege
sudo python3 posture.py
```

## pupil_processor

Using the Pupil Labs eye tracker to track changes in the operators pupil size

_How to run from within the pupil processor directory:_

```bash
python3.9 -m venv pupil
source pupil/bin/activate
pip install -r requirements.txt
python3 processor.py
```

Make sure, that the Pupil Labs Capture Software is running and the eye tracker is connected. On Mac OS, the Pupil Labs Capture Software needs to be started with sudo privileges (e.g. `sudo /Applications/Pupil\ Capture.app/Contents/MacOS/pupil_capture`).

## mosquitto

A MQTT broker used for debugging at the moment in combination with a Grafana dashboard.

_Mosquitto auth:_

- username = mosquittoUser
- pw = MosquittoPassword
- _also allows anonymous connections_

_Grafana auth:_

- username = admin
- pw = admin

## robot_controller

Allowing routes to controll the workflow of the Robot (xArm 7).
It requires a _.env_ file in the _/robot_controller_ directory which includes the `ROBOT_IP` attribute.  
Build the docker image with `docker build --tag robot-controller .` so that it can be used by the docker compose file.
