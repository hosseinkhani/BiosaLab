# from lib.interfaces import *
from lib.controller import *
from lib.gui import *


def main():
    app = QApplication(sys.argv)
    window = MainWindow(Controller(devices=[CimosDevice(f"device{i}") for i in range(3)], interfaces=[Serial()]))
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
    # s = Serial('/dev/ttyACM0', boud=115200, timeout=1)
    # Device.from_json('./device0.json')

    print(Serial.list_available_devices())

