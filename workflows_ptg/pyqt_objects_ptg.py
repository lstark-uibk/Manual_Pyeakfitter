import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtGui as QtGui
from PyQt5.QtGui import QRegExpValidator
import workflows_ptg.trace_objects as to
from PyQt5.QtCore import *
import numpy as np
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
        self.layout.addLayout(self.jump_to_mass_layout)
        self.layout.addLayout(self.jump_to_compound_layout)
        self.layout.addLayout(self.multiple_check_layout)
        self.layout.addLayout(self.sorting_layout)
        self.layout.addWidget(self.masslist_widget)

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
        regexcomp = QRegExp(r'^(([a-zA-Z]+)(\d+)?)+\+$')
        validatorcomp = QRegExpValidator(regexcomp, self.jump_to_compound_input)
        self.jump_to_compound_input.setValidator(validatorcomp)
        self.jump_to_compound_button = QtWidgets.QPushButton("OK")
        self.jump_to_mass_layout.addWidget(self.label_jump_mass)
        self.jump_to_mass_layout.addWidget(self.jump_to_mass_input)
        self.jump_to_compound_layout.addWidget(self.label_jump_compound)
        self.jump_to_compound_layout.addWidget(self.jump_to_compound_input)
        # self.jump_to_compound_layout.addWidget(self.jump_to_compound_button)

        self.sort_mass = to.Sorting(self, self.sorting_layout, self.sort_on_mass, "Sort masses")
        self.sort_rel = to.Sorting(self, self.sorting_layout, self.sort_biggest_relative_difference,"Sorting on highest rel diff")
        self.sort_max = to.Sorting(self, self.sorting_layout, self.sorting_max, "Sorting on highest trace")

    def sort_on_mass(self, masses):
        sorted = np.argsort(masses)
        return sorted

    def sort_biggest_relative_difference(self, traces):
        if traces.ndim == 3:
            traces = traces[0]
        rel_diffs = np.empty(traces.shape[0])
        for i, trace in enumerate(traces):
            if np.mean(trace) > 0.7 * np.std(trace):
                # preselect for noise
                biggestdiff = np.ptp(trace)
                mean = np.mean(trace)
                rel_diff = biggestdiff / mean
                rel_diffs[i] = rel_diff
            else:
                rel_diffs[i] = 0
        sorted = np.argsort(rel_diffs)[::-1]
        return sorted

    def sorting_max(self, traces):
        if traces.ndim == 3:
            traces = traces[0]
        means = np.mean(traces, axis=1)
        sorted = np.argsort(means)
        sorted = sorted[::-1]
        return sorted




class PlotSettingsWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(PlotSettingsWindow, self).__init__(parent)
        self.centralWidget = QtWidgets.QWidget(self)
        self.centralLayout = QtWidgets.QVBoxLayout(self.centralWidget)
        self.parent = parent

        # here I have to use a checkbox not a radiobutton because radionbuttons are exclusively only one on
        Checkbox = QtWidgets.QCheckBox("Show high time resolution Spectra")
        Checkbox.setChecked(True)
        Checkbox.stateChanged.connect(self.set_high_time_res)
        self.centralLayout.addWidget(Checkbox)

        Checkbox1 = QtWidgets.QCheckBox("Take raw data")
        Checkbox1.setChecked(True)
        Checkbox1.stateChanged.connect(self.set_raw)

        self.centralLayout.addWidget(Checkbox1)
        self.setCentralWidget(self.centralWidget)

    def set_high_time_res(self):
        checkbox = self.sender()
        if checkbox.isChecked():
            self.parent.tr.useaveragesonly = False
        else:
            self.parent.tr.useaveragesonly = True
        self.parent.tr.update_Times_Traces(self.parent.masslist_widget.currentmasses)
        self.parent.update_plots()
    def set_raw(self):
        checkbox = self.sender()
        if checkbox.isChecked():
            self.parent.tr.raw = True
        else:
            self.parent.tr.raw = False
        self.parent.tr.update_Times_Traces(self.parent.masslist_widget.currentmasses)
        self.parent.update_plots()
