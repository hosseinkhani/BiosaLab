from .device import *
from .interfaces import *


class Controller:
    """
    The class which gui uses to interact with devices
    """

    def __init__(self, devices: list[Device], interfaces: list[Interface]):
        self.devices = devices
        self.interfaces = interfaces

    def get_interface_names(self):
        return [type(f).__name__ for f in self.interfaces]

    def get_device_names(self):
        return [d.name for d in self.devices]

    def connection_init(self, interface: Interface):
        return interface.list_available_devices()

