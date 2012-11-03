import pygtk
pygtk.require('2.0')
import gtk
gtk.widget_set_default_direction(gtk.TEXT_DIR_LTR)


class UIProperty(property):
    pass

def ui_property(default = None):
    def deco(func):
        def getter(self):
            return self._attrs.get(func.__name__, default)
        def setter(self, val):
            if val != self._attrs.get(func.__name__, default):
                self._attrs[func.__name__] = val
                func(self, val)
                self._on_changed(func.__name__)
        prop = UIProperty(getter, setter, doc = func.__doc__)
        prop.default = default
        prop.name = func.__name__
        return prop
    return deco


class UIElement(object):
    def __init__(self, constraint, solver, children):
        self._constraint = constraint
        self._solver = solver
        self._children = children
        self._attrs = {v.name : v.default for cls in reversed(type(self).mro()) 
            for k, v in cls.__dict__.items() if isinstance(v, UIProperty)}
        self._observers = {}
        self._gtkobj = self._build()
        #for k, v in attrs.items():
        #    if k not in self._attrs:
        #        raise ValueError("Unknown attribute %r" % (k,))
        #    setattr(self, k, v)
        self._gtkobj.connect("size-allocate", self._handle_configure)
    
    def _build(self):
        raise NotImplementedError()
    
    def when_changed(self, attrname, callback):
        if attrname not in self._observers:
            self._observers[attrname] = []
        self._observers[attrname].append(callback)
    def _on_changed(self, attrname):
        for cb in self._observers.get(attrname, ()):
            cb()
    def _handle_configure(self, wgt, evt):
        self.width = evt.width
        self.height = evt.height
        
    @ui_property()
    def width(self, val):
        """gets/sets the widget's width"""
    @ui_property()
    def height(self, val):
        """gets/sets the widget's height"""
    @ui_property(True)
    def visible(self, val):
        """gets/sets the widget's visibility (True or False)"""
        if val:
            self._gtkobj.show()
        else:
            self._gtkobj.hide()
            # TODO: set width, height = 0

class Window(UIElement):
    def __init__(self, constraint, solver, child):
        UIElement.__init__(self, constraint, solver, [child])
    def _build(self):
        wnd = gtk.Window(gtk.WINDOW_TOPLEVEL)
        wnd.connect("delete_event", lambda *args: False)
        wnd.connect("destroy", self._handle_close)
        wnd.add(self._children[0]._gtkobj)
        wnd.show()
        return wnd
    
    def _handle_close(self, *args):
        self.closed = 1
        self.closed = 0
        gtk.main_quit()

    @ui_property()
    def width(self, val):
        """gets/sets the widget's width"""
        self._solver["WindowWidth"] = val
    @ui_property()
    def height(self, val):
        """gets/sets the widget's height"""
        self._solver["WindowHeight"] = val
    
    @ui_property("Untitled")
    def title(self, val):
        self._gtkobj.set_title(val)
    @ui_property(0)
    def closed(self, val):
        pass

class Layout(UIElement):
    GTK_PANE = None
    DIR = None

class HLayout(Layout):
    PANE = gtk.HPaned
    
    def _build(self):
        self._box = gtk.Layout()
        for e in self._children:
            if self._solver.is_free(e._constraint.w):
                pass
            else:
                self._box.add(e._gtkobj)
        self._box.show()
        scr = gtk.ScrolledWindow()
        scr.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scr.add(self._box)
        scr.show()
        return scr

#    def render(self, solution):
#        self.build()
#        for e in self.elems:
#            e.render(solution)
#        w = int(evaluate(solution, self.w))
#        h = int(evaluate(solution, self.h))
#        self._box.set_size_request(w, h)
#        bottom = 0
#        x_offset = 0
#        for e in self.elems:
#            wgt = e.build()
#            w = int(evaluate(solution, e.w))
#            h = int(evaluate(solution, e.h))
#            hp = int(evaluate(solution, "padder%d" % (e.id,)))
#            bottom = max(bottom, h)
#            wgt.set_size_request(w, h)
#            self._box.move(wgt, x_offset, hp / 2)
#            x_offset += w
#        self._box.set_size(x_offset, 60)

class VLayout(Layout):
    PANE = gtk.VPaned

class Atom(UIElement):
    def __init__(self, constraint, solver):
        UIElement.__init__(self, constraint, solver, ())

class Label(Atom):
    def _build(self):
        lbl = gtk.Label()
        lbl.show()
        return lbl
    
    @ui_property("")
    def text(self, val):
        self._gtkobj.set_text(val)

class Button(Atom):
    def _build(self):
        btn = gtk.Button(self.text)
        btn.connect("clicked", self._handle_click)
        return btn

    def _handle_click(self, *_):
        self.clicked = 1
        self.clicked = 0
    
    @ui_property("")
    def text(self, text):
        self._gtkobj.set_text(text)
    @ui_property(0)
    def clicked(self, val):
        pass



if __name__ == "__main__":
    pass






