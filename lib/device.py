from .interfaces import Interface


class Device:
    """
    Device information and mostly command specifics
    """

    def __init__(self, name: str, commands: dict, **kwargs):
        assert len(name) > 0, f"Device name should have a valid name with len more than 0"

        self.name = name
        self.commands = commands

    def commands_list(self):
        return self.commands

    def command_parameters(self, command):
        assert command in self.commands, f"{command} is not in device definition!"
        return self.commands[command]
