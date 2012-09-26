import itertools
from dsl import parse_layout
from dsl.ast import ContainerAST, AtomicWidget, ExpressionAST, ArithmeticExpression

import pygtk
pygtk.require('2.0')
import gtk

gtk.widget_set_default_direction(gtk.TEXT_DIR_LTR)


class CyclicDependency(Exception):
    pass


class Variable(object):
    _counter = itertools.count()
    def __init__(self, name = None):
        self.name = name
        self.id = self._counter.next()
    def __repr__(self):
        return "var%d" % (self.id,)

class Expr(object):
    def __init__(self, op, lhs, rhs):
        pass


class UIElement(object):
    def __init__(self, attrs):
        self.attrs = attrs
        if "width" not in self.attrs or self["width"] is None or self["width"] == "?":
            self["width"] = None #Variable()
        if "height" not in self.attrs or self["height"] is None or self["height"] == "?":
            self["height"] = None #Variable()
    def __contains__(self, name):
        return name in self.attrs
    def __getitem__(self, name):
        return self.attrs[name]
    def __setitem__(self, name, value):
        self.attrs[name] = value
    def unify(self):
        pass

class Layout(UIElement):
    HOR = "H"
    VER = "V"
    
    def __init__(self, dir, subelems, attrs):
        UIElement.__init__(self, attrs)
        self.dir = dir
        self.subelems = list(subelems)
        self.constraints = []
    def __repr__(self):
        return "%s[%s, %s]" % (self.dir, ", ".join(repr(e) for e in self.subelems), 
            ", ".join("%s=%r" % (k, v) for k, v in self.attrs.items()))
    def unify(self):
        total_w = self["width"]
        total_h = self["height"]
        for e in self.subelems:
            e.unify()
        
        widths = [e["width"] for e in self.subelems]
        heights = [e["heights"] for e in self.subelems]
        
        if self.dir == self.HOR:
            max_h = max(heights)
            if max_h is None:
                pass
            else:
                pass
            
        else:
            pass
        
        
    

class Padding(object):
    def __init__(self, elem, extra_width, extra_height):
        self.elem = elem
        self.extra_width = extra_width
        self.extra_height = extra_height

class Atom(UIElement):
    def __init__(self, name, attrs):
        UIElement.__init__(self, attrs)
        self.name = name
    def __repr__(self):
        return "%s(%s)" % (self.name, ", ".join("%s=%r" % (k, v) for k, v in self.attrs.items()))


def simplify_expression(node):
    if node.root == '""':
        return node.subtrees[0].root
    else:
        return node

def simplify_attrs(node):
    attrs = node.attributes.copy()
    attrs["width"] = node.width
    attrs["height"] = node.height
    for k, val in attrs.items():
        if isinstance(val, ExpressionAST):
            attrs[k] = simplify_expression(val)
    return attrs

def _ast_to_dom(dom, doc, node):
    if isinstance(node, ContainerAST):
        return Layout(Layout.VER if node.direction.startswith("v") else Layout.HOR, 
            [_ast_to_dom(dom, doc, n) for n in node.subtrees], 
            simplify_attrs(node))
    elif isinstance(node, AtomicWidget):
        if node.kind in doc:
            if node.kind not in dom:
                dom[node.kind] = None
                dom[node.kind] = _ast_to_dom(dom, doc, doc[node.kind])
            if dom[node.kind] is None:
                raise CyclicDependency("%r is part of a circle" % (node.kind,))
            return dom[node.kind]
        else:
            return Atom(node.kind, simplify_attrs(node))
    else:
        raise TypeError(type(node), node)

def ast_to_dom(doc):
    dom = {}
    for name, node in doc.items():
        if name not in dom:
            dom[name] = _ast_to_dom(dom, doc, node)
    return dom

def run(dom):
    window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    window.set_title("Hello Buttons!")
    window.connect("delete_event", lambda *args: False)
    window.connect("destroy", lambda *args: gtk.main_quit())
        



if __name__ == "__main__":
    doc = parse_layout("""
    foo <- (label:20x20)[text="hello"] | (label)[text="world"]
    
    """)
    
    dom = ast_to_dom(doc)
    foo = dom["foo"]
    print foo


