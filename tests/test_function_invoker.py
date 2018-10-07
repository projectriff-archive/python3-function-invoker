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

import unittest
import os

sys.path.append('invoker')
sys.path.append('tests/functions')

import invoker.function_invoker


class FunctionInvokerTest(unittest.TestCase):
    """
    Loads a function in memory for testing. Easier for debugging
    Assumes os.getcwd() is the project base directory
    """

    def test_upper(self):
        env = function_env('upper.py', 'handle')

        function_invoker = invoker.function_invoker.install_function(env)
        self.assertEqual('handle', function_invoker.name)

        def generate_messages():
            messages = [
                "hello",
                "world",
                "foo",
                "bar",
            ]

            for msg in messages:
                yield msg

        responses = function_invoker.invoke(generate_messages())
        expected = ["HELLO", "WORLD", "FOO", "BAR"]

        for response in responses:
            self.assertTrue(response in expected)
            expected.remove(response)

        self.assertEqual(0, len(expected))

    def test_bidirectional(self):
        env = function_env('streamer.py', 'bidirectional')
        function_invoker = invoker.function_invoker.install_function(env)
        self.assertEqual('bidirectional', function_invoker.name)

        def generate_messages():
            messages = [
                "foo",
                "bar",
                "baz",
                "faz",
            ]
            for msg in messages:
                yield msg

        responses = function_invoker.invoke(generate_messages())
        expected = ["FOO", "BAR", "BAZ", "FAZ"]

        for response in responses:
            self.assertTrue(response in expected)
            expected.remove(response)

        self.assertEqual(0, len(expected))

    def test_filter(self):
        env = function_env('streamer.py', 'filter')

        function_invoker = invoker.function_invoker.install_function(env)
        self.assertEqual('filter', function_invoker.name)

        def generate_messages():
            messages = [
                "foo",
                "bar",
                "foobar",
            ]
            for msg in messages:
                yield msg

        responses = function_invoker.invoke(generate_messages())
        expected = ["foo", "foobar"]

        for response in responses:
            self.assertTrue(response in expected)
            expected.remove(response)

        self.assertEqual(0, len(expected))

    def test_discrete_window(self):

        from itertools import count
        import struct
        import json

        env = function_env('windows.py', 'discrete_window')

        function_invoker = invoker.function_invoker.install_function(env)

        '''
        unbounded generator of int
        '''
        messages = (struct.pack(">I", i) for i in count())

        responses = function_invoker.invoke(messages)

        '''
        Check the first 10 responses. Each message is a json serialized tuple of size 3 containing the next sequence of ints.
        '''
        for i in range(10):
            tpl = json.loads(next(responses))
            self.assertEqual(3, len(tpl))
            for j in range(len(tpl)):
                self.assertEqual(i * 3 + j, tpl[j])

    def test_sliding_window(self):

        from itertools import count
        import struct
        import json

        env = function_env('windows.py','sliding_window')

        function_invoker = invoker.function_invoker.install_function(env)

        '''
        unbounded generator of int
        '''
        messages = (struct.pack(">I", i) for i in count())

        responses = function_invoker.invoke(messages)

        '''
        Check the first 10 responses. Each message is a json serialized tuple of size 3 containing the next sequence 
        of ints: ((0,1,2),(1,2,3),(2,3,4))
        '''
        for i in range(10):
            tpl = json.loads(next(responses))
            self.assertEqual(3, len(tpl))
            for j in range(len(tpl)):
                self.assertEqual(i + j, tpl[j])

    def test_source(self):
        env = function_env('streamer.py', 'source')

        function_invoker = invoker.function_invoker.install_function(env)

        def messages():
            yield

        responses = function_invoker.invoke(messages())

        for i in range(10):
            self.assertEqual(str(i), next(responses))

    def test_zip(self):
        env = {
            'FUNCTION_URI': 'file://%s/tests/zip/myfunc.zip?handler=func.handler' % os.getcwd()
        }
        function_invoker = invoker.function_invoker.install_function(env)

        generator = (message for message in ["hello"])

        self.assertEqual('HELLO', next(function_invoker.invoke(generator)))
        os.remove('func.py')
        os.remove('helpers.py')
        self.assertEqual('handler', function_invoker.name)


def function_env(module, handler):
    return {
        'FUNCTION_URI': 'file://%s/tests/functions/%s?handler=%s' % (os.getcwd(), module, handler),
    }
