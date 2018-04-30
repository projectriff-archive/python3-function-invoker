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

from tests.utils import testutils
import sys

if sys.version_info[0] != 3:
    raise RuntimeError("Requires Python 3")

import unittest
import os
import threading
import grpc
import uuid

sys.path.append('invoker')
sys.path.append('tests/functions')

import invoker.function_invoker
import invoker.function_pb2_grpc as function
import invoker.function_pb2 as message


class FunctionInvokerTest(unittest.TestCase):
    """
    Forks function_invoker in a background thread. Easier for debugging
    Assumes os.getcwd() is the project base directory
    """
    def test_upper(self):
        env = function_env('upper.py','handle')

        func, interaction_model = invoker.function_invoker.install_function(env)
        self.assertEqual('handle',func.__name__)
        self.assertIsNone(interaction_model)

        threading.Thread(target=invoker.function_invoker.invoke_function, args=([func,interaction_model,env])).start()

        channel = grpc.insecure_channel('localhost:%s' % env['GRPC_PORT'])
        testutils.wait_until_channel_ready(channel)

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

        responses = function.MessageFunctionStub(channel).Call(generate_messages())
        expected = [b'HELLO', b'WORLD', b'FOO', b'BAR']

        for response in responses:
            self.assertTrue(response.payload in expected)
            expected.remove(response.payload)

        self.assertEqual(0, len(expected))
        invoker.function_invoker.stop()

    def test_bidirectional(self):
        env = function_env('streamer.py','bidirectional')
        func, interaction_model = invoker.function_invoker.install_function(env)
        self.assertEqual('bidirectional', func.__name__)
        self.assertEqual('stream',interaction_model)

        threading.Thread(target=invoker.function_invoker.invoke_function,
                                            args=([func, interaction_model, env])).start()

        channel = grpc.insecure_channel('localhost:%s' % env['GRPC_PORT'])
        testutils.wait_until_channel_ready(channel)

        stub = function.MessageFunctionStub(channel)

        def generate_messages():
            headers = {
                'Content-Type': message.Message.HeaderValue(values=['text/plain']),
            }

            messages = [
                message.Message(payload=b'foo', headers=headers),
                message.Message(payload=b'bar', headers=headers),
                message.Message(payload=b'baz', headers=headers),
                message.Message(payload=b'faz', headers=headers),
            ]
            for msg in messages:
                yield msg

        responses = stub.Call(generate_messages())

        expected = [b'FOO', b'BAR', b'BAZ', b'FAZ']

        for response in responses:
            self.assertTrue(response.payload in expected)
            expected.remove(response.payload)

        self.assertEqual(0, len(expected))
        invoker.function_invoker.stop()

    def test_filter(self):
        env = function_env('streamer.py','filter')

        func, interaction_model = invoker.function_invoker.install_function(env)
        self.assertEqual('filter', func.__name__)
        self.assertEqual('stream',interaction_model)

        threading.Thread(target=invoker.function_invoker.invoke_function,
                                            args=([func, interaction_model, env])).start()

        channel = grpc.insecure_channel('localhost:%s' % env['GRPC_PORT'])
        testutils.wait_until_channel_ready(channel)

        def generate_messages():
            headers = {
                'Content-Type': message.Message.HeaderValue(values=['text/plain'])
            }

            messages = [
                message.Message(payload=b'foo', headers=headers),
                message.Message(payload=b'bar', headers=headers),
                message.Message(payload=b'foobar', headers=headers),
            ]
            for msg in messages:
                yield msg

        responses = function.MessageFunctionStub(channel).Call(generate_messages())

        expected = [b'foo', b'foobar']

        for response in responses:
            self.assertTrue(response.payload in expected)
            expected.remove(response.payload)

        self.assertEqual(0, len(expected))
        invoker.function_invoker.stop()

    def test_discrete_window(self):

        from itertools import count
        import struct
        import json

        env = function_env('windows.py','discrete_window')

        func, interaction_model = invoker.function_invoker.install_function(env)

        threading.Thread(target=invoker.function_invoker.invoke_function,
                                            args=([func, interaction_model, env])).start()

        channel = grpc.insecure_channel('localhost:%s' % env['GRPC_PORT'])
        testutils.wait_until_channel_ready(channel)

        '''
        unbounded generator of Messages converting int to bytes
        '''
        messages = (message.Message(payload=struct.pack(">I",i), headers = {'Content-Type': message.Message.HeaderValue(values=['application/octet-stream'])}) for i in count())

        responses = function.MessageFunctionStub(channel).Call(messages)

        '''
        Check the first 10 responses. Each message is a json serialized tuple of size 3 containing the next sequence of ints.
        '''
        for i in range(10):
            tpl = json.loads(next(responses).payload)
            self.assertEqual(3, len(tpl))
            for j in range(len(tpl)):
                self.assertEqual(i*3+j, tpl[j])

        invoker.function_invoker.stop()

    def test_discrete_window_text(self):

        from itertools import count
        import json

        env = function_env('windows.py','discrete_window_text')

        func, interaction_model = invoker.function_invoker.install_function(env)

        threading.Thread(target=invoker.function_invoker.invoke_function,
                                            args=([func, interaction_model, env])).start()

        channel = grpc.insecure_channel('localhost:%s' % env['GRPC_PORT'])
        testutils.wait_until_channel_ready(channel)

        '''
        unbounded generator of Messages converting int to bytes
        '''
        messages = (message.Message(payload=bytes("X%d" % i,'UTF-8') , headers = {'Content-Type': message.Message.HeaderValue(values=['text/plain'])}) for i in count())

        responses = function.MessageFunctionStub(channel).Call(messages)

        '''
        Check the first 10 responses. Each message is a json serialized tuple of size 3 containing the next sequence of ints.
        '''
        for _ in range(10):
            tpl = json.loads(next(responses).payload)

        invoker.function_invoker.stop()

    def test_sliding_window(self):
        from itertools import count
        import struct
        import json

        env = function_env('windows.py','sliding_window')

        func, interaction_model = invoker.function_invoker.install_function(env)

        threading.Thread(target=invoker.function_invoker.invoke_function,
                                            args=([func, interaction_model, env])).start()

        channel = grpc.insecure_channel('localhost:%s' % env['GRPC_PORT'])
        testutils.wait_until_channel_ready(channel)

        '''
        unbounded generator of Messages converting int to bytes
        '''
        messages = (message.Message(payload=struct.pack(">I",i), headers = {'Content-Type': message.Message.HeaderValue(values=['application/octet-stream'])}) for i in count())

        responses = function.MessageFunctionStub(channel).Call(messages)

        '''
        Check the first 10 responses. Each message is a json serialized tuple of size 3 containing the next sequence 
        of ints: ((0,1,2),(1,2,3),(2,3,4))
        '''
        for i in range(10):
            tpl = json.loads(next(responses).payload)
            self.assertEqual(3, len(tpl))
            for j in range(len(tpl)):
                self.assertEqual(i+j, tpl[j])

        invoker.function_invoker.stop()
    

    def test_source(self):
        env = function_env('streamer.py','source')

        func, interaction_model = invoker.function_invoker.install_function(env)

        threading.Thread(target=invoker.function_invoker.invoke_function,
                                            args=([func, interaction_model, env])).start()

        channel = grpc.insecure_channel('localhost:%s' % env['GRPC_PORT'])
        testutils.wait_until_channel_ready(channel)

        def messages():
            yield message.Message()

        responses = function.MessageFunctionStub(channel).Call(messages())

        for i in range(10):
            self.assertEqual(bytes(str(i),'utf-8'),  next(responses).payload)
        
        invoker.function_invoker.stop()
    
    def test_zip(self):
        env = {
            'FUNCTION_URI' : 'file://%s/tests/zip/myfunc.zip?handler=func.handler' % os.getcwd(),
            'GRPC_PORT': testutils.find_free_port()
        }
        func, interaction_model = invoker.function_invoker.install_function(env)
        self.assertEqual('HELLO',func('hello'))
        os.remove('func.py')
        os.remove('helpers.py')
        self.assertEqual('handler',func.__name__)


def function_env(module,handler):
    return {
        'FUNCTION_URI': 'file://%s/tests/functions/%s?handler=%s' % (os.getcwd(),module,handler),
        'GRPC_PORT': testutils.find_free_port()
    }