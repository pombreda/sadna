import itertools
from linear import LinVar, LinEq, LinSys, FreeVar, BinExpr


class LinearConstraint(object):
    _counter = itertools.count()
    def __init__(self, elems = (), **attrs):
        self.attrs = attrs
        self.id = self._counter.next()
        self.w = LinVar("w%d" % (self.id,), self, "user")
        self.h = LinVar("h%d" % (self.id,), self, "user")
        self.w.owner = self
        self.h.owner = self
        self.attrs["w_constraint"] = None
        self.attrs["h_constraint"] = None
        self.elems = list(elems)
    def __repr__(self):
        attrs = ", ".join("%s=%r" % (k.split("_constraint")[0], v) for k, v in self.attrs.items() 
            if not k.endswith("_constraint") or v is not None)
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
        return HLayout.combine(self, other)
    def __sub__(self, other):
        return VLayout.combine(self, other)
    def __neg__(self):
        return self
    def X(self, w = None, h = None):
        if w:
            self.attrs["w_constraint"] = w
        if h:
            self.attrs["h_constraint"] = h
        return self
    def get_constraints(self):
        if self.attrs["w_constraint"]:
            yield LinEq(self.w, self.attrs["w_constraint"])
        if self.attrs["h_constraint"]:
            yield LinEq(self.h, self.attrs["h_constraint"])
        for e in self.elems:
            for cons in e.get_constraints():
                yield cons

#===================================================================================================
# Layout combinators
#===================================================================================================
class Layout(LinearConstraint):
    def __init__(self, elems, **attrs):
        LinearConstraint.__init__(self, elems, **attrs)
        self.scroller = LinVar("scroller%d" % (self.id,), self, "overflow")
        self.padders = {}
    
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
            self.padders[e] = LinVar("padding%d" % (e.id,), e, "padding")
        return self.padders[e]
    
    @classmethod
    def foreach(cls, func, array):
        return cls([func(elem) for elem in array])

class HLayout(Layout):
    def get_constraints(self):
        for cons in Layout.get_constraints(self):
            yield cons
        yield LinEq(sum(e.w for e in self.elems) + self.scroller, self.w)
        for e in self.elems:
            yield LinEq(e.h + self._get_padder(e), self.h)

class VLayout(Layout):
    def get_constraints(self):
        for cons in Layout.get_constraints(self):
            yield cons
        yield LinEq(sum(e.h for e in self.elems) + self.scroller, self.h)
        for e in self.elems:
            yield LinEq(e.w + self._get_padder(e), self.w)

#===================================================================================================
# Atoms
#===================================================================================================
class Atom(LinearConstraint):
    def __init__(self, **attrs):
        LinearConstraint.__init__(self, **attrs)

class Label(Atom):
    pass
class Button(Atom):
    pass
class TextBox(Atom):
    pass
class Image(Atom):
    pass
class CheckBox(Atom):
    pass
class RadioBox(Atom):
    pass
class ComboBox(Atom):
    pass
class ListBox(Atom):
    pass
class Slider(Atom):
    pass


#===================================================================================================
# APIs
#===================================================================================================
class DependencySolver(object):
    def __init__(self, root):
        self.root = root
        self.solution = self._unify()
        for var in self._get_freevars():
            if var.type in ("padding", "overflow"):
                self.solution[var] = 0
        self.dependencies = self._calculate_dependencies()
        self.results = {}
    
    def __str__(self):
        return "\n".join("%s = %s" % (k, v) for k, v in self.solution.items())
    
    def _unify(self):
        linsys = LinSys(list(self.root.get_constraints()))
        ww = LinVar("WindowWidth", None, "input")
        wh = LinVar("WindowHeight", None, "input")
        linsys.append(LinEq(self.root.w, ww))
        linsys.append(LinEq(self.root.h, wh))
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
    
    def eval(self, freevars):
        for k in freevars.keys():
            for k2 in self.dependencies[k]:
                self.results.pop(k2, None)
        
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
        return self.results
    
    def is_free(self, var):
        return isinstance(self.solution[var], FreeVar)


if __name__ == "__main__":
    x = LinVar("x")
    root = (Label(text = "foo").X(x,50) | Label(text = "bar").X(2 * x,50) | Label(text = "spam").X(50,60))
    depsol = DependencySolver(root)
    print depsol
    print depsol.eval({"WindowWidth" : 300, "WindowHeight" : 200})
    print depsol.eval({"WindowHeight" : 400})





