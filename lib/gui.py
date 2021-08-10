import sys
from functools import partial

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QPushButton, QLineEdit, QHBoxLayout, QGridLayout, QFormLayout, QDialog
import PyQt5.QtWidgets as widgets

from .controller import Controller

class MainWindow(QDialog):
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

    def _create_main_widget(self):
        res = widgets.QWidget()
        main_layout = QGridLayout()
        fields = ['Name', 'Familly', 'Age', 'Email', 'Phone Number']
        form_layout = QFormLayout()
        qlines = {}
        for f in fields:
            qlines[f] = QLineEdit()
            form_layout.addRow(f, qlines[f])

        start_button = QPushButton("ok")
        def start_onclick(ffs):
            self.logger.append('<font color="Yellow">'+str([ffs[f].text() for f in ffs])+'</font>')

            for f in ffs:
                ffs[f].setEnabled(not ffs[f].isEnabled())
        start_button.clicked.connect(partial(start_onclick, ffs=qlines))

        main_layout.addLayout(form_layout, 0, 0, len(fields), 3)
        main_layout.addWidget(start_button, len(fields), 2)

        res.setLayout(main_layout)
        return res

    def _create_connection_widget(self):
        res = QWidget()
        layout = QGridLayout()

        interface = widgets.QComboBox()
        interface.addItems(self.controller.get_interface_list())
        layout.addWidget(interface, 0, 0)

        device_list = widgets.QListWidget()
        def on_device_click(item):
            print(item.text())
        device_list.itemClicked.connect(on_device_click)
        device_list.addItems(['com1', 'com2'])
        layout.addWidget(device_list, 1, 0, 3, 1)

        res.setLayout(layout)
        return res

    def _create_log_widget(self):
        res = widgets.QTextEdit()

        p = QPalette()
        p.setColor(QPalette.Base, QColor(0, 0, 0, alpha=100))
        p.setColor(QPalette.Text, QColor('white'))
        res.setPalette(p)

        res.setAlignment(Qt.AlignLeft|Qt.AlignTop)
        res.setReadOnly(True)
        res.setFixedHeight(200)

        self.logger = res
        return res


