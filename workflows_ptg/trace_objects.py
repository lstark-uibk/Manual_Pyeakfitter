import numpy as np
import math
import h5py
import datetime
import random
import pyqtgraph
from PyQt5.QtCore import QDateTime, Qt, pyqtSignal
from PyQt5.QtWidgets import QListWidgetItem, QListWidget, QPushButton
from PyQt5.QtGui import QColor
import pyqtgraph as pg
import  workflows_pyeakfitter.pyqtgraph_objects as pyqto
import workflows_pyeakfitter.masslist_objects as mo
import re
class Traces():
    MasslistElements =["C", "C(13)", "H", "H+", "N", "O", "O(18)", "S","S(34)", "I", "Si"] #iodine, silizium
    Order_of_letters = [0, 1, 2, 9, 4, 5, 6, 7 ,8 , 10 ,3]
    MasslistElementsMasses = np.array([12,
                                13.00335,
                                1.00783,
                                1.007276,
                                14.00307,
                                15.99492,
                                17.99916,
                                31.97207,
                                33.967867, # https://en.wikipedia.org/wiki/Isotopes_of_sulfur
                                126.90448,
                                27.9763
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
        order_input_masses = np.argsort(massesToLoad)
        # massesToLoad = massesToLoad[order_input_masses]
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
            Traces = ds[:, self.Timeindices][Massestoloadindices, :][np.argsort(order_input_masses),:] # gives the Traces in the same order as it was input
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
            item = QListWidgetItem(f"{str(index)}\t{str(round(mass,6))} {mo.get_names_out_of_element_numbers(element_numbers)}")
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
        print(compoundstring)
        mass, elementnumber = mo.get_element_numbers_out_of_names(compoundstring)
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

        def random_color():
            """
            Generate a random color in RGB format.
            """
            r = random.randint(0, 255)  # Red component
            g = random.randint(0, 255)  # Green component
            b = random.randint(0, 255)  # Blue component
            return (r, g, b)

        for x in range(0, 1000):
            self.defaultcolorcycle.append(random_color())
        self.defaultcolorassignment = {}
        self.highlight_this_mass_vline = []


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
                lower_index = np.argmin(np.abs(parent.masslist_frame.masslist_widget.masses - lowermass))
                upper_index = np.argmin(np.abs(parent.masslist_frame.masslist_widget.masses - uppermass))

                # print(lower_index,upper_index)
                new_masses = parent.masslist_frame.masslist_widget.masses[lower_index:upper_index]
                new_compositions = parent.masslist_frame.masslist_widget.compositions[lower_index:upper_index]
                print(f"new mass {new_masses}, {new_compositions}")
                for new_mass,new_composition in zip(new_masses,new_compositions):
                    if new_mass not in self.selectedmasses:
                        self.selectedmasses = np.append(self.selectedmasses, new_mass)
                        self.selectedcompositions = np.append(self.selectedcompositions, [new_composition], axis=0)
                # print(self.selectedmasses,self.selectedcompositions)
                parent.tr.update_Traces(self.selectedmasses)
                self.redo_qlist()
                parent.update_plots()

    def add_compound(self,text,parent):
        mass, elementnumber = mo.get_element_numbers_out_of_names(text)
        print(mass,elementnumber)
        elementnumber = elementnumber[0:8]
        if mass in parent.masslist_frame.masslist_widget.masses:
            self.add_one_mass(mass, np.array(elementnumber), parent)
            parent.masslist_frame.jump_to_compound_status.setText("")
        else:
            parent.masslist_frame.jump_to_compound_status.setText("Not in masslist")

    def add_item_to_selected_masses(self,item,button,parent):
        if button == 1:#left click
            row = int(parent.masslist_frame.masslist_widget.row(item))
            print(f"index {row}")
            massclickedon = parent.masslist_frame.masslist_widget.masses[row]
            compositionclickedon = parent.masslist_frame.masslist_widget.compositions[row, :]
            self.add_one_mass(massclickedon,compositionclickedon,parent)
    def add_one_mass(self,mass,composition,parent):
        '''

        Parameters
        ----------
        mass: float
        composition: np.array()
        parent

        Returns
        -------

        '''
        default_widow = 0.05

        print(f"new mass {mass}, {composition}")
        if mass not in self.selectedmasses:
            self.selectedmasses = np.append(self.selectedmasses, mass)
            self.selectedcompositions = np.append(self.selectedcompositions, [composition], axis=0)
            parent.tr.update_Traces(self.selectedmasses)
            self.redo_qlist()
            parent.update_plots()

        # update the current peak
        parent.plot_peak_frame.graph_peak_Widget.removeItem(self.highlight_this_mass_vline)
        self.highlight_this_mass_vline = []
        print(f"Right click update peak plot for mass {mass}")
        color_this_mass = self.defaultcolorcycle[np.where(self.selectedmasses == mass)[0][0]]
        print(color_this_mass)
        parent.plot_peak_frame.peakmasscolor.set_color(color_this_mass)
        parent.plot_peak_frame.peakmasslabel.setText(str(round(mass,6)))
        xlims = (mass-default_widow,mass+default_widow)
        # pyqto.replot_spectra(parent,parent.graph_peak_Widget,parent.plot_settings["show_plots"],alterable_plot=False)
        parent.vb_peak.setXRange(*xlims)
        pyqto.redraw_vlines(parent,parent.plot_peak_frame.graph_peak_Widget,xlims,not_changeable=True)
        if composition.sum() > 0:
            # if we have any entries in the composition
            vertlinecol = parent.plot_settings["vert_lines_color_masslist"]
        else:
            vertlinecol = parent.plot_settings["vert_lines_color_masslist_without_composition"]
        self.highlight_this_mass_vline = pyqtgraph.InfiniteLine(pos=mass, pen = {"color": vertlinecol, "width": 4},angle = 90)
        self.highlight_this_mass_vline.setZValue(2000)
        parent.plot_peak_frame.graph_peak_Widget.addItem(self.highlight_this_mass_vline)
        pyqto.redraw_localfit(parent,parent.plot_peak_frame.graph_peak_Widget,xlims)


    def add_index_to_selected_masses(self,lower_index,parent,upper_index = 0):
        # print(f"--------------{lower_index},{upper_index}")
        if upper_index == 0:
            for_addition = parent.masslist_frame.masslist_widget.masses[lower_index]
            mask_duplicates = np.isin(for_addition, self.selectedmasses, invert=False)

            self.selectedmasses = np.append(self.selectedmasses, for_addition[~mask_duplicates])
            self.selectedcompositions = np.append(self.selectedcompositions, parent.masslist_frame.masslist_widget.compositions[lower_index,:][~mask_duplicates,:], axis=0)
        else:
            for_addition = parent.masslist_frame.masslist_widget.masses[lower_index:upper_index]
            mask_duplicates =np.isin(for_addition, self.selectedmasses, invert=False)
            self.selectedmasses = np.append(self.selectedmasses, for_addition[~mask_duplicates])
            self.selectedcompositions = np.append(self.selectedcompositions, parent.masslist_frame.masslist_widget.compositions[lower_index:upper_index,:][~mask_duplicates,:], axis=0)

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
            item = QListWidgetItem(f"{str(index)}\t{str(round(mass,6))} {mo.get_names_out_of_element_numbers(element_numbers)}")
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






# tr = Traces(r"D:\Uniarbeit 23_11_09\CERN\CLOUD16\arctic_runs\2023-11-09to2023-11-12\results\_result_avg.hdf5")
# traces = tr.load_Traces("all")

def robust_scale(data):
    # Calculate the median and interquartile range (IQR) for each signal
    median_vals = np.median(data, axis=1, keepdims=True)
    q1 = np.percentile(data, 25, axis=1, keepdims=True)
    q3 = np.percentile(data, 75, axis=1, keepdims=True)
    iqr = q3 - q1

    # Robust scaling
    scaled_data = (data - median_vals) / iqr

    return scaled_data[0,:,:]


def highest_change_signal(data):
    # Scale the data using robust scaling
    scaled_data = robust_scale(data)

    # Compute the sum of absolute differences for each signal
    sum_abs_diff = np.sum(np.abs(np.diff(scaled_data, axis=1)), axis=1)


    return sum_abs_diff

