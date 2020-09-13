import threading


def lock_method(method):

    if getattr(method, '_is_locked', None):
        raise Exception('Method already locked')

    def inner(self, *args, **kwargs):
        with self._lock:
            return method(self, *args, **kwargs)
    
    inner.__name__ = method.__name__
    inner._is_locked = True
    return inner


def make_threadsafe(cls, methodnames, lockfactory):
    init = cls.__init__
    def newinit(self, *args, **kwargs):
        init(self, *args, **kwargs)
        self._lock = lockfactory()
    cls.__init__ = newinit
    for methodname in methodnames:
        old_method = getattr(cls, methodname)
        new_method = lock_method(old_method)
        setattr(cls, methodname, new_method)
    return cls


def lock_collection(methodnames, lockfactory):
    return lambda cls: make_threadsafe(cls, methodnames, lockfactory)

