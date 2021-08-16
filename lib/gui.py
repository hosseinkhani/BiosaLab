import sys
from functools import partial

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor, QIcon
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QPushButton, QLineEdit, QHBoxLayout, QGridLayout, QFormLayout, QDialog
import PyQt5.QtWidgets as widgets

from .controller import Controller


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
        self.main_layout.addWidget(self._create_connection_widget())
        self.main_layout.addWidget(self._create_main_widget())
        self.main_layout.addWidget(self._create_log_widget())

        self.setLayout(self.main_layout)
        self.setWindowIcon(QIcon('icon.png'))

        # default connection
        self.interface_selector.setCurrentIndex(0)
        self.device_selector.setCurrentIndex(0)

    def _create_connection_widget(self):
        res = widgets.QGroupBox("Connection")
        layout = QGridLayout()

        self.interface_selector = widgets.QComboBox()
        self.interface_selector.addItems(self.controller.get_interface_names())
        self.interface_selector.setCurrentIndex(-1)
        def on_interface_select(index):
            self.log(self.controller.connection_init(self.controller.interfaces[self.interface_selector.currentIndex()]))
        self.interface_selector.currentIndexChanged.connect(on_interface_select)

        layout.addWidget(self.interface_selector, 0, 0)

        device_list = widgets.QListWidget()
        def on_device_click(item):
            print(item.text())
        device_list.itemClicked.connect(on_device_click)
        device_list.addItems(['com1', 'com2'])
        device_list.setMaximumHeight(100)
        layout.addWidget(device_list, 1, 0, 3, 1)

        res.setLayout(layout)
        return res

    def _create_main_widget(self):
        res = widgets.QGroupBox("Commands")
        main_layout = widgets.QVBoxLayout()

        self.device_selector = widgets.QComboBox()
        self.device_selector.addItems(self.controller.get_device_names())
        self.device_selector.setCurrentIndex(-1)
        def on_device_select(index, main_window: MainWindow):
            new_widget = main_window.controller.devices[index].get_widget()
            if hasattr(main_window, "device_widget"):
                # main_layout.removeWidget(main_window.device_widget)
                main_layout.itemAt(1).widget().deleteLater()
            main_layout.insertWidget(1, new_widget)
            main_window.device_widget = new_widget
        self.device_selector.currentIndexChanged.connect(partial(on_device_select, main_window=self))
        main_layout.addWidget(self.device_selector)

        submit_button = widgets.QPushButton("Start")
        def submit_onclick():
            ffs = self.controller.devices[self.device_selector.currentIndex()].fields
            for f in ffs:
                ffs[f].setEnabled(not ffs[f].isEnabled())

            if submit_button.text() == "Start":
                self.log(str(vals), MainWindow.INFO)

                submit_button.setText("Stop")
                self.rotate_buttons()
            else:
                submit_button.setText("Start")
                self.rotate_buttons()
        submit_button.clicked.connect(submit_onclick)
        main_layout.addWidget(submit_button)





        res.setLayout(main_layout)
        return res

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

    def rotate_buttons(self):
        for attr in ["interface_selector", "device_selector"]:
            if getattr(self, attr, False):
                getattr(self, attr, False).setEnabled(not getattr(self, attr, False).isEnabled())