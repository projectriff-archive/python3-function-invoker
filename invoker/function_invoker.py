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

import http_server


def run(function_invoker, env):
    """
    Start an http Server to serve the function
    :param function_invoker: a function object that can be invoked with invoke()
    :param env: a dict containing the runtime environment, usually os.environ
    :return: None
    """

    port = int(env.get("PORT", 8080))
    http_server.run(function_invoker=function_invoker, port=port)


class FunctionInvoker(object):
    """The Function Invoker provides an object for calling functions
    """

    def __init__(self, func, interaction_model):
        """
        :param: func callable function
        :param interaction_model function's interaction model request_response or stream
        """
        self.interaction_model = interaction_model
        self.func = func

    @property
    def name(self):
        return self.func.__name__

    def invoke(self, iterator):
        """invoke the function"""

        if is_source(self.func):
            return self.func()
        elif self.interaction_model == "stream":
            return self.func(iterator)
        else:
            return (self.func(arg) for arg in iterator)


def install_function(env):
    """
    Locate and install the function resources given by the FUNCTION_URI
    :param env:  a dict containing the runtime environment, usually os.environ
    :return: a function invoker object that can invoke functions
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
        return FunctionInvoker(getattr(mod, func_name), getattr(mod, 'interaction_model', None))

    except KeyError:
        sys.stderr.write("required environment variable FUNCTION_URI is missing\n")
        exit(1)

def is_source(func):
    return func.__code__.co_argcount == 0

if __name__ == '__main__':
    function_invoker = install_function(os.environ)
    run(function_invoker, os.environ)
