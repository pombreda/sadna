import itertools
import numpy

EPSILON = 1e-50
scalar_types = (int, long, float)

class NoSolutionsExist(Exception):
    pass

def eliminate(mat):
    """Original code by Jarno Elonen, Public Domain
    http://elonen.iki.fi/code/misc-notes/python-gaussj/index.html"""
    m, n = mat.shape
    for y in range(0, m):
        maxrow = y
        # Find max pivot
        for y2 in range(y+1, m):
            if abs(mat[y2][y]) > abs(mat[maxrow][y]):
                maxrow = y2
        mat[[y, maxrow],:] = mat[[maxrow, y],:]
        if y >= n:
            # more rows than columns!
            raise ValueError("more rows than columns")
            #continue
        if abs(mat[y][y]) <= EPSILON:
            # Singular
            continue
        # Eliminate column y
        for y2 in range(y+1, m):
            c = mat[y2][y] / mat[y][y]
            for x in range(y, n):
                mat[y2][x] -= mat[y][x] * c
    
    # Backsubstitute
    for y in range(m-1, -1, -1):
        for i in range(0, n):
            if abs(mat[y][i]) > EPSILON:
                break
        else:
            continue
        c = mat[y][i]
        for y2 in range(0, y):
            for x in range(n-1, y-1, -1):
                mat[y2][x] -= mat[y][x] * mat[y2][i] / c
        # Normalize row y
        for x in range(i, n):
            mat[y][x] /= c

def sub(a,b):
    return a-b
sub.__name__ = "-"

def mul(a,b):
    return a*b
mul.__name__ = "*"

class ExprMixin(object):
    __slots__ = []
    def __mul__(self, other):
        if isinstance(other, scalar_types) and abs(other) <= EPSILON:
            return 0.0
        return BinExpr(mul, self, other)
    def __sub__(self, other):
        if isinstance(other, scalar_types) and abs(other) <= EPSILON:
            return self
        return BinExpr(sub, self, other)
    def __rmul__(self, other):
        if isinstance(other, scalar_types) and abs(other) <= EPSILON:
            return 0.0
        return BinExpr(mul, other, self)
    def __rsub__(self, other):
        if isinstance(other, scalar_types) and abs(other) <= EPSILON:
            return self
        return BinExpr(sub, other, self)

class BinExpr(ExprMixin):
    __slots__ = ["op", "lhs", "rhs"]
    def __init__(self, op, lhs, rhs):
        self.op = op
        self.lhs = lhs
        self.rhs = rhs
    def eval(self, freevars):
        lv = self.lhs.eval(freevars) if hasattr(self.lhs, "eval") else self.lhs
        rv = self.rhs.eval(freevars) if hasattr(self.rhs, "eval") else self.rhs
        return self.op(lv, rv)
    def __repr__(self):
        return "(%s %s %s)" % (self.lhs, self.op.__name__, self.rhs)

class FreeVar(ExprMixin):
    __slots__ = ["name"]
    def __init__(self, name):
        self.name = name
    def eval(self, freevars):
        return freevars[self.name]
    def __repr__(self):
        return "<FreeVar %s>" % (self,)
    def __str__(self):
        return str(self.name)

def solve_matrix(mat, variables):
    m, n = mat.shape
    if len(variables) != n - 1:
        raise ValueError("Expected %d variables" % (n - 1,))
    eliminate(mat)
    assignments = {}
    
    for row in mat[::-1]:
        nonzero = list(itertools.dropwhile(lambda v: abs(v) <= EPSILON, row))
        if not nonzero:
            continue
        const = nonzero.pop(-1)
        if not nonzero:
            # a row of the form (0 0 ... 0 x) means a contradiction
            raise NoSolutionsExist()
        vars = variables[-len(nonzero):]
        assignee = vars.pop(0)
        assert abs(nonzero.pop(0) - 1) <= EPSILON
        assignments[assignee] = const
        
        for i, v in enumerate(vars):
            if v not in assignments:
                assignments[v] = FreeVar(v)
            assignments[assignee] -= (-nonzero[i] * assignments[v])
    return assignments

#===================================================================================================
# linear systems
#===================================================================================================
class LinearMixin(object):
    __slots__ = []
    def __add__(self, other):
        return LinSum(self, other)
    def __radd__(self, other):
        return LinSum(other, self)
    def __sub__(self, other):
        return self + (-1 * other)
    def __rsub__(self, other):
        return other + (-1 * self)
    def __neg__(self):
        return -1 * self
    def __mul__(self, scalar):
        return Coeff(self, scalar)
    def __rmul__(self, scalar):
        return Coeff(self, scalar)

class LinEq(object):
    __slots__ = ["lhs", "rhs"]
    def __init__(self, lhs, rhs):
        if not isinstance(lhs, LinSum):
            lhs = LinSum(lhs)
        if not isinstance(rhs, LinSum):
            rhs = LinSum(rhs)
        self.lhs = lhs
        self.rhs = rhs
    def __repr__(self):
        return "%r = %r" % (self.lhs, self.rhs)

class LinVar(LinearMixin):
    __slots__ = ["name", "owner", "type", "default"]
    def __init__(self, name, owner = None, type = None, default = None):
        self.name = name
        self.owner = owner
        self.type = type
        self.default = default
    def __repr__(self):
        return self.name
    def __eq__(self, other):
        if isinstance(other, LinVar):
            return self.name == other.name
        else:
            return self.name == other
    def __ne__(self, other):
        return not (self == other)
    def __hash__(self):
        return hash(self.name)
    def __getitem__(self, default):
        self.default = default

class NonLinVar(object):
    def __init__(self, name):
        pass


class Coeff(LinearMixin):
    __slots__ = ["var", "coeff"]
    def __init__(self, var, scalar):
        if not isinstance(scalar, scalar_types):
            raise TypeError("%r is not a scalar" % (scalar,))
        if isinstance(var, Coeff):
            self.var = var.var
            self.coeff = var.coeff * scalar
        else:
            self.var = var
            self.coeff = scalar
    def __repr__(self):
        if self.coeff == 1:
            return repr(self.var)
        elif self.coeff == -1:
            return "-%r" % (self.var,)
        elif self.coeff == 0:
            return "0"
        else:
            return "%r%r" % (self.coeff, self.var)

class LinSum(LinearMixin):
    __slots__ = ["elements"]
    def __init__(self, *elements):
        self.elements = []
        for elem in elements:
            if isinstance(elem, LinSum):
                self.elements.extend(elem.elements)
            elif isinstance(elem, Coeff):
                self.elements.append(elem)
            elif isinstance(elem, LinVar):
                self.elements.append(Coeff(elem, 1))
            elif isinstance(elem, scalar_types):
                self.elements.append(elem)
            else:
                raise TypeError("cannot sum %r" % (elem,))
    def __repr__(self):
        return " + ".join(repr(e) for e in self.elements)
    def __iter__(self):
        return iter(self.elements)

class LinSys(object):
    __slots__ = ["equations"]
    def __init__(self, equations):
        self.equations = equations
    def append(self, equation):
        self.equations.append(equation)
    def extend(self, equations):
        self.equations.extend(equations)
    def __delitem__(self, index):
        del self.equations[index]
    def __str__(self):
        return "\n".join(repr(eq) for eq in self.equations)
    
    def to_matrix(self):
        vars_indexes = {}
        equations = []
        for eq in self.equations:
            vars = []
            scalars = []
            
            if isinstance(eq.lhs, LinSum):
                vars.extend(e for e in eq.lhs if isinstance(e, Coeff))
                scalars.extend(-e for e in eq.lhs if isinstance(e, scalar_types))
            elif isinstance(eq.lhs, Coeff):
                vars.append(eq.lhs)
            elif isinstance(eq.lhs, scalar_types):
                scalars.append(-eq.lhs)
            elif isinstance(eq.lhs, LinVar):
                vars.append(Coeff(eq.lhs, 1))
            else:
                raise ValueError(eq.lhs)
            
            if isinstance(eq.rhs, LinSum):
                vars.extend(-e for e in eq.rhs if isinstance(e, Coeff))
                scalars.extend(e for e in eq.rhs if isinstance(e, scalar_types))
            elif isinstance(eq.rhs, Coeff):
                vars.append(-eq.rhs)
            elif isinstance(eq.rhs, scalar_types):
                scalars.append(eq.rhs)
            elif isinstance(eq.rhs, LinVar):
                vars.append(Coeff(eq.rhs, -1))
            else:
                raise ValueError(eq.rhs)
            
            scalars = sum(scalars)
            varbins = {}
            for v in vars:
                if v.var not in vars_indexes:
                    vars_indexes[v.var] = len(vars_indexes)
                if v.var not in varbins:
                    varbins[v.var] = v.coeff
                else:
                    varbins[v.var] += v.coeff
            equations.append((varbins.items(), scalars))
        
        matrix = numpy.zeros((len(equations), len(vars_indexes) + 1), float)
        for i, (vars, scalar) in enumerate(equations):
            matrix[i, -1] = scalar
            for v, coeff in vars:
                matrix[i, vars_indexes[v]] = coeff
        
        return matrix, sorted(vars_indexes.keys(), key = lambda v: vars_indexes[v])
    
    def solve(self):
        matrix, vars = self.to_matrix()
        return solve_matrix(matrix, vars)


if __name__ == "__main__":
#    m = numpy.array([
#        [1,2,4,2], 
#        [3,7,6,8],
#    ], float)
#    
#    eliminate(m)
#    print m
#    sol = solve_matrix(m, ["x", "y", "z"])
#    print sol
#    print sol["x"].eval({"z" : 10})
#    
#    a = LinVar("a")
#    b = LinVar("b")
#    
#    ls = LinSys([
#        LinEq(2 * a + 7 * b - 2 , 9 + 2 * b),
#        LinEq(4 * a             , b + 11),
#    ])
#    print ls.solve()
#
#    ls2 = LinSys([
#        LinEq(a + b, 7),
#    ])
#    print ls2.solve()
    w2 = LinVar("w2")
    p0 = LinVar("p0")
    p1 = LinVar("p1")
    x = LinVar("x")
    o0 = LinVar("o0")
    h2 = LinVar("h2")
    o1 = LinVar("o1")
    w2 = LinVar("w2")
    WW = LinVar("WW")
    WH = LinVar("WH")

    ls = LinSys([
        LinEq(50 + p0, h2),
        LinEq(o1, 0 + x),
        LinEq(w2, 0 + x + x),
        LinEq(o0, 0),
        LinEq(50 + p1, h2),
        LinEq(h2, WH),
        LinEq(w2, WW),
    ])
    print ls
    print ls.solve()

#    x = LinVar("x")
#    y = LinVar("y")
#    z = LinVar("z")
#    w = LinVar("w")
#
#    ls = LinSys([
#        LinEq(2 * x, w),
#        LinEq(2 * y + w, z),
#        LinEq(z * 3, y + x),
#        #LinEq(),
#    ])
#    print ls.solve()




