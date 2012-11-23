import functools


class uiproperty(object):
    pass

def uiaction(**params):
    def deco(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            pass
        return wrapper
    return deco


class ObserableObject(object):
    def __init__(self):
        self._callbacks = []
    def watch(self, callback):
        self._callbacks.append(callback)
    def _notify_watchers(self, *extra):
        for cb in self._callbacks:
            cb(self, *extra)

class ObservableList(object):
    def __init__(self, items = ()):
        self.items = list(items)
    def __repr__(self):
        return repr(self.items)
    def append(self, elem):
        self.items.append(elem)
        self._notify_watchers()
    def __setitem__(self, index, elem):
        self.items[index] = elem
        self._notify_watchers()


class IRCClient(object):
    pass


class DialogQuit(Exception):
    pass

class ChatLogin(object):
    @uiaction(server = str, port = (int, 6667), nickname = str, password = str)
    def send(self, server, port, nickname, password):
        self.server = server
        self.port = port
        self.nickname = nickname
        self.password = password
        return DialogQuit()

class ChatWindow(object):
    history = uiproperty(ObservableList)
    people = uiproperty(ObservableList)
    rooms = uiproperty(ObservableList)
    
    def __init__(self, credentials):
        self.credentials = credentials
        try:
            self.irc = IRCClient(credentials)
        except IOError as ex:
            raise DialogQuit("Server rejected your credentials", str(ex))
        self.irc.on_recv(self._process_input)
    
    def _process_input(self, line):
        if line.startswith("/join"):
            self.people.append(line)
        else:
            self.history.append(line)
    
    @uiaction(text = str)
    def send(self, text):
        self.irc.send(text)

    @uiaction(rooms.selection_changed)
    def change_room(self):
        pass

    @uiaction(people.selection_changed)
    def privmsg(self):
        pass

    model = (
        history 
        --- 
        send) | (
        rooms 
        --- 
        people)















