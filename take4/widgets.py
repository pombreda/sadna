from functools import partial
import pygtk
pygtk.require('2.0')
import gtk
gtk.widget_set_default_direction(gtk.TEXT_DIR_LTR)


class Widget(object):
    def __init__(self, solver, model, subwidgets = ()):
        self.model = model
        self.solver = solver
        self.subwidgets = subwidgets
        self._gtkobj = self.build()
        self._gtkobj.connect("size-allocate", self._handle_configure)
        self.model.when_changed("width", self.set_width)
        self.model.when_changed("height", self.set_height)
        self.model.when_changed("visible", self.set_visibility)
        self._gtkobj.show()

    def build(self):
        raise NotImplementedError()

    def _handle_configure(self, _, event):
        pass
    
    def set_width(self, _, neww):
        if neww < 0:
            print "!! neg width", self
            return
        neww = max(neww, 0)
        w, h = self._gtkobj.get_size_request()
        self._gtkobj.set_size_request(int(neww), h)
    def set_height(self, _, newh):
        if newh < 0:
            print "!! neg height", self
            return
        #newh = max(newh, 0)
        w, h = self._gtkobj.get_size_request()
        self._gtkobj.set_size_request(w, int(newh))
    def set_visibility(self, _, val):
        if val:
            self._gtkobj.show()
        else:
            self._gtkobj.hide()


class Window(Widget):
    def __init__(self, solver, model, child):
        Widget.__init__(self, solver, model, [child])
    def build(self):
        wnd = gtk.Window(gtk.WINDOW_TOPLEVEL)
        wnd.connect("delete_event", lambda *args: False)
        wnd.connect("destroy", self._handle_close)
        if not self.solver.is_free("WindowHeight") or not self.solver.is_free("WindowWidth"):
            wnd.set_resizable(False)
        wnd.add(self.subwidgets[0]._gtkobj)
        wnd.set_size_request(300,200)
        return wnd
    
    def _handle_configure(self, _, event):
        self.solver.update({"WindowHeight" : event.height, "WindowWidth" : event.width})
    
    def _handle_close(self, *args):
        self.model.set("closed", 1)
        self.model.set("closed", 0)
        gtk.main_quit()
    def set_title(self, _, title):
        self._gtkobj.set_title(title)


class HLayout(Widget):
    def build(self):
        self._box = gtk.Layout()
        for sw in self.subwidgets:
            if self.solver.is_free(sw.model.w):
                assert False
            else:
                self._box.add(sw._gtkobj)
            sw.model.when_changed(self.model._get_offset(sw.model), partial(self.set_position, sw))
        sw.model.when_changed("width", self.set_box_width)
        
        self._box.show()
        scr = gtk.ScrolledWindow()
        scr.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scr.add(self._box)
        return scr
    
    def set_box_width(self, _, neww):
        w, h = self._box.get_size()
        self._box.set_size(int(neww), h)
    
    def set_position(self, subwgt, _, newx):
        self._box.move(subwgt, newx, 0)

class Atomic(Widget):
    def __init__(self, solver, model):
        Widget.__init__(self, solver, model)

class Label(Widget):
    def build(self):
        lbl = gtk.Label(repr(self))
        self.model.when_changed("text", self.set_text)
        return lbl
    
    def set_text(self, _, text):
        self._gtkobj.set_text(text)
        #self.model.set("native-width")

class Button(Widget):
    def build(self):
        btn = gtk.Button(repr(self))
        btn.connect("clicked", self._handle_click)
        self.model.when_changed("text", self.set_text)
        return btn

    def _handle_click(self, *_):
        self.model.set("clicked", 1)
        self.model.set("clicked", 0)
    
    def set_text(self, _, text):
        self._gtkobj.set_text(text)




