from abc import ABC, abstractmethod

import serial


class Interface(ABC):
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
    def open(self):
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
    def send(self, command:str):
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

    def always_read(self):
        import time
        import threading

        def read(ser):
            while True:
                o = ser.read_all().decode().split('\r\n')
                if len(o) > 1:
                    print(o[:-1])
                time.sleep(1)
        x = threading.Thread(target=read, args=(self.ser,), daemon=True)
        x.start()



class Bluetooth(Interface):
    def __init__(self):
        pass


class Wifi(Interface):
    def __init__(self):
        pass

