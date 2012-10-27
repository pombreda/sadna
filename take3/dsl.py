import itertools
from linear import LinVar, LinEq, LinSys, FreeVar


class LinearElement(object):
    _counter = itertools.count()
    def __init__(self, elems = (), **attrs):
        self.attrs = attrs
        self.id = self._counter.next()
        self.w = LinVar("w%d" % (self.id,), self, "width")
        self.h = LinVar("h%d" % (self.id,), self, "height")
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
class Layout(LinearElement):
    def __init__(self, elems, **attrs):
        LinearElement.__init__(self, elems, **attrs)
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
class Atom(LinearElement):
    def __init__(self, **attrs):
        LinearElement.__init__(self, **attrs)

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
def unify(root):
    linsys = LinSys(list(root.get_constraints()))
    ww = LinVar("WindowWidth", None, "input")
    wh = LinVar("WindowHeight", None, "input")
    linsys.append(LinEq(root.w, ww))
    linsys.append(LinEq(root.h, wh))
    return linsys.solve()

def enum_freevars(solution):
    for k, v in solution.items():
        if isinstance(v, FreeVar):
            yield k

def evaluate(solution, freevars):
    output = {}
    
    class RecEvalDict(object):
        def __getitem__(self, key):
            return rec_eval(key)
    rec_eval_dict = RecEvalDict()

    def rec_eval(key):
        if key in output:
            if output[key] is NotImplemented:
                raise ValueError("cyclic dependency found")
            return output[key]
        # set up sentinel to detect cycles
        output[key] = NotImplemented
        v = solution[key]
        if isinstance(v, FreeVar):
            output[key] = freevars[key]
        elif hasattr(v, "eval"):
            output[key] = v.eval(rec_eval_dict)
        else:
            output[key] = v
        return output[key]
    
    for k in solution:
        rec_eval(k)
    return output


if __name__ == "__main__":
    x = LinVar("x")
    root = (Label(text = "foo").X(x,50) | Label(text = "bar").X(2 * x,50) | Label(text = "spam").X(50,60)).X(None, 100)
    sol = unify(root)
    print sol
    ev = evaluate(sol, {"WindowWidth" : 300, "scroller2" : 150})
    print ev






