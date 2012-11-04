import itertools
from linear_system import LinVar, LinEq, LinSys, FreeVar, BinExpr
import pygtk
pygtk.require('2.0')
import gtk
gtk.widget_set_default_direction(gtk.TEXT_DIR_LTR)


class BaseModel(object):
    _counter = itertools.count()
    ATTRS = {}
    def __init__(self, children, **attrs):
        self.id = self._counter.next()
        self.attrs = {"width" : None, "height" : None}
        self.attrs.update(self.ATTRS)
        self[attrs]
        self.children = children
        self.width = LinVar("_w%d" % (self.id,), self, "user")
        self.height = LinVar("_h%d" % (self.id,), self, "user")
        if self.attrs["width"] is None:
            self.attrs["width"] = self.width
        if self.attrs["height"] is None:
            self.attrs["height"] = self.height

    def __repr__(self):
        attrs = ", ".join(sorted("%s = %r" % (k, v) for k, v in self.attrs.items()))
        children = ", ".join(repr(child) for child in self.children)
        text = self.__class__.__name__
        if children:
            text += "(" + children + ")"
        if attrs:
            text += "[" + attrs + "]"
        return text
    
    #
    # DSL
    #
    def __getitem__(self, attrs):
        for k, v in attrs.items():
            if k not in self.attrs:
                raise KeyError("Unknown attribute %r" % (k,))
            self.attrs[k] = v
    def X(self, w, h):
        if w is not None:
            self.attrs["width"] = w
        if h is not None:
            self.attrs["height"] = h
        return self
    def __neg__(self):
        return self
    def __sub__(self, other):
        return VLayoutModel.combine(self, other)
    def __or__(self, other):
        return HLayoutModel.combine(self, other)

    #
    # constraints
    #
    def get_constraints(self):
        yield LinEq(self.width, self.attrs["width"])
        yield LinEq(self.height, self.attrs["height"])
        for child in self.children:
            for cons in child.get_constraints():
                yield cons


class BaseLayoutModel(BaseModel):
    def __init__(self, children, **attrs):
        BaseModel.__init__(self, children, **attrs)
        self._scroller = LinVar("_s%d" % (self.id), self, "padding")

    def _get_padder(self, child):
        return LinVar("_p%d" % (child.id,), self, "padding")
    def _get_offset(self, child):
        return LinVar("_o%d" % (child.id,), self, "offset")

    @classmethod
    def combine(cls, lhs, rhs):
        if isinstance(lhs, cls) and isinstance(rhs, cls):
            lhs.children.extend(rhs.children)
            return lhs
        elif isinstance(lhs, cls):
            lhs.children.append(rhs)
            return lhs
        elif isinstance(rhs, cls):
            rhs.children.insert(0, lhs)
            return rhs
        else:
            return cls([lhs, rhs])

class HLayoutModel(BaseLayoutModel):
    def get_constraints(self):
        for cons in BaseLayoutModel.get_constraints(self):
            yield cons
        yield LinEq(self.width, sum(child.width for child in self.children) + self._scroller)
        for i, child in enumerate(self.children):
            yield LinEq(child.height + self._get_padder(child), self.attrs["height"])
            yield LinEq(self._get_offset(child), sum(child.width for child in self.children[:i]))

class VLayoutModel(BaseLayoutModel):
    pass

class AtomModel(BaseModel):
    def __init__(self, **attrs):
        BaseModel.__init__(self, (), **attrs)

class Label(AtomModel):
    ATTRS = {"text" : ""}





if __name__ == "__main__":
    root = (Label(text = "hello").X(None, 50) | Label(text = "world").X(None, 50)).X(200,60)
    print list(root.get_constraints())













