from collections.abc import MutableSequence, Mapping

def rec_truncate(obj, maxlen=79):
    if isinstance(obj, str) and len(obj) > maxlen:
        return obj[:maxlen] + "..."
    if isinstance(obj, bytes) and len(obj) > maxlen:
        return obj[:maxlen] + b"..."
    if isinstance(obj, Mapping):
        return {rec_truncate(k, maxlen): rec_truncate(v, maxlen)
                for k, v in obj.items()}
    if isinstance(obj, MutableSequence):
        return type(obj)(rec_truncate(e, maxlen) for e in obj)
    return obj
