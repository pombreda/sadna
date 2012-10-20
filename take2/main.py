import pygtk
pygtk.require('2.0')
import gtk
import gobject

gtk.widget_set_default_direction(gtk.TEXT_DIR_LTR)

from linear_system import LinVar, LinSys, LinEq
import itertools


UNSPEC = None


class UIElement(object):
    _counter = itertools.count()
    def __init__(self):
        self.id = self._counter.next()
        self.width = LinVar("w%d" % (self.id,))
        self.height = LinVar("h%d" % (self.id,))
        self.width_constraint = UNSPEC
        self.height_constraint = UNSPEC
    def X(self, width_constraint, height_constraint):
        if width_constraint is not UNSPEC:
            self.width_constraint = width_constraint
        if height_constraint is not UNSPEC:
            self.height_constraint = height_constraint
        return self

    def __sub__(self, other):
        return VStack.build(self, other)
    def __neg__(self):
        return self
    def __or__(self, other):
        return HStack.build(self, other)
    
    def get_constraints(self):
        if self.width_constraint is not UNSPEC:
            yield LinEq(self.width, self.width_constraint)
        if self.height_constraint is not UNSPEC:
            yield LinEq(self.height, self.height_constraint)

class Widget(UIElement):
    def __init__(self, **attrs):
        UIElement.__init__(self)
        self.attrs = attrs
    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, ", ".join("%s = %r" % (k, v) for k, v in self.attrs.items()))

class Stack(UIElement):
    def __init__(self, elems):
        UIElement.__init__(self)
        self.elems = elems
    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.elems)
    @classmethod
    def build(cls, lhs, rhs):
        if isinstance(lhs, cls):
            if isinstance(rhs, cls):
                lhs.elems.extend(rhs.elems)
            else:
                lhs.elems.append(rhs)
            return lhs
        elif isinstance(rhs, cls):
            rhs.elems.insert(0, lhs)
            return rhs
        else:
            return cls([lhs, rhs])
    

class VStack(Stack):
    pass
class HStack(Stack):
    def get_constraints(self):
        for c in Stack.get_constraints(self):
            yield c
        yield LinEq(sum(e.width for e in self.elems), self.width)
        for e in self.elems:
            for c in e.get_constraints():
                yield c
        #if not all(e.height_constraint is UNSPEC for e in self.elems):
        for e in self.elems:
            yield LinEq(e.height, self.height)
    
    def render(self, solution):
        box = gtk.HBox()
        box.show()
        for e in self.elems:
            box.pack_start(e.render(solution), False, False)
        box.set_size_request(solution[self.width.name], solution[self.height.name])
        return box


class Label(Widget):
    def render(self, solution):
        lbl = gtk.Label(self.attrs["text"])
        lbl.show()
        lbl.set_size_request(solution[self.width.name], solution[self.height.name])
        return lbl

class Text(Widget):
    pass
class Image(Widget):
    pass
class Button(Widget):
    pass


def render(root):
    window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    window.set_title("Hello World")
    window.connect("delete_event", lambda *args: False)
    window.connect("destroy", lambda *args: gtk.main_quit())
    if not root.width_constraint:
        fixed_size = False
        w, h = window.get_size()
        root.X(w, h)
    else:
        fixed_size = True
    
    linsys = LinSys(*root.get_constraints())
    print linsys
    solution = linsys.solve()
    print solution
    #solution["window-width"] = lambda: window.get_size()[0]
    #solution["window-height"] = lambda: window.get_size()[0]
    
    if fixed_size:
        print "!! fixed_size"
        window.set_size_request(solution[root.width.name], solution[root.height.name])
        window.set_resizable(False)
    
    window.add(root.render(solution))
    window.show()
    gtk.main()



if __name__ == "__main__":
    x = LinVar("x")
    l1 = Label(text = "hello").X(x, UNSPEC)
    l2 = Label(text = "world").X(x, UNSPEC)
    p = (l1 | l2) #.X(600, 200)
    print p
    
    render(p)
















