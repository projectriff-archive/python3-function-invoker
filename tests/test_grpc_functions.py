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

import sys
if sys.version_info[0] != 3:
    raise RuntimeError("Requires Python 3")

import grpc
import unittest
import subprocess
import os
import uuid
import time
import signal
import warnings

sys.path.append('invoker')

import function_pb2_grpc as function
import function_pb2 as message

PYTHON = sys.executable

class GrpcFunctionTest(unittest.TestCase):
    """
    Assumes os.getcwd() is the project base directory
    """

    @classmethod
    def setUpClass(cls):
        cls.workingdir = os.path.abspath("./invoker")
        cls.command = "%s function_invoker.py" % PYTHON
        cls.PYTHONPATH = '%s:%s' % ('%s/tests/functions:$PYTHONPATH' % os.getcwd(), '%s/invoker' % os.getcwd())

    def setUp(self):
        pass

    def tearDown(self):
        warnings.simplefilter("ignore")
        os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)

    def test_upper(self):
        port = find_free_port()
        env = {
            'PYTHONPATH': self.PYTHONPATH,
            'GRPC_PORT': str(port),
            'FUNCTION_URI': 'file://%s/tests/functions/upper.py?handler=handle' % os.getcwd()
        }

        self.process = subprocess.Popen(self.command,
                                        cwd=self.workingdir,
                                        shell=True,
                                        env=env,
                                        preexec_fn=os.setsid,
                                        )

        channel = grpc.insecure_channel('localhost:%s' % port)
        wait_until_channel_ready(channel)

        self.stub = function.MessageFunctionStub(channel)

        def generate_messages():
            headers = {
                'Content-Type': message.Message.HeaderValue(values=['text/plain']),
                'correlationId': message.Message.HeaderValue(values=[str(uuid.uuid4())])
            }

            messages = [
                message.Message(payload=bytes("hello", 'UTF-8'), headers=headers),
                message.Message(payload=bytes("world", 'UTF-8'), headers=headers),
                message.Message(payload=bytes("foo", 'UTF-8'), headers=headers),
                message.Message(payload=bytes("bar", 'UTF-8'), headers=headers),
            ]
            for msg in messages:
                yield msg

        responses = self.stub.Call(generate_messages())
        expected = [b'HELLO', b'WORLD', b'FOO', b'BAR']

        for response in responses:
            self.assertTrue(response.payload in expected)
            expected.remove(response.payload)

        self.assertEqual(0, len(expected))

    def test_upper_no_correlation(self):
        port = find_free_port()
        env = {
            'PYTHONPATH': '%s/tests/functions:$PYTHONPATH' % os.getcwd(),
            'GRPC_PORT': str(port),
            'FUNCTION_URI': 'file://%s/tests/functions/upper.py?handler=handle' % os.getcwd()
        }

        self.process = subprocess.Popen(self.command,
                                        cwd=self.workingdir,
                                        shell=True,
                                        env=env,
                                        preexec_fn=os.setsid,
                                        )

        channel = grpc.insecure_channel('localhost:%s' % port)
        wait_until_channel_ready(channel)

        self.stub = function.MessageFunctionStub(channel)

        def generate_messages():
            headers = {}

            messages = [
                message.Message(payload=b"hello", headers=headers),
                message.Message(payload=b"world", headers=headers),
                message.Message(payload=b"foo", headers=headers),
                message.Message(payload=b"bar", headers=headers),
            ]
            for msg in messages:
                yield msg

        responses = self.stub.Call(generate_messages())
        expected = [b'HELLO', b'WORLD', b'FOO', b'BAR']

        for response in responses:
            self.assertTrue(response.payload in expected)
            self.assertEqual([], response.headers['correlationId'].values)
            expected.remove(response.payload)

        self.assertEquals(0, len(expected))

    def test_concat(self):
        port = find_free_port()
        env = {
            'PYTHONPATH': self.PYTHONPATH,
            'GRPC_PORT': str(port),
            'FUNCTION_URI': 'file://%s/tests/functions/concat.py?handler=concat' % os.getcwd()
        }

        self.process = subprocess.Popen(self.command,
                                        cwd=self.workingdir,
                                        shell=True,
                                        env=env,
                                        preexec_fn=os.setsid,
                                        )

        channel = grpc.insecure_channel('localhost:%s' % port)
        wait_until_channel_ready(channel)

        self.stub = function.MessageFunctionStub(channel)

        def generate_messages():
            headers = {
                'Content-Type': message.Message.HeaderValue(values=['application/json']),
                'correlationId': message.Message.HeaderValue(values=[str(uuid.uuid4())])
            }

            messages = [
                message.Message(payload=b'{"foo":"bar","hello":"world"}', headers=headers),
            ]
            for msg in messages:
                yield msg

        responses = self.stub.Call(generate_messages())

        for response in responses:
            self.assertEqual(b'{"result": "foobarhelloworld"}', response.payload)

    def test_accepts_application_json(self):
        port = find_free_port()
        env = {
            'PYTHONPATH': self.PYTHONPATH,
            'GRPC_PORT': str(port),
            'FUNCTION_URI': 'file://%s/tests/functions/concat.py?handler=concat' % os.getcwd()
        }

        self.process = subprocess.Popen(self.command,
                                        cwd=self.workingdir,
                                        shell=True,
                                        env=env,
                                        preexec_fn=os.setsid,
                                        )

        channel = grpc.insecure_channel('localhost:%d' % port)
        wait_until_channel_ready(channel)

        self.stub = function.MessageFunctionStub(channel)

        def generate_messages():
            headers = {
                'Content-Type': message.Message.HeaderValue(values=['application/json']),
                'Accept': message.Message.HeaderValue(values=['application/json']),
                'correlationId': message.Message.HeaderValue(values=[str(uuid.uuid4())])
            }

            messages = [
                message.Message(payload=b'{"foo":"bar","hello":"world"}', headers=headers),
            ]
            for msg in messages:
                yield msg

        responses = self.stub.Call(generate_messages())

        for response in responses:
            self.assertEqual(b'{"result": "foobarhelloworld"}', response.payload)

    def test_accepts_text_plain(self):
        port = find_free_port()
        env = {
            'PYTHONPATH': self.PYTHONPATH,
            'GRPC_PORT': str(port),
            'FUNCTION_URI': 'file://%s/tests/functions/concat.py?handler=concat' % os.getcwd()
        }

        self.process = subprocess.Popen(self.command,
                                        cwd=self.workingdir,
                                        shell=True,
                                        env=env,
                                        preexec_fn=os.setsid,
                                        )

        channel = grpc.insecure_channel('localhost:%d' % port)
        wait_until_channel_ready(channel)

        self.stub = function.MessageFunctionStub(channel)

        def generate_messages():
            headers = {
                'Content-Type': message.Message.HeaderValue(values=['application/json']),
                'Accept': message.Message.HeaderValue(values=['text/plain']),
                'correlationId': message.Message.HeaderValue(values=[str(uuid.uuid4())])
            }

            messages = [
                message.Message(payload=b'{"foo":"bar","hello":"world"}', headers=headers),
            ]
            for msg in messages:
                yield msg

        responses = self.stub.Call(generate_messages())

        for response in responses:
            self.assertEqual(b'{"result": "foobarhelloworld"}', response.payload)

    def test_accepts_not_supported(self):
        port = find_free_port()
        env = {
            'PYTHONPATH': self.PYTHONPATH,
            'GRPC_PORT': str(port),
            'FUNCTION_URI': 'file://%s/tests/functions/concat.py?handler=concat' % os.getcwd()
        }

        self.process = subprocess.Popen(self.command,
                                        cwd=self.workingdir,
                                        shell=True,
                                        env=env,
                                        preexec_fn=os.setsid,
                                        )

        channel = grpc.insecure_channel('localhost:%s' % port)
        wait_until_channel_ready(channel)

        self.stub = function.MessageFunctionStub(channel)

        def generate_messages():
            headers = {
                'Content-Type': message.Message.HeaderValue(values=['application/json']),
                'Accept': message.Message.HeaderValue(values=['application/xml']),
                'correlationId': message.Message.HeaderValue(values=[str(uuid.uuid4())])
            }

            messages = [
                message.Message(payload=b'{"foo":"bar","hello":"world"}', headers=headers),
            ]
            for msg in messages:
                yield msg

        try:
            responses = self.stub.Call(generate_messages())
            self.assertEqual(grpc._channel._Rendezvous, type(responses))
            # TODO: Investigate error handling
            # https://github.com/projectriff/python2-function-invoker/issues/5
        except RuntimeError:
            pass


import socket
from contextlib import closing


def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


def wait_until_channel_ready(channel):
    max_tries = 100
    ready = grpc.channel_ready_future(channel)
    tries = 0
    while not ready.done():
        time.sleep(0.1)
        tries = tries + 1
        if tries == max_tries:
            raise RuntimeError("cannot connect to gRPC server")
