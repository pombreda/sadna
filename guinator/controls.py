import sys
from PyQt4 import QtCore, QtGui


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
        self._future_attrs = attrs
        self._attrs = {}
        self._on_change_callbacks = {}
        self._bound_funcs = {}
        self._widget = None
    
    def render(self, parent = None):
        if self._widget:
            return
        self._widget = self._build(parent)
        self._widget.setObjectName(repr(self))
        size = self._widget.sizeHint()
        self._attrs["native_width"] = size.width()
        self._attrs["native_height"] = size.height()
        if hasattr(self._widget, "size"):
            size = self._widget.size()
            self._attrs["width"] = size.width()
            self._attrs["height"] = size.height()
        else:
            self._attrs["width"] = self._attrs["native_width"]
            self._attrs["height"] = self._attrs["native_height"]
        self._super_resizeEvent = self._widget.resizeEvent
        self._widget.resizeEvent = self._handle_resized
        for k, v in self._future_attrs.items():
            setattr(self, k, v)
        del self._future_attrs
    
    def _build(self, parent):
        raise NotImplementedError()

    @ui_property
    def width(self, _):
        self._widget.resize(self.width, self.height)
    @ui_property
    def height(self, _):
        self._widget.resize(self.width, self.height)
    
    @ui_property
    def native_width(self, _): 
        raise TypeError("cannot set native_width")
    @ui_property
    def native_height(self, _): 
        raise TypeError("cannot set native_height")

    def _on_changed(self, attr):
        for callback in self._on_change_callbacks.get(attr, ()):
            callback(self._attrs[attr])

    def _handle_resized(self, event):
        self._super_resizeEvent(event)
        self.width = event.size().width()
        self.height = event.size().height()
        #self._widget.adjustSize()

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
    
    def _build(self, parent):
        assert len(self.children) == 1
        wnd = QtGui.QMainWindow()
        wnd.closeEvent = self._handle_closed
        child = self.children[0]
        child.render(wnd)
        print "setCentralWidget", child._widget
        wnd.setCentralWidget(child._widget)
        wnd.show()
        return wnd
    
    def _handle_closed(self, event):
        self.closed = 1
        self.closed = 0
        event.accept()
        #QtGui.QApplication.instance().quit()

    @ui_property
    def closed(self, _):
        pass
    @ui_property
    def title(self, text):
        self._widget.setWindowTitle(text)

class Splitter(ControlContainer):
    ORIENATATION = None

    def _build(self, parent):
        splitter = QtGui.QSplitter(self.ORIENATATION, parent)
        for child in self.children:
            child.render(splitter)
            splitter.addWidget(child._widget)
        return splitter

class HSplitter(Splitter):
    ORIENATATION = QtCore.Qt.Horizontal

class VSplitter(Splitter):
    ORIENATATION = QtCore.Qt.Vertical

class Box(ControlContainer):
    WIDGET_CLASS = None
    
    def _build(self, parent):
        widget = QtGui.QWidget(parent)
        box = self.WIDGET_CLASS()
        widget.setLayout(box)
        for child in self.children:
            child.render(widget)
            box.addWidget(child._widget)
        return widget

class HBox(Box):
    WIDGET_CLASS = QtGui.QHBoxLayout

class VBox(Box):
    WIDGET_CLASS = QtGui.QVBoxLayout

class Button(Control):
    def _build(self, parent):
        btn = QtGui.QPushButton(parent)
        btn.clicked.connect(self._handle_click)
        return btn
    
    def _handle_click(self):
        self.clicked = 1
        self.clicked = 0
    
    @ui_property
    def text(self, text):
        self._widget.setText(text)
        self._widget.adjustSize()

    @ui_property
    def clicked(self, _): 
        pass

class Label(Control):
    def _build(self, parent):
        lbl = QtGui.QLabel(parent)
        return lbl
    
    @ui_property
    def text(self, text):
        self._widget.setText(text)
        self._widget.adjustSize()

class LineEdit(Control):
    def _build(self, parent):
        le = QtGui.QLineEdit(parent)
        le.textChanged.connect(self._handle_change)
        return le
    
    def _handle_change(self, text):
        self.text = unicode(text)
    
    @ui_property
    def text(self, text):
        self._widget.setText(unicode(text))

class TextBox(Control):
    def _build(self, parent):
        le = QtGui.QPlainTextEdit(parent)
        le.textChanged.connect(self._handle_change)
        return le
    
    def _handle_change(self, text):
        self.text = unicode(text)
    
    @ui_property
    def text(self, text):
        self._widget.setText(unicode(text))


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    app.setStyle(QtGui.QStyleFactory.create('Cleanlooks'))

    w2 = Window(VSplitter([
            HBox([
                Label(text = "First name"),
                LineEdit(),
            ]),
            HBox([
                Label(text = "Last name"),
                LineEdit(), 
            ])
        ]),
        title = "foo", width = 700, height = 200)
    w2.render()
    app.exec_()








