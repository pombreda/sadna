from dsl import parse_layout, parse_arithmetic



subprograms_1 = """
L <- (label)[text=question]
     ----------------------------
     (radio)[checked=v] | (label)[text="Yes"] | (radio)[checked=!v] | (label)[text="No"]
I <- (image:32x32)[filename={(v)=>("dislike.png"), otherwise ("dislike.png")}]
main_window <- ((L) | (I))[question="Do you like?"]
"""
print parse_layout(subprograms_1)


subprograms_2 = """
        L <-  (((label:?x?)[text="Do you like"]
                ---((radio:?x?)[checked=v]|(label:20x10)[text="Yes"]|(radio:?x?)[checked=v]|(label:20x?)[text="No"] )))
        I <-   (button:30x?)[text="Tell a friend"]
        main_window <- (L)[v=?(1)]
        """      

print '-----'
a = parse_layout(subprograms_2)
print a
for key in a:
    if hasattr(a[key], 'attributes'):
        print key, ":", a[key].attributes
print '-----'

vsplit_w_scroll_1 = """ main_window <- (
    (button:?x(height*0.5))
           -----
    (button:?x(height*0.5))
           ---
    (button:?x(height*0.5))
  )
    """
    
print parse_layout(vsplit_w_scroll_1)


iteration_1 = """L <- ( (label)[text=A[i]] | (checkbox:10x10)[checked=(v=i)] )
                *-------*
                i = 1 .. 10 """
print parse_layout(iteration_1)


funcdef_1 = """
f(x,y) { x = y
 y = 2*x }
"""

print parse_arithmetic(funcdef_1)
