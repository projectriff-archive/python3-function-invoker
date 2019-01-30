import sys
from urllib.error import HTTPError
from tests.utils import testutils
from threading import Thread

import unittest
import os
import urllib.request
import time

PYTHONPATH = ['invoker', '%s/tests/functions' % os.getcwd(), '%s/invoker' % os.getcwd()]
for p in PYTHONPATH:
    sys.path.append(p)

from invoker import function_invoker


# PYTHON = sys.executable


class HttpFunctionTest(unittest.TestCase):
    """
    Spawns function_invoker in a separate thread.
    Assumes os.getcwd() is the project base directory
    """

    def setUp(self):
        self.port = testutils.find_free_port()

    def tearDown(self):
        function_invoker.stop()

    def test_upper(self):
        run_function(port=self.port, module="upper.py", handler="handle")

        def generate_messages():
            messages = [
                "hello",
                "world",
                "foo",
                "bar",
            ]
            for msg in messages:
                yield msg

        responses = call_multiple_http_messages(self.port, generate_messages())
        expected = [b'HELLO', b'WORLD', b'FOO', b'BAR']

        for response in responses:
            r = response.read()
            self.assertTrue(r in expected)

        self.assertEqual(len(responses), len(expected))

        function_invoker.stop()

    def test_bidirectional_stream(self):
        run_function(port=self.port, module="streamer.py", handler="bidirectional")

        def generate_messages():
            messages = [
                "hello",
                "world",
                "foo",
                "bar",
            ]
            for msg in messages:
                yield msg

        responses = call_multiple_http_messages(self.port, generate_messages(),{'correlationId':'1234'})
        expected = [b'HELLO', b'WORLD', b'FOO', b'BAR']

        for response in responses:
            r = response.read()
            self.assertTrue(r in expected)
            self.assertEqual(response.getheader('correlationId'),'1234')

        self.assertEqual(len(responses), len(expected))

    def test_window(self):
        run_function(port=self.port, module="windows.py", handler="discrete_window_text")

        responses = call_multiple_http_messages(self.port, ("%d" % i for i in range(12)))
        expected = [b'["0", "1", "2"]', b'["3", "4", "5"]', b'["6", "7", "8"]', b'["9", "10", "11"]']

        for response in responses:
            r = response.read()
            if len(r):
                self.assertTrue(r in expected)

    def test_json_processing(self):
        run_function(port=self.port, module="concat.py", handler="concat")

        response = call_http(port=self.port, message='{"foo":"bar","hello":"world"}', headers={'Content-Type':'application/json'})

        self.assertEqual(b'{"result": "foobarhelloworld"}', response.read())

    def test_error_handling(self):
        run_function(port=self.port, module="error.py", handler="nogood")

        try:
            call_http(port=self.port, message='{"foo":"bar"}', headers={'Content_Type':"application/json"})
            raise AssertionError("Error expected for HTTP call")
        except HTTPError as e:
            response = e.read().decode("utf-8")

        self.assertRegex(response, "Error Invoking Function:")
        self.assertRegex(response, "Error thrown by Function")


def call_http(port, message, headers):
    url = 'http://localhost:' + str(port)

    req = urllib.request.Request(url, message.encode(), method="POST", headers=headers)
    return urllib.request.urlopen(req)


def call_multiple_http_messages(port, messages, headers={}):
    return [call_http(port, message,headers) for message in messages]


def run_function(port, module, handler):
    fi = function_invoker.install_function(function_env(port, module, handler))

    thread = Thread(target=function_invoker.run, args=(fi, {"PORT": port}))
    thread.start()
    time.sleep(1)
    return thread


def function_env(port, module, handler):
    return {
        'FUNCTION_URI': 'file://%s/tests/functions/%s?handler=%s' % (os.getcwd(), module, handler),
    }
