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

import collections

def concat(vals):
    '''
    :param vals: expects a dict
    :return: a singleton dict whose value is concatenated keys and values
    '''
    od = collections.OrderedDict(sorted(vals.items()))
    result = ''
    for k, v in od.items():
        result = result + k + v
    return {'result': result}

