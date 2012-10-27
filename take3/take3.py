import itertools
import pygtk
pygtk.require('2.0')
import gtk
gtk.widget_set_default_direction(gtk.TEXT_DIR_LTR)
from linear import LinVar, LinEq, LinSys, FreeVar


def ui_property(func):
    def getter(self):
        return self.attrs.get(func.__name__)
    def setter(self, value):
        if value != self.attrs.get(func.__name__):
            self.attrs[func.__name__] = value
            func(self, value)
            self._on_changed(func.__name__)
    return property(getter, setter, None, func.__doc__)


class UIElement(object):
    _counter = itertools.count()
    def __init__(self, elems = (), **attrs):
        self.attrs = attrs
        self.id = self._counter.next()
        self.w = LinVar("w%d" % (self.id,))
        self.h = LinVar("h%d" % (self.id,))
        self.w.owner = self
        self.h.owner = self
        self.attrs["w_constraint"] = None
        self.attrs["h_constraint"] = None
        self.elems = list(elems)
        self._top_widget = None
        self._on_change_callbacks = {}
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
        if w:
            self.attrs["w_constraint"] = w
        if h:
            self.attrs["h_constraint"] = h
        return self
    def get_constraints(self):
        if self.attrs["w_constraint"]:
            yield LinEq(self.w, self.attrs["w_constraint"])
        if self.attrs["h_constraint"]:
            yield LinEq(self.h, self.attrs["h_constraint"])
        for e in self.elems:
            for cons in e.get_constraints():
                yield cons
    def build(self):
        if not self._top_widget:
            self._top_widget = self._build()
            self._top_widget.connect("size-allocate", self._handle_configure)
        return self._top_widget
    def _build(self):
        raise NotImplementedError()
    
    def _handle_configure(self, wgt, evt):
        self.width = evt.width
        self.height = evt.height
    @ui_property
    def width(self, _):
        #self._gtkobj.set_size_request(self.width, self.height)
        pass 
    @ui_property
    def height(self, _):
        pass
        #self._gtkobj.set_size_request(self.width, self.height)     
    def _on_changed(self, attr):
        for callback in self._on_change_callbacks.get(attr, ()):
            callback(self.attrs[attr])

    def when_changed(self, attr, callback):
        if attr not in self._on_change_callbacks:
            self._on_change_callbacks[attr] = []
        self._on_change_callbacks[attr].append(callback)

class Layout(UIElement):
    DIR = None
    
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

class EvaluatingDict(object):
    __slots__ = ["solution"]
    def __init__(self, solution):
        self.solution = solution
    def __getattr__(self, var):
        return evaluate(self.solution, var)

def evaluate(solution, var):
    if hasattr(var, "name"):
        var = var.name
    if not var in solution:
        return None
    val = solution[var]
    if isinstance(val, (int, long, float, FreeVar)):
        return val
    else:
        return val.eval(EvaluatingDict(solution))

class Hor(Layout):
    def get_constraints(self):
        for cons in Layout.get_constraints(self):
            yield cons
        scroller = LinVar("scroller%d" % (self.id,), self, "overflow")
        yield LinEq(sum(e.w for e in self.elems) + scroller, self.w)
        for e in self.elems:
            padder = LinVar("padder%d" % (e.id,), type = "padding")
            yield LinEq(e.h + padder, self.h)
    
    def _build(self):
        self._box = gtk.Layout()
        for e in self.elems:
            wgt = e.build()
            self._box.add(wgt)
        self._box.show()
        wnd = gtk.ScrolledWindow()
        wnd.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        wnd.add(self._box)
        wnd.show()
        return wnd
    
    def render(self, solution):
        self.build()
        for e in self.elems:
            e.render(solution)
        w = int(evaluate(solution, self.w))
        h = int(evaluate(solution, self.h))
        self._box.set_size_request(w, h)
        bottom = 0
        x_offset = 0
        for e in self.elems:
            wgt = e.build()
            w = int(evaluate(solution, e.w))
            h = int(evaluate(solution, e.h))
            hp = int(evaluate(solution, "padder%d" % (e.id,)))
            bottom = max(bottom, h)
            wgt.set_size_request(w, h)
            self._box.move(wgt, x_offset, hp / 2)
            x_offset += w
        self._box.set_size(x_offset, 60)


class Ver(Layout):
    pass

#===================================================================================================
# Atoms
#===================================================================================================
class Atom(UIElement):
    pass

class Label(Atom):
    def _build(self):
        lbl = gtk.Label(self.text)
        lbl.show()
        return lbl
    def render(self, solution):
        self.build()
    @ui_property
    def text(self, text):
        self._top_widget.set_text(text)

class Button(Atom):
    def _build(self):
        btn = gtk.Button(self.text)
        btn.show()
        btn.connect("clicked", self._handle_click)
        return btn

    def render(self, solution):
        self.build()
    
    def _handle_click(self, *_):
        self.clicked = 1
        self.clicked = 0
    
    @ui_property
    def text(self, text):
        self._top_widget.set_text(text)
    @ui_property
    def clicked(self, _):
        pass

#===================================================================================================
# Top-level Window
#===================================================================================================
class Window(Atom):
    def __init__(self, root, **attrs):
        Atom.__init__(self, [root], **attrs)
    
    def _build(self):
        wnd = gtk.Window(gtk.WINDOW_TOPLEVEL)
        wnd.set_title("Untitled")
        wnd.connect("delete_event", lambda *args: False)
        wnd.connect("destroy", self._handle_destroy)
        wnd.show()
        #window.set_size_request(int(solution["WindowWidth"]), int(solution["WindowHeight"]))
        #wnd.set_resizable(False)
        assert len(self.elems) == 1
        wnd.add(self.elems[0].build())
        return wnd
    
    def render(self, solution):
        self.build()
        root = self.elems[0]
        root.render(solution)

    def _handle_destroy(self, widget, *_):
        self.closed = 1
        self.closed = 0
        gtk.main_quit()
    
    @ui_property
    def width(self, _):
        pass
        #self._gtkobj.resize(self.width, self.height)
    @ui_property
    def height(self, _):
        pass
        #self._gtkobj.resize(self.width, self.height)
    @ui_property
    def closed(self, _):
        pass
    @ui_property
    def title(self, text):
        self._top_widget.set_title(text)


#===================================================================================================
# APIs
#===================================================================================================
def unify(root):
    constraints = list(root.get_constraints())
    ww = LinVar("WindowWidth")
    wh = LinVar("WindowHeight")
    constraints.append(LinEq(root.w, ww))
    constraints.append(LinEq(root.h, wh))
    linsys = LinSys(constraints)
    return linsys.solve()


def run(root):
    solution = unify(root)
    wnd = Window(root, **root.attrs)
    wnd.render(solution)
    gtk.main()



if __name__ == "__main__":
    x = LinVar("x")
    main = (Label(text = "foo").X(50,50) | Label(text = "bar").X(50,50) | Label(text = "spam").X(50,60)).X(100,60)
    run(main)







