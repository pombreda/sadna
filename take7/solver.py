from linsys import LinVar, LinSys, FreeVar, BinExpr


class RecEvalDict(object):
    __slots__ = ["rec_eval"]
    def __init__(self, rec_eval):
        self.rec_eval = rec_eval
    def __getitem__(self, key):
        return self.rec_eval(key)

class ModelSolver(object):
    def __init__(self, root):
        self.root = root
        self.linsys = LinSys(list(self.root.get_constraints()))
        self._solve_and_eliminate_padding()
        self.dependencies = self._calculate_dependencies()
        self.results = {} #v : v.default for v in self.get_freevars() if v.default is not None}
        self.observed = {}
    
    def __str__(self):
        return "\n".join("%s = %s" % (k, v) for k, v in self.solution.items()
            if not isinstance(v, FreeVar))
    
    def __getitem__(self, var):
        if var in self.results:
            return self.results[var]
        return self.solution[var]

    def __contains__(self, var):
        return var in self.results or var in self.solution

    def _resolve(self):
        freeness_relation = [None, "user", "offset", "cons", "padding", "default", "input"]
        var_order = sorted(self.linsys.get_vars(), key = lambda v: freeness_relation.index(v.type))
        self.solution = self.linsys.solve(var_order)

    def _solve_and_eliminate_padding(self):
        self._resolve()
        for var in self.get_freevars():
            if var.type == "padding":
                self.solution[var] = 0.0
        
        #fixed = set()
        #unfixed = set()
        #for var, val in self.solution.items():
        #    if var.type == "padding":
        #        if isinstance(val, (int, float)):
        #            fixed.add(var)
        #        else:
        #            unfixed.add(var)
        #
        #unfixed -= fixed
        #print "!! unfixed =", unfixed
        #for var in list(unfixed):
        #    try:
        #        self._resolve({var})
        #    except NoSolutionsExist:
        #        unfixed.discard(var)
        #self._resolve(unfixed)

    def get_freevars(self):
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
        for var in self.get_freevars():
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
                    raise ValueError("cyclic dependency found, var = %r" % (key,))
                return self.results[key]
            # set up sentinel to detect cycles
            self.results[key] = NotImplemented
            v = self.solution[key]
            if isinstance(v, FreeVar):
                if key not in freevars and key.default is not None:
                    self.results[key] = key.default
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
            if oldv != v and k in self.observed:
                for cb in self.observed[k]:
                    cb(v)
        
        return self.results
    
    def is_free(self, var):
        return isinstance(self.solution[var], FreeVar)
    
    def watch(self, var, callback):
        if var not in self.observed:
            self.observed[var] = []
        self.observed[var].append(callback)
    
    def invoke_observers(self):
        for var, callbacks in self.observed.items():
            if var not in self:
                continue
            val = self[var]
            for cb in callbacks:
                cb(val)







