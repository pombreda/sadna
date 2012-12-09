class GUIError(Exception):
    pass

class UIModel(object):
    def generate_model(self):
        raise NotImplementedError()

class ArgModel(UIModel):
    def __init__(self, argname, displayname = None, default = NotImplemented):
        self.argname = argname
        self.displayname = displayname if displayname else argname
        self.default = default

class StrArgModel(ArgModel):
    pass
class PasswordArgModel(StrArgModel):
    pass
class IntArgModel(ArgModel):
    pass

def FuncModel(args, displayname):
    class FuncModelCls(UIModel):
        def __init__(self, func):
            self.args = args
            self.func = func
            self.displayname = displayname if displayname else func.__name__
        def __call__(self, *args, **kwargs):
            return self.func(*args, **kwargs)
        def generate_model(self):
            if not self.args:
                return Button(text = self.displayname)
            elif len(self.args) == 1:
                a = self.args[0]
                return ((Label(text = a.displayname) | a.generate_model()) 
                    if a.displayname else a.generate_model()) | Button(text = self.displayname)
            else:
                w = None
                return (VLayout.foreach(
                    (Label(text = a).X(w, None) | a.generate_model()) for a in self.args) --- 
                     Padding().X(w, None) | Button(text = self.displayname))
    return FuncModelCls

class ClassModel(UIModel):
    @classmethod
    def run(cls):
        if isinstance(cls.__init__, UIModel):
            kwargs = run_ui(cls.__init__.generate_model())
            inst = cls(**kwargs)
        else:
            inst = cls()
        return run_ui(inst.generate_model())


class PropertyModel(UIModel):
    class __metaclass__(type):
        def __new__(cls, name, bases, env):
            if env.get("DELEGATEE"):
                for n in env.get("NOTIFIED_METHODS"):
                    exec("""def %(method)s(self, *args):
                                res = self.%(delegatee)s.%(method)s(*args)
                                self._notify()
                                return res""" % {"method" : n, "delegatee" : env["DELEGATEE"]}, 
                            env)
                for n in env.get("DELEGATED_METHODS"):
                    exec("""def %(method)s(self, *args):
                                return self.%(delegatee)s.%(method)s(*args)""" % {
                                    "method" : n, "delegatee" : env["DELEGATEE"]}, 
                            env)
            return type.__new__(cls, name, bases, env)
    def __init__(self, displayname):
        self._displayname = displayname
        self._watchers = []
    def watch(self, callback):
        self._watchers.append(callback)
    def _notify(self):
        for callback in self._watchers:
            callback(self)

class ListPropertyModel(PropertyModel):
    DELEGATEE = "_items"
    NOTIFIED_METHODS = ["append", "extend", "insert", "remove", "reverse", "sort", "pop", 
        "__setitem__", "__delitem__", "__delslice__", "__setslice__", "__iadd__", "__imul__"]
    DELEGATED_METHODS = ['__add__', '__contains__', '__eq__', '__format__', '__ge__', 
        '__getitem__', '__getslice__', '__gt__', '__hash__', '__iter__', '__le__', '__len__', 
        '__lt__', '__mul__', '__ne__', '__repr__', '__reversed__', '__rmul__', 'count', 'index']
    def __init__(self, displayname):
        PropertyModel.__init__(self, displayname)
        self._items = []
    def generate_model(self):
        v = None
        v.when_changed
        return ListAtom(selected = v, items = None)







