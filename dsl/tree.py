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
    
    def __unicode__(self):
        return "%s(%s)" % (self.root, ", ".join(repr(x) for x in self.subtrees))

    __repr__ = __unicode__
        
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

