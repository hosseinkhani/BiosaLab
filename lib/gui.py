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
        self.log(controller.connection_init(controller.interfaces[self.interface_selector.currentIndex()]))

    def _create_connection_widget(self):
        res = widgets.QGroupBox("Connection")
        layout = QGridLayout()

        self.interface_selector = widgets.QComboBox()
        self.interface_selector.addItems(self.controller.get_interface_names())
        def on_interface_select(index):
            print(index, self.controller.interfaces[index], "selected")
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
        main_layout = QGridLayout()

        self.device_selector = widgets.QComboBox()
        self.device_selector.addItems(self.controller.get_device_names())
        def on_device_select(index):
            print(index, self.controller.devices[index], "selected")

        self.device_selector.currentIndexChanged.connect(on_device_select)
        main_layout.addWidget(self.device_selector, 0, 0)

        fields = ['Name', 'Familly', 'Age', 'Email', 'Phone Number']
        form_layout = QFormLayout()
        qlines = {}
        for f in fields:
            qlines[f] = QLineEdit()
            form_layout.addRow(f, qlines[f])

        start_button = QPushButton("ok")
        def start_onclick(ffs):
            self.log(str([ffs[f].text() for f in ffs]), self.ERROR)
            for f in ffs:
                ffs[f].setEnabled(not ffs[f].isEnabled())
        start_button.clicked.connect(partial(start_onclick, ffs=qlines))

        main_layout.addLayout(form_layout, 1, 0, len(fields), 3)
        main_layout.addWidget(start_button, 1+len(fields), 2)

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
