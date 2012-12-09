import models
from controls import run
from linsys import LinVar


#    m = models.WindowModel(
#        models.Horizontal([
#            models.LabelAtom(text = "foobar", width=x),
#            models.LineEditAtom(placeholder="Type something...", width = 3*x, accepted = k),
#            models.ButtonAtom(text = "Send", width = 60, clicked = k),
#        ]),
#        #width = 300, height = 200,
#        title = "foo"
#    )


x = LinVar("x")
k = models.Target("k")
    
m = models.WindowModel(
    models.Horizontal([
        models.LabelAtom(text = "foobar", width=100),
        models.LineEditAtom(placeholder="Type something...", width = 100),
        models.ButtonAtom(text = "Send", width = 100, clicked = k),
    ]),
    width = 250, height = 100,
    title = "foo"
)

@k.when_changed
def on_click(val):
    print "on_click", val

run(m)











