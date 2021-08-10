from abc import ABC

from .interfaces import Interface

import serial
import serial.tools.list_ports


class Serial(Interface):
    def __init__(self, port, boud, timeout):
        super(Serial, self).__init__()
        self.port = port
        self.boud = boud
        self.timeout = timeout

    def open(self):
        try:
            self.ser = serial.Serial(self.port, baudrate=self.boud, timeout=self.timeout)
            self.status = Interface.CONNECTED
            print(f"serial port oppend on {self.ser.name}")
            return True
        except Exception as e:
            self.status = Interface.CONNECTION_FAILED
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
    def list_ports() -> list:
        """
        List COM ports
        :return: list of ports
        """
        myports = [tuple(p) for p in list(serial.tools.list_ports.comports(True))]
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
