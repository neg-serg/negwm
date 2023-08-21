class bindmap(list):
    def __init__(*args, **kw):
        if not args:
            raise TypeError("descriptor '__init__' of 'WeakValueDictionary' "
                            "object needs an argument")
        self = args[0]
        args = args[1:]
        if len(args) > 1:
            raise TypeError('expected at most 1 arguments, got %d' % len(args))
        setattr(self, 'bind', kw.get('bind', ''))
        setattr(self, 'name', kw.get('name', ''))
        list.__init__(self, *args)
