#!/bin/bash

version=${1:-`cat VERSION`}

docker build . -t projectriff/python3-function-invoker:$version
