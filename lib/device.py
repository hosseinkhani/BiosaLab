import json
from abc import ABC, abstractmethod
import os
import time
import threading
import multiprocessing
from collections import OrderedDict
from datetime import datetime


import numpy as np
import matplotlib

# from matplotlib.backends.backend_qt5agg import FI
from matplotlib import cm
import matplotlib.pyplot as plt

from PyQt5.QtCore import Qt, QObject, pyqtSignal, pyqtSlot, QTime
import PyQt5.QtWidgets as widgets
from PyQt5.QtCore import *
from functools import partial
from .interfaces import Interface

matplotlib.use('Qt5Agg')


class Device(QObject):#ABC,
    INFO = 0
    ERROR = 1
    WARNING = 2

    query_finished = pyqtSignal()  # after every thing is finished
    stop_query = pyqtSignal()  # force to stop it

    """
    Device information and mostly command specifics
    """

    def __init__(self, name: str = None, **kwargs):
        super().__init__()
    #     # QObject.__init__()
        self.halt = False

        self.name = name if name is not None else type(self).__name__
        self.fields = {}
        self.commands = {}

        self.defaults = {}
        if os.path.isfile(self.cfg_file_path()):
            with open(self.cfg_file_path(), 'r') as cfg_file:
                self.defaults = json.load(cfg_file)

        # signals
        self.stop_query.connect(self.finalize_query)
        # self.query_finished.connect(self.finalize_query)

    @abstractmethod
    def get_widget(self):
        pass

    def save_last_config(self, vals: dict):
        self.defaults = vals
        with open(self.cfg_file_path(), 'w') as cfg_file:
            json.dump(vals, cfg_file)

    def cfg_file_path(self):
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), self.name + '.cfg')

    @abstractmethod
    def start_query(self, interface: Interface) -> list[str]:
        pass

    def reset_halt(self):
        self.halt = False
        self.stop_query.emit()

    @pyqtSlot()
    def finalize_query(self):
        self.query_finished.emit()


class CimosDevice(Device):
    # new_result = pyqtSignal(list)
    CHANNEL_BITS = {}

    def __init__(self, name: str=None, **kwargs):
        super(CimosDevice, self).__init__(name)

        self.commands = OrderedDict([
            ("Measurment Channel", {"values": ["Left", "Internal Cap", "Right", "Left&Right"]}),
            ("Measurment Type", {"values": ["Capacitance Sweep", "Fixed Refrence"]}),
            ("Refrence Value", {"values": "NUM", "min": -1, "max": 127}),  # in fixed point only
            ("CCO Resolution", {"values": ["000", "001", "011", "111"]}),
            ("Number of Samples", {"values": "NUM", "min": 1, "max": 1000}),
            ("Repeats", {"values": "NUM", "min": 1, "max": 1000}),
            ("Repeat Interval", {"values": "TIME"}),
            ("Stop Time", {"values": "TIME"}),
            ("Plot Type", {"values": ["2D", "3D"]})
        ])

        self.outputs = None
        self.ax = None
        self.fig = None
        self.plots = {}

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_plot)

    def get_widget(self):
        res = widgets.QWidget()
        form_layout = widgets.QFormLayout()

        for f in self.commands:
            if isinstance(self.commands[f]['values'], dict):  # combo box/radio button
                w = widgets.QComboBox()
                w.addItems(self.commands[f]['values'])
                if f in self.defaults:
                    w.setCurrentText(self.defaults[f])
            elif isinstance(self.commands[f]['values'], list):  # combo box/lineedit
                w = widgets.QComboBox()
                w.addItems(self.commands[f]['values'])
                if f in self.defaults:
                    w.setCurrentText(self.defaults[f])
            elif self.commands[f]['values'] == "TIME":
                w = widgets.QTimeEdit()
                if f in self.defaults:
                    tmp = int(self.defaults[f])
                    w.setTime(QTime(tmp//3600, (tmp % 3600)//60, tmp % 60))
                w.setTimeRange(QTime(0, 0, 0), QTime(24, 0, 0))
                w.setDisplayFormat('hh:mm:ss')
            elif self.commands[f]['values'] == "NUM":
                w = widgets.QSpinBox()
                w.setMinimum(self.commands[f].get('min', 0))
                w.setMaximum(self.commands[f].get('max', 9999))
                if f in self.defaults:
                    w.setValue(self.defaults[f])
            else:  # lineedit
                print(f"undifined type for field {f}!")
                w = widgets.QLineEdit()
                if f in self.defaults:
                    w.setText(self.defaults[f])
            self.fields[f] = w
            form_layout.addRow(f, self.fields[f])

        # on change ################################################
        def measurment_changed(value):
            if value == "Fixed Refrence":
                self.fields["Refrence Value"].setEnabled(True)
            elif value == "Capacitance Sweep":
                self.fields["Refrence Value"].setEnabled(False)
            else:
                print("unknown value for measurment!!")
        self.fields['Measurment Type'].currentTextChanged.connect(measurment_changed)
        measurment_changed(self.fields['Measurment Type'].currentText())
        ##############################################################

        res.setLayout(form_layout)
        return res

    def start_query(self, interface: Interface) -> list[str]:
        plt.close()

        errors = []

        vals = {}
        for f in self.fields:
            if isinstance(self.fields[f], widgets.QComboBox):
                vals[f] = self.fields[f].currentText()
            elif isinstance(self.fields[f], widgets.QTimeEdit):
                vals[f] = int(self.fields[f].time().hour() * 3600 +
                              self.fields[f].time().minute() * 60 +
                              self.fields[f].time().second())
            elif isinstance(self.fields[f], widgets.QSpinBox):
                vals[f] = self.fields[f].value()
                try:
                    int(vals[f])
                except Exception as e:
                    errors.append(f"{str(e)} in field {f}")
            else:
                vals[f] = self.fields[f].text()
        print(vals)
        self.vals = vals

        if errors:
            return errors

        self.outputs = OrderedDict()
        self.plots = {}

        def query(interface:Interface, vals, **kwargs):  # whole query management
            interface.send(f"G{vals['CCO Resolution']}")
            o = interface.read(until=Interface.TERMINATION_CHAR)
            # print(f"o:{o}")
            if self.halt:
                self.reset_halt()
                return

            n_sample = vals['Number of Samples']
            interface.send(f"S{n_sample}\0")
            o = interface.read(until=Interface.TERMINATION_CHAR)
            # print(f"o:{o}")
            if self.halt:
                self.reset_halt()
                return

            last_bit = []
            if vals['Measurment Channel'] == "Left":
                last_bit.append(' ')
            elif vals['Measurment Channel'] == "Right":
                last_bit.append('1')
            elif vals['Measurment Channel'] == "Internal Cap":
                last_bit.append('0')
            elif vals['Measurment Channel'] == "Left&Right":
                last_bit.append(' ')
                last_bit.append('1')
            for lb in last_bit:
                self.outputs[lb] = []

            if vals.get('refrence_pulse', None):
                self.outputs['cide'] = []

            if vals['Stop Time'] and vals['Repeat Interval']:
                repeats = vals['Stop Time']//vals['Repeat Interval']
            else:
                repeats = vals['Repeats']
            repeat_interval = vals['Repeat Interval']

            time_sum = 0
            if vals['Measurment Type'] == "Capacitance Sweep":
                for rep in range(repeats):
                    time0 = time.time()

                    output = OrderedDict([(lb, []) for lb in last_bit])  # np.zeros((128, n_sample), dtype=np.int32)
                    if kwargs.get('refrence_pulse', None):
                        output['cide'] = []

                    for x in range(128):
                        for lb in last_bit:
                            interface.send(f"W{format(x, '07b')}" + lb)
                            o = interface.read(until=Interface.TERMINATION_CHAR)
                            # print(f"o:{o}")
                            if self.halt:
                                self.reset_halt()
                                return

                            interface.send(f"R")
                            while not interface.ser.in_waiting:
                                pass

                            o = interface.read(until=Interface.TERMINATION_CHAR).strip(str(Interface.TERMINATION_CHAR))

                            # output update
                            output[lb].append(np.mean([int(raw)+rep**2 for raw in o.strip(',').split(',')], dtype=int))
                            # output[lb].append(np.mean([int(raw) for raw in o.strip(',').split(',')], dtype=int))

                            if self.halt:
                                self.reset_halt()
                                return
                            # interface.ser.reset_input_buffer()
                    time_sum = time.time() - time0

                    # right sweep case
                    if vals.get('refrence_pulse', None):
                        for r in range(len(output['1'])):  # only the right channel needs it
                            if output['1'][r] >= vals['refrence_pulse']:
                                break
                        output['cide'] = r

                    for k in output:
                        self.outputs[k].append(output[k])

                    if kwargs.get('output_name', None):
                        if vals['Measurment Channel'] == "Left&Right":
                            self.save_output("Left", self.outputs[' '][-1], output_name)
                            self.save_output("Right", self.outputs['1'][-1], output_name)
                        else:
                            self.save_output(vals['Measurment Channel'], self.outputs[last_bit[0]][-1], output_name)

                    if repeat_interval and repeat_interval > (time.time()-time0):
                        time.sleep(repeat_interval - (time.time()-time0))

            elif vals["Measurment Type"] == "Fixed Refrence":
                refrence = vals['Refrence Value']

                for rep in range(repeats):
                    time0 = time.time()

                    output = OrderedDict([(lb, []) for lb in last_bit])  # np.zeros((128, n_sample), dtype=np.int32)
                    for lb in last_bit:
                        interface.send(f"W{format(refrence, '07b')}" + lb)
                        o = interface.read(until=Interface.TERMINATION_CHAR)
                        # print(f"o:{o}")
                        if self.halt:
                            self.reset_halt()
                            return

                        interface.send(f"R")
                        while not interface.ser.in_waiting:
                            pass

                        o = interface.read(until=Interface.TERMINATION_CHAR).strip(str(Interface.TERMINATION_CHAR))

                        # update output
                        # output[lb].append(np.mean([int(raw) for raw in o.strip(',').split(',')], dtype=int))
                        output[lb].append(np.mean([int(raw)+rep**2 for raw in o.strip(',').split(',')], dtype=int))

                        if self.halt:
                            self.reset_halt()
                            return
                        # interface.ser.reset_input_buffer()
                    time_sum = time.time() - time0

                    for k in output:
                        self.outputs[k].append(output[k])

                    if kwargs.get('output_name', None):
                        if vals['Measurment Channel'] == "Left&Right":
                            self.save_output("Left", self.outputs[' '][-1], output_name)
                            self.save_output("Right", self.outputs['1'][-1], output_name)
                        else:
                            self.save_output(vals['Measurment Channel'], self.outputs[last_bit[0]][-1], output_name)

                    if repeat_interval and repeat_interval > (time.time()-time0):
                        time.sleep(repeat_interval - (time.time()-time0))

            if kwargs.get('save_config', True):
                self.save_last_config(vals)

            if kwargs.get('finish_query', True):
                time.sleep(1)
                self.reset_halt()

                print(f"average time= {time_sum/repeats:.3f} s")
                print("query finished!")

        print("Not fully capacitance mode...")

        xlabels = [296.77, 299.66, 305.01, 307.9, 318.59, 321.48, 326.83, 329.72, 349.35, 352.24, 357.59, 360.48,
                   371.17, 374.06, 379.41, 382.3, 416.16, 419.05, 424.4, 427.29, 437.98, 440.87, 446.22, 449.11,
                   468.74, 471.63, 476.98, 479.87, 490.56, 493.45, 498.8, 501.69, 551.43, 554.32, 559.67, 562.56,
                   573.25, 576.14, 581.49, 584.38, 604.01, 606.9, 612.25, 615.14, 625.83, 628.72, 634.07, 636.96,
                   670.82, 673.71, 679.06, 681.95, 692.64, 695.53, 700.88, 703.77, 723.4, 726.29, 731.64, 734.53,
                   745.22, 748.11, 753.46, 756.35, 794.11, 797, 802.35, 805.24, 815.93, 818.82, 824.17, 827.06, 846.69,
                   849.58, 854.93, 857.82, 868.51, 871.4, 876.75, 879.64, 913.5, 916.39, 921.74, 924.63, 935.32, 938.21,
                   943.56, 946.45, 966.08, 968.97, 974.32, 977.21, 987.9, 990.79, 996.14, 999.03, 1048.77, 1051.66,
                   1057.01, 1059.9, 1070.59, 1073.48, 1078.83, 1081.72, 1101.35, 1104.24, 1109.59, 1112.48, 1123.17,
                   1126.06, 1131.41, 1134.3, 1168.16, 1171.05, 1176.4, 1179.29, 1189.98, 1192.87, 1198.22, 1201.11,
                   1220.74, 1223.63, 1228.98, 1231.87, 1242.56, 1245.45, 1250.8, 1253.69]

        if vals['Measurment Channel'] == "Right" and vals['Measurment Type'] == "Capacitance Sweep":
            # process the internal cap
            vals_backup = vals.copy()
            vals['Measurment Channel'] = "Internal Cap"
            vals['Number of Samples'] = 5
            vals['Repeats'] = 1
            vals['Repeat Interval'] = 0

            self.query_proc = threading.Thread(target=query, args=(interface, vals),
                                               kwargs={'finish_query': False, 'save_config': False}, daemon=True)
            self.query_proc.start()
            self.query_proc.join()

            slope = (self.outputs['0'][0][16] - self.outputs['0'][0][15]) / (xlabels[16] - xlabels[15])
            intercept = self.outputs['0'][0][16] - slope * xlabels[16]
            vals = vals_backup
            vals['refrence_pulse'] = 402.7 * slope + intercept + 35  # todo: delete this test number
            self.vals = vals
            print(f"refrence pulse = {vals['refrence_pulse']:.1f}")

            self.outputs = OrderedDict()

            # plot part
            self.fig = plt.figure()
            self.ax = []
            if vals['Plot Type'] == "3D":
                self.ax.append(self.fig.add_subplot(1, 2, 1, projection='3d'))

                # self.ax.yaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter("{x:.0f}"))
                # self.ax[0].set_yticks(range(0, 1000, self.vals['Repeats'] // 7))
                self.ax[0].set_ylabel('Time')

                self.ax[0].set_zlabel('Number Of Pulses')
                # self.ax.set_zticks(range(0, 5000, 100))
                self.ax[0].set_zlim(bottom=-1, top=100)
            else:
                self.ax.append(self.fig.add_subplot(1, 2, 1))

                self.ax[0].set_xlabel('CR')
                self.ax[0].set_xlim(left=-1, right=128)
                self.ax[0].set_xticks(range(0, 128, 7))
                self.ax[0].set_xticklabels([int(x) for i, x in enumerate(xlabels) if i % 7 == 0], rotation=90, ha='center')

                self.ax[0].set_ylabel('Number Of Pulses')
                self.ax[0].set_ylim(bottom=-1, top=100)

            # x_axis
            self.ax[0].grid(axis='x')

            self.ax[0].set_title(f"{self.vals['Measurment Channel']} {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")
            self.ax[0].set_xlabel('CR')
            self.ax[0].set_xlim(left=-1, right=128)
            self.ax[0].set_xticks(range(0, 128, 7))
            self.ax[0].set_xticklabels([int(x) for i, x in enumerate(xlabels) if i % 7 == 0], rotation=90, ha='center')

            # cide value
            self.ax.append(self.fig.add_subplot(1, 2, 2))
            self.ax[1].set_title(f"{'Refrence Pulse'}")

            self.ax[1].set_xlabel('Time')
            self.ax[1].set_xticks(range(0, 200, 2))

            self.ax[1].set_ylabel('C_ide')
            self.ax[1].set_yticks(range(0, 128, 7))
            self.ax[1].set_yticklabels([int(x) for i, x in enumerate(xlabels) if i % 7 == 0])
        else:
            if vals['Plot Type'] == "3D":  # 3d case
                self.fig, self.ax = plt.subplots(1, 2 if vals['Measurment Channel'] == "Left&Right" else 1, subplot_kw={"projection": "3d"})
                if not isinstance(self.ax, np.ndarray):
                    self.ax = [self.ax]

                for axis in self.ax:
                    # self.ax.yaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter("{x:.0f}"))
                    axis.set_ylabel('Time')
                    axis.set_yticks(range(0, self.vals['Repeats'], self.vals['Repeats'] // 7))

                    axis.set_zlabel('Number Of Pulses')
                    # self.ax.set_zticks(range(0, 5000, 100))
                    axis.set_zlim(bottom=-1, top=100)
            else:  # 2d simple plot
                self.fig, self.ax = plt.subplots(1, 2 if vals['Measurment Channel'] == "Left&Right" else 1)
                if not isinstance(self.ax, np.ndarray):
                    self.ax = [self.ax]

                for axis in self.ax:
                    axis.set_ylabel('Number Of Pulses')
                    # self.ax.set_yticks(range(0, 5000, 100))
                    axis.set_ylim(bottom=-1, top=100)
                self.fig.subplots_adjust(left=.1, bottom=.25)

            for i, axis in enumerate(self.ax):
                axis.grid(axis='x')

                if vals["Measurment Type"] == "Fixed Refrence":
                    axis.set_xlabel('Time')
                    axis.set_xticks(range(0, 200, 2))
                else:
                    axis.set_xlabel('CR')
                    axis.set_xlim(left=-1, right=128)
                    axis.set_xticks(range(0, 128, 7))
                    axis.set_xticklabels([int(x) for i, x in enumerate(xlabels) if i % 7 == 0], rotation=90, ha='center')
                axis.set_title(f"{self.vals['Measurment Channel'].split('&')[i]} {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")

        mngr = plt.get_current_fig_manager()
        mngr.window.setGeometry(500, 80, 800, 500)

        plt.ion()
        self.fig.show()

        self.timer.start(300)
        output_name = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                   "outputs",
                                   f"{{channel}}_{datetime.now().strftime('%d-%m-%Y %H:%M:%S')}_{self.name}.csv")
        self.query_proc = threading.Thread(target=query, args=(interface, vals), kwargs={'output_name': output_name}, daemon=True)
        # self.query_proc = multiprocessing.Process(target=query, args=(interface, vals, output_name), daemon=True)
        self.query_proc.start()
        # self.query_proc.join()

        return errors

    def update_plot(self):
        if self.vals["Measurment Type"] == "Fixed Refrence":
            if self.vals['Plot Type'] == '3D':
                for ax_ind, k in enumerate([x for x in self.outputs.keys() if not x.endswith("_ind")]):
                    ind = self.outputs.get(f"{k}_ind", 0)
                    if ind < len(self.outputs[k]):
                        if self.plots.get(k, None) is not None:
                            self.plots[k].remove()

                        self.plots[k] = self.ax[ax_ind].scatter([self.vals['Refrence Value']] * len(self.outputs[k]),
                                                        range(len(self.outputs[k])), self.outputs[k],
                                                        cmap=plt.get_cmap('coolwarm'), c=self.outputs[k], alpha=.99)

                        self.ax[ax_ind].set_zbound([-1, np.max(self.outputs[k])+10])

                        # if len(self.outputs[k]) == self.vals['Repeats']:
                        #     self.fig.colorbar(self.plots[k])

                        self.outputs[f"{k}_ind"] = len(self.outputs[k])
            else:
                for ax_ind, k in enumerate([x for x in self.outputs.keys() if not x.endswith("_ind")]):
                    ind = self.outputs.get(f"{k}_ind", 0)
                    if ind < len(self.outputs[k]):
                        if self.plots.get(k, None) is not None:
                            self.plots[k].remove()

                        self.plots[k] = self.ax[ax_ind].scatter(range(len(self.outputs[k])), self.outputs[k], alpha=.5)
                        self.ax[ax_ind].set_ybound([-1, np.max(self.outputs[k])+10])

                        self.outputs[f"{k}_ind"] = len(self.outputs[k])
        else:
            if self.vals['Plot Type'] == '3D':
                for ax_ind, k in enumerate([x for x in self.outputs.keys() if not x.endswith("_ind")]):
                    if k == 'cide':
                        ind = self.outputs.get(f"{k}_ind", 0)
                        if ind < len(self.outputs[k]):
                            if self.plots.get(k, None) is not None:
                                # print(self.plots[k])
                                self.plots[k].remove()

                            self.plots[k] = self.ax[ax_ind].plot(self.outputs[k], alpha=.5)[0]
                            self.ax[ax_ind].set_ybound([-1, np.max(self.outputs[k]) + 10])

                            self.outputs[f"{k}_ind"] = len(self.outputs[k])
                    else:
                        ind = self.outputs.get(f"{k}_ind", 0)
                        if ind < len(self.outputs[k]):
                            if self.plots.get(k, None) is not None:
                                self.plots[k].remove()

                            x, y = np.meshgrid(range(128), range(len(self.outputs[k])))
                            self.plots[k] = self.ax[ax_ind].plot_surface(x, y, np.array(self.outputs[k]), rstride=2, cstride=2, alpha=.99,
                                                                         cmap=plt.get_cmap('coolwarm'), linewidth=1, antialiased=True)

                            self.ax[ax_ind].set_zbound([-1, np.max(self.outputs[k])+10])

                            # if len(self.outputs[k]) == self.vals['Repeats']:
                            #     self.fig.colorbar(self.plots[k])

                            self.outputs[f"{k}_ind"] = len(self.outputs[k])
            else:
                for ax_ind, k in enumerate([x for x in self.outputs.keys() if not x.endswith("_ind")]):
                    if k == 'cide':
                        ind = self.outputs.get(f"{k}_ind", 0)
                        if ind < len(self.outputs[k]):
                            if self.plots.get(k, None) is not None:
                                # print(self.plots[k])
                                self.plots[k].remove()

                            self.plots[k] = self.ax[ax_ind].plot(self.outputs[k], alpha=.5)[0]
                            self.ax[ax_ind].set_ybound([-1, np.max(self.outputs[k]) + 10])

                            self.outputs[f"{k}_ind"] = len(self.outputs[k])
                    else:
                        ind = self.outputs.get(f"{k}_ind", 0)
                        if ind < len(self.outputs[k]):
                            for i in range(ind, len(self.outputs[k])):
                                self.ax[ax_ind].plot(self.outputs[k][i], alpha=.5)
                            self.ax[ax_ind].set_ybound([-1, np.max(self.outputs[k])+10])

                            self.outputs[f"{k}_ind"] = len(self.outputs[k])

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def save_output(self, channel, output, file_name):
        with open(file_name.format(channel=channel), 'a') as out:
            out.write(','.join([str(x) for x in output])+'\n')

    @pyqtSlot()
    def finalize_query(self):
        self.timer.stop()
        super(CimosDevice, self).finalize_query()

