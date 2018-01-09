
def pathify(src, root="", separator="/"):
    for (k, v) in src.iteritems():
        topic = separator.join((root, k))
        if type(v)==dict:
            for i in pathify(v, topic, separator):
                yield i
        else:
            yield (topic, v)


def changes(old, new):
    old_k=set(old.keys())
    new_k=set(new.keys())

    _ret = {}
    for k in (new_k-old_k):
        _ret[k] = new[k]
    for k in (old_k-new_k):
        _ret[k] = None
    for k in old_k.intersection(new_k):
        if type(old[k])!=type(new[k]):
            _ret[k] = new[k]
        if type(new[k])==dict:
            inner = changes(old[k], new[k])
            if inner:
                _ret[k] = inner
        elif old[k] != new[k]:
            _ret[k] = new[k]
    return _ret


def merge(iterator):
    tgt = {}
    for i in iterator:
        tgt.update(i)
    return tgt
