import pyqtgraph as pg
from pyqtgraph import functions as fn
from pyqtgraph.graphicsItems.TextItem import TextItem
from pyqtgraph.Qt import QtCore
import workflows.masslist_objects as mf
import PyQt5.QtGui as QtGui
import numpy as np

def _redraw_vline(parent, xlims, massisosugg, color, width, type = "mass", hover = True, movable = False, deletable = False):
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
            compound_name = mf.get_names_out_of_element_numbers(element_numbers[0])
            #print in layer suggstions<isotopes<masslist
            if mass in parent.ml.suggestions.masses:
                z = 0
            elif mass in parent.ml.isotopes.masses:
                z = 500
            else: z = 1000
            if np.any(element_numbers):
                sugisomass_line = InfiniteLine_Mass(parent, pos=mass, pen=pg.mkPen(color, width=width), Type = type, hover = hover, movable= movable,
                                                angle=90, hoverPen={"color": (0,0,0),"width": 2}, label= compound_name,
                                                labelOpts={"position": 0,#0.8 - len(compound_name)* 0.01,
                                                           "rotateAxis":(1, 0),
                                                           "anchors": [(0, 0), (0, 0)]},deletable=deletable)
            else:
                sugisomass_line = InfiniteLine_Mass(parent, pos=mass, Type = "mass_without_comp", pen=pg.mkPen(parent.plot_settings["vert_lines_color_masslist_without_composition"], width=width), hover = hover, movable= movable,
                                                angle=90, hoverPen={"color": (0,0,0),"width": 2}, label= compound_name,
                                                labelOpts={"position": 0,#0.8 - len(compound_name)* 0.01,
                                                           "rotateAxis":(1, 0),
                                                           "anchors": [(0, 0), (0, 0)]},deletable=deletable)
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
        _redraw_vline(parent, xlims, parent.ml.suggestions, type = "sugg",
                                        color=parent.plot_settings["vert_lines_color_suggestions"], width=parent.plot_settings["vert_lines_width_suggestions"])
        _redraw_vline(parent, xlims, parent.ml.masslist, type = "mass",
                                        color=parent.plot_settings["vert_lines_color_masslist"], width=parent.plot_settings["vert_lines_width_masslist"], movable=True, deletable = True)
        _redraw_vline(parent, xlims, parent.ml.isotopes, type = "iso",
                                    color=parent.plot_settings["vert_lines_color_isotopes"], width=parent.plot_settings["vert_lines_width_isotopes"], hover=False)


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
                                                       pen={'color': parent.plot_settings["max_spectrum_color"], 'width': parent.plot_settings["spectra_width"]}, name="max spectrum")
        parent.spectrum_max_plot.setLogMode(None, True)
    if parent.spectrum_min_plot:
        parent.graphWidget.removeItem(parent.spectrum_min_plot)
    if plotsetting_show[2]:
        parent.spectrum_min_plot = parent.graphWidget.plot(parent.sp.massaxis, parent.sp.spectrum_min,
                                                       pen={'color': parent.plot_settings["min_spectrum_color"], 'width': parent.plot_settings["spectra_width"]}, name="min spectrum")
        parent.spectrum_min_plot.setLogMode(None, True)
    if parent.subspec_plot:
        parent.graphWidget.removeItem(parent.subspec_plot)
    if plotsetting_show[3]:
        parent.subspec_plot = parent.graphWidget.plot(parent.sp.massaxis, parent.sp.sum_specs[0, :],
                                                  pen={'color': parent.plot_settings["sub_spectrum_color"], 'width': parent.plot_settings["spectra_width"]}, name="subspectrum")
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
    numbersubspec = int(parent.slider.value())
    if parent.plot_settings["show_plots"][3]:
        parent.graphWidget.removeItem(parent.subspec_plot )
        parent.subspec_plot = parent.graphWidget.plot(parent.sp.massaxis, parent.sp.sum_specs[numbersubspec, :],
                                                  pen=parent.plot_settings["sub_spectrum_color"], name="subspectrum")
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
    def __init__(self,Parent,hover=True, deletable = False, Type = "mass" ,*args,**kwargs):
        """

        """
        self.parent = Parent
        super().__init__(*args,**kwargs)
        self.hover = hover
        self.delatable = deletable
        self.vb = self.parent.spectrumplot.getViewBox()
        self.xlims, self.ylims = self.vb.viewRange()
        self.type = Type
        font = self.parent.plot_settings["font"]
        font.setPointSize(12)
        self.label.textItem.setFont(font)
        self.label.setColor([0,0,0])


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
        print(ev)
        self.sigClicked.emit(self, ev)
        if ev.button() == QtCore.Qt.MouseButton.LeftButton and self.hover:
            print("try to add mass", self.value())
            if self.value() not in self.parent.ml.masslist.masses:
                self.parent.ml.add_mass_to_masslist(self.parent, self.value())
                self.penmasslist = fn.mkPen(self.parent.plot_settings["vert_lines_color_masslist"])
                self.pen = self.penmasslist
                redraw_localfit(self.parent,self.xlims)
                self.update()
            else:
                print("is already in ml")

        if ev.button() == QtCore.Qt.MouseButton.RightButton and self.hover:
            print("try to delete mass", self.value())
            if self.value() in self.parent.ml.masslist.masses :
                self.parent.ml.delete_mass_from_masslist(self.parent, self.value())
                # self.penmasslist = fn.mkPen(self.parent.plot_settings["vert_lines_color_default"])
                self.pen = fn.mkPen(0.5)
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
                self.moving = False
                self.sigPositionChangeFinished.emit(self)
                # if the line was already in masslist delet it
                if self.startPosX in self.parent.ml.masslist.masses:
                    self.parent.ml.delete_mass_from_masslist(self.parent, self.startPosX)
                #if the new position is close to a suggestion -> add the suggestion to the masslist, otherwise only take the mass (no isotopes posiible)
                close_to_suggestion = self.parent.ml.suggestions.masses[np.isclose(self.value(),self.parent.ml.suggestions.masses, atol = np.diff(self.xlims)*0.0001)]
                if close_to_suggestion.shape[0] > 0:
                    self.parent.ml.add_mass_to_masslist(self.parent, close_to_suggestion)
                else:
                    self.parent.ml.add_mass_to_masslist(self.parent, self.value())
                redraw_localfit(self.parent, self.xlims)
