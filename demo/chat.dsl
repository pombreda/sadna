login_screen <- ((image)[image="logo.png"]
				 -------------------------
				 (label : (lw)x(h))[text = "Server"] | (textbox: (tw)x(h))[text="irc.freenode.net:6667"]
				 -------------------------
				 (label : (lw)x(h))[text = "Nick"] | (textbox: (tw)x(h))[text=""]
				 -------------------------
				 (label : (lw)x(h))[text = "Real Name"] | (textbox: (tw)x(h))[text="Anonymous"]
				 -------------------------
				 () : (lw)x? | (button)[text="Connect"])
				[title="#IRC client"]

chat_screen <- ChatBox | (ChannelList --- UsersList)

chat_history <- (text:?x?)[]
				-----
				(label:30x20)[text=">>>"] | (text: ?x(20))[text=""] | (button : 40x20)[text="send"]
				


main-window <- login_screen
