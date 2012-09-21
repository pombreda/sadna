import pygtk
pygtk.require('2.0')
import gtk


class UNSPEC(object):
    pass

class UIElement(object):
    def resize(self, w, h):
        raise NotImplementedError()

class H(UIElement):
    def __init__(self, *children):
        self.children = list(children)

class V(UIElement):
    def __init__(self, *children):
        self.children = list(children)

class Widget(UIElement):
    def get_default_size(self):
        return UNSPEC, UNSPEC

class Button(UIElement):
    def __init__(self, text, image = None):
        self.text = text
        self.image = image

class Label(Widget):
    pass




