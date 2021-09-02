import sys
from functools import partial

from PyQt5.QtCore import Qt, QObject, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QPalette, QColor, QIcon
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QPushButton, QLineEdit, QHBoxLayout, QGridLayout, QFormLayout, QDialog
import PyQt5.QtWidgets as widgets

from .controller import Controller
from .device import Device
from .interfaces import Interface


class MainWindow(QDialog):
    INFO = 0
    ERROR = 1
    WARNING = 2
    LOG_COLORS = {INFO: "White", ERROR: "Red", WARNING: "Yellow"}

    def __init__(self, controller: Controller, parent=None):
        self.controller = controller

        super().__init__(parent)
        self.setWindowTitle('PyQt5 App')
        self.setGeometry(100, 100, 280, 80)

        self.main_layout = widgets.QVBoxLayout()

        self.interface_box, self.connect_btn = self._create_connection_box()
        self.main_layout.addWidget(self.interface_box)
        self.main_layout.addWidget(self.connect_btn)

        self.device_box, self.submit_btn = self._create_device_box()
        self.main_layout.addWidget(self.device_box)
        self.main_layout.addWidget(self.submit_btn)

        self.main_layout.addWidget(self._create_log_widget())

        self.setLayout(self.main_layout)
        self.setWindowIcon(QIcon('icon.png'))

        # default connection
        self.interface_selector.setCurrentIndex(0)
        self.device_selector.setCurrentIndex(0)
        self.on_interface_disconnect()

        # signals
        self.current_device().query_finished.connect(self.on_query_finished)

    def _create_connection_box(self):
        res = widgets.QGroupBox("Connection")
        main_layout = widgets.QVBoxLayout()

        self.interface_selector = widgets.QComboBox()
        self.interface_selector.addItems(self.controller.get_interface_names())
        self.interface_selector.setCurrentIndex(-1)

        def on_interface_select(index):
            new_widget = self.controller.interfaces[index].get_widget()
            if hasattr(self, "interface_widget"):
                # main_layout.removeWidget(main_window.device_widget)
                main_layout.itemAt(1).widget().deleteLater()
            main_layout.insertWidget(1, new_widget)
            self.interface_widget = new_widget
        self.interface_selector.currentIndexChanged.connect(on_interface_select)
        main_layout.addWidget(self.interface_selector)

        res.setLayout(main_layout)

        connect_btn = widgets.QPushButton("Connect")

        def submit_onclick():
            interface = self.controller.interfaces[self.interface_selector.currentIndex()]
            if connect_btn.text() == "Connect":
                if not interface.open():
                    c = self.interface_selector.currentIndex()
                    self.interface_selector.setCurrentIndex(-1)
                    self.interface_selector.setCurrentIndex(c)
                    return

                # p = QPalette()
                # p.setColor(QPalette.Base, QColor(0, 255, 0, alpha=100))
                # connect_btn.setPalette(p)

                self.on_interface_change(True)
            else:
                interface.close()
                self.on_interface_disconnect()

        connect_btn.clicked.connect(submit_onclick)

        return res, connect_btn

    def _create_device_box(self):
        res = widgets.QGroupBox("Commands")
        main_layout = widgets.QVBoxLayout()

        self.device_selector = widgets.QComboBox()
        self.device_selector.addItems(self.controller.get_device_names())
        self.device_selector.setCurrentIndex(-1)

        def on_device_select(index):
            new_widget = self.controller.devices[index].get_widget()
            if hasattr(self, "device_widget"):
                # main_layout.removeWidget(main_window.device_widget)
                main_layout.itemAt(1).widget().deleteLater()
            main_layout.insertWidget(1, new_widget)
            self.device_widget = new_widget
        self.device_selector.currentIndexChanged.connect(on_device_select)
        main_layout.addWidget(self.device_selector)
        res.setLayout(main_layout)

        submit_btn = widgets.QPushButton("Start")

        def submit_onclick():
            if submit_btn.text() == "Start":
                self.on_query_change(True)

                errors = self.current_device().start_query(self.current_interface())
                if errors:
                    for e in errors:
                        self.log(e, MainWindow.ERROR)

                    self.on_query_change(False)
            else:
                self.current_device().halt = True
                submit_btn.setEnabled(False)

                # self.on_query_finished()
        submit_btn.clicked.connect(submit_onclick)

        return res, submit_btn

    def _create_log_widget(self):
        res = widgets.QGroupBox("Logs")
        self.logger = widgets.QTextEdit()

        p = QPalette()
        p.setColor(QPalette.Base, QColor(0, 0, 0, alpha=190))
        p.setColor(QPalette.Text, QColor('white'))
        self.logger.setPalette(p)

        self.logger.setAlignment(Qt.AlignLeft|Qt.AlignTop)
        self.logger.setReadOnly(True)
        self.logger.setMinimumHeight(200)

        layout = QHBoxLayout()
        layout.addWidget(self.logger)
        res.setLayout(layout)
        return res

    def log(self, message, level=INFO):
        self.logger.append(f'<font color="{MainWindow.LOG_COLORS[level]}">' + str(message) + '</font>')

    def current_interface(self) -> Interface:
        return self.controller.interfaces[self.interface_selector.currentIndex()]

    def current_device(self) -> Device:
        return self.controller.devices[self.device_selector.currentIndex()]

    def rotate_buttons(self, btns):
        for attr in btns:
            if getattr(self, attr, False):
                getattr(self, attr, False).setEnabled(not getattr(self, attr, False).isEnabled())

    @pyqtSlot()
    def on_query_finished(self):
        self.on_query_change(False)

    @pyqtSlot()
    def on_interface_disconnect(self):
        self.on_interface_change(False)

    def on_interface_change(self, is_connected):
        self.connect_btn.setText("Connect" if not is_connected else "Disconnect")
        self.interface_box.setEnabled(not is_connected)
        self.device_box.setEnabled(is_connected)
        self.submit_btn.setEnabled(is_connected)

    def on_query_change(self, is_started):
        self.submit_btn.setText("Start" if not is_started else "Stop")
        if not is_started:
            self.submit_btn.setEnabled(True)
        self.connect_btn.setEnabled(not is_started)
        self.device_box.setEnabled(not is_started)


