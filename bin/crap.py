from dsl import parse_layout

doc = parse_layout("""
chatbox <- (text:?x?)[text = "History", autoscroll=1]
           ---
           (text:?x20)[text = "Chat line"] | (button:40x20)[text = "send", clicked=sendbtn]

""")

def traverse(node, i = 0):
    print "%s%s %r" % ("  " * i, node.kind, node.attributes.get("text", None))
    for child in node.subtrees:
        traverse(child, i + 1)

traverse(doc["chatbox"])



