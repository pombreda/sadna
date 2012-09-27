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
    
    self.setGeometry(300, 300, 300, 150)
    self.setWindowTitle('Buttons')    
    self.show()
    return self
    
def buttonClicked():
    app.quit()


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    print dir(app)
    ex = build()
    app.processEvents()






