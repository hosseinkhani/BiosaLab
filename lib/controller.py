from .device import Device
from .interfaces import Interface


class Controller:
    """
    The class which gui uses to interact with devices
    """

    def __init__(self, device: Device, interface: Interface):
        self.device = device
        self.interface = interface

    def send_command(self, command):
        self.interface.send(command)