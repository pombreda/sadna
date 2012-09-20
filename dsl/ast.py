from dsl.tree import Tree


class AST(Tree):
    pass

class ControlAST(AST):
    def __unicode__(self):
        if not self.subtrees:
            return unicode(self.root)
        else:
            return u"%s\n%s" % (self.root, indent(bulleted_list(self.subtrees)))

class ASTDict(dict):
    def __unicode__(self):
        return bulleted_list(self._fmt_element(k, v)
                             for k, v in self.iteritems())

    def _fmt_element(self, k, v):
        k = unicode(k) + " -> "
        indent_by = " " * max(10, len(k))
        v = indent(unicode(v), indent_by)
        return k + v[len(k):]

    def __repr__(self):
        return unicode(self)

def bulleted_list(items, bullet="-"):
    return "\n".join(u"%s %s" % (bullet, x) for x in items)

def indent(text, indent="    "):
    return "\n".join(indent + line for line in text.splitlines())

class AtomicWidget(AST):
    def __init__(self, kind, attributes, (width, height)):
        super(AtomicWidget, self).__init__(kind, [])
        self.kind = kind
        self.attributes = attributes
        self.width = width
        self.height = height
        
    def __unicode__(self):
        p = ",".join("%s=%s" % kv for kv in self.attributes.iteritems())
        if any(x not in [None, '?'] for x in (self.width, self.height)):
            return "(%s:%sx%s)[%s]" % (self.kind, self.width or '?', self.height or '?', p)
        else:
            return "%s[%s]" % (self.kind, p)
        
    __repr__ = __unicode__


class Literal(AST):
    def __init__(self, value):
        super(Literal, self).__init__(value, [])
        
    @property
    def value(self):
        return self.root


class ContainerAST(ControlAST):
    def __init__(self, *a, **kw):
        super(ContainerAST, self).__init__(*a, **kw)
        self.attributes = {}
        self.width = self.height = None
    
    @property
    def direction(self):
        return self.root
    
    @property
    def subelements(self):
        return self.subtrees

    def __unicode__(self):
        if not self.attributes:
            return super(ContainerAST, self).__unicode__()
        else:
            r = AtomicWidget(self.root, self.attributes, (self.width, self.height))
            return unicode(ContainerAST(r, self.subtrees))


class ArithmeticExpression(object):
    def __init__(self, (coeff, free)):
        (self.coeff, self.free) = (coeff, free)
    
    def __unicode__(self):
        if not self.coeff:
            return unicode(self.free)
        elif len(self.coeff) == 1 and self.coeff.values() == [1] and self.free == 0:
            return unicode(self.coeff.keys()[0])
        else:
            poly = u" ".join("%+.9g%s" % (v, k) for k, v in self.coeff.iteritems()) \
                + (u" %+.9g" % self.free if self.free != 0 else '')
            if poly.startswith("+"): poly = poly[1:]
            return u"(%s)" % poly
    
    __repr__ = __unicode__


class ExpressionAST(AST):
    pass
