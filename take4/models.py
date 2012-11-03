import itertools
from linear import LinVar, LinEq, LinSys, FreeVar, BinExpr


class BaseModel(object):
    _counter = itertools.count()
    def __init__(self, elems = (), **attrs):
        self.attrs = attrs
        self.computed_attrs = {}
        self._locked_attrs = set()
        if "width" not in self.attrs:
            self.attrs["width"] = None
        if "height" not in self.attrs:
            self.attrs["height"] = None
        self.id = self._counter.next()
        self.w = LinVar("_w%d" % (self.id,), self, "user")
        self.h = LinVar("_h%d" % (self.id,), self, "user")
        self.elems = list(elems)
        self.observers = {}
    def __repr__(self):
        attrs = ", ".join("%s=%r" % (k, v) for k, v in self.attrs.items() if v is not None)
        elems = ", ".join(repr(e) for e in self.elems)
        if attrs and elems:
            return "%s(%s)[%s]" % (self.__class__.__name__, elems, attrs)
        elif attrs:
            return "%s[%s]" % (self.__class__.__name__, attrs)
        else:
            return "%s(%s)" % (self.__class__.__name__, elems)

    def __getitem__(self, attrs):
        self.attrs.update(attrs)
    def __or__(self, other):
        return HLayoutModel.combine(self, other)
    def __sub__(self, other):
        return VLayoutModel.combine(self, other)
    def __neg__(self):
        return self
    def X(self, w = None, h = None):
        if w:
            self.attrs["width"] = w
        if h:
            self.attrs["height"] = h
        return self
    def get_constraints(self):
        if self.attrs["width"]:
            yield LinEq(self.w, self.attrs["width"])
        if self.attrs["height"]:
            yield LinEq(self.h, self.attrs["height"])
        for e in self.elems:
            for cons in e.get_constraints():
                yield cons
    
    def set(self, var, value):
        if var == self.w:
            self.set("width", value)
        elif var == self.h:
            self.set("height", value)

        old = self.attrs.get(var, NotImplemented)
        if old != value:
            if var in self._locked_attrs:
                raise ValueError("cyclic dependency: %r is being recursively re-set")
            self._locked_attrs.add(var)

            print "SET %r = %r (%r)" % (var, value, old)
            self.attrs[var] = value
            self._invoke_observers(var, value)
            for k, func in self.computed_attrs:
                self.set(k, func())
            self._locked_attrs.discard(var)
    
    def _invoke_observers(self, var, value):
        for callback in self.observers.get(var, ()):
            callback(var, value)
    
    def when_changed(self, var, callback):
        if var not in self.observers:
            self.observers[var] = []
        self.observers[var].append(callback)


#===================================================================================================
# Layout combinators
#===================================================================================================
class LayoutModel(BaseModel):
    def __init__(self, elems, **attrs):
        BaseModel.__init__(self, elems, **attrs)
        self.scroller = LinVar("_s%d" % (self.id,), self, "padding")
        self.padders = {}
        self.offsets = {}
    
    @classmethod
    def combine(cls, lhs, rhs):
        if isinstance(lhs, cls):
            if isinstance(rhs, cls):
                lhs.elems.extend(rhs.elems)
                return lhs
            else:
                lhs.elems.append(rhs)
                return lhs
        elif isinstance(rhs, cls):
            rhs.insert(0, lhs)
            return rhs
        else:
            return cls([lhs, rhs])

    def _get_padder(self, e):
        if e not in self.padders:
            self.padders[e] = LinVar("_p%d" % (e.id,), self, "padding")
        return self.padders[e]
    def _get_offset(self, e):
        if e not in self.offsets:
            self.offsets[e] = LinVar("_o%d" % (e.id,), self, "offset")
        return self.offsets[e]
    
    @classmethod
    def foreach(cls, func, array):
        return cls([func(elem) for elem in array])

class HLayoutModel(LayoutModel):
    def get_constraints(self):
        for cons in LayoutModel.get_constraints(self):
            yield cons
        for i, e in enumerate(self.elems):
            yield LinEq(sum(e.w for e in self.elems[:i]), self._get_offset(e))
        yield LinEq(sum(e.w for e in self.elems) + self.scroller, self.w)
        for e in self.elems:
            yield LinEq(e.h + self._get_padder(e), self.h)

class VLayoutModel(LayoutModel):
    def get_constraints(self):
        for cons in LayoutModel.get_constraints(self):
            yield cons
        for i, e in enumerate(self.elems):
            yield LinEq(sum(e.h for e in self.elems[:i]), self._get_offset(e))
        yield LinEq(sum(e.h for e in self.elems) + self.scroller, self.h)
        for e in self.elems:
            yield LinEq(e.w + self._get_padder(e), self.w)

class Splitter(BaseModel):
    pass

#===================================================================================================
# Atoms
#===================================================================================================
class AtomModel(BaseModel):
    def __init__(self, **attrs):
        BaseModel.__init__(self, **attrs)

class LabelModel(AtomModel):
    pass
class ButtonModel(AtomModel):
    pass


#===================================================================================================
# Solver
#===================================================================================================
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
    
#    def _order_of(self, eq):
#        ORDERED_TYPES = ("user", "offset", "padding", "input")
#        if isinstance(eq.lhs, LinVar):
#            return ORDERED_TYPES.index(eq.lhs.type)
#        elif isinstance(eq.rhs, LinVar):
#            return ORDERED_TYPES.index(eq.rhs.type)
#        else:
#            return 0

    def _unify(self):
        linsys = LinSys(list(self.root.get_constraints()))
        linsys.append(LinEq(self.root.w, LinVar("WindowWidth", None, "input")))
        linsys.append(LinEq(self.root.h, LinVar("WindowHeight", None, "input")))
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
        
        class RecEvalDict(object):
            def __getitem__(self, key):
                return rec_eval(key)
        rec_eval_dict = RecEvalDict()
        
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
    root = (LabelModel(text = "foo", width = x) | LabelModel(text = "bar", width = x)).X(200,50)

    linsys = LinSys(list(root.get_constraints()))
    linsys.append(LinEq(root.w, LinVar("WindowWidth", None, "input")))
    linsys.append(LinEq(root.h, LinVar("WindowHeight", None, "input")))
    #print linsys
    
    print "==========="

    solver = ModelSolver(root)
    print solver





