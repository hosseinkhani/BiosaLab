from abc import ABC, abstractmethod


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
