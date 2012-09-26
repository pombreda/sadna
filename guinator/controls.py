def ui_property(func):
    def getter(self):
        return self._attrs[func.__name__]
    def setter(self, value):
        self._attrs[func.__name__] = value
        func(self, value)
        self._on_change(func.__name__)
    return property(getter, setter)

class Control(object):
    @ui_property
    def width(self):
        pass

    @ui_property
    def height(self):
        pass


class Window(Control):
    @ui_property
    def title(self, text):
        self.gtkobj.set_title(text)


