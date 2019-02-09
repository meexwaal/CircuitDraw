import sys, math
from enum import Enum
from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import Qt, QPoint, QRect
from PySide2.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QLineEdit)
from PySide2.QtGui import QPen, QPainter, QPolygon, QPalette, QColor

MIN_SIZE = 5

def test_modifier(modifier):
    return (int(QApplication.keyboardModifiers()) & int(modifier)) != 0

class BaseObject():
    def __init__(self):
        self.pos = [200,200]
        self.size = [100,100]
        self.label = None
        self.selected = False

    def in_bounds(self, pos):
        return False

    def draw(self, painter):
        pen = QPen(Qt.black, 2, Qt.SolidLine)
        if self.selected:
            pen = QPen(Qt.green, 2, Qt.SolidLine)
        painter.setPen(pen)

    def select(self, selected):
        self.selected = selected

    def move(self, dx, dy):
        self.pos[0] += dx
        self.pos[1] += dy

    def set_pos(self, pos):
        self.pos = list(pos)

    def set_size(self, size):
        self.size = [max(d, MIN_SIZE) for d in size]

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
        self.update_rect()

    def update_rect(self):
        self.rect = QRect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    def draw(self, painter):
        super().draw(painter)

        painter.drawRect(self.rect)
        # Text is drawn based on self.rect
        painter.drawText(self.rect, 0, self.label)


    def in_bounds(self, pos):
        return self.rect.contains(pos[0], pos[1])

    def move(self, dx, dy):
        super().move(dx, dy)
        self.update_rect()

    def set_pos(self, pos):
        super().set_pos(pos)
        self.update_rect()

    def set_size(self, size):
        super().set_size(size)
        self.update_rect()

class Wire(BaseObject):
    def __init__(self, points = []):
        super().__init__()

        self.port = None
        self.points = [list(p) for p in points] # For mutability
        self.update_line()

    def update_line(self):
        self.line = QPolygon([QPoint(p[0],p[1]) for p in self.points])

    def draw(self, painter):
        super().draw(painter)

        painter.drawPolyline(self.line)

    def in_bounds(self, pos):
        BOX_RADIUS = 10 # Distance from the wire where a click will register
        for i in range(1, len(self.points)):
            p0 = self.points[i-1]
            p1 = self.points[i]
            if ((min(p0[0],p1[0]) - BOX_RADIUS
                 <= pos[0]
                 <= max(p0[0],p1[0]) + BOX_RADIUS) and
                (min(p0[1],p1[1]) - BOX_RADIUS
                 <= pos[1]
                 <= max(p0[1],p1[1]) + BOX_RADIUS)):
                return True

    def move(self, dx, dy):
        super().move(dx, dy)
        for p in self.points:
            p[0] += dx
            p[1] += dy

        self.update_line()

    # Return point p algined with q
    def align(self, p, q):
        if abs(p[0]-q[0]) < abs(p[1]-q[1]):
            # x values are closer than y's
            return [q[0], p[1]]
        else:
            return [p[0], q[1]]

    # Add a point as close to p as is reasonable
    def add_point(self, p):
        if len(self.points) == 0:
            self.points.append(list(p))
        else:
            last_pt = self.points[-1]
            self.points.append(self.align(p, last_pt))
        self.update_line()

    # Remove point at index idx
    def remove_pt(self, idx):
        del self.points[idx]
        self.update_line()

class CanvasMode(Enum):
    NORMAL = 0
    DRAW_WIRE = 1
    DRAW_MODULE = 2

class Canvas(QWidget):
    def __init__(self):
        QWidget.__init__(self)

        test_module = Module()
        test_wire = Wire([[100,200],[100,350],[350,350],[350,250]])
        self.objects = [test_module, test_wire]
        self.selected = []
        self.last_mouse_pos = None
        self.mode = CanvasMode.NORMAL
        self.setMouseTracking(True) # Always receive mouse move events
        self.active = None # Object we are drawing/resizing

        self.setFocusPolicy(Qt.StrongFocus)
        self.prop_box = None # Connected PropertiesBox

    def set_prop_box(self, prop_box):
        self.prop_box = prop_box

    # Define a default size
    def sizeHint(self):
        return QtCore.QSize(500,500)

    def paintEvent(self, event):
        pen = QPen()
        painter = QPainter()
        painter.begin(self)
        painter.setPen(pen)

        for o in self.objects:
            o.draw(painter)

        painter.end()

    # Called by PropertiesBox when a field is changed
    def update_prop(self, prop):
        def f(val): # Do you even curry, bro?
            if prop == "Name":
                for o in self.selected:
                    o.label = val

            self.update()
        return f

    def mousePressEvent(self, event):
        self.last_mouse_pos = event.pos()
        pos = (event.pos().x(), event.pos().y())

        if self.mode == CanvasMode.NORMAL:
            for o in self.objects:
                if o.in_bounds(pos):
                    print("clicked:", o)
                    if not o.selected:
                        o.select(True)
                        self.selected.append(o)
                elif (o.selected
                      and not test_modifier(Qt.ShiftModifier)
                      and not test_modifier(Qt.ControlModifier)):
                    o.select(False)
                    self.selected.remove(o)

            if len(self.selected) == 1:
                self.prop_box.show_props({"Name" : self.selected[0].label})
            else:
                self.prop_box.clear_props()

        elif self.mode == CanvasMode.DRAW_WIRE:
            if self.active == None:
                print("New wire")
                # The last point will be moved as you move your mouse,
                # so we need another copy to anchor the wire
                new_wire = Wire([pos, pos])

                self.active = new_wire
                self.objects.append(new_wire)
            elif self.active.__class__ == Wire:
                print("Adding point")
                self.active.add_point(pos)

        elif self.mode == CanvasMode.DRAW_MODULE:
            if self.active == None:
                print("New module")
                new_module = Module()
                new_module.set_pos(pos)
                new_module.set_size((0,0))
                self.active = new_module
                self.objects.append(new_module)

        self.update()

    def mouseReleaseEvent(self, event):
        self.last_mouse_pos = event.pos()
        pos = (event.pos().x(), event.pos().y())

        if self.mode == CanvasMode.NORMAL:
            pass
        elif self.mode == CanvasMode.DRAW_WIRE:
            pass
        elif self.mode == CanvasMode.DRAW_MODULE:
            print("Ended module")
            self.active = None # Finish drawing module
            self.mode = CanvasMode.NORMAL

        self.update()

    def mouseDoubleClickEvent(self, event):
        self.last_mouse_pos = event.pos()
        pos = (event.pos().x(), event.pos().y())

        if self.mode == CanvasMode.NORMAL:
            pass
        elif self.mode == CanvasMode.DRAW_WIRE:
            if self.active != None and self.active.__class__ == Wire:
                print("Ending wire")
                self.active.remove_pt(-1) # Remove the currently-drawing pt
                self.active = None
                self.mode = CanvasMode.NORMAL

        elif self.mode == CanvasMode.DRAW_MODULE:
            pass

        self.update()

    def mouseMoveEvent(self, event):
        if self.last_mouse_pos == None:
            self.last_mouse_pos = event.pos()

        dx = event.pos().x() - self.last_mouse_pos.x()
        dy = event.pos().y() - self.last_mouse_pos.y()
        pos = (event.pos().x(), event.pos().y())

        if self.mode == CanvasMode.NORMAL:
            if event.buttons() != Qt.NoButton: # Only drag if mouse down
                for o in self.selected:
                    o.move(dx, dy)
        elif self.mode == CanvasMode.DRAW_WIRE:
            if self.active != None and self.active.__class__ == Wire:
                self.active.remove_pt(-1)  # Remove the last point
                self.active.add_point(pos) # Add it back
        elif self.mode == CanvasMode.DRAW_MODULE:
            if self.active != None and self.active.__class__ == Module:
                self.active.set_size((pos[0] - self.active.pos[0],
                                      pos[1] - self.active.pos[1]))

        self.last_mouse_pos = event.pos()
        self.update()

    def keyPressEvent(self, event):
        if self.mode == CanvasMode.NORMAL:
            if event.key() == Qt.Key_W:
                # Go into wire drawing mode
                self.mode = CanvasMode.DRAW_WIRE
                self.active = None
            elif event.key() == Qt.Key_M:
                # Go into module drawing mode
                self.mode = CanvasMode.DRAW_MODULE
                self.active = None
            elif event.key() == Qt.Key_Backspace:
                # Delete selected objects
                for i in range(len(self.objects)-1, -1, -1):
                    # Iterate backwards so we don't have to fix i on deletion
                    if self.objects[i].selected:
                        to_del = self.objects[i]
                        self.selected.remove(to_del)
                        del self.objects[i]

        elif event.key() == Qt.Key_Escape:
            # Go into normal mode
            self.mode = CanvasMode.NORMAL
            self.active = None

        print(self.mode)
        self.update()

    def focusInEvent(self, event):
        # Set a yellow background
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(240,240,220))
        self.setAutoFillBackground(True)
        self.setPalette(palette)
        self.update()

    def focusOutEvent(self, event):
        # Set a grey background
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(230,230,230))
        self.setAutoFillBackground(True)
        self.setPalette(palette)
        self.update()

class PropertiesBox(QWidget):
    def __init__(self, canvas):
        QWidget.__init__(self)
        self.canvas = canvas

        # Set a background
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(200,200,200))
        self.setAutoFillBackground(True)
        self.setPalette(palette)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.widgets = {}

    # Define a default size
    def sizeHint(self):
        return QtCore.QSize(100,500)

    def clear_props(self):
        for k in self.widgets:
            for w in self.widgets[k]:
                self.layout.removeWidget(w)
                w.deleteLater()
        self.widgets.clear()
        self.update()

    def show_props(self, props):
        self.clear_props()

        for k in props:
            prop_label = QLabel(k)
            prop_field = QLineEdit()
            prop_field.setText(props[k])
            prop_field.textChanged.connect(self.canvas.update_prop(k))

            self.layout.addWidget(prop_label)
            self.layout.addWidget(prop_field)
            self.widgets[k] = [prop_label, prop_field]


def update_prop(val0):
    print(val0)

class Window(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.canvas = Canvas()
        self.prop_box = PropertiesBox(self.canvas)
        self.canvas.set_prop_box(self.prop_box)

        self.layout = QHBoxLayout()
        self.layout.addWidget(self.canvas)
        self.layout.addWidget(self.prop_box)
        self.setLayout(self.layout)

if __name__ == "__main__":
    app = QtWidgets.QApplication()

    window = Window()
    window.show()

    sys.exit(app.exec_())
