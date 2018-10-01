#!/usr/bin/env python
__copyright__ = '''
Copyright 2017 the original author or authors.

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
import os
import zipfile
import importlib
import ntpath
import os.path
from urllib.parse import urlparse
from shutil import copyfile

import grpc_server
import http_server


def invoke_function(func,interaction_model, env):
    """
    Start a gRPC Server to invoke the function
    :param func: the function
    :param interaction_model: indicates interaction model: None is single value parameter and return type, 'stream' indicates input and output are generators
    :param env: a dict containing the runtime environment, usually os.environ
    :return: None
    """

    if env.get("GRPC_PORT") is not None:
        grpc_server.run(func, interaction_model, env.get("GRPC_PORT", 10382))
    else:
        http_server.run(func=func, port=int(env.get("HTTP_PORT", 8080)))


def install_function(env):
    """
    Locate and install the function resources given by the FUNCTION_URI
    :param env:  a dict containing the runtime environment, usually os.environ
    :return: function plus the given interaction_model (from a global variable in the handler module)
    """
    try:
        function_uri = env['FUNCTION_URI']
        url = urlparse(function_uri)
        if url.scheme == 'file':
            if not os.path.isfile(url.path):
                sys.stderr.write("file %s does not exist\n" % url.path)
                exit(1)

            filename, extension = os.path.splitext(url.path)

            if extension == '.zip':
                zip_ref = zipfile.ZipFile(url.path, 'r')
                zip_ref.extractall('.')
                zip_ref.close()
                sys.stdout.write("Files extracted\n")
            elif extension == '.py':
                if not os.path.isfile(url.path):
                    copyfile(url.path, ('./%s' % ntpath.basename(url.path)))

        else:
            sys.stderr.write("scheme %s is not supported\n" % url.scheme)
            exit(1)

        indx = len('handler=')
        if len(url.query) <= indx or url.query[0:indx] != 'handler=':
            sys.stderr.write("FUNCTION_URI missing handler\n")
            exit(1)

        handler = url.query[indx:]
        if extension == '.py' and '.' not in handler:
            func_name = handler
            mod_name = ntpath.basename(filename)
        else:
            mod_name, func_name = handler.rsplit('.', 1)

        mod = importlib.import_module(mod_name)
        return getattr(mod, func_name), getattr(mod, 'interaction_model',None)

    except KeyError:
        sys.stderr.write("required environment variable FUNCTION_URI is missing\n")
        exit(1)


def stop(grace=None):
    """
    Stop the server. Currently used for testing.
    :param grace: A grace period in seconds to wait for termination
    :return: None
    """
    grpc_server.stop(grace)


if __name__ == '__main__':
    func, interaction_model = install_function(os.environ)
    invoke_function(func,interaction_model,os.environ)
