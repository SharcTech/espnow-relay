FROM amd64/python:3.12-slim-bullseye AS build

RUN apt-get update -q && \
    apt-get install -y --fix-missing --no-install-recommends gcc libc6-dev libpcap-dev tcpdump net-tools wireless-tools

RUN python3 -m venv /venv

ENV PATH=/venv/bin:$PATH

WORKDIR /app

COPY ./requirements.txt .

RUN pip install --no-cache-dir --trusted-host pypi.python.org -r requirements.txt

COPY . .

ENV PATH=/venv/bin:$PATH

ARG LOG_LEVEL=20
ENV LOG_LEVEL ${LOG_LEVEL}

ARG INTERFACE=wlxc01c3038d5a8
ENV INTERFACE ${INTERFACE}

ARG BROKER_IP=sharc.tech
ENV BROKER_IP ${BROKER_IP}

ARG BROKER_PORT=1883
ENV BROKER_PORT ${BROKER_PORT}

ARG BROKER_USERNAME=
ENV BROKER_USERNAME ${BROKER_USERNAME}

ARG BROKER_PASSWORD=
ENV BROKER_PASSWORD ${BROKER_PASSWORD}

ARG ESP_TO_BROKER_CUSTOM=1
ENV ESP_TO_BROKER_CUSTOM ${ESP_TO_BROKER_CUSTOM}

ARG BROKER_TO_ESP_CUSTOM=1
ENV BROKER_TO_ESP_CUSTOM ${BROKER_TO_ESP_CUSTOM}

ARG DROP_INCOMING_INVALID_PEER=1
ENV DROP_INCOMING_INVALID_PEER ${DROP_INCOMING_INVALID_PEER}

STOPSIGNAL SIGTERM

CMD ["python3", "-u", "main.py"]