from threading import Lock


class Singleton(object):
    __singleton_lock = Lock()
    __singleton_instance = None

    @classmethod
    def __call__(cls, *args, **kwargs):
        if not cls.__singleton_instance:
            with cls.__singleton_lock:
                if not cls.__singleton_instance:
                    cls.__singleton_instance = \
                        super(Singleton, cls).__call__(*args, **kwargs)
        return cls.__singleton_instance

