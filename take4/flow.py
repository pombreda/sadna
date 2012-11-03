import models
import widgets


MODELS_TO_WIDGETS = {
    models.LabelModel : widgets.Label,
    models.HLayoutModel : widgets.HLayout,
}

def _generate(solver, model):
    factory = MODELS_TO_WIDGETS[type(model)]
    if isinstance(factory, models.AtomModel):
        return factory(solver, model)
    else:
        children = [_generate(solver, submodel) for submodel in model.elems]
        return factory(solver, model, children)

def generate(root):
    solver = models.ModelSolver(root)
    top = _generate(solver, root)
    return widgets.Window(solver, root, top)



if __name__ == "__main__":
    from models import LabelModel
    from linear import LinVar
    import gtk
    
    x = LinVar("x")
    root = (LabelModel(text = "foo", width = x) | LabelModel(text = "bar", width = x))
    top = generate(root)
    gtk.main()










