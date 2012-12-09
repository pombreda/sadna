import irc.client
import threading
import itertools
import socket
from Queue import Queue


class Closed(object):
    def __nonzero__(self):
        return False
    __bool__ = __nonzero__
    def __getattr__(self):
        raise ValueError("Closed")
Closed = Closed()

def consume(queue):
    while True:
        item = queue.get()
        if item is StopIteration:
            break
        yield item

class IRCClient(object):
    _counter = itertools.count()
    
    def __init__(self, server, port, nick, username = None, password = None):
        self._irc = irc.client.IRC()
        self.nick = nick
        self._conn = self._irc.server()
        self._irc.add_global_handler("all_events", self._all_events)
        self._conn.connect(server, port, nick)
        self._thd = threading.Thread(target = self._bg_thread)
        self._thd.setDaemon(True)
        self._thd.start()
        self._watchers = {}
    
    def __enter__(self):
        return self
    def __exit__(self, t, v, tb):
        self.close()
    
    def _bg_thread(self):
        try:
            while self._conn:
                self._irc.process_once()
        except (socket.error, EnvironmentError):
            if self._conn:
                raise

    def watch(self, callback):
        wid = self._counter.next()
        self._watchers[wid] = callback
        return wid
    def unwatch(self, wid):
        self._watchers.pop(wid, None)
    
    def _all_events(self, server, event):
        #if event.eventtype() != "all_raw_messages":
        #    print "!! %s %s->%s %s" % (event.eventtype(), event.source(), event.target(), event.arguments())
        for watcher in self._watchers.values():
            watcher(event)
    
    def close(self):
        if not self._conn:
            return
        self._conn.quit()
        self._conn.close()
        self._conn = None
        self._irc = None
        self._thd.join()
    
    def list_channels(self):
        channels = Queue()
        def collect_channles(event):
            if event.eventtype() == "list":
                channels.put(event.arguments()[0])
            elif event.eventtype() == "listend":
                self.unwatch(wid)
                channels.put(StopIteration)
        
        wid = self.watch(collect_channles)
        self._conn.list()
        return consume(channels)
    
    def change_nick(self, newnick):
        self._conn.nick(newnick)
        self.nick = newnick
    
    def join(self, channame):
        if not channame.startswith("#"):
            channame = "#" + channame
        self._conn.join(channame)
        return Channel(self, channame)
    
    def private_chat(self, username):
        return Channel(self, username)


class Channel(object):
    def __init__(self, client, channame):
        self.client = client
        self.channame = channame
        self._message_watchers = []
        
        def on_message(event):
            if event.eventtype() in ("pubmsg", "action") and event.target() == self.channame:
                self._invoke(event.eventtype(), event.source(), event.arguments()[0])
            elif event.eventtype() == "privmsg" and event.target() == self.client.nick:
                self._invoke("privmsg", event.source(), event.arguments()[0])
            #elif event.eventtype() in ("privnotice", "notice"):
            #    self._invoke(event.eventtype(), event.source(), event.arguments()[0])
        self._onmsg_wid = client.watch(on_message)
    
    def __enter__(self):
        return self
    def __exit__(self, t, v, tb):
        self.leave()
    
    def send(self, msg):
        self.client._conn.privmsg(self.channame, msg)
        self._invoke("pubmsg", self.client.nick, msg)
    def send_to(self, nick, msg):
        self.client._conn.privmsg(nick, msg)
        self._invoke("privmsg", self.client.nick, msg)
    
    def listen(self, callback):
        self._message_watchers.append(callback)
    def _invoke(self, msgtype, source, text):
        for callback in self._message_watchers:
            callback(msgtype, source, text)
    
    def list_members(self):
        names = Queue()
        def collect_names(event):
            if event.eventtype() == "namreply" and event.arguments()[0] == '=' and event.arguments()[1].lower() == self.channame.lower():
                for nick in event.arguments()[2].split():
                    names.put(nick)
            elif event.eventtype() == "endofnames" and event.arguments()[0].lower() == self.channame.lower():
                self.client.unwatch(wid)
                names.put(StopIteration)
        
        wid = self.client.watch(collect_names)
        self.client._conn.names([self.channame])
        return consume(names)
    
    def leave(self):
        self.client._conn.part([self.channame])
        self.client.unwatch(self._onmsg_wid)
        self.client = Closed



if __name__ == "__main__":
    with IRCClient("irc.inter.net.il", 6667, "moishe328") as client:
        #channels = list(client.list_channels())
        chan = client.join("test873")
        names = list(chan.list_users())
        def listener(msgtype, source, text):
            print ">>", msgtype, source, text
        
        chan.listen(listener)
        chan.send("hello everybody")
        chan.send_to("tomer", "sup?")
        while True:
            inp = raw_input(">>> ")
            if not inp.strip():
                continue
            if inp.strip() == "quit":
                break
            res = eval(inp)
            if res is not None:
                print res
    
    #print names
    #print channels[:100], len(channels)






