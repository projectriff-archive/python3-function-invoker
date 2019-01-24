# Python3 Function Invoker [![Build Status](https://travis-ci.org/projectriff/python3-function-invoker.svg?branch=master)](https://travis-ci.org/projectriff/python3-function-invoker)

## About

The Python 3 function invoker, as the name implies, supports functions written in Python 3.  The invoker supports function arguments of type `str` or `dict`, determined by the message's `Content-Type` header.
For messages containing `Content-Type:application/json`, the bytes payload is converted to a dict. Reflection is used to convert the return value. Currently only UTF-8 encoding is supported.

Supported Python Version: 3.6.x, 3.7.x

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

## Running functions on Riff

TBD