import sys
from PyQt4 import QtGui
from PyQt4.QtCore import Qt
import models
from solver import ModelSolver


_control_to_model = {}

def control_for(model):
    def deco(cls):
        _control_to_model[model] = cls
        return cls
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
        return self.widget
    
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
        self.model.when_changed("title", lambda val: wnd.setWindowTitle(val))
        if not self.solver.is_free("WindowWidth"):
            wnd.setFixedWidth(self.solver["WindowWidth"])
        if not self.solver.is_free("WindowHeight"):
            wnd.setFixedHeight(self.solver["WindowHeight"])
        return wnd

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

@control_for(models.Horizontal)
class HLayout(CompositeControl):
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
        hor = QtGui.QWidget(parent)
        for child in self.children:
            child.build(hor)
            off = self.model._get_offset(child.model)
            def set_offset(val, child = child):
                #print "!! set_offset", child, val
                child.widget.move(int(val), 0)
            self.solver.watch(off, set_offset)
        return hor
    
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
class VLayout(CompositeControl):
    def _build(self, parent):
        return self._build_fixed(parent)

    def _build_fixed(self, parent):        
        ver = QtGui.QWidget(parent)
        for child in self.children:
            child.build(ver)
            off = self.model._get_offset(child.model)
            def set_offset(val, child = child):
                #print "!! set_offset", child, val
                child.widget.move(0, int(val))
            self.solver.watch(off, set_offset)
        return ver
    
    def _build_with_splitter(self, parent):
        pass

#===================================================================================================
# Atoms
#===================================================================================================
class LabeledControl(Control):
    def _post_init(self):
        self.model.when_changed("text", self.set_text)
        self.model.when_changed("halign", self.set_halign)
        self.model.when_changed("valign", self.set_valign)

    def set_text(self, val):
        self.widget.setText(val)

    _haligns = {"left" : Qt.AlignLeft, "center" : Qt.AlignHCenter, "right" : Qt.AlignRight}    
    def set_halign(self, val):
        self.widget.setAlignment(self._haligns[val.lower()])

    _valigns = {"top" : Qt.AlignTop, "middle" : Qt.AlignVCenter, "bottom" : Qt.AlignBottom}    
    def set_valign(self, val):
        self.widget.setAlignment(self._valigns[val.lower()])

@control_for(models.LabelAtom)
class Label(LabeledControl):
    def _build(self, parent):
        lbl = QtGui.QLabel("", parent)
        lbl.setStyleSheet("* { background-color: yellow }")
        return lbl

@control_for(models.ButtonAtom)
class Button(Control):
    def _build(self, parent):
        btn = QtGui.QPushButton("", parent)
        #btn.setStyleSheet("* { background-color: yellow }")
        btn.clicked.connect(self._handle_clicked)
        self.model.when_changed("text", self.set_text)
        return btn

    def set_text(self, val):
        self.widget.setText(val)
    
    def _handle_clicked(self, event):
        self.model.flash("clicked")


@control_for(models.LineEditAtom)
class LineEdit(Control):
    def _build(self, parent):
        txt = QtGui.QLineEdit(parent)
        self.model.when_changed("text", self.set_text)
        self.model.when_changed("placeholder", self.set_placeholder)
        txt.textEdited.connect(self._handle_edit)
        txt.returnPressed.connect(self._handle_accept)
        return txt
    
    def set_text(self, val):
        self.widget.setText(val)
    
    def _handle_edit(self, val):
        self.model.set("text", val)
    
    def _handle_accept(self):
        self.model.flash("accepted")
    
    def set_placeholder(self, val):
        self.widget.setPlaceholderText(val)


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



if __name__ == "__main__":
    from linsys import LinVar
    x = LinVar("x")
    
    k = models.Target("k")
    
    m = models.WindowModel(
        models.Horizontal([
            models.LineEditAtom(placeholder="Type something...", width = 3*x, accepted = k),
            models.ButtonAtom(text = "Send", width = 60, clicked = k),
        ]),
        #width = 300, height = 200,
        title = "foo"
    )
    
    def on_click(val):
        print "on_click", val
    
    k.when_changed(on_click)
    
    run(m)












