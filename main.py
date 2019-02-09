from enum import Enum

class BaseObject():
    def __init__(self):
        self.pos = (0,0)
        self.size = (10,10)
        self.label = None

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

class WireSegment(BaseObject):
    def __init__(self):
        super().__init__()


class Wire(BaseObject):
    def __init__(self):
        super().__init__()

        self.port = None
        self.segments = []
