import pygtk
pygtk.require('2.0')
import gtk
import gobject

gtk.widget_set_default_direction(gtk.TEXT_DIR_LTR)

def ui_property(func):
    def getter(self):
        return self._attrs.get(func.__name__)
    def setter(self, value):
        if value != self._attrs.get(func.__name__):
            self._attrs[func.__name__] = value
            func(self, value)
            self._on_changed(func.__name__)
    return property(getter, setter)

class Control(object):
    def __init__(self, **attrs):
        self._attrs = {}
        self._on_change_callbacks = {}
        self._bound_funcs = {}
        self._gtkobj = self._build()
        self._attrs["native_width"], self._attrs["native_height"] = self._gtkobj.size_request()
        if hasattr(self._gtkobj, "get_size"):
            self._attrs["width"], self._attrs["height"] = self._gtkobj.get_size()
        else:
            self._attrs["width"] = self._attrs["native_width"]
            self._attrs["height"] = self._attrs["native_height"]
        for k, v in attrs.items():
            setattr(self, k, v)
        #self._gtkobj.connect("configure_event", self._handle_configure)
        self._gtkobj.connect("size-allocate", self._handle_configure)
        self._gtkobj.show()
    
    def _build(self):
        raise NotImplementedError()

    @ui_property
    def width(self, _):
        #self._gtkobj.set_size_request(self.width, self.height)
        pass 
    @ui_property
    def height(self, _):
        pass
        #self._gtkobj.set_size_request(self.width, self.height) 
    
    @ui_property
    def native_width(self, _): pass
    @ui_property
    def native_height(self, _): pass

    def _on_changed(self, attr):
        for callback in self._on_change_callbacks.get(attr, ()):
            callback(self._attrs[attr])

    def _handle_configure(self, widget, event):
        self.width = event.width
        self.height = event.height

    #
    # API
    #    
    def when_changed(self, attr, callback):
        if attr not in self._on_change_callbacks:
            self._on_change_callbacks[attr] = []
        self._on_change_callbacks[attr].append(callback)
        
    def set(self, attr, value):
        setattr(self, attr, value)
    
    def bind(self, name, func):
        self._bound_funcs[name] = func

class ControlContainer(Control):
    def __init__(self, children, **attrs):
        self.children = list(children)
        Control.__init__(self, **attrs)

class Window(ControlContainer):
    def __init__(self, child, **attrs):
        ControlContainer.__init__(self, [child], **attrs)
    
    def _build(self):
        wnd = gtk.Window(gtk.WINDOW_TOPLEVEL)
        wnd.connect("delete_event", lambda *args: False)
        wnd.connect("destroy", self._handle_destroy)
        assert len(self.children) == 1
        wnd.add(self.children[0]._gtkobj)
        return wnd

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
        self._gtkobj.set_title(text)

class Glider(ControlContainer):
    GTK_CLASS = None

    def _rec_build(self, children):
        if not children:
            raise ValueError("children cannot be empty")
        elif len(children) == 1:
            pane = children[0]
        elif len(children) == 2:
            pane = self.GTK_CLASS()
            f1 = gtk.Frame()
            f1.set_shadow_type(gtk.SHADOW_ETCHED_IN)
            f1.add(children[0]._gtkobj)
            f1.show()
            f2 = gtk.Frame()
            f2.set_shadow_type(gtk.SHADOW_ETCHED_IN)
            f2.add(children[1]._gtkobj)
            f2.show()
            pane.add1(f1)
            pane.add2(f2)
        else:
            pane = self.GTK_CLASS()
            f1 = gtk.Frame()
            f1.set_shadow_type(gtk.SHADOW_ETCHED_IN)
            f1.add(children[0]._gtkobj)
            f1.show()
            pane.add1(f1)
            pane.add2(self._rec_build(children[1:]))
        return pane

    def _build(self):
        return self._rec_build(self.children)

class HGlider(Glider):
    GTK_CLASS = gtk.HPaned

class VGlider(Glider):
    GTK_CLASS = gtk.VPaned

class Box(ControlContainer):
    GTK_CLASS = None
    
    def _build(self):
        box = self.GTK_CLASS()
        for child in self.children:
            box.pack_start(child._gtkobj)
        return box

class HBox(Box):
    GTK_CLASS = gtk.HBox

class VBox(Box):
    GTK_CLASS = gtk.VBox


class Button(Control):
    def _build(self):
        btn = gtk.Button()
        btn.connect("clicked", self._handle_click)
        return btn
    
    def _handle_click(self, widget, *_):
        self.clicked = 1
        self.clicked = 0
    
    @ui_property
    def text(self, text):
        self._gtkobj.set_text(text)

    @ui_property
    def clicked(self, _):
        pass


class Label(Control):
    def _build(self):
        lbl = gtk.Label()
        return lbl
    
    @ui_property
    def text(self, text):
        self._gtkobj.set_text(text)



if __name__ == "__main__":
    w = Window(HGlider([Label(text = "hello"), Label(text = "world")]), title = "foo")
    gtk.main()








