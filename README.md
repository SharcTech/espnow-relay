# ESPNOW-Relay

Relay ESPNOW messages to and from an MQTT broker.

## SHARC Support

Supported Events:
- `avail`
    - https://github.com/SharcTech/sharc-support?tab=readme-ov-file#mqtt-connect
    - https://github.com/SharcTech/sharc-support?tab=readme-ov-file#mqtt-disconnect
- `io`
    - https://github.com/SharcTech/sharc-support?tab=readme-ov-file#sensor-values

Supported Commands
- `action`: `device.reset`
    - https://github.com/SharcTech/sharc-support?tab=readme-ov-file#device-reset
- `action`: `io.publish`
    - https://github.com/SharcTech/sharc-support?tab=readme-ov-file#publish-io-data
- `action`: `di.counter.reset`
    - https://github.com/SharcTech/sharc-support?tab=readme-ov-file#reset-digital-input-counters
- `cfg`
    - https://github.com/SharcTech/sharc-support?tab=readme-ov-file#configuration-changes

## ESPythoNOW Setup

https://github.com/ChuckMash/ESPythoNOW


## clone repo

```
cd ~
git clone https://$(cat ~/secret.ghuser):$(cat ~/secret.ghpat)@github.com/SharcTech/espnow-relay.git
```


## build image

```
git -C ~/espnow-relay pull
export BUILD_VERSION=2.0.1
docker build -f ~/espnow-relay/Dockerfile --tag=ladder99/espnow-relay:latest --tag=ladder99/espnow-relay:$BUILD_VERSION ~/espnow-relay
cat ~/secret.dhpass| docker login --username ladder99 --password-stdin
docker push ladder99/espnow-relay --all-tags
docker logout
```


## standup

```
docker compose \
  -f ~/espnow-relay/docker-compose.yml \
  up -d --force-recreate
```


## edgeshark

```
wget -q --no-cache -O - \
  https://github.com/siemens/edgeshark/raw/main/deployments/wget/docker-compose.yaml \
  | DOCKER_DEFAULT_PLATFORM= docker compose -f - up
```



