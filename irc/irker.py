"""
JSON to IRC message relay

Run the server, then here's an example using wget to send a message:

MESSAGE='{"url": "irc://chat.freenode.net/#dcpython", "message": "hello"}'
wget --post-data $MESSAGE http://localhost:8080
"""

from __future__ import unicode_literals

import json
import urlparse
import threading

import cherrypy

import irc.client

class Server(object):
	def __init__(self):
		self.irc_servers = dict()

	@cherrypy.expose
	def default(self):
		message = json.load(cherrypy.serving.request.body)
		assert set(message) <= set('message url'.split())
		host, port, channel = self.parse_url(message['url'])
		conn = self.get_conn(host, port)
		conn.join(channel)
		conn.privmsg(channel, message['message'])
		return 'OK'

	def parse_url(self, url):
		parsed = urlparse.urlparse(url)
		host, sep, port = parsed.netloc.partition(':')
		if not port:
			port = 6667
		port = int(port)
		channel = parsed.path.lstrip('/')
		return host, port, channel

	def get_conn(self, host, port):
		if (host, port) in self.irc_servers:
			return self.irc_servers[(host, port)]
		client = irc.client.IRC()
		conn = client.server()
		conn.connect(host, port, nickname='irker')

		self.irc_servers[(host, port)] = conn
		thread = threading.Thread(target=conn.irclibobj.process_forever)
		client._thread = thread
		thread.daemon = True
		thread.start()
		return conn

	@classmethod
	def start(cls):
		cherrypy.quickstart(cls())

if __name__ == '__main__':
	Server.start()
