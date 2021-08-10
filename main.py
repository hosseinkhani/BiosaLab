from lib.serial_interface import Serial


if __name__ == '__main__':
    s = Serial('COM8', boud=115200, timeout=1)
    print(Serial.list_ports())
