# syntax=docker/dockerfile:1

FROM python:3.10-slim-buster

WORKDIR /python-docker

# RUN apt-get install librealsense2-utils
# RUN apt-get install librealsense2-dev
RUN apt update && apt-get install -y libusb-1.0-0-dev ffmpeg libsm6 libxext6
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
# RUN apt-get -y install libusb-1.0-0

COPY . .

CMD [ "python3", "test_connection.py"]