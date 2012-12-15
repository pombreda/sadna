import itertools

class LinVar(object):
    def __init__(self, name):
        self.name = name
class LinEq(object):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

class Node(object):
    _counter = itertools.count()
    def __init__(self):
        self.id = self._counter.next()
        self.width = LinVar("_w%d" % (self.id,))
        self.height = LinVar("_h%d" % (self.id,))
        self.width_expr = None
        self.height_expr = None
    
    def X(self, w, h):
        self.width_expr = w
        self.height_expr = h
    def __or__(self, other):
        return HorNode.compose(self, other)
    def __neg__(self):
        return self
    def __sub__(self, other):
        return VerNode.compose(self, other)
    
    def get_constraints(self):
        if self.width_expr:
            yield LinEq(self.width, self.width_expr)
        if self.height_expr:
            yield LinEq(self.height, self.height_expr)

class LayoutNode(Node):
    def __init__(self, elements):
        Node.__init__(self)
        self.elements = elements
        self.total = LinVar("_t%d" % (self.id,))
        self.scroll = LinVar("_s%d" % (self.id,))
    @classmethod
    def compose(cls, lhs, rhs):
        if isinstance(lhs, cls) and isinstance(rhs, cls):
            lhs.elements.extend(rhs.elements)
            return lhs
        elif isinstance(lhs, cls):
            lhs.elements.append(rhs)
            return lhs
        elif isinstance(rhs, cls):
            rhs.elements.insert(0, lhs)
            return rhs
        else:
            return cls([lhs, rhs])
    
    def get_padder(self, elem):
        return LinVar("_p%d" % (elem.id,))

    @classmethod
    def foreach(cls, iterable):
        # HorNode.foreach(RadioBox(checked = v == i) for i in range(4))
        return cls(list(iterable))


class HorNode(LayoutNode):
    def get_constraints(self):
        for con in LayoutNode.get_constraints():
            yield con
        for elem in self.elements:
            for con in elem.get_constraints():
                yield con
            yield LinEq(self.height, elem.height + self.get_padder(elem))
        yield LinEq(self.total, sum(elem.width for elem in self.elements))
        yield LinEq(self.width, self.total + self.scroll)

class VerNode(LayoutNode):
    def get_constraints(self):
        for con in LayoutNode.get_constraints():
            yield con
        for elem in self.elements:
            for con in elem.get_constraints():
                yield con
            yield LinEq(self.width, elem.width + self.get_padder(elem))
        yield LinEq(self.total, sum(elem.height for elem in self.elements))
        yield LinEq(self.height, self.total + self.scroll)

class AtomNode(Node):
    def __init__(self, **attrs):
        Node.__init__(self)
        self.attrs = attrs
    
    def get_constraints(self):
        for con in Node.get_constraints(self):
            yield con
        for con in self.get_attr_constraints(self):
            yield con
    
    def get_attr_constraints(self):
        return ()

class LabelNode(AtomNode):
    def __init__(self):
        pass

class TextNode(AtomNode):
    pass

class RadioNode(AtomNode):
    def __init__(self, **attrs):
        AtomNode.__init__(self, **attrs)
        self.checked = LinVar("_checked%d" % (self.id,))

    def get_attr_constraints(self):
        checked = self.attrs.get("checked")
        if not checked:
            return
        lincheck = linearize(checked)
        yield LinEq()


class ImageNode(AtomNode):
    def __init__(self):
        pass
    
class ButtonNode(AtomNode):
    def __init__(self, **attrs):
        AtomNode.__init__(self, **attrs)
        self.clicked = LinVar("_clicked%d" % (self.id,))











