import pygtk
pygtk.require('2.0')
import gtk

gtk.widget_set_default_direction(gtk.TEXT_DIR_LTR)

window = gtk.Window(gtk.WINDOW_TOPLEVEL)
window.set_default_size(400, 200)
window.connect("destroy", lambda q: gtk.main_quit())

hbox = gtk.HBox(homogeneous=False, spacing=5)
window.add(hbox)

hpane = gtk.HPaned()
hbox.pack_start(hpane, True, True, 0)

label = gtk.Label("HPane Left")
hpane.add1(label)
label = gtk.Label("HPane Right")
hpane.add2(label)

vpane = gtk.VPaned()
hbox.pack_start(vpane, True, True, 0)

label = gtk.Label("VPane Top")
vpane.add1(label)
label = gtk.Label("VPane Bottom")
vpane.add2(label)

window.show_all()

gtk.main()


