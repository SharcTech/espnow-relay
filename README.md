## clone repo

```
cd ~
git clone https://$(cat ~/secret.ghuser):$(cat ~/secret.ghpat)@github.com/SharcTech/espnow-relay.git
```

## build image

```
export BUILD_VERSION=0.0.005
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