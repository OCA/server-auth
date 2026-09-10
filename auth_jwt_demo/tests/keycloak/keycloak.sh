#!/bin/sh
set -x
$(which docker || which podman) run --rm \
  -v $(dirname $0)/keycloak-config.json:/tmp/keycloak-config.json \
  -p 8080:8080 \
  quay.io/keycloak/keycloak:12.0.4 \
  -Dkeycloak.migration.action=import \
  -Dkeycloak.migration.provider=singleFile \
  -Dkeycloak.migration.file=/tmp/keycloak-config.json \
  -Dkeycloak.migration.strategy=OVERWRITE_EXISTING
