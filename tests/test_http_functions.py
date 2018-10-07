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

    @classmethod
    def setUpClass(cls):
        cls.workingdir = os.path.abspath("./invoker")
        cls.command = "%s function_invoker.py" % PYTHON
        cls.PYTHONPATH = '%s:%s' % ('%s/tests/functions:$PYTHONPATH' % os.getcwd(), '%s/invoker' % os.getcwd())

    def tearDown(self):
        os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
        self.process.wait()

    def test_upper(self):
        port = testutils.find_free_port()

        env = {
            'PYTHONPATH': self.PYTHONPATH,
            'PORT': str(port),
            'FUNCTION_URI': 'file://%s/tests/functions/upper.py?handler=handle' % os.getcwd()
        }

        self.process = subprocess.Popen(self.command,
                                        cwd=self.workingdir,
                                        shell=True,
                                        env=env,
                                        preexec_fn=os.setsid,
                                        )

        def generate_messages():
            messages = [
                ("hello", 'UTF-8'),
                ("world", 'UTF-8'),
                ("foo", 'UTF-8'),
                ("bar", 'UTF-8'),
            ]
            for msg in messages:
                yield msg

        responses = self.call_multiple_http_messages(port, generate_messages())
        expected = [b'HELLO', b'WORLD', b'FOO', b'BAR']

        for response in responses:
            self.assertTrue(response in expected)

        self.assertEqual(len(responses), len(expected))

    def call_http(self, port, message):
        url = 'http://localhost:' + str(port)

        req = urllib.request.Request(url, message.encode(), method="POST", headers={"content-type": "text/plain"})
        response = urllib.request.urlopen(req)
        return response.read()

    def call_multiple_http_messages(self, port, messages):
        time.sleep(1)
        return [self.call_http(port, message[0]) for message in messages]
