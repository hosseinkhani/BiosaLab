# from lib.interfaces import *
from lib.controller import *
from lib.gui import *


def main():
    app = QApplication(sys.argv)
    window = MainWindow(Controller(devices=[Device(f"device{i}", {}) for i in range(3)], interfaces=[Serial, Bluetooth, Wifi]))
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
    # s = Serial('COM8', boud=115200, timeout=1)
    # print(Serial.list_ports())
