from concurrent import futures

__copyright__ = '''
Copyright 2018 the original author or authors.

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
'''
__author__ = 'David Turanski'

import grpc
import time
import function_pb2_grpc as function
import function_pb2 as message
import json
import logging
import os

stopped = True
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
log = logging.getLogger(__name__)


def run(func, interaction_model, port):
    """
    Runs the gRPC server
    :param func: the function to invoke for each gRPC Call() method
    :param interaction_model: indicates interaction model: None is single value parameter and return type, 'stream' indicates input and output are generators
    :param port: the gRPC port
    :return: None
    """
    global server, stopped
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    function.add_MessageFunctionServicer_to_server(MessageFunctionServicer(func, interaction_model), server)
    server.add_insecure_port('%s:%s' % ('[::]', port))

    server.start()
    stopped = False
    while not stopped:
        time.sleep(3)


def stop(grace=None):
    """
    Stop the server
    :param grace: a grace period, in seconds, to wait
    :return: None
    """
    global server, stopped
    log.info("stopping server")
    server.stop(grace)
    stopped = True
    log.info("server stopped")


"""
The gRPC server implementation. Will invoke a function for each Call() using the interaction model given by the value 
of `interaction_model` defined in the function module. `stream` indicates bidirectional streaming. By default, the parameter 
and value are primitive types given by the `Content-Type` message header. For `text/plain` the function is expected to accept and 
return a str. For `Content-Type=application/json`, the function is expected to accept and return a dict.  
"""


class MessageFunctionServicer(function.MessageFunctionServicer):

    def __init__(self, func, interaction_model):
        self.func = func
        self.interaction_model = interaction_model

    def Call(self, request_iterator, context):
        """
        The gRPC server implementation
        :param request_iterator: a generator representing a stream of request messages
        :param context: the gRPC request context
        :return:
        """

        if self.interaction_model == 'stream':
            for item in map(self.wrap_message, self.func(self.convert_request_payload(msg) for msg in request_iterator)):
                yield item
        else:
            for request in request_iterator:
                result = self.func(self.convert_request_payload(request))

                reply = self.build_reply_message(request.headers, result)
                yield reply



    @classmethod
    def wrap_message(cls, payload, headers={}):
        """
        Wrap a payload in a Message
        :param payload:
        :param headers:
        :return: the Message
        """
        return cls.build_reply_message(headers, payload)

    @classmethod
    def convert_request_payload(cls, request):
        """
        Convert the request payload from bytes for a given request's Content Type header
        :param request: the request Message
        :return: varies by content type header, e.g., dict or str
        """
        if 'application/json' in request.headers['Content-Type'].values:
            return json.loads(request.payload)
        elif 'application/octet-stream' in request.headers['Content-Type'].values:
            return request.payload
        elif 'text/plain' in request.headers['Content-Type'].values:
            return request.payload.decode('UTF-8')
        
        return request.payload

    @classmethod
    def build_reply_message(cls, headers, val):
        """
        Convert the reply payload to bytes given the request's Accept header
        :param headers: The request header values
        :param val: the payload
        :return: bytes
        """

        reply = message.Message()
        if headers.get('correlationId', None):
            reply.headers['correlationId'].values[:] = headers['correlationId'].values[:]

        accepts = headers.get('Accepts',message.Message.HeaderValue()).values

        if len(accepts) == 0 or 'text/plain' in accepts or "*/*" in accepts:
            if type(val) is dict:
                reply.payload = bytes(json.dumps(val), 'UTF-8')
            else:
                if type(val) is str:
                    reply.payload = bytes(val, 'UTF-8')
                    reply.headers['Content-type'].values[:] = ["text/plain"]
                else:
                    reply.payload = val
                    reply.headers['Content-type'].values[:] = ["application/octet-stream"]

        elif 'application/json' in accepts:
            if type(val) is dict:
                reply.payload = bytes(json.dumps(val), 'UTF-8')
                reply.headers['Content-type'].values[:] = ["application/json"]
            else:
                raise RuntimeError('Cannot convert type %s to JSON' % type(val))
        else:
            raise RuntimeError('Unsupported Accept header %s' % accepts)

        return reply
