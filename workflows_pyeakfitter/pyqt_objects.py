import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtCore as QtCore
import numpy as np
import re

import pandas as pd

import workflows_pyeakfitter.pyqtgraph_objects as pyqtgraph_objects
import workflows_pyeakfitter.masslist_objects as mo
from PyQt5.QtCore import Qt

import configparser
import os
import sys
#menu functions

class Config():
    def __init__(self):

        self.config = configparser.ConfigParser()
        self.config_path = self.get_config_path()
        sections_and_keys = {
            'filepaths': {
                'filepath_lastreadin': '',
                'filepath_last_import_masslist':''
            },
            'ranges': {
                'lastrangesettings': '',
            }
        }
        if not os.path.exists(self.config_path):
            print("Create new config file")
            self.create_config_file(self.config_path,sections_and_keys)

    def get_config_path(self):
        # Check if the script is bundled with PyInstaller
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # Get the path to the bundled INI file
            return os.path.join(sys._MEIPASS, 'config.ini')
        else:
            # Use the relative path if running from the source code
            return 'config.ini'

    def create_config_file(self, config_file_path, sections_and_keys):
        # Create a ConfigParser instance
        config = configparser.ConfigParser()

        # Add sections and keys to the ConfigParser instance
        for section, keys in sections_and_keys.items():
            config.add_section(section)
            for key, value in keys.items():
                config.set(section, key, str(value))
        print(f"Create a config file at {config_file_path}")
        # Write the configuration to the file
        with open(config_file_path, 'w') as configfile:
            config.write(configfile)
    def save_to_config(self,section,key,value):
        try:
            config = configparser.ConfigParser()
            config.read(self.config_path)
            config.set(section, key, str(value))

            # Write the changes back to the file
            with open(self.config_path, 'w') as configfile:
                config.write(configfile)
        except:
            print("Couldnot write to config file")
    def read_from_config(self,section,key):
        try:
            config = configparser.ConfigParser()
            config.read(self.config_path)
            value = config.get(section,key)
            print(f"read in .ini from {self.config_path} for {section}, {key}: {value} ")
            return value
        except:
            print("Couldnot read config file")
            return ""

def open_file(parent):
    # show the dialog
    co = Config()
    filepath_lastreadin = co.read_from_config("filepaths","filepath_lastreadin")
    print(filepath_lastreadin)
    try:
        dialog = QtWidgets.QFileDialog()
        filepath, filter = dialog.getOpenFileName(None, "Window name", filepath_lastreadin, "HDF5_files (*.hdf5)")
    except:
        print("Old filepath not reachable")
        dialog = QtWidgets.QFileDialog()
        filepath, filter = dialog.getOpenFileName(None, "Window name", "", "HDF5_files (*.hdf5)")
    co.save_to_config("filepaths","filepath_lastreadin",filepath)
    # filepath = "D:\\Uniarbeit 23_11_09\\CERN\\CLOUD16\\arctic_runs\\2023-11-13\\results\\_result_avg.hdf5"
    print(f"Try to read in data from {filepath}")
    parent.filename = filepath
    if filepath:
        if parent.plot_added:
            print("remove old plot stuff")
            pyqtgraph_objects.remove_all_plot_items(parent)
        try:
            parent.init_basket_objects()
        except:
            print(f"Error reading in data")
            msg_box = QtWidgets.QMessageBox()
            msg_box.setIcon(QtWidgets.QMessageBox.Critical)
            msg_box.setWindowTitle("Error")
            msg_box.setText(".h5 File not readable, try it maybe with an average only file.")
            msg_box.exec_()
            open_file(parent)
        parent.file_loaded = True
        parent.init_UI_file_loaded()
        parent.init_plots(parent.graphWidget)


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

class Import_Dialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()


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
        '''
        make all layouts but add the entries after with the load function because this is dependent on the masslist and has to be loaded evertime newly
        Parameters
        ----------
        parent
        '''
        super(AddnewElement, self).__init__(parent)
        self.centralWidget = QtWidgets.QWidget(self)
        self.centralLayout = QtWidgets.QVBoxLayout(self.centralWidget)
        self.show_mass_layout = QtWidgets.QHBoxLayout()

        self.parent = parent
        self.setWindowTitle("Add new Element")


        self.setCentralWidget(self.centralWidget)
    def load(self, names_elements):
        #make form layout
        elements_implemented = ", ".join(names_elements)
        self.label_add_compound = QtWidgets.QLabel(f"Add compound (elements implemented: {elements_implemented}): ")
        self.add_compound_input = QtWidgets.QLineEdit()
        self.add_compound_input.returnPressed.connect(lambda: self.add_compound(self.add_compound_input.text()))

        self.centralLayout.addWidget(self.label_add_compound)
        self.centralLayout.addWidget(self.add_compound_input)

        self.centralLayout.addLayout(self.show_mass_layout)
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
    def add_compound(self,compoundstring):
        mass, compound = mo.get_element_numbers_out_of_names(compoundstring)
        self.parent.jump_to_mass(float(mass))
        if not (self.parent.ml.suggestions.element_numbers == compound).all(axis=1).any():
            self.parent.ml.add_suggestion_to_sugglist(self.parent, compound)
        self.showmass_label.setText(f"{round(mass,4)}")

    def addElement(self):
        compoundarray = [0]*len(self.parent.ml.names_elements)
        for index, compound in enumerate(self.compound_inquiry):
            if self.compound_inquiry[compound].text() == '':
                compoundarray[index] = 0
            else:
                compoundarray[index] = int(self.compound_inquiry[compound].text())
        compoundarray = np.array(compoundarray)
        self.parent.ml.add_suggestion_to_sugglist(self.parent, compoundarray)

    def closeWindow(self):
        self.close()
class TableModel(QtCore.QAbstractTableModel):

    def __init__(self, data):
        super(TableModel, self).__init__()
        self._data = data

    def data(self, index, role):
        if role == Qt.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]
            return str(value)

    def rowCount(self, index):
        return self._data.shape[0]

    def columnCount(self, index):
        return self._data.shape[1]

    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._data.columns[section])

            if orientation == Qt.Vertical:
                return str(self._data.index[section])
class Show_total_Masslist(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(Show_total_Masslist, self).__init__(parent)
        self.setGeometry(10,10, 1000, 1000)
        self.centralWidget = QtWidgets.QWidget(self)
        self.centralLayout = QtWidgets.QVBoxLayout(self.centralWidget)

        self.table = QtWidgets.QTableView()

        self.centralLayout.addWidget(self.table)

        self.parent = parent
        self.setWindowTitle("Total Masslist")


        closebutton = QtWidgets.QPushButton("Close")
        closebutton.clicked.connect(self.closeWindow)
        self.centralLayout.addWidget(closebutton)

        self.setCentralWidget(self.centralWidget)

    def load(self,ml):
        mass_iso_sugg_list = ml

        names_isotopes = [mo.get_names_out_of_element_numbers(el_numbers_one_parent_mass) for
                                    el_numbers_one_parent_mass in mass_iso_sugg_list.isotopes.element_numbers]
        names_masses_isotopes = [[str(round(mass,6)) +" -- "+ el_names for mass, el_names in zip(row_masses, row_names)] for
                                 row_masses, row_names in zip(mass_iso_sugg_list.isotopes.masses, names_isotopes)]
        names_masses_parent = [str(round(mass,6)) +" -- "+ el_names for mass, el_names in zip(mass_iso_sugg_list.masslist.masses,mo.get_names_out_of_element_numbers(mass_iso_sugg_list.masslist.element_numbers))]
        dataparent = pd.DataFrame(names_masses_parent,columns = ['parent mass'])
        dataiso = pd.DataFrame(names_masses_isotopes,columns=mass_iso_sugg_list.isotopes_to_include)
        data = pd.concat([dataparent, dataiso], axis=1)
        self.model = TableModel(data)
        self.table.setModel(self.model)

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
        self.instruction = QtWidgets.QLabel("Change ranges by editing the lines\n Input the range like: 1-3 & 5 & 7-10")

        self.centralWidget = QtWidgets.QWidget(self)
        self.centralLayout = QtWidgets.QVBoxLayout(self.centralWidget)

        self.formlayout = QtWidgets.QFormLayout(self)
        self.centralLayout.addLayout(self.formlayout)

        collectbutton = QtWidgets.QPushButton("OK")
        collectbutton.clicked.connect(self.change_ranges)
        self.centralLayout.addWidget(collectbutton)

        backtodefault = QtWidgets.QPushButton("Go back to default ranges")
        backtodefault.clicked.connect(self.go_backtodefault)
        self.centralLayout.addWidget(backtodefault)

        self.parent = parent

        self.setCentralWidget(self.centralWidget)

    def load(self,names_elements,mass_suggestions_numbers):
        line_edits = {}
        regex_validator = RegExpValidator(self)

        for i, key in enumerate(names_elements):
            line_edits[key] = QtWidgets.QLineEdit(self)
            line_edits[key].returnPressed.connect(self.change_ranges)

            line_edits[key].setValidator(regex_validator)
            pretext = self.get_regexp_outoflist(mass_suggestions_numbers[key])
            line_edits[key].setText(pretext)
            label = QtWidgets.QLabel(key)
            self.formlayout.addRow(label, line_edits[key])
    def go_backtodefault(self):
        mass_suggestions_numbers = {}
        for i, key in enumerate(self.parent.ml.names_elements):
            mass_suggestions_numbers[key] = list(
                range(self.parent.ml.mass_suggestions_ranges[i][0], self.parent.ml.mass_suggestions_ranges[i][1] + 1))
        self.parent.ml.mass_suggestions_numbers = mass_suggestions_numbers
        pyqtgraph_objects.remove_all_vlines(self.parent)
        self.parent.ml.reinit_old_sugg_ranges()
        xlims, ylims = self.parent.vb.viewRange()
        pyqtgraph_objects.redraw_vlines(self.parent,self.parent.graphWidget,xlims)
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
        self.parent.ml.reinit_suggestions()
        xlims, ylims = self.parent.vb.viewRange()
        pyqtgraph_objects.redraw_vlines(self.parent, self.parent.graphWidget, xlims)
        print("change the input ranges to")
        print(self.parent.ml.mass_suggestions_numbers)
        print("suggestions", self.parent.ml.suggestions.masses, self.parent.ml.suggestions.masses.shape)
        co = Config()
        co.save_to_config("ranges", "lastrangesettings", mass_suggestions_numbers)

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
                    string = string + f"{x[0]} - {x[-1]} & "
                else:
                    string = string + f"{x[0]} & "
            else:
                if len(x) > 1:
                    string = string + f"{x[0]} - {x[-1]}"
                else:
                    string = string + f"{x[0]}"
            return string


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
            pyqtgraph_objects.replot_spectra(self.parent,self.parent.graphWidget,self.parent.plot_settings["show_plots"])


class LabeledSlider(QtWidgets.QWidget):
    # implementation of labeled sliders out of https://stackoverflow.com/questions/47494305/python-pyqt4-slider-with-tick-labels
    def __init__(self, minimum, maximum, interval=1, orientation=Qt.Horizontal,
            labels=None, parent=None):
        max_number_labels = 10
        super(LabeledSlider, self).__init__(parent=parent)

        levels=range(minimum, maximum+interval, interval)
        if labels is not None:
            if not isinstance(labels, (tuple, list)):
                raise Exception("<labels> is a list or tuple.")
            if len(labels) != len(levels):
                raise Exception("Size of <labels> doesn't match levels.")

            if len(levels) > max_number_labels:
                labels_selected = [""]*len(levels)
                stepsize = int(np.floor((len(levels)+1)/max_number_labels))
                for i in range(0,max_number_labels):
                    labels_selected[i*stepsize]=labels[i*stepsize]
                labels = labels_selected
            self.levels=list(zip(levels,labels))
        else:
            self.levels=list(zip(levels,map(str,levels)))

        if orientation==Qt.Horizontal:
            self.layout=QtWidgets.QVBoxLayout(self)
        elif orientation==Qt.Vertical:
            self.layout=QtWidgets.QHBoxLayout(self)
        else:
            raise Exception("<orientation> wrong.")

        # gives some space to print labels
        self.left_margin=10
        self.top_margin=10
        self.right_margin=10
        self.bottom_margin=10

        self.layout.setContentsMargins(self.left_margin,self.top_margin,
                self.right_margin,self.bottom_margin)

        self.sl=QtWidgets.QSlider(orientation, self)
        self.sl.setMinimum(minimum)
        self.sl.setMaximum(maximum)
        self.sl.setValue(minimum)
        if orientation==Qt.Horizontal:
            self.sl.setTickPosition(QtWidgets.QSlider.TicksBelow)
            self.sl.setMinimumWidth(300) # just to make it easier to read
        else:
            self.sl.setTickPosition(QtWidgets.QSlider.TicksLeft)
            self.sl.setMinimumHeight(300) # just to make it easier to read
        self.sl.setTickInterval(interval)
        self.sl.setSingleStep(1)

        self.layout.addWidget(self.sl)

    def paintEvent(self, e):

        super(LabeledSlider,self).paintEvent(e)

        style=self.sl.style()
        painter=QtGui.QPainter(self)
        st_slider=QtWidgets.QStyleOptionSlider()
        st_slider.initFrom(self.sl)
        st_slider.orientation=self.sl.orientation()

        length=style.pixelMetric(QtWidgets.QStyle.PM_SliderLength, st_slider, self.sl)
        available=style.pixelMetric(QtWidgets.QStyle.PM_SliderSpaceAvailable, st_slider, self.sl)

        for v, v_str in self.levels:

            # get the size of the label
            rect=painter.drawText(QtCore.QRect(), Qt.TextDontPrint, v_str)

            if self.sl.orientation()==Qt.Horizontal:
                # I assume the offset is half the length of slider, therefore
                # + length//2
                x_loc=QtWidgets.QStyle.sliderPositionFromValue(self.sl.minimum(),
                        self.sl.maximum(), v, available)+length//2

                # left bound of the text = center - half of text width + L_margin
                left=x_loc-rect.width()//2+self.left_margin
                bottom=self.rect().bottom()

                # enlarge margins if clipping
                if v==self.sl.minimum():
                    if left<=0:
                        self.left_margin=rect.width()//2-x_loc
                    if self.bottom_margin<=rect.height():
                        self.bottom_margin=rect.height()

                    self.layout.setContentsMargins(self.left_margin,
                            self.top_margin, self.right_margin,
                            self.bottom_margin)

                if v==self.sl.maximum() and rect.width()//2>=self.right_margin:
                    self.right_margin=rect.width()//2
                    self.layout.setContentsMargins(self.left_margin,
                            self.top_margin, self.right_margin,
                            self.bottom_margin)

            else:
                y_loc=QtWidgets.QStyle.sliderPositionFromValue(self.sl.minimum(),
                        self.sl.maximum(), v, available, upsideDown=True)

                bottom=y_loc+length//2+rect.height()//2+self.top_margin-3
                # there is a 3 px offset that I can't attribute to any metric

                left=self.left_margin-rect.width()
                if left<=0:
                    self.left_margin=rect.width()+2
                    self.layout.setContentsMargins(self.left_margin,
                            self.top_margin, self.right_margin,
                            self.bottom_margin)

            pos=QtCore.QPoint(left, bottom)
            painter.drawText(pos, v_str)

        return


