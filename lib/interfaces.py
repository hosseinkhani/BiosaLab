from abc import ABC, abstractmethod
import time
import threading

import serial
import PyQt5.QtWidgets as widgets
from PyQt5.QtGui import QPalette, QColor
from functools import partial

# ToDo: refresh list every 5 sec


class Interface(ABC):
    TERMINATION_CHAR = b'#'

    NOT_CONNECTED = 0
    CONNECTED = 1
    CONNECTION_FAILED = 2
    DISCONNECTED = 3
    """
    Interface api
    All classes should implement these methods
    """

    def __init__(self):
        self.status = Interface.NOT_CONNECTED

    @abstractmethod
    def open(self, **kwargs):
        """
        initiate connection
        :return:
        """
        pass

    @abstractmethod
    def close(self):
        """
        close connection
        :return:
        """
        pass

    @abstractmethod
    def send(self, command):
        """
        send any command
        :param command:
        :return:
        """
        pass

    @abstractmethod
    def interupt(self):
        """
        Interrupt ongoing command
        :return:
        """
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """
        Used to show connection status
        :return: boolean to show connection status
        """
        pass

    @staticmethod
    @abstractmethod
    def list_available_devices() -> list:
        pass

    @abstractmethod
    def get_widget(self):
        pass

    @abstractmethod
    def read(self, **kwargs):
        pass


class Serial(Interface):
    def __init__(self, boud=115200, timeout=1):
        super(Serial, self).__init__()

        self.defaults = { "Boud": str(boud), "Timeout": str(timeout)}

    def open(self, **kwargs):
        try:
            port = self.list_available_devices()[self.fields['Devices'].currentRow()][0]
            boud = self.fields["Boud"].text()
            timeout = self.fields["Timeout"].text()

            self.ser = serial.Serial(port=port, baudrate=int(boud), timeout=int(timeout))
            self.status = Interface.CONNECTED
            print(f"serial port oppend on {self.ser.name}")

            # self.always_read()
            return True
        except Exception as e:
            self.status = Interface.CONNECTION_FAILED
            if "log" in kwargs:
                kwargs['log'](e)
                print(e)
            return False

    def close(self):
        self.ser.close()

    def send(self, command: str):
        self.ser.write(command.encode())

    def interupt(self):
        pass

    def is_connected(self) -> bool:
        return self.status == Interface.CONNECTED

    @staticmethod
    def list_available_devices() -> list:
        """
        List COM ports
        :return: list of ports
        """
        import serial.tools.list_ports
        myports = [tuple(p) for p in list(serial.tools.list_ports.comports(False))]
        return myports

    @staticmethod
    def check_connection():
        pass
        # import time
        #
        # def check_presence(correct_port, interval=0.1):
        #     while True:
        #         myports = [tuple(p) for p in list(serial.tools.list_ports.comports())]
        #     if arduino_port not in myports:
        #         print
        #         "Arduino has been disconnected!"
        #         break
        #     time.sleep(interval)
        #
        #
        # import threading
        # port_controller = threading.Thread(target=check_presence, args=(arduino_port, 0.1,))
        # port_controller.setDaemon(True)
        # port_controller.start()

    def get_widget(self):
        res = widgets.QWidget()
        form_layout = widgets.QFormLayout()

        self.fields = {"Devices": widgets.QListWidget(),
                       "Boud": widgets.QLineEdit(),
                       "Timeout": widgets.QLineEdit()}
        self.fields["Boud"].setText(self.defaults["Boud"])
        self.fields["Timeout"].setText(self.defaults["Timeout"])

        for fk in self.fields:
            form_layout.addRow(fk, self.fields[fk])
        self.fields['Devices'].addItems([x[1] for x in self.list_available_devices()])
        self.fields['Devices'].setMaximumHeight(100)

        # def on_device_click(item):
        #     sucsess = self.open(port=self.list_available_devices()[self.fields['Devices'].currentRow()][0],
        #                         boud=self.fields["Boud"].text(), timeout=self.fields["Timeout"].text())
        #     if sucsess:
        #         print(dir(item))
        #         item.setBackground(QColor(0, 255, 0, alpha=250))
        #         item.setSelected(False)
        #     else:
        #         self.fields['Devices'].addItems([x[1] for x in self.list_available_devices()])
        # self.fields['Devices'].itemDoubleClicked.connect(on_device_click)

        # res = widgets.QLabel()
        # res.setText(self.name)
        res.setLayout(form_layout)
        return res

    # def always_read(self):
    #     def read(ser):
    #         while True:
    #             # o = ser.read_all().decode().split('\r\n')
    #             o = ser.read_all()
    #             try:
    #                 o = o.decode()
    #             except:
    #                 pass
    #             # if o:
    #             print("out: ", o)
    #             time.sleep(1)
    #     x = threading.Thread(target=read, args=(self.ser,), daemon=True)
    #     x.start()

    def read(self, **kwargs):
        if kwargs.get('until', None) is None:
            o = self.ser.read_all()
        else:
            o = self.ser.read_until(b'#')
        try:
            o = o.decode()
        except Exception as e:
            pass
        return o


class Bluetooth(Interface):
    def __init__(self):
        pass


class Wifi(Interface):
    def __init__(self):
        pass

