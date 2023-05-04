# syntax=docker/dockerfile:1

FROM python:3.8-buster

WORKDIR /python-docker

RUN git clone https://github.com/xArm-Developer/xArm-Python-SDK.git
RUN cp -R xArm-Python-SDK/xarm .
RUN rm -rf xArm-Python-SDK

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]