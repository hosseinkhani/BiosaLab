import json
from abc import ABC, abstractmethod

import PyQt5.QtWidgets as widgets
from functools import partial


class Device(ABC):
    INFO = 0
    ERROR = 1
    WARNING = 2

    """
    Device information and mostly command specifics
    """

    def __init__(self, name: str=None, **kwargs):
        self.name = name if name is not None else type(self).__name__
        self.fields = {}
        self.commands = {}

    @abstractmethod
    def get_widget(self, logger):
        pass


class CimosDevice(Device):
    def __init__(self, name: str=None, **kwargs):
        super(CimosDevice, self).__init__(name)

        self.commands = {
            "Measurment Channel": {"values": {"Right": 1, "Left": 0}, "command": "S"},
            "Measurment Type": {"values": {"Capacitance Sweep": 0, "Fixed Refrence": 1}},
            "Refrence Value": {"values": "NUM", "command": "R"},  # in fixed point only
            "CCO Resulotion": {"values": ["000", "001", "011", "111"], "command": "C"},
            "Time": {"values": "TIME"},
            "Measurment Frequency": {"values": "NUM", "command": "F"},
        }

    def get_widget(self):
        res = widgets.QWidget()
        form_layout = widgets.QFormLayout()

        for f in self.commands:
            if isinstance(self.commands[f]['values'], dict):  # combo box/radio button
                self.fields[f] = widgets.QComboBox()
                self.fields[f].addItems(self.commands[f]['values'])
            elif isinstance(self.commands[f]['values'], list):  # combo box/lineedit
                self.fields[f] = widgets.QComboBox()
                self.fields[f].addItems(self.commands[f]['values'])
            else:  # lineedit
                self.fields[f] = widgets.QLineEdit()
            form_layout.addRow(f, self.fields[f])

        # res = widgets.QLabel()
        # res.setText(self.name)
        res.setLayout(form_layout)
        return res

    def get_values(self):
        vals = {}
        for f in self.fields:
            if isinstance(self.fields[f], widgets.QComboBox):
                vals[f] = self.fields[f].currentText()
            else:
                vals[f] = self.fields[f].text()
        return True, vals
