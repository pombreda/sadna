import functools


class ObserableObject(object):
    def __init__(self):
        self._callbacks = []
    def watch(self, callback):
        self._callbacks.append(callback)
    def _notify_watchers(self, *extra):
        for cb in self._callbacks:
            cb(self, *extra)

class ObservableList(ObserableObject):
    def __init__(self, items = ()):
        self.items = list(items)
    def __repr__(self):
        return repr(self.items)
    def append(self, elem):
        self.items.append(elem)
        self._notify_watchers()
    def __setitem__(self, index, elem):
        self.items[index] = elem
        self._notify_watchers()

class UIable(object):
    def get_model(self):
        raise NotImplementedError()

class Param(UIable):
    def __init__(self, name, default):
        self.name = name
        self.default = default
    def get_value(self):
        raise NotImplementedError()

class StrParam(Param):
    def __init__(self, name, default = ""):
        Param.__init__(self, name, default)
        self.lineed = LineEdit(text = default)
    def get_model(self):
        return self.lineed.attrs["text"]
    def get_value(self):
        raise NotImplementedError()

class IntParam(Param):
    def __init__(self, name, default = None, minvalue = 0, maxvalue = 100):
        Param.__init__(self, minvalue if default is None else default)
        self.minvalue = minvalue
        self.maxvalue = maxvalue
        self.slider = Slider(value = self.default)
    def get_value(self):
        return self.slider.attrs["value"]
    def get_model(self):
        return self.slider

class FunctionModel(UIable):
    def __init__(self, func, params):
        self.func = func
        self.params = params
        k = 5
        self.button = Button(text = func.__name__, clicked = k)
        k.watch(self.invoke)
    def get_model(self):
        if not self.params:
            return self.button
        elif len(self.params) == 1:
            return H([self.params[0].get_model(), self.button])
        else:
            return V(
                [p.get_model() for p in self.params] + [H([Padding(), self.button])]
            )
    def invoke(self):
        kwargs = {p.name:p.get_value() for p in self.params}
        self.func(**kwargs)

class WindowModel(UIable):
    pass














