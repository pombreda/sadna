import itertools
from linear_system import LinVar, LinEq, LinSys, FreeVar, BinExpr
import pygtk
pygtk.require('2.0')
import gtk
gtk.widget_set_default_direction(gtk.TEXT_DIR_LTR)


class BaseModel(object):
    ATTRS = {}
    _counter = itertools.count()
    def __init__(self, children, **attrs):
        self.id = self._counter.next()
        self.children = children
        self.attrs = {"width" : None, "height" : None}
        self.attrs.update(self.ATTRS)
        self._observers = {}
        self._computed_attrs = {}
        self[attrs]
        self.width = LinVar("_w%d" % (self.id,))
        self.height = LinVar("_h%d" % (self.id,))
        if self.attrs["width"] is None:
            self.attrs["width"] = self.width
        if self.attrs["height"] is None:
            self.attrs["height"] = self.height
        self._gtkobj = None
    
    def __repr__(self):
        attrs = ", ".join(sorted("%s = %r" % (k, v) for k, v in self.attrs.items()))
        children = ", ".join(repr(child) for child in self.children)
        text = self.__class__.__name__
        if children:
            text += "(" + children + ")"
        if attrs:
            text += "[" + attrs + "]"
        return text
    
    #
    # DSL API
    #
    def __getitem__(self, attrs):
        for k, v in attrs.items():
            if k not in self.attrs:
                raise ValueError("Unknown attr %r for %r" % (k, self))
            self.attrs[k] = v
    def __or__(self, other):
        return HLayoutModel.combine(self, other)
    def __neg__(self, other):
        return self
    def __sub__(self, other):
        return VLayoutModel.combine(self, other)
    def X(self, w = None, h = None):
        if w is not None:
            self.attrs["width"] = w
        if h is not None:
            self.attrs["height"] = h
        return self
    def get_constraints(self):
        yield LinEq(self.width, self.attrs["width"])
        yield LinEq(self.height, self.attrs["height"])
        for child in self.children:
            for cons in child.get_constraints():
                yield cons

    #
    # Programmatic API
    #
    def set(self, attr, value):
        if attr not in self.attrs:
            raise KeyError("Unknown attr %r" % (attr,))
        old = self._computed_attrs.get(attr, None)
        if old != value:
            self._computed_attrs[attr] = value
            for callback in self._observers.get(attr, ()):
                callback(value)
    
    def when_changed(self, attr, callback):
        if attr not in self.attrs:
            raise KeyError("Unknown attr %r" % (attr,))
        if attr not in self._observers:
            self._observers[attr] = []
        self._observers[attr].append(callback)

class TopLevelModel(BaseModel):
    ATTRS = {"title" : "Untitled"}
    
    def __init__(self, child, **attrs):
        BaseModel.__init__(self, [child], **attrs)
    
    def render(self):
        linsys = LinSys(list(self.get_constraints()))
        linsys.solve()

#===================================================================================================
# Layout
#===================================================================================================
class BaseLayoutModel(BaseModel):
    def __init__(self, children, **attrs):
        BaseModel.__init__(self, children, **attrs)
        self._scroller = LinVar("_s%d" % (self.id,), self, "padding")
    def _get_padder(self, child):
        return LinVar("_p%d" % (child.id,), self, "padding")
    def _get_offset(self, child):
        return LinVar("_o%d" % (child.id,), self, "offset")
    
    @classmethod
    def combine(cls, lhs, rhs):
        if isinstance(lhs, cls) and isinstance(rhs, cls):
            lhs.children.extend(rhs.children)
            return lhs
        elif isinstance(lhs, cls):
            lhs.children.append(rhs)
            return lhs
        elif isinstance(rhs, cls):
            rhs.children.insert(0, lhs)
            return rhs
        else:
            return cls([lhs, rhs])


class HLayoutModel(BaseLayoutModel):
    def get_constraints(self):
        for cons in BaseLayoutModel.get_constraints(self):
            yield cons
        yield LinEq(self.attrs["width"], sum(child.attrs["width"] for child in self.children) + self._scroller)
        for i, child in enumerate(self.children):
            yield LinEq(child.attrs["height"] + self._get_padder(child), self.attrs["height"])
            yield LinEq(self._get_offset(child), sum(child.attrs["width"] for child in self.children[:i]))
    
    #def build(self, solver):
    #    for child in self.children:
    #        if child.attrs["width"]

class VLayoutModel(BaseLayoutModel):
    pass

#===================================================================================================
# atoms
#===================================================================================================
class AtomModel(BaseModel):
    def __init__(self, **attrs):
        BaseModel.__init__(self, (), **attrs)

class Label(AtomModel):
    ATTRS = {"text" : ""}
    
    def build(self, solver):
        lbl = gtk.Label(repr(self))
        self.when_changed("text", self.set_text)
        return lbl
    
    def set_text(self, text):
        self._gtkobj.set_text(text)

class Button(AtomModel):
    ATTRS = {"text" : "", "clicked" : 0}
    
    def build(self, solver):
        btn = gtk.Button(repr(self))
        self.when_changed("text", self.set_text)
        btn.connect("clicked", self._handle_click)
        return btn
    
    def _handle_click(self, *_):
        self.set("clicked", 1)
        self.set("clicked", 0)
    
    def set_text(self, text):
        self._gtkobj.set_text(text)


#===================================================================================================
# Solver
#===================================================================================================
class RecEvalDict(object):
    def __init__(self, rec_eval):
        self.rec_eval = rec_eval
    def __getitem__(self, key):
        return self.rec_eval(key)


class ModelSolver(object):
    def __init__(self, root):
        self.root = root
        self.solution = self._unify()
        for var in self._get_freevars():
            if var.type == "padding":
                self.solution[var] = 0
        self.dependencies = self._calculate_dependencies()
        self.results = {}
    
    def __str__(self):
        return "\n".join("%s = %s" % (k, v) for k, v in self.solution.items()
            if not isinstance(v, FreeVar))
    
    def __getitem__(self, var):
        return self.results[var]

    def _unify(self):
        linsys = LinSys(list(self.root.get_constraints()))
        linsys.append(LinEq(self.root.attrs["width"], LinVar("WindowWidth", None, "input")))
        linsys.append(LinEq(self.root.attrs["height"], LinVar("WindowHeight", None, "input")))
        return linsys.solve()

    def _get_freevars(self):
        for k, v in self.solution.items():
            if isinstance(v, FreeVar):
                yield k
    
    def _get_equation_vars(self, expr):
        if isinstance(expr, (str, LinVar, FreeVar)):
            return {expr.name}
        elif isinstance(expr, BinExpr):
            return self._get_equation_vars(expr.lhs) | self._get_equation_vars(expr.rhs)
        else:
            return set()
    
    def _transitive_closure(self, deps):
        oldlen = -1
        while oldlen != len(deps):
            oldlen = len(deps)
            for resvar, expr in self.solution.items():
                depvars = self._get_equation_vars(expr)
                if deps & depvars:
                    deps.add(resvar)
    
    def _calculate_dependencies(self):
        dependencies = {}
        for var in self._get_freevars():
            dependencies[var] = {var}
            self._transitive_closure(dependencies[var])
        return dependencies
    
    def update(self, freevars):
        changed = {}
        for k in freevars.keys():
            if not self.is_free(k):
                raise ValueError("%r is not a free variable" % (k,))
            for k2 in self.dependencies[k]:
                v = self.results.pop(k2, NotImplemented)
                if k2 not in changed:
                    changed[k2] = v
        
        def rec_eval(key):
            if key in self.results:
                if self.results[key] is NotImplemented:
                    raise ValueError("cyclic dependency found")
                return self.results[key]
            # set up sentinel to detect cycles
            self.results[key] = NotImplemented
            v = self.solution[key]
            if isinstance(v, FreeVar):
                if key.default is not None:
                    self.results[key] = freevars[key]
                else:
                    self.results[key] = freevars[key]
            elif hasattr(v, "eval"):
                self.results[key] = v.eval(rec_eval_dict)
            else:
                self.results[key] = v
            return self.results[key]

        rec_eval_dict = RecEvalDict(rec_eval)
        for k in self.solution:
            rec_eval(k)
        
        for k, oldv in changed.items():
            v = self.results[k]
            if oldv != v and k.owner:
                k.owner.set(k, v)
        
        return self.results
    
    def is_free(self, var):
        return isinstance(self.solution[var], FreeVar)





if __name__ == "__main__":
    x = LinVar("x")
    root = Label(text = "hello").X(x, 50) | Label(text = "world").X(x, 50)
    solver = ModelSolver(root)
    print solver
    
    #print root
    #ls = LinSys(list(root.get_constraints()))
    #print ls
    #print ls.solve()
    



