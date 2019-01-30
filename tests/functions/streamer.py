interaction_model = "stream"


def bidirectional(stream):
    return (item.upper() for item in stream)


def filter(stream):
    return (item for item in stream if "foo" in item)

def source():
    from itertools import count
    return(str(item) for item in count())

