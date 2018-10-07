# Python3 Function Invoker [![Build Status](https://travis-ci.org/projectriff/python3-function-invoker.svg?branch=master)](https://travis-ci.org/projectriff/python3-function-invoker)

## About

The Python 3 function invoker, as the name implies, supports functions written in Python 3.  The invoker supports function arguments of type `str` or `dict`, determined by the message's `Content-Type` header.
For messages containing `Content-Type:application/json`, the bytes payload is converted to a dict. Reflection is used to convert the return value. Currently only UTF-8 encoding is supported.

Supported Python Version: 3.6.x

## Streams (experimental)
If the function module contains a global variable `interaction_model='stream'`, the invoker will pass a generator yielding each message payload. The response should be a generator yielding the response payload.

For example:

```
interaction_model = "stream"


def bidirectional(stream):
    return (item.upper() for item in stream)
```

## Running Tests

This script will install a virtual environment for python 3.6 and run the tests.

```bash
./run_tests.sh
```

## Update grpc modules

```bash
./setup.py grpc
```

## Build the docker image

```bash
./build.sh
```

## Running functions on Riff

1. Create a Dockerfile that loads your function and uses the function invoker as a base image.
```Dockerfile
FROM projectriff/python3-function-invoker:0.0.8-snapshot
ARG FUNCTION_MODULE=<FUNCTION_MODULE>
ARG FUNCTION_HANDLER=<FUNCTION_HANDLER>
ADD ./${FUNCTION_MODULE} /
ENV FUNCTION_URI file:///${FUNCTION_MODULE}?handler=${FUNCTION_HANDLER}
```
Where <FUNCTION_MODULE> is the python module and <FUNCTION_HANDLER> is the python handler function

2. Build your docker image and push to your image repository

```bash
docker build . -t <DOCKER_ID>/<FUNCTION_NAME>
docker push <DOCKER_ID>/<FUNCTION_NAME>
```

3. Deploy your function

```bash
riff service create <FUNCTION_NAME> --image <DOCKER_ID>/<FUNCTION_NAME>
```

4. Invoke your function

```bash
riff service invoke <FUNCTION_NAME> --json -- -d '{"hi": " python"}'
```
