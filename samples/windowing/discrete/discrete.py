from itertools import zip_longest
import json

interaction_model = 'stream'

def discrete(stream):
    window_size=3
    """
    Adapted from https://mail.python.org/pipermail/python-ideas/2013-December/024492.html
    First create a list of generators of len(window_size)
    The zip function merges the next element from each generator in the list into tuples. The output is a stream of tuples 
    ((0,1,2),(3,4,5),(6,7,8),...) . Each tuple is serialized as json.    
    """

    repeated_iterable = [stream] * window_size
    return (json.dumps(tpl) for tpl in zip_longest(*repeated_iterable, fillvalue=None))




