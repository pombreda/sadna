class Tree(object):
    def __init__(self, root, subtrees=None):
        self.root = root
        if subtrees is None:
            self.subtrees = []
        else:
            self.subtrees = subtrees
        
    def __eq__(self, other):
        if not isinstance(other, Tree): 
            return NotImplemented
        return (type(self) == type(other) and 
               (self.root, self.subtrees) == (other.root, other.subtrees))    
    
    def __ne__(self, other):
        return not (self == other)
    
    def __hash__(self):
        return hash((self.root, tuple(self.subtrees)))
    
    def __repr__(self):
        return "%r(%r)" % (self.root, self.subtrees)

    @property
    def nodes(self):
        return list(PreorderWalk(self))
    
    @property
    def leaves(self):
        return [n for n in PreorderWalk(self) if not n.subtrees]
    
    @property
    def terminals(self):
        """ @return a list of the values located at the leaf nodes. """
        return [n.root for n in self.leaves]


class TreeWalk(object):
    """
    Traditional tree walks:
    - Pre-order walk
    - Post-order walk [not implemented yet]
    - In-order walk - for binary trees [not implemented yet]
    """
    class Visitor(object):
        def visit_node(self, tree_node):
            pass
        def done(self):
            return None
    
    def __init__(self, tree):
        self.tree = tree
    
    def __call__(self, visitor):
        for x in self:
            visitor.visit_node(x)
        return visitor.done()
    
    def __iter__(self):
        raise NotImplementedError
    

class PreorderWalk(TreeWalk):
    def __iter__(self):
        queue = [self.tree]
        while queue:
            top = queue[0]
            yield top
            queue[:1] = top.subtrees


class RichTreeWalk(object):
    """
    Provides advanced tree traversal by calling the visitor not only for each 
    node, but also when entering and when leaving a subtree.
    @todo: The interface of RichTreeWalk does not match that of TreeWalk; 
    should unify. 
    """
    class Visitor(object):
        SKIP = ('skip',)  # return this from enter() to prune
        def enter(self, subtree, prune=lambda:None):
            pass
        def leave(self, subtree):
            pass
        def join(self, node, prefix, infix, postfix):
            return None
        def done(self, root, final):
            return final

    def __init__(self, visitor):
        self.visitor = visitor
    
    def __call__(self, tree):
        final = self._traverse(tree)
        return self.visitor.done(tree, final)
    
    def _traverse(self, tree):
        descend = [1]
        prefix = self.visitor.enter(tree, descend.pop)
        if prefix is self.Visitor.SKIP:
            return prefix
        elif descend:
            infix = self._descend(tree)
        else:
            infix = []
        postfix = self.visitor.leave(tree)
        return self.visitor.join(tree, prefix, infix, postfix)

    def _descend(self, tree):
        return [self._traverse(sub) for sub in tree.subtrees]


