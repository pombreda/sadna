from irc2 import IRCClient


class UIModel(object):
    def generate_model(self):
        raise NotImplementedError()

class ArgModel(UIModel):
    def __init__(self, argname, displayname = None, default = NotImplemented):
        self.argname = argname
        self.displayname = displayname if displayname else argname
        self.default = default

class StrArgModel(ArgModel):
    pass
class PasswordArgModel(StrArgModel):
    pass
class IntArgModel(ArgModel):
    pass

class FuncModel(UIModel):
    def __init__(self, args, displayname = None):
        self.args = args
        self.displayname = displayname
    def __call__(self, func):
        self.func = func
        if not self.displayname:
            self.displayname = func.__name__
    def generate_model(self):
        if not self.args:
            return Button(text = self.displayname)
        elif len(self.args) == 1:
            a = self.args[0]
            return ((Label(text = a.displayname) | a.generate_model()) 
                if a.displayname else a.generate_model()) | Button(text = self.displayname)
        else:
            w = None
            return (VLayout.foreach(
                (Label(text = a).X(w, None) | a.generate_model()) for a in self.args) --- 
                 Padding().X(w, None) | Button(text = self.displayname))

class ClassModel(UIModel):
    @classmethod
    def run(cls):
        if isinstance(cls.__init__, UIModel):
            kwargs = run_ui(cls.__init__.generate_model())
            inst = cls(**kwargs)
        else:
            inst = cls()
        return run_ui(inst.generate_model())

class UIProperty(UIModel):
    def __init__(self, attrname, displayname = None):
        self.attrname = attrname
        self.displayname = displayname if displayname else attrname

class ListProperty(UIProperty):
    pass


class IRC(ClassModel):
    history = ListProperty("history")
    rooms = ListProperty("rooms")
    members = ListProperty("members")
    
    @FuncModel([
            StrArgModel("host", "Host", default = "chat.freenode.net"),
            IntArgModel("port", "Port", default = 6667),
            StrArgModel("nick", "Nickname"),
            StrArgModel("user", "Username"),
            PasswordArgModel("password", "Password"),
        ], 
        displayname = "Connect"
    )
    def __init__(self, host, port, nick, user, password):
        self.client = IRCClient(host, port, nick, user, password)

    @FuncModel([StrArgModel("text", displayname = "", )], displayname = "Send")
    def send(self, text):
        self.client.send(text)

    def generate_model(self):
        y = None #LinVar("y")
        return ((self.history.generate_model() --- self.send.generate_model().X(None, 25)) |
                (self.rooms.generate_model().X(None, y) --- self.members.generate_model().X(None, y)))





