import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtGui as QtGui

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
