import sys
from PyQt4 import QtCore, QtGui
import models


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
            print "building %r son of %r" % (self.widget, parent)
    
    def _build(self, parent):
        raise NotImplementedError()
    
    def set_width(self, newwidth):
        self.widget.resize(newwidth, self.widget.height())
    def set_height(self, newheight):
        self.widget.resize(self.widget.width(), newheight)


class Label(Control):
    def _build(self, parent):
        return QtGui.QLabel(parent)

_atoms_to_controls = {
    "label" : Label,
}

def get_control_for_model(model):
    if isinstance(model, models.Atom):
        return _atoms_to_controls[model.name]
    elif isinstance(model, models.Horizontal):
        return HLayout
    #elif isinstance(model, models.Vertical):
    #    return VLayout
    else:
        pass

class CompositeControl(Control):
    def __init__(self, model, solver):
        Control.__init__(self, model, solver)
        self.children = []
        for child in self.model.children:
            cls = get_control_for_model(child)
            self.children.append(cls(child, solver))


class Window(CompositeControl):
    def __init__(self, model, solver):
        CompositeControl.__init__(self, model, solver)
        assert len(self.children) == 1
    
    def _build(self, parent):
        wnd = QtGui.QMainWindow()
        wnd.closeEvent = self._handle_closed
        self.children[0].build(wnd)
        wnd.setCentralWidget(self.children[0].widget)
        wnd.show()
        return wnd

    def _handle_closed(self, event):
        self.closed = 1
        self.closed = 0
        event.accept()

class HLayout(CompositeControl):
    def __init__(self, model, solver):
        CompositeControl.__init__(self, model, solver)

    def _build(self, parent):
        scrollarea = QtGui.QScrollArea(parent)
        hor = QtGui.QWidget()
        scrollarea.setWidget(hor)
        for child in self.children:
            child.build(hor)
            coff = self.model._get_offset(child.model)
            self.solver.watch(coff, lambda offset: child.widget.move(offset, 0))
        return scrollarea


def run(model):
    app = QtGui.QApplication(sys.argv)
    sol = ModelSolver(model)
    w = Window(model, sol)
    w.build(None)
    w.widget.show()
    return app.exec_()



if __name__ == "__main__":
    from models import LinVar, Horizontal, Atom
    from solver import ModelSolver
    x = LinVar("x")
    m = Horizontal([
            Horizontal([
                Atom("label", text="foo", width = x),
                Atom("label", text="bar", width = 2*x),
                Atom("label", text="spam", width = 3*x),
            ])
        ])

    run(m)












