def deep_getattr(obj, name):
    names = name.split('.')
    for name in names:
        obj = getattr(obj, name)
    return obj
