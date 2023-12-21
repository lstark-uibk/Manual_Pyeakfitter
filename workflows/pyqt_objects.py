import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets
import numpy as np
import re
import workflows.pyqtgraph_objects as pyqtgraph_objects
import workflows.masslist_objects as mo
from PyQt5.QtCore import Qt

#menu functions
def open_file(parent):
    # show the dialog
    # dialog = QtWidgets.QFileDialog()
    # filepath, filter = dialog.getOpenFileName(None, "Window name", "", "HDF5_files (*.hdf5)")
    filepath = "D:\\Uniarbeit 23_11_09\\CERN\\CLOUD16\\arctic_runs\\2023-11-13\\results\\_result_avg.hdf5"
    parent.filename = filepath

    if filepath:
        if parent.file_loaded:
            print("remove old plot stuff")
            pyqtgraph_objects.remove_all_plot_items(parent)
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

        self.head = QtWidgets.QLabel("Help on the Manual Pyeak Fitter")
        self.head.setFont(QtGui.QFont('Arial', 20))
        self.head.setAlignment(Qt.AlignCenter)
        self.general0 = QtWidgets.QLabel("General")
        self.general1 = QtWidgets.QLabel("This is a program to produce a masslists for massspectra in _result.hdf5 files which are processed by the TOFTracer https://github.com/lukasfischer83/TOF-Tracer2 \nIt is a continuation of the ManualPeakfitter program https://github.com/lukasfischer83/peakFit in Python \nSo first load in a spectrum and begin")
        self.spectra0 = QtWidgets.QLabel("The spectra shown are:")
        self.spectra1 = QtWidgets.QLabel("- average spectrum of all spectra that are included in the _result.hdf5 file \nIn the settings you can select other spectra to show (For best performance only use average spectrum): \n- maximum and minimum spectra \n- subspectra which are average spectra of the TOFDaq .h5 files input into the TOF-Tracer2. \n--> By dragging the Slider at the bottom of the graphs you can slide through the subspectra.\n- if zoomed in, there is a local fit added, according to the masses which are in the masslist. ")
        self.movement0 = QtWidgets.QLabel("Movement")
        self.movement1 = QtWidgets.QLabel("Drag with left mouse to move left and right \nScroll for zoom \nDrag with right mouse to zoom \nMove one mass up or down with D or A \nYou can also acces certain mass by searching an the upper left or clicking on a specific mass in the masslist on the left")
        self.horizontallines0 = QtWidgets.QLabel("If you zoom in enough, horizontal lines will appear")
        self.horizontallines1 = QtWidgets.QLabel("Grey horizontal lines = Suggestions based on reasonable combinations of elements given by ranges \nRed horizontal lines = Masses in Masslist with corresponding composition \nBlue horizontal lines = Masses in masslist without composition \nGreen horizontal lines = Isotopes corresponding to the red lines")
        self.selection0 = QtWidgets.QLabel("Actions")
        self.selection1 = QtWidgets.QLabel("One Click on suggestion lines to add them to the masslist \nDouble click on an empty space to add a new mass \nDrag masses so that the local fit is best \nIf you drag the masses close to a suggestion line it will stick and link the composition with the mass \nDelete mass from masslist by rightclick or pressing delete when hovered above it")
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

class AddnewElement(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(AddnewElement, self).__init__(parent)
        self.centralWidget = QtWidgets.QWidget(self)
        self.centralLayout = QtWidgets.QVBoxLayout(self.centralWidget)
        self.add_compound_layout = QtWidgets.QHBoxLayout()
        self.centralLayout.addLayout(self.add_compound_layout)
        self.show_mass_layout = QtWidgets.QHBoxLayout()
        self.centralLayout.addLayout(self.show_mass_layout)



        self.parent = parent
        self.setWindowTitle("Add new Element")
        #make form layout
        self.label_add_compound = QtWidgets.QLabel("Add compound: ")
        self.add_compound_input = QtWidgets.QLineEdit()
        self.add_compound_input.returnPressed.connect(lambda: self.add_compound(self.add_compound_input.text()))

        self.add_compound_layout.addWidget(self.label_add_compound)
        self.add_compound_layout.addWidget(self.add_compound_input)

        self.showcompound_label = QtWidgets.QLabel("Mass:")
        self.showmass_label = QtWidgets.QLabel()
        self.show_mass_layout.addWidget(self.showcompound_label)
        self.show_mass_layout.addWidget(self.showmass_label)


        collectbutton = QtWidgets.QPushButton("Add Element")
        collectbutton.clicked.connect(lambda: self.add_compound(self.add_compound_input.text()))
        self.centralLayout.addWidget(collectbutton)
        closebutton = QtWidgets.QPushButton("Close")
        closebutton.clicked.connect(self.closeWindow)
        self.centralLayout.addWidget(closebutton)

        self.setCentralWidget(self.centralWidget)
    def add_compound(self,compoundstring):
        print(compoundstring)
        mass, compound = mo.get_element_numbers_out_of_names(compoundstring)
        self.parent.jump_to_mass(float(mass))
        if not (self.parent.ml.suggestions.element_numbers == compound).all(axis=1).any():
            self.parent.ml.add_suggestion_to_sugglist(self.parent, compound)
        self.showmass_label.setText(f"{mass}")
        print(mass, compound)

    def addElement(self):
        compoundarray = [0]*len(self.parent.ml.names_elements)
        for index, compound in enumerate(self.compound_inquiry):
            if self.compound_inquiry[compound].text() == '':
                compoundarray[index] = 0
            else:
                compoundarray[index] = int(self.compound_inquiry[compound].text())
        print(compoundarray)
        compoundarray = np.array(compoundarray)
        self.parent.ml.add_suggestion_to_sugglist(self.parent, compoundarray)

    def closeWindow(self):
        self.close()



class RegExpValidator(QtGui.QValidator):
    def __init__(self, parent=None):
        super(RegExpValidator, self).__init__(parent)
        self.reg_exp = re.compile(r'(((\d+)?\s*-?\s*(\d+)?)\s*&?\s*)*')
        self.reg_expfindall = re.compile(r'(\d+)?\s*-?\s*(\d+)?\s*&?\s*')
        # self.reg_exp = re.compile(r'(\d+)\s*')

    def validate(self, input_text, pos):
        input_numbers = re.findall(self.reg_expfindall,input_text)
        numberordering_correct = True
        for y in input_numbers:
            try:
                if float(y[0]) > float(y[1]):
                    numberordering_correct = False
            except:
                pass
        if self.reg_exp.fullmatch(input_text) and numberordering_correct:
            return QtGui.QValidator.Acceptable, input_text, pos
        elif input_text == '':
            return QtGui.QValidator.Intermediate, input_text, pos
        else:
            return QtGui.QValidator.Invalid, input_text, pos

class SelectMassRangeWindow(QtWidgets.QMainWindow):
    def __init__(self,parent):
        super(SelectMassRangeWindow, self).__init__(parent)
        self.centralWidget = QtWidgets.QWidget(self)
        self.centralLayout = QtWidgets.QVBoxLayout(self.centralWidget)
        self.parent = parent

        self.instruction = QtWidgets.QLabel("Change ranges by editing the lines\n Input the range like: 1-3 & 5 & 7-10")
        line_edits = {}
        regex_validator = RegExpValidator(self)
        self.formlayout = QtWidgets.QFormLayout(self)
        self.centralLayout.addLayout(self.formlayout)

        for i, key in enumerate(self.parent.ml.names_elements):
            line_edits[key] = QtWidgets.QLineEdit(self)
            line_edits[key].returnPressed.connect(self.change_ranges)

            line_edits[key].setValidator(regex_validator)
            pretext = self.get_regexp_outoflist(self.parent.ml.mass_suggestions_numbers[key])
            line_edits[key].setText(pretext)
            label = QtWidgets.QLabel(key)
            self.formlayout.addRow(label, line_edits[key])

        collectbutton = QtWidgets.QPushButton("OK")
        collectbutton.clicked.connect(self.change_ranges)
        self.centralLayout.addWidget(collectbutton)

        backtodefault = QtWidgets.QPushButton("Go back to default ranges")
        backtodefault.clicked.connect(self.go_backtodefault)
        self.centralLayout.addWidget(backtodefault)



        self.setCentralWidget(self.centralWidget)
    def go_backtodefault(self):
        mass_suggestions_numbers = {}
        for i, key in enumerate(self.parent.ml.names_elements):
            mass_suggestions_numbers[key] = list(
                range(self.parent.ml.mass_suggestions_ranges[i][0], self.parent.ml.mass_suggestions_ranges[i][1] + 1))
        self.parent.ml.mass_suggestions_numbers = mass_suggestions_numbers
        pyqtgraph_objects.remove_all_vlines(self.parent)
        self.parent.ml.reinit(self.parent.filename)
        xlims, ylims = self.parent.vb.viewRange()
        pyqtgraph_objects.redraw_vlines(self.parent, xlims)
        print("Go back to default Suggestions")
        print(self.parent.ml.mass_suggestions_numbers)
        print("suggestions", self.parent.ml.suggestions.masses, self.parent.ml.suggestions.masses.shape)
        for row in range(self.formlayout.count()):
            label_item = self.formlayout.itemAt(row, QtWidgets.QFormLayout.LabelRole)
            field_item = self.formlayout.itemAt(row, QtWidgets.QFormLayout.FieldRole)
            if field_item:
                element = label_item.widget().text()
                field_item.widget().setText(self.get_regexp_outoflist(self.parent.ml.mass_suggestions_numbers[element]))

    def change_ranges(self):
        #read in the mass suggestion numbers, that are put in
        mass_suggestions_numbers = {}
        for row in range(self.formlayout.count()):
            label_item = self.formlayout.itemAt(row, QtWidgets.QFormLayout.LabelRole)
            field_item = self.formlayout.itemAt(row, QtWidgets.QFormLayout.FieldRole)
            if field_item:
                line_edit = field_item.widget()
                text = line_edit.text()
                element = label_item.widget().text()
                mass_suggestions_numbers[element] = []
                pattern = re.compile(r'(\d+)?\s*-?\s*(\d+)?\s*&?\s*')
                readinlist = re.findall(pattern,text)

                for i, x in enumerate(readinlist):
                    start = 0
                    end = 0
                    try:
                        start = int(x[0])
                        try:
                            end = int(x[1])
                        except:
                            pass
                    except:
                        pass
                    if start or end:
                        if end:
                            mass_suggestions_numbers[element] += list(range(start,end+1))
                        else:
                            mass_suggestions_numbers[element].append(start)
                    else:
                        pass
                        mass_suggestions_numbers[element].append(0)
                mass_suggestions_numbers[element] = list(set(mass_suggestions_numbers[element]))
        #assign them to the ml object
        self.parent.ml.mass_suggestions_numbers = mass_suggestions_numbers
        pyqtgraph_objects.remove_all_vlines(self.parent)
        self.parent.ml.reinit(self.parent.filename)
        xlims, ylims = self.parent.vb.viewRange()
        pyqtgraph_objects.redraw_vlines(self.parent, xlims)
        print("change the input ranges to")
        print(self.parent.ml.mass_suggestions_numbers)
        print("suggestions", self.parent.ml.suggestions.masses, self.parent.ml.suggestions.masses.shape)

    def get_regexp_outoflist(self, sugg_numbers):
        result = []
        current_group = []
        for number in sugg_numbers:
            if not current_group or number == current_group[-1] + 1:
                current_group.append(number)
            else:
                result.append(current_group)
                current_group = [number]
        if current_group:
            result.append(current_group)

        string = ""
        for i, x in enumerate(result):
            if i < len(result) - 1:
                if len(x) > 1:
                    print(x[0])
                    string = string + f"{x[0]} - {x[-1]} & "
                else:
                    string = string + f"{x[0]} & "
            else:
                if len(x) > 1:
                    string = string + f"{x[0]} - {x[-1]}"
                else:
                    string = string + f"{x[0]}"
            return string
            print(string)


class Show_suggestions(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(AddnewElement, self).__init__(parent)
        self.centralWidget = QtWidgets.QWidget(self)
        self.centralLayout = QtWidgets.QVBoxLayout(self.centralWidget)

class PlotSettingsWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(PlotSettingsWindow, self).__init__(parent)
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

