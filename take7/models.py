import itertools
from linsys import LinVar, LinEq


#def Default(value):
#    return LinVar("_d%d" % (BaseModel._counter.next()), None, "default", default = value)

class Default(object):
    def __init__(self, value):
        self.value = value

#===================================================================================================
# Computed values
#===================================================================================================
class ComputedValue(object):
    def __call__(self, *args):
        raise NotImplementedError()

class InitValue(ComputedValue):
    def __init__(self, default):
        self.value = default
    def __call__(self, value):
        if value is not NotImplemented:
            self.value = value
        return self.value

class ComputedVar(ComputedValue):
    def __init__(self, linvar):
        self.linvar = linvar
    def __call__(self, solver):
        return solver[self.linvar]

class ComputedExprMixing(ComputedValue):
    def __add__(self, other):
        return ComputedBinExpr(lambda x,y:x+y, self, other)
    def __sub__(self, other):
        return ComputedBinExpr(lambda x,y:x-y, self, other)
    def __mul__(self, other):
        return ComputedBinExpr(lambda x,y:x*y, self, other)
    def __div__(self, other):
        return ComputedBinExpr(lambda x,y:x/y, self, other)

class ComputedUniExpr(ComputedExprMixing):
    def __init__(self, op, subexpr):
        self.op = op
        self.subexpr = subexpr
    def __call__(self):
        return self.op(self.subexpr())

class ComputedBinExpr(ComputedExprMixing):
    def __init__(self, op, lhs, rhs):
        self.op = op
        self.lhs = lhs
        self.rhs = rhs
    def __call__(self):
        return self.op(self.lhs(), self.rhs())

class Target(ComputedValue):
    def __init__(self, name):
        self.name = name
        self._callbacks = []
    def when_changed(self, callback):
        self._callbacks.append(callback)
    def __call__(self, val):
        for cb in self._callbacks:
            cb(val)
        return val




#===================================================================================================
# Models
#===================================================================================================
class BaseModel(object):
    _counter = itertools.count()
    
    def __init__(self, **attrs):
        self.id = self._counter.next()
        self.width_cons = attrs.pop("width", None)
        self.height_cons = attrs.pop("height", None)
        self.width = LinVar("_w%d" % (self.id,), self, "cons")
        self.height = LinVar("_h%d" % (self.id,), self, "cons")
        if isinstance(self.width_cons, Default):
            self.width.default = self.width_cons.value
        if isinstance(self.height_cons, Default):
            self.height.default = self.height_cons.value
        
        self._observed_attrs = {}
        self._attr_values = {}
        self.computed_attrs = {}
        for cls in reversed(type(self).mro()):
            if hasattr(cls, "ATTRS"):
                self.computed_attrs.update(cls.ATTRS)
        for k, v in attrs.items():
            #if k not in self.attrs:
            #    raise TypeError("invalid attribute %r for %s" % (k, self.__class__.__name__))
            if isinstance(v, ComputedValue):
                self.computed_attrs[k] = v
            else:
                self.computed_attrs[k] = InitValue(v)

    def get_constraints(self):
        if self.width_cons is not None:
            yield LinEq(self.width, self.width_cons)
        if self.height_cons is not None:
            yield LinEq(self.height, self.height_cons)

    def flash(self, attrname):
        self.set(attrname, 1)
        self.set(attrname, 0)
    
    def invoke_observers(self):
        for attrname, callbacks in self._observed_attrs.items():
            compattr = self.computed_attrs.get(attrname, None)
            if not compattr:
                continue
            val = compattr(NotImplemented)
            for cb in callbacks:
                cb(val)

    #
    # User API
    #
    def when_changed(self, attrname, callback):
        if attrname not in self._observed_attrs:
            self._observed_attrs[attrname] = []
        self._observed_attrs[attrname].append(callback)
    
    def set(self, attrname, value):
        if attrname not in self.computed_attrs:
            raise ValueError("unknown attribute %r for %s" % (attrname, self.__class__.__name__))
        
        curr = self._attr_values.get(attrname, NotImplemented)
        if value != curr:
            value = self.computed_attrs[attrname](value)
            print ">> set %r, val = %r, curr = %r" % (attrname, value, curr)
            self._attr_values[attrname] = value
            for cb in self._observed_attrs.get(attrname, ()):
                cb(value)

    def bind(self, name, callback):
        raise NotImplementedError()

#===================================================================================================
# Composite models
#===================================================================================================
class ContainerModel(BaseModel):
    def __init__(self, children, **attrs):
        BaseModel.__init__(self, **attrs)
        self.children = children

    def get_constraints(self):
        for cons in BaseModel.get_constraints(self):
            yield cons
        for child in self.children:
            for cons in child.get_constraints():
                yield cons

    def invoke_observers(self):
        for child in self.children:
            child.invoke_observers()
        BaseModel.invoke_observers(self)


class WindowModel(ContainerModel):
    ATTRS = {"title" : InitValue("Untitled"), "closed" : InitValue(0)}
    
    def __init__(self, child, **attrs):
        ContainerModel.__init__(self, [child], **attrs)
        self.child = child
        self.ww = LinVar("WindowWidth", None, "input") #, default = self.child.width.default)
        self.wh = LinVar("WindowHeight", None, "input") #, default = self.child.height.default)

    def get_constraints(self):
        for cons in ContainerModel.get_constraints(self):
            yield cons
        yield LinEq(self.width, self.child.width)
        yield LinEq(self.height, self.child.height)
        yield LinEq(self.width, self.ww)
        yield LinEq(self.height, self.wh)


class LayoutModel(ContainerModel):
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
            " ".join("%s=%r" % (k, v) for k, v in self.computed_attrs.items()))
    
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
            " ".join("%s=%r" % (k, v) for k, v in self.computed_attrs.items()))

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

#===================================================================================================
# Atom models
#===================================================================================================
class AtomModel(BaseModel):
    def __init__(self, **attrs):
        BaseModel.__init__(self, **attrs)
    def __str__(self):
        return "%s[%s]" % (self.__class__.__name__, 
            " ".join("%s=%r" % (k, v) for k, v in self.computed_attrs.items()))

class LabelAtom(AtomModel):
    ATTRS = {"text" : InitValue(""), "valign" : InitValue("top"), "halign" : InitValue("left"), 
        "native_width" : InitValue(None), "native_height" : InitValue(None)}

class ButtonAtom(AtomModel):
    ATTRS = {"text" : InitValue(""), "clicked" : InitValue(0), "native_width" : InitValue(None), 
        "native_height" : InitValue(None)}

class ImageAtom(AtomModel):
    ATTRS = {"image" : InitValue(""), "native_width" : InitValue(None), "native_height" : InitValue(None)}

class LineEditAtom(AtomModel):
    ATTRS = {"text" : InitValue(""), "placeholder" : InitValue(""), "accepted" : InitValue(0)}







