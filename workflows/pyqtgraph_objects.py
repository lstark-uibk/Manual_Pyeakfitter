import pyqtgraph as pg
from pyqtgraph import functions as fn
from pyqtgraph.graphicsItems.TextItem import TextItem
from pyqtgraph.Qt import QtCore
import workflows.masslist_objects as mf
import PyQt5.QtGui as QtGui
import numpy as np
import datetime as dt


def _redraw_vline(parent, xlims, type = "mass"):
    if type == "mass":
        massisosugg = parent.ml.masslist
        z = 1000
    if type == "sugg":
        massisosugg = parent.ml.suggestions
        z = 0
    if type == "iso":
        massisosugg = parent.ml.isotopes
        z = 500
    new_xlim_current_masses = massisosugg.masses[
        (massisosugg.masses > xlims[0]) & (massisosugg.masses < xlims[1])]
    # first remove lines which are not in the view field anymore
    if massisosugg.current_lines:
        for item in massisosugg.current_lines:
            if item.value() not in new_xlim_current_masses:
                parent.graphWidget.removeItem(item)
                massisosugg.current_lines.remove(item)

    # then add masses if they are not already in the view field
    for mass in new_xlim_current_masses:
        if mass not in [item.value() for item in massisosugg.current_lines]:
            element_numbers = massisosugg.element_numbers[np.where(massisosugg.masses == mass)]
            compound_name = massisosugg.compound_names[massisosugg.masses == mass]
            label = compound_name[0]
            print(mass, element_numbers, compound_name)
            #print in layer suggstions<isotopes<masslist
            if np.any(element_numbers):
                sugisomass_line = InfiniteLine_Mass(parent, Pos=mass, Type= type, Label= label)
            else:
                sugisomass_line = InfiniteLine_Mass(parent, Pos=mass, Type = "mass_without_comp", Label= "")
            sugisomass_line.setZValue(z)
            parent.graphWidget.addItem(sugisomass_line)
            massisosugg.current_lines.append(sugisomass_line)

def redraw_vlines(parent, xlims):
    """replot all vertical lines between given xlimson Mainwindow.graphWidget
     Suggestions, Isotopes and Masslist masses given in Mainwindow.ml

    Parameters:
    -----------
    parent: object
        Mainwindow object where the Line are stored
    xlims: tuple
        Current x-limits of view

    Returns
    -------
    []
    """

    if np.diff(xlims) < 0.7:
        _redraw_vline(parent, xlims, type = "sugg")
        _redraw_vline(parent, xlims, type = "mass")
        _redraw_vline(parent, xlims, type = "iso",
)


def redraw_localfit(parent,xlims):
    """calculate a new local fit with given x-limits and current isotopes and masslists and replot it on  Mainwindow.graphWidget

    Parameters:
    -----------
    parent: object
        Mainwindow object where the Line are stored
    xlims: tuple
        Current x-limits of view to calculate the influence of masses and isotopes on local fit

    Returns
    -------
    []
    """

    middle = (xlims[0]+xlims[1])/2
    influence_limits = [round(middle) - 0.5, round(middle) + 0.5] # alway include the .5 up and down the full number
    masses_influencing_localfit = parent.ml.masslist.masses[(parent.ml.masslist.masses > influence_limits[0] ) & (parent.ml.masslist.masses < influence_limits[1])]

    if not np.array_equal(masses_influencing_localfit,parent.sp.current_local_fit_masses):
        print("because there is a new mass make new local fit")

        fitmassaxis, fitspectrum, coefficients, A = parent.sp.get_mass_coefficients(xlims,parent.ml)
        if not parent.sp.current_local_fit_init:
            print("Make a new local fit")
            localfit = parent.graphWidget.plot(fitmassaxis, fitspectrum, pen=parent.plot_settings["local_fit"], name="Local Fit")
            localfit.setLogMode(None, True)
            parent.sp.current_local_fit_masses = masses_influencing_localfit
            parent.sp.current_local_fit = localfit
            parent.sp.current_local_fit_init = True
        else:
            print("Redo local fit data")
            parent.sp.current_local_fit.setData(fitmassaxis, fitspectrum)
            parent.sp.current_local_fit_masses = masses_influencing_localfit
        # localfit.setLogMode(None, True)
        # # for i in range(coefficients.shape[0]):
        # #     subfit = parent.graphWidget.plot(fitmassaxis, A[:,i]*coefficients[i], pen="k")
        # #     subfit.setLogMode(None, True)
        # #     parent.sp.current_local_fit.append(subfit)


def replot_spectra(parent, plotsetting_show):
    """replot all spectrum lines with the setting given in Mainwindow.plotsettings

    Parameters:
    -----------
    parent: object
        Mainwindow object where the Line are stored
    plotsetting_show: list
        List of True/False which plots to show (defined in Mainwindow.plotsettings)

    Returns
    -------
    []
    """
    if parent.spectrumplot:
        parent.graphWidget.removeItem(parent.spectrumplot)
    if plotsetting_show[0]:
        pen = {'color': 'red', 'width': 2}
        parent.spectrumplot = parent.graphWidget.plot(parent.sp.massaxis, parent.sp.spectrum,
                                                  pen={'color': parent.plot_settings["average_spectrum_color"], 'width': parent.plot_settings["spectra_width"]}, name="average spectrum")
        parent.spectrumplot.setLogMode(None, True)
        # make this when doubleclicking
        # is shifted
        parent.spectrumplot.scene().sigMouseClicked.connect(parent.mouse_double_click_on_empty)

    if parent.spectrum_max_plot:
        parent.graphWidget.removeItem(parent.spectrum_max_plot)
    if plotsetting_show[1]:
        parent.spectrum_max_plot = parent.graphWidget.plot(parent.sp.massaxis, parent.sp.spectrum_max,
                                                       pen={'color': parent.plot_settings["max_spectrum_color"], 'width': 1}, name="max spectrum")
        parent.spectrum_max_plot.setLogMode(None, True)
    if parent.spectrum_min_plot:
        parent.graphWidget.removeItem(parent.spectrum_min_plot)
    if plotsetting_show[2]:
        parent.spectrum_min_plot = parent.graphWidget.plot(parent.sp.massaxis, parent.sp.spectrum_min,
                                                       pen={'color': parent.plot_settings["min_spectrum_color"], 'width': 1}, name="min spectrum")
        parent.spectrum_min_plot.setLogMode(None, True)
    if parent.subspec_plot:
        parent.graphWidget.removeItem(parent.subspec_plot)
    if plotsetting_show[3]:
        current_subspectrum_time_str = parent.sp.current_subspectrum_time.astype(dt.datetime).strftime("%Y-%m-%d %H:%M")
        parent.subspec_plot = parent.graphWidget.plot(parent.sp.massaxis, parent.sp.sum_specs[0, :],
                                                  pen={'color': parent.plot_settings["sub_spectrum_color"], 'width': parent.plot_settings["spectra_width"]}, name=f"subspectrum at {current_subspectrum_time_str}")
        parent.subspec_plot.setLogMode(None, True)

def _remove_plot_items(parent,item_list):
    if item_list:
        for item in item_list:
            parent.graphWidget.removeItem(item)
    return []

def remove_all_vlines(parent):
    """remove all v_lines in the basket objects and in the graphWidget

    Parameters
    ----------
    parent: object
        Mainwindow object where the Line are stored

    Returns
    -------
    None
    """
    parent.ml.suggestions.current_lines = _remove_plot_items(parent, parent.ml.suggestions.current_lines)
    parent.ml.masslist.current_lines = _remove_plot_items(parent, parent.ml.masslist.current_lines)
    parent.ml.isotopes.current_lines = _remove_plot_items(parent, parent.ml.isotopes.current_lines)

def remove_all_plot_items(parent):
    """remove all plot_items in the graphWidget

    Parameters
    ----------
    parent: object
        Mainwindow object where the Line are stored

    Returns
    -------
    None
    """
    # used: https://www.geeksforgeeks.org/pyqtgraph-getting-all-child-items-of-graph-item/
    for item in parent.graphWidget.allChildItems():
        parent.graphWidget.removeItem(item)
def redraw_subspec(parent):
    """redraw the subspectrum line with a new slider value

    Parameters
    ----------
    parent: object
        Mainwindow object where the Line are stored

    Returns
    -------
    None
    """
    numbersubspec = int(parent.slider.sl.value())
    parent.sp.current_subspectrum_time = parent.sp.specs_times[numbersubspec]
    if parent.plot_settings["show_plots"][3]:
        parent.graphWidget.removeItem(parent.subspec_plot )
        current_subspectrum_time_str = parent.sp.current_subspectrum_time.astype(dt.datetime).strftime("%Y-%m-%d %H:%M")
        parent.subspec_plot = parent.graphWidget.plot(parent.sp.massaxis, parent.sp.sum_specs[numbersubspec, :],
                                                  pen=parent.plot_settings["sub_spectrum_color"], name=f"subspectrum at {current_subspectrum_time_str}")
        parent.subspec_plot.setLogMode(None, True)



class InfiniteLine_Mass(pg.InfiniteLine):
    """
    A class inheriting the Attributes from pyqtgraph.InfiniteLine and adding the necessary abilities for a Masslist vline

    Parameters
    ----------
    Parent : object
        Mainwindow object where the Line will be drawn
    hover : True/False
    deletable : True/False
    *args,**kwargs: arguments for pyqtgraph.InfiniteLin
    """
    def __init__(self,Parent, Pos=0, Type = "none", Label="",**kwargs):
        """

        """
        self.parent = Parent
        self.type = Type
        self.position = Pos
        angle = 90
        hoverPen = {"color": (0, 0, 0), "width": 2}
        label = Label
        labelOpts = {"position": 0,  # 0.8 - len(compound_name)* 0.01,
                     "rotateAxis": (1, 0),
                     "anchors": [(0, 0), (0, 0)]}
        self.hover = False
        self.delatable = False
        self.movable = False
        color = (0,0,0)
        width = 1
        if self.type == "sugg":
            color = self.parent.plot_settings["vert_lines_color_suggestions"]
            width = self.parent.plot_settings["vert_lines_width_suggestions"]
            self.hover = True
        if self.type == "mass":
            color = self.parent.plot_settings["vert_lines_color_masslist"]
            width = self.parent.plot_settings["vert_lines_width_masslist"]
            self.hover = True
            self.delatable = True
            self.movable = True
        if self.type == "iso":
            color = self.parent.plot_settings["vert_lines_color_isotopes"]
            width = self.parent.plot_settings["vert_lines_width_isotopes"]
        if self.type == "highlight":
            color = (0,0,0)
            width = 2
        if self.type == "mass_without_comp":
            color = self.parent.plot_settings["vert_lines_color_masslist_without_composition"]
            width = self.parent.plot_settings["vert_lines_width_masslist"]
            self.hover = True
            self.delatable = True
            self.movable = True

        pen = pg.mkPen(color, width=width)


        if self.type == "none":
            super().__init__(pos=self.position,label= label,labelOpts= labelOpts **kwargs)
        else:
            super().__init__(pos = self.position, angle = angle, pen = pen, movable = self.movable, hoverPen= hoverPen, label= label, labelOpts= labelOpts)

        self.vb = self.parent.spectrumplot.getViewBox()
        self.xlims, self.ylims = self.vb.viewRange()
        self.type = Type
        font = self.parent.plot_settings["font"]
        font.setPointSize(12)
        self.label.textItem.setFont(font)
        self.label.setColor([0,0,0])
        print(f"Make {self.type} line at {self.position} with label {self.label.format}")


    def hoverEvent(self, ev):
        if (not ev.isExit()) and ev.acceptDrags(QtCore.Qt.MouseButton.LeftButton) and self.hover:
            self.setMouseHover(True)
            if self.delatable:
                self.parent.ml.currently_hovered = self
            if self.value() in self.parent.ml.masslist.masses:
                #jumpt to the hoovered mass in qlist
                # if the current Item in qlist is not the hoovered mass, change it
                # if self.parent.masslist_widget.currentItem().text().split()[0] != str(round(self.value(),6)):
                for index in range(self.parent.masslist_widget.count()):
                    item = self.parent.masslist_widget.item(index)
                    if item.text().split()[0] == str(round(self.value(),6)):
                        # Set the current item and scroll to it
                        self.parent.masslist_widget.setCurrentItem(item)
                        break  # Exit the loop if found

        else:
            self.setMouseHover(False)
            if self.delatable:
                self.parent.ml.currently_hovered = []


    def mouseClickEvent(self, ev):
        self.sigClicked.emit(self, ev)
        if ev.button() == QtCore.Qt.MouseButton.LeftButton and self.hover:
            print("try to add mass", self.value())
            if self.value() not in self.parent.ml.masslist.masses:
                # look whether there are suggestions nearby
                threshold_closeness = np.diff(self.xlims) * 0.01  # should be 0.01 percent of the current view near
                nearest_mass_or_suggestion = self.parent.ml.check_whether_suggmass_nearby(self.value(), self.parent.ml.suggestions, threshold_closeness)
                self.parent.ml.add_mass_to_masslist(self.parent, nearest_mass_or_suggestion)
                redraw_localfit(self.parent,self.xlims)
            else:
                print("is already in ml")

        if ev.button() == QtCore.Qt.MouseButton.RightButton and self.hover:
            print("try to delete mass", self.value())
            if self.value() in self.parent.ml.masslist.masses :
                self.parent.ml.delete_mass_from_masslist(self.parent, self.value())
                redraw_localfit(self.parent,self.xlims)
            else:
                print("This mass is not already in Masslist to delete")
                # self.update()



    def mouseDragEvent(self, ev):
        if self.movable and ev.button() == QtCore.Qt.MouseButton.LeftButton:
            if ev.isStart():
                self.moving = True
                self.cursorOffset = self.pos() - self.mapToParent(ev.buttonDownPos())
                self.startPosition = self.pos()
                self.startPosX = self.value()
            ev.accept()

            if not self.moving:
                return

            self.setPos(self.cursorOffset + self.mapToParent(ev.pos()))
            self.sigDragged.emit(self)
            if ev.isFinish(): # do this when we finished the dragging
                print(f"Mouse dragged to {self.value()}")

                self.moving = False
                self.sigPositionChangeFinished.emit(self)
                # if the line was already in masslist delet it
                if self.startPosX in self.parent.ml.masslist.masses:
                    self.parent.ml.delete_mass_from_masslist(self.parent, self.startPosX)
                # look whether there are suggestions nearby
                threshold_closeness = np.diff(self.xlims) * 0.01  # should be 0.01 percent of the current view near
                nearest_mass_or_suggestion = self.parent.ml.check_whether_suggmass_nearby(self.value(), self.parent.ml.suggestions, threshold_closeness)
                self.parent.ml.add_mass_to_masslist(self.parent, nearest_mass_or_suggestion)
                redraw_localfit(self.parent, self.xlims)
