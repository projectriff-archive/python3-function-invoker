from itertools import tee
import json

interaction_model = 'stream'

def sliding(stream):
    window_size=3
    """
    Adapted from https://stackoverflow.com/questions/6822725/rolling-or-sliding-window-iterator
    The zip function merges the next element from each generator in the list into tuples. The output is a stream of tuples.
    Each tuple is serialized as json
    """

    iters = tee(stream, window_size)
    '''
    iters = (count(),count(),count())
    '''

    '''
    consume first i elements 
    '''
    for i in range(1, window_size):
        for each in iters[i:]:
            next(each)

    '''
    (0,1,2,3,4,5,...)
    (1,2,3,4,5,...)
    (2,3,4,5,...)
    '''
    return (json.dumps(tpl) for tpl in zip(*iters))
    
