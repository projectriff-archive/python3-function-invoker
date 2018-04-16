
import grpc
import uuid
import sys
import time
sys.path.append('invoker')

import function_pb2_grpc as function
import function_pb2 as message
import json



def generate_messages():
    headers = {
        'Content-Type': message.Message.HeaderValue(values=['text/plain']),
        'correlationId': message.Message.HeaderValue(values=[str(uuid.uuid4())])
    }

    messages = [
        message.Message(payload=bytes(json.dumps({"text":"happy"}), 'UTF-8'), headers=headers),
        message.Message(payload=bytes(json.dumps({"text":"sad"}), 'UTF-8'), headers=headers),
    ]
    for msg in messages:
        print("sending message %s" % msg)
        yield msg


def wait_until_channel_ready(channel):
    max_tries = 100
    ready = grpc.channel_ready_future(channel)
    tries = 0
    while not ready.done():
        time.sleep(0.1)
        tries = tries + 1
        if tries == max_tries:
            raise RuntimeError("cannot connect to gRPC server")


port = 10382
channel = grpc.insecure_channel('localhost:%s' % port)

stub = function.MessageFunctionStub(channel)
wait_until_channel_ready(channel)

responses = stub.Call(generate_messages())

for response in responses:
        print("Received message %s" % response)



