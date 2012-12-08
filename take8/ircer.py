import irc.client


class UIModel(object):
    pass

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
    def generate(self):
        pass

class ClassModel(UIModel):
    pass

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
        self.host = host
        self.port = port
        self.nick = nick
        self.user = user
        self.password = password
        self.client = irc.client.IRC()
        self.server = self.client.server()
        self.server.connect(host, port, nick, username = user, password = password)

    @FuncModel([StrArgModel("text", displayname = "", )], displayname = ">>")
    def send(self, text):
        self.server.send(text)

    def generate_model(self):
        return 



if __name__ == "__main__":
    import threading, traceback, sys
    #import logging
    #logging.basicConfig(level = logging.DEBUG)
    
    client = irc.client.IRC()
    server = client.server()

    def all_events(server, event):
        if event.eventtype() == "all_raw_messages":
            return
        print "%s %s->%s %s" % (event.eventtype(), event.source(), event.target(), event.arguments())
    
    client.add_global_handler("all_events", all_events)

    #server.connect("irc.freenode.net", 6667, "moishe3287")
    server.connect("irc.inter.net.il", 6667, "moishe3287")
    server.join("#test873")
        
    thd = threading.Thread(target = client.process_forever)
    thd.setDaemon(True)
    thd.start()

    try:
        while True:
            try:
                inp = raw_input(">>> ")
                if not inp.strip():
                    continue
                print ":::", eval(inp)
            except (KeyboardInterrupt, EOFError):
                break
            except Exception:
                print "".join(traceback.format_exception(*sys.exc_info()))
    finally:
        server.close()




