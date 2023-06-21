
FROM python:3.8-slim-buster

WORKDIR /python-docker

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6 -y
COPY app.py app.py

COPY ./weights/*.h5 /root/.deepface/weights/

RUN pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host=files.pythonhosted.org deepface

ENV PYTHONUNBUFFERED=1
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]
