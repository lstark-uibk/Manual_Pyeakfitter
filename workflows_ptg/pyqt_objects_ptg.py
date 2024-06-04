import PyQt5.QtWidgets as QtWidgets
from PyQt5.QtWidgets import QMessageBox
import PyQt5.QtGui as QtGui
from PyQt5.QtGui import QRegExpValidator
import workflows_ptg.trace_objects as to
from PyQt5.QtCore import *
import numpy as np
import pyqtgraph as pg
from scipy.ndimage import uniform_filter1d


class ColorField(QtWidgets.QWidget):
    def __init__(self, color, parent=None):
        self.color = color
        super().__init__(parent)
        self.setAutoFillBackground(True)
        self.set_color(color)

    def set_color(self, color):
        '''

        Parameters
        ----------
        color: RGB Triple

        Returns
        -------

        '''
        self.color = color
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QtGui.QColor(*color))
        self.setPalette(palette)

class Masslist_Frame(QtWidgets.QFrame):
    def __init__(self):
        super().__init__()
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)
        self.jump_to_mass_layout = QtWidgets.QHBoxLayout()
        self.jump_to_compound_layout = QtWidgets.QHBoxLayout()
        self.multiple_check_layout = QtWidgets.QHBoxLayout()
        self.sorting_layout = QtWidgets.QHBoxLayout()


        # list of masses
        self.masslist_widget = to.QlistWidget_Masslist(self,[],[])
        regex = QRegExp(r'^-?\d+(-\d+)?$')
        # Create a validator based on the regular expression
        self.multiple_check = QtWidgets.QLineEdit()
        validator = QRegExpValidator(regex, self.multiple_check)
        self.multiple_check.setValidator(validator)
        multiple_check_label = QtWidgets.QLabel("Select traces (e.g. 1-10)")
        self.multiple_check_OK_Button = QtWidgets.QPushButton("OK")
        self.multiple_check_layout.addWidget(multiple_check_label)
        self.multiple_check_layout.addWidget(self.multiple_check)
        # self.multiple_check_layout.addWidget(self.multiple_check_OK_Button)

        self.label_jump_mass = QtWidgets.QLabel("Select masses (e.g. 69.420-70): ")
        self.jump_to_mass_input = QtWidgets.QLineEdit()
        regexmass = QRegExp(r'^\d+(\.\d*)?(-(\d+)(\.\d*)?)?$')
        validator = QRegExpValidator(regexmass, self.jump_to_mass_input)
        self.jump_to_mass_input.setValidator(validator)
        self.jump_to_mass_layout.addWidget(self.label_jump_mass)
        self.jump_to_mass_layout.addWidget(self.jump_to_mass_input)

        self.label_jump_compound = QtWidgets.QLabel("Select compound (e.g. H3O+): ")
        self.jump_to_compound_input = QtWidgets.QLineEdit()
        self.jump_to_compound_status = QtWidgets.QLabel("")
        self.jump_to_compound_layout.addWidget(self.label_jump_compound)
        self.jump_to_compound_layout.addWidget(self.jump_to_compound_input)

        self.jump_to_compound_layout.addWidget(self.jump_to_compound_status)

        self.sort_mass = to.Sorting(self, self.sorting_layout, self.sort_on_mass, "Sort masses")
        self.sort_rel = to.Sorting(self, self.sorting_layout, self.sort_biggest_relative_difference,"Sorting on highest rel diff")
        self.sort_max = to.Sorting(self, self.sorting_layout, self.sorting_max, "Sorting on highest trace")
        self.sort_primary_ions = to.Sorting(self, self.sorting_layout, self.sort_on_primary, "Primary Ions")


        self.layout.addLayout(self.jump_to_mass_layout)
        self.layout.addLayout(self.jump_to_compound_layout)
        self.layout.addLayout(self.multiple_check_layout)
        self.layout.addLayout(self.sorting_layout)
        self.layout.addWidget(self.masslist_widget)

    def sort_on_primary(self, masses):
        primary_ions = to.Traces.Primary_ions
        mask = np.any((np.isclose(masses[:, None], primary_ions, rtol=1e-5, atol=1e-8)), axis=1)
        primary_ions_indices = np.where(mask)[0]
        others_indices = np.where(~mask)[0]
        sorted = np.concatenate([primary_ions_indices,others_indices])
        return sorted

    def sort_on_mass(self, masses):
        sorted = np.argsort(masses)
        return sorted

    def sort_biggest_relative_difference(self, traces):
        if traces.ndim == 3:
            traces = traces[0]

        def robust_scale(data):
            # Calculate the median and interquartile range (IQR) for each signal
            median_vals = np.median(data, axis=1, keepdims=True)
            q1 = np.percentile(data, 25, axis=1, keepdims=True)
            q3 = np.percentile(data, 75, axis=1, keepdims=True)
            iqr = q3 - q1

            # Robust scaling
            scaled_data = (data - median_vals) / iqr

            return scaled_data
        smoothed_data = uniform_filter1d(traces, size=30, mode='nearest')
        scaled_data = robust_scale(smoothed_data)
        sum_abs_diff = np.sum(np.abs(np.diff(scaled_data, axis=1)), axis=1)

        sorted = np.argsort(sum_abs_diff)[::-1]
        # rel_diffs = np.empty(traces.shape[0])
        # for i, trace in enumerate(traces):
        #     if np.mean(trace) > 0.7 * np.std(trace):
        #         # preselect for noise
        #         biggestdiff = np.ptp(trace)
        #         mean = np.mean(trace)
        #         rel_diff = biggestdiff / mean
        #         rel_diffs[i] = rel_diff
        #     else:
        #         rel_diffs[i] = 0
        # sorted = np.argsort(rel_diffs)[::-1]
        return sorted

    def sorting_max(self, traces):
        if traces.ndim == 3:
            traces = traces[0]
        means = np.mean(traces, axis=1)
        sorted = np.argsort(means)
        sorted = sorted[::-1]
        return sorted

class SelectedMassesFrame(QtWidgets.QFrame):
    def __init__(self):
        super().__init__()
        # #list of selected masses
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)
        self.masses_selected_widget = to.QlistWidget_Selected_Masses(self)
        self.header = QtWidgets.QHBoxLayout()
        # self.header.addWidget(QtWidgets.QLabel("Selected Masses"))
        self.deselectall_button = QtWidgets.QPushButton("Deselect all")
        self.export_button = QtWidgets.QPushButton("Export as .csv")
        self.header.addWidget(self.deselectall_button)
        self.header.addWidget(self.export_button)

        self.layout.addLayout(self.header)
        self.layout.addWidget(self.masses_selected_widget)

class Peak_Frame(QtWidgets.QFrame):
    def __init__(self):
        super().__init__()
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        self.header = QtWidgets.QHBoxLayout()
        self.header.addWidget(QtWidgets.QLabel("Peak of selected Mass"))
        self.peakmasslabel = QtWidgets.QLabel("")
        self.header.addWidget(self.peakmasslabel)
        self.peakmasscolor = ColorField((0,0,0))
        self.header.addWidget(self.peakmasscolor)
        # self.peak_info_deselectall_button = QtWidgets.QPushButton("Deselect")
        # self.peak_info_layout_header.addWidget(self.peak_info_deselectall_button)
        self.plot_peak_layout = QtWidgets.QVBoxLayout()
        self.graph_peak_Widget = pg.PlotWidget()
        axis = pg.DateAxisItem()
        self.graph_peak_Widget.setAxisItems({'bottom': axis})
        self.plot_peak_layout.addWidget(self.graph_peak_Widget)

        self.layout.addLayout(self.header)
        self.layout.addLayout(self.plot_peak_layout)

class PlotSettingsWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(PlotSettingsWindow, self).__init__(parent)
        self.centralWidget = QtWidgets.QWidget(self)
        self.centralLayout = QtWidgets.QVBoxLayout(self.centralWidget)
        self.parent = parent

        self.setCentralWidget(self.centralWidget)

    def load(self,hightimeres_status,bg_corr_status,averaging_time_s):
        # here I have to use a checkbox not a radiobutton because radionbuttons are exclusively only one on
        Checkbox = QtWidgets.QCheckBox("High time resolution")
        Checkbox.setChecked(False)
        Checkbox.stateChanged.connect(self.set_high_time_res)
        self.label_status_high_time_res = QtWidgets.QLabel("")
        self.centralLayout.addWidget(Checkbox)
        self.centralLayout.addWidget(self.label_status_high_time_res)


        Checkbox1 = QtWidgets.QCheckBox("Background correction")
        Checkbox1.setChecked(True)
        Checkbox1.stateChanged.connect(self.set_raw)
        self.label_status_background = QtWidgets.QLabel("")
        self.centralLayout.addWidget(Checkbox1)
        self.centralLayout.addWidget(self.label_status_background)


        self.change_labels(hightimeres_status,bg_corr_status,averaging_time_s)

    def change_labels(self,hightimeres_status,bg_corr_status,averaging_time_s):
        if hightimeres_status:
            curr_loaded_time_res = "High Time Resolution averages over 60 s"
        else: curr_loaded_time_res = f"Averages over {averaging_time_s}s"
        if bg_corr_status:
            curr_loaded_bg_corr_status = "Background corrected"
        else:
            curr_loaded_bg_corr_status = "No Background correction"



        self.label_status_high_time_res.setText(f"Currently loaded: {curr_loaded_time_res}")
        self.label_status_background.setText(f"Currently loaded: {curr_loaded_bg_corr_status}")

    def set_high_time_res(self):
        checkbox = self.sender()
        if checkbox.isChecked():
            self.parent.tr.hightimeres = True
            message_box = QMessageBox()
            message_box.setIcon(QMessageBox.Information)
            message_box.setText("Loading...")
            message_box.setWindowTitle("Loading")
            message_box.setStandardButtons(QMessageBox.NoButton)
            message_box.show()
        else:
            self.parent.tr.hightimeres = False

        self.parent.tr.update_Times_Traces("all")
        if checkbox.isChecked():
            message_box.close()
        self.change_labels(self.parent.tr.hightimeres_status,self.parent.tr.bg_corr_status,self.parent.tr.averaging_time_s)
        self.parent.update_plots()
    def set_raw(self):
        checkbox = self.sender()
        if checkbox.isChecked():
            self.parent.tr.bg_corr = True
        else:
            self.parent.tr.bg_corr = False
        self.parent.tr.update_Times_Traces("all")
        self.change_labels(self.parent.tr.hightimeres_status,self.parent.tr.bg_corr_status,self.parent.tr.averaging_time_s)
        self.parent.update_plots()


