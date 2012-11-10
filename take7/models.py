import itertools
from linsys import LinVar, LinEq
from solver import ModelSolver


def Default(value):
    return LinVar("_d%d" % (BaseModel._counter.next()), None, "user", default = value)

class BaseModel(object):
    _counter = itertools.count()
    def __init__(self, **attrs):
        self.attrs = attrs
        self.id = self._counter.next()
        self.width = LinVar("_w%d" % (self.id,), self, "cons")
        self.height = LinVar("_h%d" % (self.id,), self, "cons")
        if self.attrs.get("width", None) is None:
            self.attrs["width"] = self.width
        if self.attrs.get("height", None) is None:
            self.attrs["height"] = self.height

    def get_constraints(self):
        yield LinEq(self.width, self.attrs["width"])
        yield LinEq(self.height, self.attrs["height"])

    def generate_dom(self, solver):
        raise NotImplementedError()

class LayoutModel(BaseModel):
    def __init__(self, children, **attrs):
        BaseModel.__init__(self, **attrs)
        self.children = children
        self._scroller = LinVar("_s%d" % (self.id), self, "padding")

    def _get_padder(self, child):
        return LinVar("_p%d" % (child.id,), self, "padding")
    def _get_offset(self, child):
        return LinVar("_o%d" % (child.id,), self, "padding")
    
    def get_constraints(self):
        for cons in BaseModel.get_constraints(self):
            yield cons
        for child in self.children:
            for cons in child.get_constraints():
                yield cons

class Horizontal(LayoutModel):
    def __str__(self):
        return "(%s)[%s]" % (" | ".join(str(child) for child in self.children),
            " ".join("%s=%r" % (k, v) for k, v in self.attrs.items()))
    
    def get_constraints(self):
        for cons in LayoutModel.get_constraints(self):
            yield cons
        yield LinEq(self.width, sum(child.width for child in self.children) + self._scroller)
        for i, child in enumerate(self.children):
            yield LinEq(child.height + self._get_padder(child), self.attrs["height"])
            yield LinEq(self._get_offset(child), sum(child.width for child in self.children[:i]))

    def generate_dom(self, solver):
        blocks = [[]]
        has_free = False
        for child in self.children:
            if solver.is_free(child.width):
                if has_free:
                    blocks.append([])
                    #has_free = False
                has_free = True
                blocks[-1].append((child, child.width))
            else:
                blocks[-1].append((child, None))
        for b in blocks:
            print b


class Vertical(LayoutModel):
    def __str__(self):
        return "(%s)[%s]" % (" --- ".join(str(child) for child in self.children),
            " ".join("%s=%r" % (k, v) for k, v in self.attrs.items()))

class Atom(BaseModel):
    def __init__(self, name, **attrs):
        BaseModel.__init__(self, **attrs)
        self.name = name
    def __str__(self):
        return "%s[%s]" % (self.name, " ".join("%s=%r" % (k, v) for k, v in self.attrs.items()))




if __name__ == "__main__":
    x = LinVar("x")
    m = Horizontal([
            Atom("label", text="foo", height=60),
            Atom("label", text="bar", height=80),
            Atom("label", text="bar", height=80),
        ], width=300, height=100)
    #print m
    solver = ModelSolver(m)
    #print solver
    #print list(solver.get_freevars())
    #print solver.update({"_w1" : 30})
    m.generate_dom(solver)







