import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets
import workflows.pyqtgraph_objects as pyqtgraph_objects
from PyQt5.QtCore import Qt

#menu functions
def open_file(parent):
    # show the dialog
    dialog = QtWidgets.QFileDialog()
    filepath, filter = dialog.getOpenFileName(None, "Window name", "", "HDF5_files (*.hdf5)")
    parent.filename = filepath

    parent.init_basket_objects()
    parent.init_UI_file_loaded()
    parent.init_plots()
    parent.file_loaded = True

class QHSeparationLine(QtWidgets.QFrame):
  '''
  a horizontal separation line\n
  '''
  def __init__(self):
    super().__init__()
    self.setMinimumWidth(1)
    self.setFixedHeight(20)
    self.setFrameShape(QtWidgets.QFrame.HLine)
    self.setFrameShadow(QtWidgets.QFrame.Sunken)
    self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
    return
class HelpWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(HelpWindow, self).__init__(parent)
        self.centralWidget = QtWidgets.QWidget(self)
        self.centralLayout = QtWidgets.QVBoxLayout(self.centralWidget)
        separator_horizontal = QHSeparationLine()
        Text = ["Help on the Manual Peak Fitter",
                "Drag right mouse to move left and right",
                "Scroll for zoom",
                "Drag left mouse to zoom",
                "Move one mass up or down with D or A "]

        self.head = QtWidgets.QLabel("Help on the Manual Peak Fitter")
        self.head.setFont(QtGui.QFont('Arial', 20))
        self.head.setAlignment(Qt.AlignCenter)
        self.general0 = QtWidgets.QLabel("General")
        self.general1 = QtWidgets.QLabel("This is a program to produce a masslists for massspectra in _result.hdf5 files which are processed by the TOFTracer https://github.com/lukasfischer83/TOF-Tracer2 \nIt is a continuation of the ManualPeakfitter program https://github.com/lukasfischer83/peakFit in Python \nSo first load in a spectrum and begin")
        self.spectra0 = QtWidgets.QLabel("The spectra shown are:")
        self.spectra1 = QtWidgets.QLabel("- average spectrum of all spectra that are included in the _result.hdf5 file \n- maximum and minimum spectra \n- subspectra which are average spectra of the TOFDaq .h5 files which are the input into the TOF-Tracer2 (at which times are they?). \nBy dragging the Slider at the bottom of the graphs you can slide through the subspectra.\nToggle in settings. For best performance only use average spectrum. \n \n- if zoomed in, there is a local fit added, according to the masses which are in the masslist. ")
        self.movement0 = QtWidgets.QLabel("Movement")
        self.movement1 = QtWidgets.QLabel("Drag right mouse to move left and right \nScroll for zoom \nDrag left mouse to zoom \nMove one mass up or down with D or A \nYou can also acces certain mass by searching an the upper left or clicking on a specific mass in the masslist on the left")
        self.horizontallines0 = QtWidgets.QLabel("If you zoom in enough, horizontal lines will appear")
        self.horizontallines1 = QtWidgets.QLabel("Grey Horizontal Lines = Suggestions based on reasonable combinations of elements given by ranges \nRed Horizontal Lines = Masses in Masslist with corresponding composition \nBlue Horizontal Lines = Masses in masslist without composition \nGreen Horizontal Lines = Isotopes corresponding to the red lines")
        self.selection0 = QtWidgets.QLabel("Actions")
        self.selection1 = QtWidgets.QLabel("Click on Suggestion Lines to add them to the Masslist \nDouble click on an empty space to add a new mass \nDrag masses so that the local fit is best \nIf you drag the masses close to a suggestion line it will stick and link the composition with the mass \nDelete mass from masslist by rightclick or pressing delete when hovered above it")
        self.centralLayout.addWidget(self.head)
        self.centralLayout.addWidget(QHSeparationLine())
        self.centralLayout.addWidget(self.spectra0)
        self.centralLayout.addWidget(self.spectra1)
        self.centralLayout.addWidget(QHSeparationLine())
        self.centralLayout.addWidget(self.movement0)
        self.centralLayout.addWidget(self.movement1)
        self.centralLayout.addWidget(QHSeparationLine())
        self.centralLayout.addWidget(self.horizontallines0)
        self.centralLayout.addWidget(self.horizontallines1)
        self.centralLayout.addWidget(QHSeparationLine())
        self.centralLayout.addWidget(self.selection0)
        self.centralLayout.addWidget(self.selection1)

        self.setCentralWidget(self.centralWidget)




class Validator_exp(QtGui.QValidator):

    def __init__(self,i, j, parent):
        QtGui.QValidator.__init__(self,parent)
        #make a validator for every input with the i,j value stored
        self.i = i -1
        self.j = j -1
        self.parent = parent

    def validate(self, a0, a1):
        if a0.isdigit() or a0 == "0":
            if a1 < 3:
                digit = int(a0)
                if len(self.parent.inputs) < len(self.parent.mass_suggestions_ranges): # if we didnot add all the input fields we also skip the validation
                    return (QtGui.QValidator.Acceptable, a0, a1)

                if self.j == 0: # the input is a minimum
                    if digit <= int(self.parent.inputs[self.i][1].text()): # check whether it is lower than the maximum
                        return (QtGui.QValidator.Acceptable, a0, a1)

                if self.j == 1:  # the input is a maximum
                    if digit >= int(self.parent.inputs[self.i][0].text()):  # check whether it is higher than the minimum
                        return (QtGui.QValidator.Acceptable, a0, a1)

            return (QtGui.QValidator.Invalid, a0, a1)
        elif a0 == "":  #it is also valid to have nothing
            return (QtGui.QValidator.Acceptable, a0, a1)
        else:
            return (QtGui.QValidator.Invalid,a0,a1)


class SelectMassRangeWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(SelectMassRangeWindow, self).__init__(parent)
        self.centralWidget = QtWidgets.QWidget(self)
        self.centralLayout = QtWidgets.QVBoxLayout(self.centralWidget)
        self.gridlayout = QtWidgets.QGridLayout()
        self.parent = parent

        self.gridlayout.addWidget(QtWidgets.QLabel("Lower Limit"), 0, 1)
        self.gridlayout.addWidget(QtWidgets.QLabel("Upper Limit"), 0, 2)
        self.labels = []
        self.inputs = []
        self.mass_suggestions_ranges = parent.mass_suggestions_ranges

        for [i, name], suggrange in zip(enumerate(parent.ml.names_elements),parent.mass_suggestions_ranges):
            i = i+1
            label = self.gridlayout.addWidget(QtWidgets.QLabel(name), i, 0)
            self.labels.append(label)
            thisline = []
            for j in range(1,3):
                input = QtWidgets.QLineEdit()
                thisline.append(input)
                validator = Validator_exp(i,j,self)
                input.setValidator(validator)
                input.setText(str(suggrange[j-1]))
                self.gridlayout.addWidget(input , i, j)
            self.inputs.append(thisline)


        self.centralLayout.addLayout(self.gridlayout)
        collectbutton = QtWidgets.QPushButton("OK")
        collectbutton.clicked.connect(self.change_ranges)
        self.centralLayout.addWidget(collectbutton)
        self.setCentralWidget(self.centralWidget)


    def change_ranges(self):
        mass_suggestions_ranges_new = [tuple([int(x.text()) for x in row]) for row in self.inputs]
        self.parent.mass_suggestions_ranges = mass_suggestions_ranges_new
        pyqtgraph_objects.remove_all_vlines(self.parent)
        self.parent.ml.reinit(self.parent.mass_suggestions_ranges,self.parent.filename)
        pyqtgraph_objects.redraw_vlines(self.parent)
        print("change the input ranges to")
        print(self.parent.mass_suggestions_ranges)
        print("suggestions", self.parent.ml.suggestions.masses, self.parent.ml.suggestions.masses.shape)


class SettingsWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(SettingsWindow, self).__init__(parent)
        self.centralWidget = QtWidgets.QWidget(self)
        self.centralLayout = QtWidgets.QVBoxLayout(self.centralWidget)
        self.parent = parent

        # here I have to use a checkbox not a radiobutton because radionbuttons are exclusively only one on
        Checkbox = QtWidgets.QCheckBox("Show Min/Max Spectrum")
        Checkbox.setChecked(False)
        Checkbox.stateChanged.connect(lambda: self.onClick([1,2]))
        self.centralLayout.addWidget(Checkbox)

        Checkbox1 = QtWidgets.QCheckBox("Show Subspectra")
        Checkbox1.setChecked(False)
        Checkbox1.stateChanged.connect(lambda: self.onClick([3]))

        self.centralLayout.addWidget(Checkbox1)
        self.setCentralWidget(self.centralWidget)

    def onClick(self, index):
        if self.parent.file_loaded:
            checkbox = self.sender()
            if checkbox.isChecked():
                for i in index:
                    self.parent.plot_settings["show_plots"][i] = True
            if not checkbox.isChecked():
                for i in index:
                    self.parent.plot_settings["show_plots"][i] = False
            # print(self.parent.plot_settings["show_plots"])
            pyqtgraph_objects.replot_spectra(self.parent,self.parent.plot_settings["show_plots"])

