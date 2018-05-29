import json
interaction_model = 'stream'

def simple(window):
    return (lst for lst in [json.dumps(list(window))])
