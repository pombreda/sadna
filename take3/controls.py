import pygtk
pygtk.require('2.0')
import gtk
gtk.widget_set_default_direction(gtk.TEXT_DIR_LTR)



def ui_property(func):
    def getter(self):
        return self.attrs.get(func.__name__)
    def setter(self, value):
        if value != self.attrs.get(func.__name__):
            self.attrs[func.__name__] = value
            func(self, value)
            self._on_changed(func.__name__)
    return property(getter, setter, None, func.__doc__)


class Control(object):
    #self._top_widget = None
    #self._on_change_callbacks = {}

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

#    def _build(self):
#        self._box = gtk.Layout()
#        for e in self.elems:
#            wgt = e.build()
#            self._box.add(wgt)
#        self._box.show()
#        wnd = gtk.ScrolledWindow()
#        wnd.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
#        wnd.add(self._box)
#        wnd.show()
#        return wnd
#    
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



#    def _build(self):
#        btn = gtk.Button(self.text)
#        btn.show()
#        btn.connect("clicked", self._handle_click)
#        return btn
#
#    def render(self, solution):
#        self.build()
#    
#    def _handle_click(self, *_):
#        self.clicked = 1
#        self.clicked = 0
#    
#    @ui_property
#    def text(self, text):
#        self._top_widget.set_text(text)
#    @ui_property
#    def clicked(self, _):
#        pass


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


def run(root):
    solution = unify(root)
    wnd = Window(root, **root.attrs)
    wnd.render(solution)
    gtk.main()

