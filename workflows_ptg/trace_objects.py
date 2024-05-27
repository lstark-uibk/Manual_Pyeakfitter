import numpy as np
import math
import h5py
import datetime
from PyQt5.QtCore import QDateTime, Qt, pyqtSignal
from PyQt5.QtWidgets import QListWidgetItem, QListWidget, QPushButton
from PyQt5.QtGui import QColor
import pyqtgraph as pg
import re
class Traces():
    MasslistElements = ["C", "C13", "H", "H+", "N", "O", "O18", "S"]
    Order_of_letters = [0, 1, 2, 7, 4, 5, 6, 3]
    MasslistElementsMasses = np.array([12,
                                13.00335,
                                1.00783,
                                1.007276,
                                14.00307,
                                15.99492,
                                17.99916,
                                31.97207,
                               ])
    def __init__(self,Filename,useAveragesOnly=True,startTime = 0, endTime = 0,Raw = True):
        self.Times = []
        self.Timeindices = []
        self.MasslistMasses = []

        self.MasslistElements = []
        self.MasslistElementsMasses = []
        self.MasslistCompositions = []
        self.Traces = np.array([])
        self.FixedTraces = np.array([])
        self.filename = Filename
        self.starttime = startTime
        self.endtime = endTime
        self.raw = True
        self.useaveragesonly = True

        self._init_information()



    def _init_information(self):
        with h5py.File(self.filename, "r") as f:
            from_timestamp_vec = np.vectorize(lambda x: QDateTime.fromSecsSinceEpoch(int(round(x))))
            # self.Times = from_timestamp_vec(self.Times)
            print("Loading Masslist Information")
            #check time ordering
            self.MasslistMasses = f["MassList"][()]
            self.MasslistCompositions = f["ElementalCompositions"][()]
        print("loading Times")
        self.update_Times()
        print("loading Traces")
        self.update_Traces(massesToLoad = "none")
    def update_Times_Traces(self,massesToLoad = "none"):
        self.update_Times()
        self.update_Traces(massesToLoad)
    def update_Times(self):
        with h5py.File(self.filename, "r") as f:
            print("Loading Times:")
            timeshifthours = 1
            if self.useaveragesonly:
                self.Times = f["AvgStickCpsTimes"][()]
            else:
                try:
                    self.Times = f["Times"][()]
                except:
                    print("Could not load high res time, maybe this is an average-only result file?")
                    return np.array([])
            if self.starttime < self.endtime:
                self.Timeindices = np.where((self.Times >= self.starttime) & (self.Times <= self.endtime))[0]
                self.Times = self.Times[self.Timeindices]
            else:
                self.Timeindices = np.where(np.full(self.Times.shape, True))[0]
            self.Times = self.Times - timeshifthours * 60*60
        return self.Times

    def load_Traces(self, massesToLoad = "none"):
        """

        :param filename:
        :param massesToLoad: np.array[] if masseToLoad = "all" -> load all masses, if "none" -> no masses
        :param Timeindices:
        :param useAveragesOnly:
        :param raw:
        :return:
        """
        filename = self.filename
        if isinstance(massesToLoad, np.ndarray) or isinstance(massesToLoad,(float,int)):
            Massestoloadindices = np.where(np.any((np.isclose(self.MasslistMasses[:, None], massesToLoad , rtol=1e-5, atol=1e-8)),axis=1))[0]
            if isinstance(massesToLoad,(float,int)):
                Massestoloadindices = int(Massestoloadindices)
            print(f"Loading Masses {massesToLoad} at indices, {Massestoloadindices}")
        else:
            if massesToLoad == "none":
                print("No Masses to load selected")
                return np.array([])
            elif massesToLoad == "all":
                print("Loading all Masses")
                Massestoloadindices = np.where(np.full(self.MasslistMasses.shape, True))
            else:
                print("Unknow Masses to Load")
                return np.array([])


        with h5py.File(filename, "r") as f:
            if self.useaveragesonly:
                self.Times = f["AvgStickCpsTimes"][()]
                print("Loading Average Traces")
                if self.raw:
                    print("Raw")
                    ds = f["AvgStickCps"]
                else:
                    print("Corrected")
                    ds = f["CorrAvgStickCps"]
            else:
                print("Loading high time resolution Traces")
                try:
                    self.Times = f["Times"][()]
                except:
                    print("Could not load high res time, maybe this is an average-only result file?")
                    return []
                if self.raw:
                    print("Raw")
                    if "StickCps" in f:
                        ds = f["StickCps"]
                    else:
                        print("No high time resolution available, is this a average only file?")
                        ds = f["AvgStickCps"]
                else:
                    if "CorrStickCps" in f:
                        print("Corrected")
                        ds = f["CorrStickCps"]
                    else:
                        print("No high time resolution available, is this a average only file?")
                        ds = f["CorrAvgStickCps"]
            Traces = ds[:, self.Timeindices][Massestoloadindices, :]
            return Traces
    def update_Traces(self, massesToLoad = "none"):
            self.Traces = self.load_Traces(massesToLoad)




            # get all the indices of massesToLoad

class QlistWidget_Masslist(QListWidget):
    itemClicked = pyqtSignal(QListWidgetItem, Qt.MouseButton)
    def __init__(self, parent, Masses, Compositions):
        super().__init__(parent)
        #this is the masses and compounds that will change during all the operations (like sorting etc
        self.masses = Masses
        self.compositions = Compositions
        self.currentmasses = np.array([])
        self.currentcompositions = np.zeros((0, 8))
        self.load_on_tick = True
        self.fixedMasses = np.array([])
        self.fixedcompositions = np.zeros((0, 8))

    def mousePressEvent(self, event):
        #override the inbuilt mousepress event to give a signal itemClicked which has the item and the button
        item = self.itemAt(event.pos())
        if item:
            self.itemClicked.emit(item, event.button())
        super().mousePressEvent(event)


    def redo_qlist(self,MasslistMasses,MasslistCompositions):
        '''Update the List on the right side of the Plot

        Parameters
        ----------
        qlist : QtWidgets.QListWidget

        Returns
        -------
        None
        '''
        self.masses = MasslistMasses
        self.compositions = MasslistCompositions
        self.clear()
        for index , (mass,element_numbers) in enumerate(zip(MasslistMasses, MasslistCompositions)):
            index += 1
            item = QListWidgetItem(f"{str(index)}\t{str(round(mass,6))} {get_names_out_of_element_numbers(element_numbers)}")
            # item.setFlags(item.flags() | 1)  # Add the Qt.ItemIsUserCheckable flag
            # item.setCheckState(0)  # 0 for Unchecked, 2 for Checked
            self.addItem(item)
    def jump_to_mass(self, event, parent):
        borders = event.split("-")
        print(borders)
        if len(borders) == 1:
            mass = float(event)
            mass_difference = np.abs(self.masses - mass)
            # Find the index of the nearest entry
            index_of_nearest = np.argmin(mass_difference)
            self.setCurrentItem(self.item(index_of_nearest))
            self.check_single(index_of_nearest,parent)
        elif len(borders) == 2:
            lowermass, uppermass = borders
            lowermass = float(lowermass)
            uppermass = float(uppermass)
            if lowermass < uppermass:
                lower_index = np.argmin(np.abs(self.masses - lowermass))
                upper_index = np.argmin(np.abs(self.masses - uppermass))
                self.setCurrentItem(self.item(lower_index))
                self.check_multiple(lower_index,upper_index,parent)
    def jump_to_compound(self,compoundstring,parent):
        mass, elementnumber = get_element_numbers_out_of_names(compoundstring)
        self.jump_to_mass(str(mass),parent)
    def masslist_tick_changed(self,parent):
        if self.load_on_tick:
            self.currentmasses = np.array([])
            self.currentcompositions = np.zeros((0, 8))

            for i in range(self.count()):
                item = self.item(i)
                state = item.checkState()
                if state == 2:
                    self.currentmasses = np.append(self.currentmasses, self.masses[i])
                    self.currentcompositions = np.append(self.currentcompositions, [self.compositions[i, :]], axis=0)

            parent.tr.update_Traces(self.currentmasses)
            parent.update_plots()

    def check_single(self, index, parent, massesselectedlist):
        item = self.item(index)
        item.setCheckState(Qt.Checked)
        self.currentmasses = np.append(self.currentmasses, self.masses[index])
        self.currentcompositions = np.append(self.currentcompositions, [self.compositions[index, :]], axis=0)

        parent.tr.update_Traces(self.currentmasses)
        parent.update_plots()
    def check_multiple(self,lower, upper,parent):
        """

        :param checkstate: True or False
        :return:
        """
        if upper-lower > 100:
            print("Too many traces selected, only plot first 100")
            upper = lower + 100
        self.load_on_tick = False
        for i in range(lower,upper):
            item = self.item(i)
            item.setCheckState(Qt.Checked)
            self.currentmasses = np.append(self.currentmasses, self.masses[i])
            self.currentcompositions = np.append(self.currentcompositions, [self.compositions[i, :]], axis=0)
        self.load_on_tick = True


        parent.tr.update_Traces(self.currentmasses)
        parent.update_plots()
        
    def uncheck_all(self,parent):
        self.load_on_tick = False
        for i in range(self.count()):
            item = self.item(i)
            item.setCheckState(Qt.Unchecked)
        self.load_on_tick = True
        self.currentmasses = np.array([])
        self.currentcompositions = np.zeros((0, 8))
        
        parent.tr.update_Traces(self.currentmasses)
        parent.update_plots()

    def handle_double_click(self,item,parent):
        print(f"Double-clicked: {item.text()}")
        # list = re.split(r'[ \t]+', item.text())
        # mass = float(list[1])
        # if not np.any(mass == self.fixedMasses):
        #     # add the mass to fixed
        #     item.setBackground(Qt.red)
        #     if len(list) >= 3:
        #         compoundstr = str(list[2])
        #         if len(list) == 4:
        #             compoundstr += str(list[3])
        #         _,compositionarray = get_element_numbers_out_of_names(compoundstr)
        #     self.fixedMasses = np.append(self.fixedMasses,mass)
        #     self.fixedcompositions = np.append(self.fixedcompositions, compositionarray[None,:], axis=0)
        #     Trace = parent.tr.load_Traces(mass)
        #     if parent.tr.FixedTraces.size == 0:
        #         parent.tr.FixedTraces = np.zeros((0,Trace.size))
        #     parent.tr.FixedTraces = np.append(parent.tr.FixedTraces, parent.tr.load_Traces(mass)[None,:], axis=0)
        # else:
        #     #if it is already in fixed -> delete it
        #     # add the mass to fixed
        #     item.setBackground(QColor(255, 255, 255))
        #     index_of_deletion = np.where(self.fixedMasses == mass)
        #     self.fixedMasses = np.delete(self.fixedMasses, index_of_deletion)
        #     self.fixedcompositions = np.delete(self.fixedcompositions , index_of_deletion, axis = 0)
        #     parent.tr.FixedTraces = np.delete(parent.tr.FixedTraces , index_of_deletion, axis = 0)
        #
        #
        # parent.update_plots()

class Sorting():
    def __init__(self, window,layout, Sorting_function, text):
        # so a sorting function should map a input corresponding to the masslist (e.g. all trace) to a list sorting the input
        self.sorting_function = Sorting_function
        self.sortingbutton = QPushButton(text, window)
        self.sortingbutton.setGeometry(10, 10, 100, 100)
        layout.addWidget(self.sortingbutton)

    def sort_qlist(self,qlist,input_to_sortingfunc):
        masses, compositions = qlist.masses, qlist.compositions
        #first sort to masses, because traces re sorted to masses
        sorted_masses = np.argsort(masses)
        masses = masses[sorted_masses]
        compositions = compositions[sorted_masses]
        sorted = self.sorting_function(input_to_sortingfunc)
        qlist.masses = masses[sorted]
        qlist.compounds = compositions[sorted]
        qlist.redo_qlist(qlist.masses,qlist.compounds)


class QlistWidget_Selected_Masses(QListWidget):
    itemClicked = pyqtSignal(QListWidgetItem, Qt.MouseButton)
    def __init__(self, parent):
        super().__init__(parent)
        # this is the masses and compounds that will change during all the operations (like sorting etc
        self.selectedmasses = np.array([])
        self.selectedcompositions = np.zeros((0, 8))
        self.current_clicked_mass = 0
        self.defaultcolorcycle = [
            (255, 0, 0),     # Red
            (0, 255, 0),     # Green
            (0, 0, 255),     # Blue
            (255, 0, 255),   # Magenta
            (0, 255, 255),   # Cyan
            (255, 165, 0),   # Orange
            (255, 192, 203), # Pink
            (128, 0, 128),   # Purple
            (0, 128, 128),   # Teal
            (64, 224, 208),  # Turquoise
            (135, 206, 235), # Sky Blue
            (50, 205, 50),   # Lime Green
            (255, 218, 185), # Peach
            (230, 230, 250), # Lavender
            (255, 99, 71),   # Tomato
            (255, 140, 0),   # DarkOrange
            (0, 255, 127),   # SpringGreen
            (255, 215, 0),   # Gold
            (255, 69, 0),    # RedOrange
            (0, 191, 255),   # DeepSkyBlue
            (0, 255, 255),   # Cyan
            (75, 0, 130),    # Indigo
            (0, 128, 0),     # Green
            (240, 128, 128)] # LightCoral
        self.defaultcolorassignment = {1:1,2:2,3:3,4:4,5:5,6:6,7:7,8:8,9:9}


    def mousePressEvent(self, event):
        #override the inbuilt mousepress event to give a signal itemClicked which has the item and the button
        item = self.itemAt(event.pos())
        if item:
            self.itemClicked.emit(item, event.button())
        super().mousePressEvent(event)

    def add_mass_to_selected_masses(self,event,parent):
        borders = event.split("-")
        print(borders)
        if len(borders) == 1:
            mass = float(event)
            mass_difference = np.abs(self.masses - mass)
            # Find the index of the nearest entry
            index_of_nearest = np.argmin(mass_difference)
            self.setCurrentItem(self.item(index_of_nearest))
            self.check_single(index_of_nearest,parent)
        elif len(borders) == 2:
            lowermass, uppermass = borders
            lowermass = float(lowermass)
            uppermass = float(uppermass)
            if lowermass < uppermass:
                lower_index = np.argmin(np.abs(parent.masslist_widget.masses - lowermass))
                upper_index = np.argmin(np.abs(parent.masslist_widget.masses - uppermass))

                print(lower_index,upper_index)
                new_masses = parent.masslist_widget.masses[lower_index:upper_index]
                new_compositions = parent.masslist_widget.compositions[lower_index:upper_index]
                print(f"new mass {new_masses}, {new_compositions}")
                for new_mass,new_composition in zip(new_masses,new_compositions):
                    if new_mass not in self.selectedmasses:
                        self.selectedmasses = np.append(self.selectedmasses, new_mass)
                        self.selectedcompositions = np.append(self.selectedcompositions, [new_composition], axis=0)
                print(self.selectedmasses,self.selectedcompositions)
                parent.tr.update_Traces(self.selectedmasses)
                self.redo_qlist()
                parent.update_plots()

    def add_item_to_selected_masses(self,item,button,parent):
        row = int(parent.masslist_widget.row(item))
        print(f"index {row}")
        new_mass = parent.masslist_widget.masses[row]
        new_composition = parent.masslist_widget.compositions[row, :]
        print(f"new mass {new_mass}, {new_composition}")
        if button == 1:#left click
            new_mass = parent.masslist_widget.masses[row]
            new_composition = parent.masslist_widget.compositions[row, :]
            print(f"new mass {new_mass}, {new_composition}")
            if new_mass not in self.selectedmasses:
                self.selectedmasses = np.append(self.selectedmasses, new_mass)
                self.selectedcompositions = np.append(self.selectedcompositions, [new_composition], axis=0)
            print(self.selectedmasses, self.selectedcompositions)
            parent.tr.update_Traces(self.selectedmasses)
            self.redo_qlist()
            parent.update_plots()
        elif button == 2:
            print(f"Right click update peak plot for mass {new_mass}")


    def add_index_to_selected_masses(self,lower_index,parent,upper_index = 0):
        print(f"--------------{lower_index},{upper_index}")
        if upper_index == 0:
            self.selectedmasses = np.append(self.selectedmasses, parent.masslist_widget.masses[lower_index])
            self.selectedcompositions = np.append(self.selectedcompositions, parent.masslist_widget.compositions[lower_index], axis=0)
        else:
            self.selectedmasses = np.append(self.selectedmasses, parent.masslist_widget.masses[lower_index:upper_index])
            self.selectedcompositions = np.append(self.selectedcompositions, parent.masslist_widget.compositions[lower_index:upper_index], axis=0)

        parent.tr.update_Traces(self.selectedmasses)
        self.redo_qlist()
        parent.update_plots()
    def redo_qlist(self):
        '''Update the List on the right side of the Plot

        Parameters
        ----------
        qlist : QtWidgets.QListWidget

        Returns
        -------
        None
        '''
        self.clear()
        for index , (mass,element_numbers,color) in enumerate(zip(self.selectedmasses, self.selectedcompositions,self.defaultcolorcycle)):
            index += 1
            item = QListWidgetItem(f"{str(index)}\t{str(round(mass,6))} {get_names_out_of_element_numbers(element_numbers)}")
            #make color alpha
            color = color+(30,)
            QListWidgetItem.setBackground(item,QColor(*color))
            self.addItem(item)
    def deselect_all(self,parent):
        self.current_clicked_mass = 0
        self.selectedmasses = np.array([])
        self.selectedcompositions = np.zeros((0, 8))
        self.redo_qlist()
        parent.update_plots()

    def clicked_on_item(self,item,button,parent):
        row = int(self.row(item))
        if row < 0:
            row = 0
        print(f"row {row}")
        clicked_mass = self.selectedmasses[row]
        print(f"clicked mass {clicked_mass}")
        if button == 1:#left click
            self.current_clicked_mass = clicked_mass
            parent.update_plots()
        elif button == 2:
            print(f"Delete Mass {clicked_mass} out of selected masses {self.selectedmasses} in row {row}")
            self.selectedmasses = np.delete(self.selectedmasses,row)
            self.selectedcompositions = np.delete(self.selectedcompositions,row,axis=0)
            print(self.selectedmasses,self.selectedcompositions)
            self.redo_qlist()
            parent.tr.update_Traces(self.selectedmasses)
            parent.update_plots()
    def check_single(self, index, parent):
        item = self.item(index)
        item.setCheckState(Qt.Checked)
        self.currentmasses = np.append(self.currentmasses, self.masses[index])
        self.currentcompositions = np.append(self.currentcompositions, [self.compositions[index, :]], axis=0)

        parent.tr.update_Traces(self.currentmasses)
        parent.update_plots()

    def check_multiple(self, lower, upper, parent):
        """

        :param checkstate: True or False
        :return:
        """
        if upper - lower > 100:
            print("Too many traces selected, only plot first 100")
            upper = lower + 100
        self.load_on_tick = False
        for i in range(lower, upper):
            item = self.item(i)
            item.setCheckState(Qt.Checked)
            self.currentmasses = np.append(self.currentmasses, self.masses[i])
            self.currentcompositions = np.append(self.currentcompositions, [self.compositions[i, :]], axis=0)
        self.load_on_tick = True

        parent.tr.update_Traces(self.currentmasses)
        parent.update_plots()

    def uncheck_all(self, parent):
        self.load_on_tick = False
        for i in range(self.count()):
            item = self.item(i)
            item.setCheckState(Qt.Unchecked)
        self.load_on_tick = True
        self.currentmasses = np.array([])
        self.currentcompositions = np.zeros((0, 8))

        parent.tr.update_Traces(self.currentmasses)
        parent.update_plots()

    def handle_double_click(self, item, parent):
        print(f"Double-clicked: {item.text()}")
        list = re.split(r'[ \t]+', item.text())
        mass = float(list[1])
        if not np.any(mass == self.fixedMasses):
            # add the mass to fixed
            item.setBackground(Qt.red)
            if len(list) >= 3:
                compoundstr = str(list[2])
                if len(list) == 4:
                    compoundstr += str(list[3])
                _, compositionarray = get_element_numbers_out_of_names(compoundstr)
            self.fixedMasses = np.append(self.fixedMasses, mass)
            self.fixedcompositions = np.append(self.fixedcompositions, compositionarray[None, :], axis=0)
            Trace = parent.tr.load_Traces(mass)
            if parent.tr.FixedTraces.size == 0:
                parent.tr.FixedTraces = np.zeros((0, Trace.size))
            parent.tr.FixedTraces = np.append(parent.tr.FixedTraces, parent.tr.load_Traces(mass)[None, :], axis=0)
        else:
            # if it is already in fixed -> delete it
            # add the mass to fixed
            item.setBackground(QColor(255, 255, 255))
            index_of_deletion = np.where(self.fixedMasses == mass)
            self.fixedMasses = np.delete(self.fixedMasses, index_of_deletion)
            self.fixedcompositions = np.delete(self.fixedcompositions, index_of_deletion, axis=0)
            parent.tr.FixedTraces = np.delete(parent.tr.FixedTraces, index_of_deletion, axis=0)

        parent.update_plots()


class Sorting():
    def __init__(self, window, layout, Sorting_function, text):
        # so a sorting function should map a input corresponding to the masslist (e.g. all trace) to a list sorting the input
        self.sorting_function = Sorting_function
        self.sortingbutton = QPushButton(text, window)
        self.sortingbutton.setGeometry(10, 10, 100, 100)
        layout.addWidget(self.sortingbutton)

    def sort_qlist(self, qlist, input_to_sortingfunc):
        masses, compositions = qlist.masses, qlist.compositions
        # first sort to masses, because traces re sorted to masses
        sorted_masses = np.argsort(masses)
        masses = masses[sorted_masses]
        compositions = compositions[sorted_masses]
        sorted = self.sorting_function(input_to_sortingfunc)
        qlist.masses = masses[sorted]
        qlist.compounds = compositions[sorted]
        qlist.redo_qlist(qlist.masses, qlist.compounds)


def get_names_out_of_element_numbers(compound_array):
    # only if any compounds are in compound array give a string
    '''Get the compound name out of a compound array

    Parameters
    ----------
    compound_array : np.array (nr_elements, nr_compounds)
        corresponding to the rules used in Masslist object

    Returns
    -------
    compoundname_list:
        str if compound_array is (nr_elements, 1)
            compound name
        list if (nr_elements, nr_compounds)
            compound names
    '''

    compoundname_list = []

    for compound in compound_array:
        if len(compound_array.shape) == 1:
            compound = compound_array
        if np.any(compound):
            order_of_letters = Traces.Order_of_letters
            names_elements = Traces.MasslistElements
            compoundletters = ""
            for index, order in enumerate(order_of_letters):
                # before the last letter (H+) add a " "
                if index == len(order_of_letters)-1:
                    compoundletters += " "
                if compound[order] == 0:
                    pass
                if compound[order] == 1:
                    compoundletters += names_elements[order]
                if compound[order] > 1:
                    compoundletters += names_elements[order] + str(round(compound[order]))
            compoundname_list.append(compoundletters)
            if len(compound_array.shape) == 1:
                return compoundletters
        else:
            if len(compound_array.shape) == 1:
                return ""
            compoundname_list.append("")

    return compoundname_list


def get_element_numbers_out_of_names(namestring):
    '''Get the compound name out of a compound array

    Parameters
    ----------
    namestring : str characters and numbers in any order

    Returns
    -------
    mass: float
        mass of the compound
    element_numbers: np.array (nr_elemets)


    '''
    ion = False
    if "+" in namestring:
        ion = True
        namestring = namestring.replace("+","")

    charlist = re.split(r'([a-zA-Z]\d+)|([a-zA-Z](?=[a-zA-Z]))', namestring)
    charlist = np.array([part for part in charlist if part],dtype="str")

    elements = np.array([""]*charlist.size, dtype = "str")
    numbers = np.zeros(charlist.size)
    for index, el_num in enumerate(charlist):
        if re.match(r'[a-zA-Z]\d', el_num):  # Character followed by a number
            splitted = re.split(r'([a-zA-Z])(\d+)',el_num)
            splitted = [part for part in splitted if part]
            element, number = splitted
            number = int(number)
            if element not in elements: #if the element is not already considered
                elements[index] = element
                numbers[index] = number
            else: #takes care of double writing eg C7H8NH4+
                numbers[element == elements] += number
        else:  # Character followed by another character
            if el_num not in elements: #if the element is not already considered
                elements[index] = el_num
                numbers[index] = 1
            else: #takes care of double writing eg C7H8NH4+
                numbers[el_num == elements] += 1


    if ion:
        elements = np.append(elements,"H+")
        numbers = np.append(numbers,1)
        number_H_mask = np.array([x.lower() for x in elements], dtype='str') == "h"
        if numbers[number_H_mask] > 0: # if the H number is more than 0
            numbers[number_H_mask] -= 1

    elementsinstring_lower = np.array([x.lower() for x in elements], dtype = 'str')

    names_elements = Traces.MasslistElements
    compound_array = np.array([0] * len(names_elements))
    for index,element in enumerate(names_elements):
        #make it lower, so that we have more freedom in writing
        element_lower = element.lower()
        if np.any(element_lower == elementsinstring_lower):
            compound_array[index] = numbers[element_lower == elementsinstring_lower]

    mass = np.sum(compound_array*Traces.MasslistElementsMasses)
    return mass, compound_array


tr = Traces(r"D:\Uniarbeit 23_11_09\CERN\CLOUD16\arctic_runs\2023-11-09to2023-11-12\results\_result_avg.hdf5")
tr.load_Traces("all")
