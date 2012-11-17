import itertools
from linsys import LinVar, LinEq


def Default(value):
    return LinVar("_d%d" % (BaseModel._counter.next()), None, "user", default = value)

class BaseModel(object):
    ATTRS = {}
    _counter = itertools.count()
    def __init__(self, **attrs):
        self.id = self._counter.next()
        self.width = LinVar("_w%d" % (self.id,), self, "cons")
        self.height = LinVar("_h%d" % (self.id,), self, "cons")
        self.observed = {}
        self.bound_funcs = {}
        self.attrs = self.ATTRS.copy()
        self.attrs["width"] = None
        self.attrs["height"] = None
        for k, v in attrs.items():
            if k not in self.attrs:
                raise TypeError("invalid attribute %r for %s" % (k, self.__class__.__name__))
            self.attrs[k] = v
        if self.attrs["width"] is None:
            self.attrs["width"] = self.width
        if self.attrs["height"] is None:
            self.attrs["height"] = self.height

    def get_constraints(self):
        yield LinEq(self.width, self.attrs["width"])
        yield LinEq(self.height, self.attrs["height"])

    def flash(self, attrname):
        self.set(attrname, 1)
        self.set(attrname, 0)
    
    def invoke_observers(self):
        for attrname, callbacks in self.observed.items():
            val = self.attrs.get(attrname, None)
            for cb in callbacks:
                cb(val)

    #
    # User API
    #
    def when_changed(self, attrname, callback):
        if attrname not in self.observed:
            self.observed[attrname] = []
        self.observed[attrname].append(callback)
    
    def set(self, attrname, value):
        if value != self.attrs.get(attrname, NotImplemented):
            self.attrs[attrname] = value
            for cb in self.observed.get(attrname, ()):
                cb(value)

    def bind(self, name, callback):
        self.bound_funcs[name] = callback

class ContainerModel(BaseModel):
    ATTRS = {"title" : "Untitled"}
    def __init__(self, children, **attrs):
        BaseModel.__init__(self, **attrs)
        self.children = children

    def get_constraints(self):
        for cons in BaseModel.get_constraints(self):
            yield cons
        for child in self.children:
            for cons in child.get_constraints():
                yield cons

class WindowModel(ContainerModel):
    def __init__(self, child, **attrs):
        ContainerModel.__init__(self, [child], **attrs)

    def get_constraints(self):
        for cons in ContainerModel.get_constraints(self):
            yield cons
        yield LinEq(self.width, self.children[0].width)
        yield LinEq(self.height, self.children[0].height)

class LayoutModel(ContainerModel):
    ATTRS = {"title" : "Untitled"}
    def __init__(self, children, **attrs):
        ContainerModel.__init__(self, children, **attrs)
        self._scroller = LinVar("_s%d" % (self.id), self, "padding")
        self._total = LinVar("_t%d" % (self.id), self, "cons")

    def _get_padder(self, child):
        return LinVar("_p%d" % (child.id,), self, "padding")
    def _get_offset(self, child):
        return LinVar("_o%d" % (child.id,), self, "offset")
    
class Horizontal(LayoutModel):
    def __str__(self):
        return "(%s)[%s]" % (" | ".join(str(child) for child in self.children),
            " ".join("%s=%r" % (k, v) for k, v in self.attrs.items()))
    
    def get_constraints(self):
        for cons in LayoutModel.get_constraints(self):
            yield cons
        yield LinEq(self.width, sum(child.width for child in self.children) + self._scroller)
        offset = 0
        for child in self.children:
            yield LinEq(child.height + self._get_padder(child), self.height)
            yield LinEq(self._get_offset(child), offset)
            offset += child.width
        yield LinEq(self._total, offset)

class Vertical(LayoutModel):
    def __str__(self):
        return "(%s)[%s]" % (" --- ".join(str(child) for child in self.children),
            " ".join("%s=%r" % (k, v) for k, v in self.attrs.items()))

    def get_constraints(self):
        for cons in LayoutModel.get_constraints(self):
            yield cons
        yield LinEq(self.height, sum(child.height for child in self.children) + self._scroller)
        offset = 0
        for child in self.children:
            yield LinEq(child.width + self._get_padder(child), self.width)
            yield LinEq(self._get_offset(child), offset)
            offset += child.height
        yield LinEq(self._total, offset)

class AtomModel(BaseModel):
    def __init__(self, name, **attrs):
        BaseModel.__init__(self, **attrs)
        self.name = name
    def __str__(self):
        return "%s[%s]" % (self.__class__.__name__, 
            " ".join("%s=%r" % (k, v) for k, v in self.attrs.items()))

class LabelAtom(AtomModel):
    ATTRS = {"text" : "", "native_width" : None, "native_height" : None}

class ButtonAtom(AtomModel):
    ATTRS = {"text" : "", "clicked" : 0, "native_width" : None, "native_height" : None}

class ImageAtom(AtomModel):
    ATTRS = {"filename" : "", "native_width" : None, "native_height" : None}
















