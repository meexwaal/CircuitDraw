import sys, math
from enum import Enum
from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QApplication, QWidget
from PySide2.QtGui import QPen, QPainter

class BaseObject():
    def __init__(self):
        self.pos = (200,200)
        self.size = (100,100)
        self.label = None
        self.selected = False

    def in_bounds(self, pos):
        return False

    def draw(self, painter):
        pass

    def select(self):
        self.selected = not self.selected

class PortType(Enum):
    UNDEF = -1
    INPUT = 0
    OUTPUT = 1
    INOUT = 2

class Port(BaseObject):
    def __init__(self):
        super().__init__()

        self.width = 1
        self.name = None
        self.port_type = PortType.UNDEF

class Module(BaseObject):
    def __init__(self):
        super().__init__()

        self.ports = []
        self.rect = QtCore.QRect(self.pos[0], self.pos[1],
                                 self.size[0], self.size[1])

    def draw(self, painter):
        pen = QPen(Qt.black, 2, Qt.SolidLine)
        if self.selected:
            pen = QPen(Qt.green, 2, Qt.SolidLine)

        painter.setPen(pen)
        painter.drawRect(self.rect)

    def in_bounds(self, pos):
        return self.rect.contains(pos[0], pos[1])

class WireSegment(BaseObject):
    def __init__(self):
        super().__init__()


class Wire(BaseObject):
    def __init__(self):
        super().__init__()

        self.port = None
        self.segments = []

class Canvas(QWidget):
    def __init__(self):
        super().__init__()

        test_module = Module()
        self.objects = [test_module]

    def paintEvent(self, event):
        pen = QPen()
        painter = QPainter()
        painter.begin(self)
        painter.setPen(pen)

        for o in self.objects:
            o.draw(painter)

        painter.end()

    def mousePressEvent(self, event):
        pos = (event.pos().x(), event.pos().y())
        for o in self.objects:
            if o.in_bounds(pos):
                o.select()
                print("clicked:", o)

        self.update()



if __name__ == "__main__":
    app = QtWidgets.QApplication()

    canvas = Canvas()
    canvas.show()

    sys.exit(app.exec_())
