import pygtk
pygtk.require('2.0')
import gtk
gtk.widget_set_default_direction(gtk.TEXT_DIR_LTR)


class UIProperty(property):
    __slots = []
    def __new__(cls, func):
        def getter(self):
            return self._attrs[func.__name__]
        def setter(self, val):
            if val != self.attrs.get(func.__name__):
                self._attrs[func.__name__] = val
                func(self, val)
                self._on_changed(func.__name__)
        return property.__new__(cls, getter, setter, doc = func.__doc__)


class UIElement(object):
    def __init__(self, **attrs):
        self._attrs = {}
        self._observers = {}
        self._gtkobj = self._build()
        allowed_attrs = {k for cls in type(self).mro() for k, v in cls.__dict__.items() 
            if isinstance(v, UIProperty)}
        for k, v in self.attrs:
            if k not in allowed_attrs:
                raise ValueError("Unknown attribute %r" % (k,))
            setattr(self, k, v)
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
        
    @UIProperty
    def width(self, val):
        """gets/sets the widget's width"""
    @UIProperty
    def height(self, val):
        """gets/sets the widget's height"""
    @UIProperty
    def visible(self, val):
        """gets/sets the widget's visibility (True or False)"""
        if val:
            self._gtkobj.show()
        else:
            self._gtkobj.hide()
            # TODO: set width, height = 0

class Layout(UIElement):
    pass

class HLayout(Layout):
    def _build(self):
        self._box = gtk.Layout()
        for e in self.elems:
            wgt = e.build()
            self._box.add(wgt)
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

class Label(UIElement):
    def _build(self):
        lbl = gtk.Label()
        lbl.show()
        return lbl
    
    @UIProperty
    def text(self, val):
        self._gtkobj.set_text(val)

class Button(UIElement):
    def _build(self):
        btn = gtk.Button(self.text)
        btn.connect("clicked", self._handle_click)
        return btn

    def _handle_click(self, *_):
        self.clicked = 1
        self.clicked = 0
    
    @UIProperty
    def text(self, text):
        self._gtkobj.set_text(text)
    @UIProperty
    def clicked(self, val):
        pass



if __name__ == "__main__":
    pass







