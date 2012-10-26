import itertools
import pygtk
pygtk.require('2.0')
import gtk
gtk.widget_set_default_direction(gtk.TEXT_DIR_LTR)


class LinearMixin(object):
    def __neg__(self):
        return -1 * self
    def __sub__(self, other):
        return self + (-other)
    def __rsub__(self, other):
        return other + (-self)
    def __add__(self, other):
        return SumExpr(self, other)
    def __radd__(self, other):
        return SumExpr(other, self)
    def __mul__(self, scalar):
        return ScalarExpr(scalar, self)
    def __rmul__(self, scalar):
        return ScalarExpr(scalar, self)
    def __or__(self, other):
        return LinEquation(self, other)
    def __ror__(self, other):
        return LinEquation(other, self)

class Var(LinearMixin):
    def __init__(self, name, owner = None, type = None):
        self.name = name
        self.owner = owner
        self.type = type
    def __repr__(self):
        return self.name

class SumExpr(LinearMixin):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs
    def __repr__(self):
        if self.lhs == 0:
            return str(self.rhs)
        elif self.rhs == 0:
            return str(self.lhs)
        else:
            return "%s + %s" % (self.lhs, self.rhs)

class ScalarExpr(LinearMixin):
    def __init__(self, scalar, var):
        self.scalar = scalar
        self.var = var
    def __repr__(self):
        if self.scalar == 0:
            return "0"
        elif self.scalar == 1:
            return str(self.var)
        elif self.scalar == -1:
            return "-%s" % (self.var,)
        else:
            return "%s%s" % (self.scalar, self.var)

class LinEquation(object):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs
    def __repr__(self):
        return "%s = %s" % (self.lhs, self.rhs)


class UIElement(object):
    _counter = itertools.count()
    def __init__(self, **attrs):
        self.attrs = attrs
        self.id = self._counter.next()
        self.w = Var("w%d" % (self.id,), self, "v")
        self.h = Var("h%d" % (self.id,), self, "h")
        self.attrs["w_constraint"] = None
        self.attrs["h_constraint"] = None
        self.elems = []
    def __repr__(self):
        attrs = ", ".join("%s=%r" % (k.split("_constraint")[0], v) for k, v in self.attrs.items() 
            if not k.endswith("_constraint") or v is not None)
        elems = ", ".join(repr(e) for e in self.elems)
        if attrs and elems:
            return "%s(%s)[%s]" % (self.__class__.__name__, elems, attrs)
        elif attrs:
            return "%s[%s]" % (self.__class__.__name__, attrs)
        else:
            return "%s(%s)" % (self.__class__.__name__, elems)
                
    def __getitem__(self, attrs):
        self.attrs.update(attrs)
    def __or__(self, other):
        return Hor.combine(self, other)
    def __sub__(self, other):
        return Ver.combine(self, other)
    def __neg__(self):
        return self
    def X(self, w = None, h = None):
        self.attrs["w_constraint"] = w
        self.attrs["h_constraint"] = h
        return self
    def get_constraints(self):
        if self.attrs["w_constraint"]:
            yield self.w | self.attrs["w_constraint"]
        if self.attrs["h_constraint"]:
            yield self.h | self.attrs["h_constraint"]
        for e in self.elems:
            for cons in e.get_constraints():
                yield cons

class Layout(UIElement):
    DIR = None
    
    def __init__(self, elems):
        UIElement.__init__(self)
        self.elems = elems
    
    @classmethod
    def combine(cls, lhs, rhs):
        if isinstance(lhs, cls):
            if isinstance(rhs, cls):
                lhs.elems.extend(rhs.elems)
                return lhs
            else:
                lhs.elems.append(rhs)
                return lhs
        elif isinstance(rhs, cls):
            rhs.insert(0, lhs)
            return rhs
        else:
            return cls([lhs, rhs])


class Hor(Layout):
    def get_constraints(self):
        for cons in Layout.get_constraints(self):
            yield cons
        yield LinEquation(sum(e.w for e in self.elems), self.w, self.resolve)
        for e in self.elems:
            yield LinEquation(e.h, self.h, self.resolve)
    
    def resolve(self):
        pass


class Ver(Layout):
    pass

class Atom(UIElement):
    pass
class Label(Atom):
    pass
class Button(Atom):
    pass

def run(root):
    window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    window.set_title("Untitled")
    window.connect("delete_event", lambda *args: False)
    window.connect("destroy", lambda *args: gtk.main_quit())
    w = Var("window_width")
    h = Var("window_height")
    root.X(w, h)
    

x = Var("x")
main = (Label(text = "foo").X(x,None) | Label(text = "bar").X(x,None)) 

print list(main.get_constraints())

















