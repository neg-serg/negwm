class keymap(dict):
    def __init__(*args, **kw):
        if not args:
            raise TypeError("descriptor '__init__' of 'WeakValueDictionary' "
                            "object needs an argument")
        self = args[0]
        args = args[1:]
        if len(args) > 1:
            raise TypeError('expected at most 1 arguments, got %d' % len(args))

        setattr(self, 'fmt', kw.get('fmt', ''))
        setattr(self, 'exit', kw.get('exit', False))

        dict.__init__(self, *args, **kw)

        self.pop('fmt', None)
        self.pop('exit', None)


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
        setattr(self, 'pretty_name', kw.get('pretty_name', ''))

        list.__init__(self, *args)
