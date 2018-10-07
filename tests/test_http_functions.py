import sys

from tests.utils import testutils

import unittest
import subprocess
import os
import signal
import urllib.request
import time

sys.path.append('invoker')

PYTHON = sys.executable


class HttpFunctionTest(unittest.TestCase):
    """
    Spawns function_invoker in a separate process.
    Assumes os.getcwd() is the project base directory
    """

    def tearDown(self):
        os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
        self.process.wait()

    def test_upper(self):
        port = testutils.find_free_port()
        self.process = run_function(port=port, module="upper.py", handler="handle")

        def generate_messages():
            messages = [
                "hello",
                "world",
                "foo",
                "bar",
            ]
            for msg in messages:
                yield msg

        responses = call_multiple_http_messages(port, generate_messages())
        expected = [b'HELLO', b'WORLD', b'FOO', b'BAR']

        for response in responses:
            self.assertTrue(response in expected)

        self.assertEqual(len(responses), len(expected))

    def test_json_processing(self):
        port = testutils.find_free_port()
        self.process = run_function(port=port, module="concat.py", handler="concat")

        response = call_http(port=port, message='{"foo":"bar","hello":"world"}', content_type="application/json")

        self.assertEqual(b'{"result": "foobarhelloworld"}', response)


def call_http(port, message, content_type="text/plain"):
    url = 'http://localhost:' + str(port)

    req = urllib.request.Request(url, message.encode(), method="POST", headers={"content-type": content_type})
    response = urllib.request.urlopen(req)
    return response.read()


def call_multiple_http_messages(port, messages):
    return [call_http(port, message) for message in messages]


def run_function(port, module, handler):
    command = "%s function_invoker.py" % PYTHON
    workingdir = os.path.abspath("./invoker")
    env = function_env(port, module, handler)
    process = subprocess.Popen(command,
                               cwd=workingdir,
                               shell=True,
                               env=env,
                               preexec_fn=os.setsid,
                               )

    time.sleep(1)
    return process


def function_env(port, module, handler):
    return {
        'PYTHONPATH': '%s:%s' % ('%s/tests/functions:$PYTHONPATH' % os.getcwd(), '%s/invoker' % os.getcwd()),
        'PORT': str(port),
        'FUNCTION_URI': 'file://%s/tests/functions/%s?handler=%s' % (os.getcwd(), module, handler),
    }
