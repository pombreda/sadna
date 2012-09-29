import sys
from PyQt4 import QtGui, QtCore

def build():
    self = QtGui.QWidget()
    okButton = QtGui.QPushButton("OK")
    cancelButton = QtGui.QPushButton("Cancel")
    okButton.clicked.connect(buttonClicked)
    
    hbox = QtGui.QHBoxLayout()
    hbox.addStretch(1)
    hbox.addWidget(okButton)
    hbox.addWidget(cancelButton)

    vbox = QtGui.QVBoxLayout()
    vbox.addStretch(1)
    vbox.addLayout(hbox)
    self.setLayout(vbox)    
    
    self.resize(300, 150)
    self.setWindowTitle('Buttons')
    def on_res(ev):
        print ev.size()
        print self.sizeHint().width()
    self.resizeEvent = on_res
    self.show()
    return self
    
def buttonClicked():
    app.quit()


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    ex = build()
    #print dir(ex)
    app.exec_()






