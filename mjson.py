try:
    import orjson as json

    tp = True
except ImportError:
    import ujson as json
    tp = False

def loads(obj):
    if tp:
        return json.loads(obj)
    else:
        return json.loads(obj)


def load(fp):
    if tp:
        return json.load(fp)
    else:
        return json.load(fp)


def dumps(obj):
    if tp:
        return json.dumps(obj).decode("utf-8")
    else:
        return json.dumps(obj)


def dump(fp):
    if tp:
        return json.loads(fp).decode("utf-8")
    else:
        return json.loads(fp)
