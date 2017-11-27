#!/bin/bash

echo Building tonico/ehex

BUILD_DIR=build
BIN_DIR=$BUILD_DIR/bin
PLUGIN_DIR=$BUILD_DIR/lib/dlvhex2/plugins
WHEELS_DIR=$BUILD_DIR/wheels

docker build -t tonico/ehex $(dirname "$0")/..
docker create --name ehex tonico/ehex

mkdir -p $BIN_DIR $PLUGIN_DIR $WHEELS_DIR
docker cp ehex:/usr/local/bin/. $BIN_DIR
docker cp ehex:/usr/local/lib/dlvhex2/plugins/. $PLUGIN_DIR
docker cp ehex:/var/cache/wheels/. $WHEELS_DIR

docker rm -f ehex
