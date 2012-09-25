from dsl import parse_layout

doc = parse_layout("""
Chatbox <- ((text:?x?)[text = "History", autoscroll=1]
            ---
            (text:?x20)[text = "Chat line"] | (button:40x20)[text = "send", clicked=sendbtn]):(0.7*w)x?

Lists <- (((label:?x20)[text="Rooms"]
          ---
          (listbox)[items="", selected=roomselect]
          ---
          (label:?x20)[text="Users"]
          ---
          (listbox)[items="", selected=userselect]
         ):(0.3*w)x?)[min_width = 200]

main <- (((Chatbox) | (Lists)):(w)x(h))[init_width = 800, init_height=600, 
                                        roomselect=?(0), userselect=?(0), sendbtn=?(0)]

""")

def traverse(node, i = 0):
    print "%s%r, %s" % ("  " * i, node.root, type(node))
    for child in node.subtrees:
        traverse(child, i + 1)

traverse(doc["main"])



