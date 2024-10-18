FROM amd64/python:3.12-slim-bullseye AS build

RUN apt-get update -q && \
    apt-get install -y --fix-missing --no-install-recommends gcc libc6-dev libpcap-dev tcpdump

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

STOPSIGNAL SIGTERM

CMD ["python3", "-u", "main.py"]