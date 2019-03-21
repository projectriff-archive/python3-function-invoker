__copyright__ = '''
Copyright 2019 the original author or authors.

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       https://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
'''

import gevent
import json
from gevent.queue import Queue, Empty
from gevent.pywsgi import WSGIServer

SERVER = None
CORRELATION_ID_HEADER = 'correlationId'


def run(function_invoker, port):
    output_channel = Queue(maxsize=50)
    input_channel = Queue(maxsize=50)

    gevent.spawn(function_invoker.invoke_async, input_channel, output_channel)

    def invoke(environ, start_response):

        body = parse_function_arguments(environ)
        input_channel.put(body, timeout=30)

        status = '200 OK'

        contenttype = content_type(environ)
        headers = [
            ('Content-Type', contenttype)
        ]

        correlationid = http_header(CORRELATION_ID_HEADER, environ)
        if correlationid is not None:
            headers.append((CORRELATION_ID_HEADER, correlationid))

        start_response(status, headers)

        try:
            # yield to spawned greenlet
            gevent.sleep()
            val = output_channel.get_nowait()
            if val == StopIteration:
                return
            elif isinstance(val, Exception):
                start_response('500 INTERNAL SERVER ERROR', [('Content-Type', 'text/plain')])
                yield response("Error Invoking Function: " + repr(val), 'text/plain')
            else:
                yield response(val, contenttype)
        except Empty:
            return

    global SERVER
    options = None
    SERVER = WSGIServer(('', port), application=invoke)  # , log=None)
    SERVER.serve_forever()


def http_header(name, env):
    key = "HTTP_%s" % name.upper()
    return env.get(key, None)


def stop():
    global SERVER
    SERVER.stop()


def content_type(env):
    return env.get('CONTENT_TYPE', 'application/json')


# When the method is POST the variable will be sent
# in the HTTP request body which is passed by the WSGI server
# in the 'wsgi.input' environment variable.
def parse_function_arguments(env):
    body = env['wsgi.input'].read().decode()
    if content_type(env).startswith('application/json'):
        return json.loads(body)
    return body


def response(val, contenttype):
    if type(val) == dict and contenttype.startswith('application/json'):
        resp = json.dumps(val)
    else:
        resp = val
    return bytearray(resp, 'UTF-8')
