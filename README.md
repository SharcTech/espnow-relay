# ESPNOW-Relay

Relay ESPNOW messages to and from an MQTT broker.

## ESPythoNOW Setup

https://github.com/ChuckMash/ESPythoNOW


## clone repo

```
cd ~
git clone https://$(cat ~/secret.ghuser):$(cat ~/secret.ghpat)@github.com/SharcTech/espnow-relay.git
```


## build image

```
export BUILD_VERSION=1.5.2
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



