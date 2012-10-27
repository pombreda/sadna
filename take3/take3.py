import itertools
import pygtk
pygtk.require('2.0')
import gtk
gtk.widget_set_default_direction(gtk.TEXT_DIR_LTR)

from linear import LinVar, LinEq, LinSys, NoSolutionsExist

class HardLinEq(LinEq):
    pass
class SoftLinEq(LinEq):
    def __init__(self, lhs, rhs, resolver):
        self.lhs = lhs
        self.rhs = rhs
        self.resolver = resolver
    def __repr__(self):
        return "! %s" % (LinEq.__repr__(self),)
    def resolve(self, prev_sol):
        return self.resolver(self, prev_sol)


class UIElement(object):
    _counter = itertools.count()
    def __init__(self, **attrs):
        self.attrs = attrs
        self.id = self._counter.next()
        self.w = LinVar("w%d" % (self.id,))
        self.h = LinVar("h%d" % (self.id,))
        self.w.owner = self
        self.h.owner = self
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
            yield HardLinEq(self.w, self.attrs["w_constraint"])
        if self.attrs["h_constraint"]:
            yield HardLinEq(self.h, self.attrs["h_constraint"])
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
        yield SoftLinEq(sum(e.w for e in self.elems), self.w, self._resolve_width)
        for e in self.elems:
            hp = LinVar("hp%d" % (e.id,))
            #hp.owner = self
            yield SoftLinEq(e.h + hp, self.h, self._resolve_height)
    
    def _resolve_width(self, equation, prev_sol):
        1/0
    def _resolve_height(self, equation, prev_sol):
        1/0
    
    def get_widget(self):
        return gtk.Scrolled()


class Ver(Layout):
    pass

class Atom(UIElement):
    pass
class Label(Atom):
    pass
class Button(Atom):
    pass

#def run(root):
#    window = gtk.Window(gtk.WINDOW_TOPLEVEL)
#    window.set_title("Untitled")
#    window.connect("delete_event", lambda *args: False)
#    window.connect("destroy", lambda *args: gtk.main_quit())
#    w = LinVar("window_width")
#    h = LinVar("window_height")
#    root.X(w, h)
    

x = LinVar("x")
main = (Label(text = "foo").X(50,50) | Label(text = "bar").X(50,50) | Label(text = "spam").X(50,60)).X(None,60)


def unify(root):
    constraints = list(root.get_constraints())
    required = [cons for cons in constraints if isinstance(cons, HardLinEq)]
    desired = [cons for cons in constraints if isinstance(cons, SoftLinEq)]
    linsys = LinSys(required)
    # if this fails - the user made a booboo
    sol = linsys.solve()

    # make sure to add these last, so they'd be free vars. if they turn out bound, the window 
    # must be non-resizable
    w = LinVar("WW")
    h = LinVar("WH")
    #if not root.attrs["w_constraint"]:
    desired.append(SoftLinEq(root.w, w, None))
    #if not root.attrs["h_constraint"]:
    desired.append(SoftLinEq(root.h, h, None))

    for cons in desired:
        linsys.append(cons)
        try:
            sol = linsys.solve()
        except NoSolutionsExist:
            del linsys[-1]
            linsys.extend(cons.resolve(sol))
            sol = linsys.solve()
    
    return sol


print unify(main)





