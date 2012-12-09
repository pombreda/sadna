import sys
from PyQt4 import QtGui
from PyQt4.QtCore import Qt
import models
from solver import ModelSolver


_control_to_model = {}

def control_for(model):
    def deco(cls):
        assert model not in _control_to_model
        _control_to_model[model] = cls
        return cls
    return deco

def propagated_attr(name):
    def deco(func):
        func._propagated_attr = name
        return func
    return deco

def get_control_for_model(model):
    return _control_to_model[type(model)]

class Control(object):
    def __init__(self, model, solver):
        self.model = model
        self.solver = solver
        self.solver.watch(self.model.width, self.set_width)
        self.solver.watch(self.model.height, self.set_height)
        self.widget = None
        self._post_init()
    
    def _post_init(self):
        pass
    
    def build(self, parent):
        if self.widget is None:
            self.widget = self._build(parent)
            self._install_propagated_attrs()
        return self.widget
    
    def _install_propagated_attrs(self):
        watched = {}
        for cls in reversed(type(self).mro()):
            for k, v in cls.__dict__.items():
                if hasattr(v, "_propagated_attr"):
                    watched[k] = (v._propagated_attr, getattr(self, k))
        for attrname, cb in watched.values():
            if attrname in self.model.computed_attrs:
                self.model.when_changed(attrname, cb)
    
    def _build(self, parent):
        raise NotImplementedError()
    
    def set_width(self, newwidth):
        #self.widget.setFixedWidth(int(newwidth))
        self.widget.resize(int(newwidth), self.widget.height())
    def set_height(self, newheight):
        #self.widget.setFixedHeight(int(newheight))
        self.widget.resize(self.widget.width(), int(newheight))

#===================================================================================================
# Composites
#===================================================================================================
class CompositeControl(Control):
    def _post_init(self):
        self.children = []
        for child_model in self.model.children:
            cls = get_control_for_model(child_model)
            self.children.append(cls(child_model, self.solver))

@control_for(models.WindowModel)
class Window(CompositeControl):
    def __init__(self, model, solver):
        CompositeControl.__init__(self, model, solver)
        assert len(self.children) == 1
    
    def _build(self, parent):
        wnd = QtGui.QWidget()
        wnd.closeEvent = self._handle_closed
        self.widget = wnd
        self.children[0].build(wnd)
        self._super_resizeEvent = wnd.resizeEvent
        wnd.resizeEvent = self._handle_resized
        if not self.solver.is_free("WindowWidth"):
            wnd.setFixedWidth(self.solver["WindowWidth"])
        if not self.solver.is_free("WindowHeight"):
            wnd.setFixedHeight(self.solver["WindowHeight"])
        return wnd

    @propagated_attr("title")
    def set_title(self, val):
        self.widget.setWindowTitle(val)

    @propagated_attr("icon")
    def set_icon(self, filename):
        if not filename:
            return
        self.widget.setWindowIcon(QtGui.QIcon(filename))

    def _handle_resized(self, event):
        self._super_resizeEvent(event)
        self.children[0].widget.move(0, 0)
        freevars = {}
        if self.solver.is_free("WindowWidth"):
            freevars["WindowWidth"] = event.size().width()
        if self.solver.is_free("WindowHeight"):
            freevars["WindowHeight"] = event.size().height()
        self.solver.update(freevars)
    
    def _handle_closed(self, event):
        self.model.flash("closed")
        event.accept()

    def set_width(self, newwidth):
        self.widget.resize(int(newwidth), self.widget.height())
    def set_height(self, newheight):
        self.widget.resize(self.widget.width(), int(newheight))

class BaseLayout(CompositeControl):
    def _build_scroll(self, parent):
        scroll = QtGui.QScrollArea(parent)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded) #ScrollBarAlwaysOff
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setWidgetResizable(False)
        scroll.setLayout(QtGui.QVBoxLayout())
        return scroll
    
@control_for(models.Horizontal)
class HLayout(BaseLayout):
    def _build(self, parent):
        #scrollarea = QtGui.QScrollArea(parent)
        #hor.setSizeHint(self.model.total_width)
        #scrollarea.setWidget(hor)
        
        has_free = False
        for child in self.children:
            if self.solver.is_free(child.model.width):
                has_free = True
                if child.model.width.default is None:
                    child.model.width.default = 100
        
        if has_free:
            return self._build_with_splitter(parent)
        else:
            return self._build_fixed(parent)

    def _build_fixed(self, parent):
        scroll = self._build_scroll(parent)        
        hor = QtGui.QWidget()
        scroll.setWidget(hor)
        
        for child in self.children:
            child.build(hor)
            off = self.model._get_offset(child.model)
            def set_offset(val, child = child):
                #print "!! set_offset", child, val
                child.widget.move(int(val), 0)
            self.solver.watch(off, set_offset)
        self.solver.watch(self.model._total, lambda val: hor.setMinimumWidth(val))
        self.solver.watch(self.model.height, lambda val: hor.setMinimumHeight(val))
        return scroll
    
    def _build_with_splitter(self, parent):
        splitter = QtGui.QSplitter(Qt.Horizontal, parent)
        
        def handle_splitter_moved(pos, index):
            newwidth = splitter.sizes()[index]
            child = self.children[index]
            w = child.model.width
            print "!! splitter_moved", child, newwidth
            if self.solver.is_free(w):
                self.solver.update({w : newwidth})

        for i, child in enumerate(self.children):
            child.build(None)
            splitter.addWidget(child.widget)
            
            off = self.model._get_offset(child.model)
            def set_offset(val, i = i):
                print "!! splitter.set_offset", i, val
                splitter.moveSplitter(int(val), i)
            self.solver.watch(off, set_offset)
            child.model.width

        splitter.splitterMoved.connect(handle_splitter_moved)
        
        return splitter

@control_for(models.Vertical)
class VLayout(BaseLayout):
    def _build(self, parent):
        return self._build_fixed(parent)

    def _build_fixed(self, parent):        
        scroll = self._build_scroll(parent)        
        ver = QtGui.QWidget(parent)
        scroll.setWidget(ver)

        for child in self.children:
            child.build(ver)
            off = self.model._get_offset(child.model)
            def set_offset(val, child = child):
                #print "!! set_offset", child, val
                child.widget.move(0, int(val))
            self.solver.watch(off, set_offset)
        self.solver.watch(self.model._total, lambda val: ver.setMinimumHeight(val))
        self.solver.watch(self.model.width, lambda val: ver.setMinimumWidth(val))
        return scroll

    def _build_with_splitter(self, parent):
        pass

#===================================================================================================
# Atoms
#===================================================================================================
class CommonAttrsMixin(object):
    @propagated_attr("text")
    def set_text(self, val):
        self.widget.setText(val)

    _haligns = {"left" : Qt.AlignLeft, "center" : Qt.AlignHCenter, "right" : Qt.AlignRight}    
    @propagated_attr("halign")
    def set_halign(self, val):
        self.widget.setAlignment(self._haligns[val.lower()])

    _valigns = {"top" : Qt.AlignTop, "middle" : Qt.AlignVCenter, "bottom" : Qt.AlignBottom}    
    @propagated_attr("valign")
    def set_valign(self, val):
        self.widget.setAlignment(self._valigns[val.lower()])
    
    @propagated_attr("font")
    def set_font(self, val):      # (name, size, style)
        assert type(val) is not tuple
        if len(val) == 1:
            self.widget.setStyleSheet("* { font-family: %s;}" % val)
        elif len(val) == 2:
            self.widget.setStyleSheet("* { font-family: %s; font-size: %s;}" % val)
        elif len(val) == 3:
            self.widget.setStyleSheet("* { font-family: %s; font-size: %s; font-style: %s; }" % val)
        else:
            raise ValueError("set_font: expected a tuple of 1 to 3 items")

    @propagated_attr("fgcolor")
    def set_fgcolor(self, val):   # 0xRRGGBB
        if isinstance(val, str):
            if val.startswith("0x"):
                val = val[2:]
        else:
            val = "#%06x" % (val,)
        self.widget.setStyleSheet("* { color: %s; }" % (val,))

    @propagated_attr("bgcolor")
    def set_bgcolor(self, val):   # 0xRRGGBB
        if isinstance(val, str):
            if val.startswith("0x"):
                val = val[2:]
        else:
            val = "#%06x" % (val,)
        self.widget.setStyleSheet("* { background-color: %s; }" % (val,))

    @propagated_attr("enabled")
    def set_enabled(self, val):
        self.widget.setEnabled(val)

    @propagated_attr("visible")
    def set_visible(self, val):
        self.widget.setVisible(val)


@control_for(models.LabelAtom)
class Label(Control, CommonAttrsMixin):
    def _build(self, parent):
        lbl = QtGui.QLabel("", parent)
        return lbl

    @propagated_attr("text")
    def set_text(self, val):
        self.widget.setText(val)
        size = self.widget.sizeHint()
        self.model.set("native_width", size.width())
        self.model.set("native_height", size.height())


@control_for(models.ImageAtom)
class Image(Control):
    def _build(self, parent):
        lbl = QtGui.QLabel("", parent)
        return lbl

    @propagated_attr("enabled")
    def set_enabled(self, val):
        self.widget.setEnabled(val)

    @propagated_attr("visible")
    def set_visible(self, val):
        self.widget.setVisible(val)

    @propagated_attr("image")
    def set_picture(self, filename):
        pic = QtGui.QPixmap(filename)
        self.widget.setPixmap(pic)
        self.model.set("native_width", pic.width())
        self.model.set("native_height", pic.height())


@control_for(models.ButtonAtom)
class Button(Control, CommonAttrsMixin):
    def _build(self, parent):
        btn = QtGui.QPushButton("", parent)
        #btn.setStyleSheet("* { background-color: yellow }")
        btn.clicked.connect(self._handle_clicked)
        return btn

    def _handle_clicked(self, event):
        self.model.flash("clicked")


@control_for(models.LineEditAtom)
class LineEdit(Control):
    def _build(self, parent):
        txt = QtGui.QLineEdit(parent)
        txt.textEdited.connect(self._handle_edit)
        txt.returnPressed.connect(self._handle_accept)
        return txt
    
    @propagated_attr("text")
    def set_text(self, val):
        self.widget.setText(val)
    
    @propagated_attr("readonly")
    def set_readonly(self, val):
        self.widget.setReadOnly(val)

    @propagated_attr("placeholder")
    def set_placeholder(self, val):
        self.widget.setPlaceholderText(val)
    
    def _handle_edit(self, val):
        self.model.set("text", val)
    
    def _handle_accept(self):
        self.model.flash("accepted")
    


def run(model):
    app = QtGui.QApplication(sys.argv)
    app.setStyle(QtGui.QStyleFactory.create('Cleanlooks'))
    sol = ModelSolver(model)
    print "free:", list(sol.get_freevars())
    root = get_control_for_model(model)(model, sol)
    root.build(None)
    root.widget.show()
    sol.invoke_observers()
    model.invoke_observers()
    return app.exec_()















