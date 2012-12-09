from irclib import IRCClient
from deducer import (ClassModel, StrArgModel, IntArgModel, PasswordArgModel, ListPropertyModel, 
    FuncModel, GUIError)


class IrcGuiClient(ClassModel):
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
        self.history = ListPropertyModel("History")
        self.channels = ListPropertyModel("Channels")
        self.members = ListPropertyModel("Members")
        self.curr_channel = Watcher(self.channels.selected)
        
        def update_history(msgtype, source, msg):
            self.history.append("%-20s %s" % (source.split("!", 1)[0], msg))
        
        def select_channel(prev_channel):
            if prev_channel:
                prev_channel.leave()
            del self.history[:]
            del self.members[:]
            self.curr_channel.listen(update_history)
            self.members.extend(self.curr_channel.list_members())
        
        self.curr_channel.when_changed(select_channel)

    @FuncModel([StrArgModel("text", displayname = "", )], displayname = "Send")
    def send(self, text):
        if not self.curr_channel:
            raise GUIError("Please select a channel first")
        self.curr_channel.send(text)

    def generate_model(self):
        h = None #LinVar("y")
        return ((self.rooms.generate_model().X(None, h) --- self.members.generate_model().X(None, h)) |
            (self.history.generate_model() --- self.send.generate_model().X(None, 25)))


if __name__ == "__main__":
    IrcGuiClient.run()








