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
import socket
from contextlib import closing
import time


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