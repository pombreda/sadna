import sys
from PyQt4 import QtCore, QtGui
import models
from solver import ModelSolver


class Control(object):
    def __init__(self, model, solver):
        self.model = model
        self.solver = solver
        self.solver.watch(self.model.width, self.set_width)
        self.solver.watch(self.model.height, self.set_height)
        self.widget = None
    
    def build(self, parent):
        if self.widget is None:
            self.widget = self._build(parent)
        return self.widget
    
    def _build(self, parent):
        raise NotImplementedError()
    
    def set_width(self, newwidth):
        self.widget.setFixedWidth(int(newwidth))
    def set_height(self, newheight):
        self.widget.setFixedHeight(int(newheight))


class Label(Control):
    def _build(self, parent):
        lbl = QtGui.QLabel(self.model.attrs["text"], parent)
        lbl.setStyleSheet("* { background-color: yellow }")
        self.model.when_changed("text", lambda val: lbl.setText(val))
        return lbl

    def set_height(self, newheight):
        Control.set_height(self, newheight)


def get_control_for_model(model):
    return _model_to_control[type(model)]

class CompositeControl(Control):
    def __init__(self, model, solver):
        Control.__init__(self, model, solver)
        self.children = []
        for child_model in self.model.children:
            cls = get_control_for_model(child_model)
            self.children.append(cls(child_model, solver))

class Window(CompositeControl):
    def __init__(self, model, solver):
        CompositeControl.__init__(self, model, solver)
        assert len(self.children) == 1
    
    def _build(self, parent):
        wnd = QtGui.QWidget()
        wnd.closeEvent = self._handle_closed
        self.widget = wnd
        self.children[0].build(wnd)
        #self.children[0].widget.move(0, 0)
        #wnd.setCentralWidget(self.children[0].widget)
        self._super_resizeEvent = wnd.resizeEvent
        wnd.resizeEvent = self._handle_resized
        self.model.when_changed("title", lambda val: wnd.setWindowTitle(val))
        #if not self.solver.is_free("WindowWidth"):
        #    wnd.setFixedWidth(self.solver["WindowWidth"])
        #if not self.solver.is_free("WindowHeight"):
        #    wnd.setFixedHeight(self.solver["WindowHeight"])
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


class HLayout(CompositeControl):
    def __init__(self, model, solver):
        CompositeControl.__init__(self, model, solver)

    def _build(self, parent):
        #scrollarea = QtGui.QScrollArea(parent)
        hor = QtGui.QWidget(parent)
        #hor.setSizeHint(self.model.total_width)
        #scrollarea.setWidget(hor)
        for child in self.children:
            child.build(hor)
            off = self.model._get_offset(child.model)
            def set_offset(val, child = child):
                child.widget.move(int(val), 0)
            self.solver.watch(off, set_offset)
        return hor #scrollarea

_model_to_control = {
    models.LabelAtom: Label,
    models.Horizontal : HLayout,
}


def run(model):
    app = QtGui.QApplication(sys.argv)
    sol = ModelSolver(model)
    print "free:", list(sol.get_freevars())
    w = Window(model, sol)
    w.build(None)
    w.widget.show()
    sol.invoke_observers()
    model.invoke_observers()
    return app.exec_()



if __name__ == "__main__":
    from linsys import LinVar
    x = LinVar("x")
    m = models.WindowModel(
        models.Horizontal([
            models.LabelAtom("label", text="foo", width = x),
            models.LabelAtom("label", text="bar", width = x, height = 100),
            models.LabelAtom("label", text="spam", width = x),
        ]),
        #width = 300, height = 200
        )
    run(m)












