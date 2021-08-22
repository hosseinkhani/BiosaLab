import json
from abc import ABC, abstractmethod
import time
import threading
import multiprocessing

import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt

from PyQt5.QtCore import Qt, QObject, pyqtSignal, pyqtSlot
import PyQt5.QtWidgets as widgets
from functools import partial

from .interfaces import Interface


class Device(QObject):#ABC,
    INFO = 0
    ERROR = 1
    WARNING = 2

    query_finished = pyqtSignal()

    """
    Device information and mostly command specifics
    """

    def __init__(self, name: str = None, **kwargs):
        super().__init__()
    #     # QObject.__init__()
    #
        self.name = name if name is not None else type(self).__name__
        self.fields = {}
        self.commands = {}

    @abstractmethod
    def get_widget(self):
        pass

    @abstractmethod
    def start_query(self, interface: Interface) -> list[str]:
        pass


class CimosDevice(Device):
    def __init__(self, name: str=None, **kwargs):
        super(CimosDevice, self).__init__(name)
        self.stop_query = False

        self.commands = {
            "Measurment Channel": {"values": {"Right": 1, "Left": 0}, "command": "S"},
            "Measurment Type": {"values": {"Capacitance Sweep": 0, "Fixed Refrence": 1}},
            "Refrence Value": {"values": "NUM", "command": "R"},  # in fixed point only
            "CCO Resolution": {"values": ["000", "001", "011", "111"], "command": "C"},
            "Number of Samples": {"values": "Num"},
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

    def start_query(self, interface: Interface) -> list[str]:
        errors = []

        vals = {}
        for f in self.fields:
            if isinstance(self.fields[f], widgets.QComboBox):
                vals[f] = self.fields[f].currentText()
            else:
                vals[f] = self.fields[f].text()

        if errors:
            return errors

        def read(ser, until=None) -> str:
            if until is None:
                o = ser.read_all()
            else:
                o = ser.read_until(b'#')

            try:
                o = o.decode()
            except Exception as e:
                pass
            return o

        def query(interface: Interface):  # whole query management
            interface.send(f"G{self.fields['CCO Resolution'].currentText()}")
            # print(f"G{self.fields['CCO Resolution'].currentText()}")
            o = read(interface.ser, until=Interface.TERMINATION_CHAR)
            # print(f"o:{o}")
            if self.stop_query: return

            n_sample = int(self.fields['Number of Samples'].text())
            interface.send(f"S{n_sample}\0")
            # print(f"S{int(self.fields['Number of Samples'].text())}\0")
            o = read(interface.ser, until=Interface.TERMINATION_CHAR)
            # print(f"o:{o}")
            if self.stop_query: return

            output = np.zeros((128, n_sample), dtype=np.int32)
            for x in range(128):
                interface.send(f"W{format(x, '07b')}"+' ')
                # print(f"W{format(x, '07b')}"+' ')
                o = read(interface.ser, until=Interface.TERMINATION_CHAR)
                # print(f"o:{o}")
                if self.stop_query: return

                interface.send(f"R")
                while not interface.ser.in_waiting:
                    pass

                o = read(interface.ser, until=Interface.TERMINATION_CHAR).strip(str(Interface.TERMINATION_CHAR))
                # print(f"out({len(o)}): {o}", [raw for raw in o.strip(',').split(',')])
                output[x] = [int(raw) for raw in o.strip(',').split(',')]

                if self.stop_query: return
                # interface.ser.reset_input_buffer()

            output = np.mean(output, axis=1)
            plt.plot(output)
            plt.interactive(True)
            plt.show()


            print("query finished!")
            self.query_finished.emit()

        self.query_proc = threading.Thread(target=query, args=(interface,), daemon=True)#multiprocessing.Process(target=query, args=(interface,))
        self.query_proc.start()

        #
        # x.join()

        return errors
