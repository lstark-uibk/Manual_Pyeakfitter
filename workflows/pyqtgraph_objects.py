import pyqtgraph as pg
from pyqtgraph import functions as fn
from pyqtgraph.Qt import QtCore
import workflows.masslist_objects as mf
import numpy as np

def redraw_vline(parent, xlims, massisosugg, color, width, hover = True, movable = False, deletable = False):
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
            if np.any(element_numbers):
                sugisomass_line = InfiniteLine_Mass(parent, pos=mass, pen=pg.mkPen(color, width=width), hover = hover, movable= movable,
                                                angle=90, hoverPen={"color": (100,0,0),"width": 2}, label= compound_name,
                                                labelOpts={"position": 0,#0.8 - len(compound_name)* 0.01,
                                                           "rotateAxis":(1, 0),
                                                           "anchors": [(0, 0), (0, 0)]},deletable=deletable)
            else:
                sugisomass_line = InfiniteLine_Mass(parent, pos=mass, pen=pg.mkPen(parent.plot_settings["vert_lines_color_masslist_without_composition"], width=width), hover = hover, movable= movable,
                                                angle=90, hoverPen={"color": (100,0,0),"width": 2}, label= compound_name,
                                                labelOpts={"position": 0,#0.8 - len(compound_name)* 0.01,
                                                           "rotateAxis":(1, 0),
                                                           "anchors": [(0, 0), (0, 0)]},deletable=deletable)
            parent.graphWidget.addItem(sugisomass_line)
            massisosugg.current_lines.append(sugisomass_line)

def redraw_vlines(parent):
    xlims,ylims = parent.vb.viewRange()
    if np.diff(xlims) < 0.7:
        redraw_vline(parent, xlims, parent.ml.suggestions,
                                        color=parent.plot_settings["vert_lines_color_suggestions"], width=parent.plot_settings["vert_lines_width_suggestions"])
        redraw_vline(parent, xlims, parent.ml.masslist,
                                        color=parent.plot_settings["vert_lines_color_masslist"], width=parent.plot_settings["vert_lines_width_masslist"], movable=True, deletable = True)
        redraw_vline(parent, xlims, parent.ml.isotopes,
                                    color=parent.plot_settings["vert_lines_color_isotopes"], width=parent.plot_settings["vert_lines_width_isotopes"], hover=False)


def redraw_localfit(parent,xlims):
    middle = (xlims[0]+xlims[1])/2
    influence_limits = [round(middle) - 0.5, round(middle) + 0.5] # alway include the .5 up and down the full number
    masses_influencing_localfit = parent.ml.masslist.masses[(parent.ml.masslist.masses > influence_limits[0] ) & (parent.ml.masslist.masses < influence_limits[1])]

    if not np.array_equal(masses_influencing_localfit,parent.sp.current_local_fit_masses):
        print("because there is a new mass make new local fit")
        for item in parent.sp.current_local_fit:
            parent.graphWidget.removeItem(item)
            parent.sp.current_local_fit = []
            parent.sp.current_local_fit_masses = []

        fitmassaxis, fitspectrum, coefficients, A = parent.sp.get_mass_coefficients(xlims,parent.ml)
        localfit = parent.graphWidget.plot(fitmassaxis, fitspectrum,pen= parent.plot_settings["local_fit"], name = "Local Fit")
        localfit.setLogMode(None, True)
        # for i in range(coefficients.shape[0]):
        #     subfit = parent.graphWidget.plot(fitmassaxis, A[:,i]*coefficients[i], pen="k")
        #     subfit.setLogMode(None, True)
        #     parent.sp.current_local_fit.append(subfit)
        parent.sp.current_local_fit_masses = masses_influencing_localfit
        parent.sp.current_local_fit = [localfit]

def replot_spectra(parent, plotsetting):
    if parent.spectrumplot:
        parent.graphWidget.removeItem(parent.spectrumplot)
    if plotsetting[0]:

        parent.spectrumplot = parent.graphWidget.plot(parent.sp.massaxis, parent.sp.spectrum,
                                                  pen=parent.plot_settings["average_spectrum_color"], name="average spectrum")
        parent.spectrumplot.setLogMode(None, True)
        # make this when doubleclicking
        # is shifted
        parent.spectrumplot.scene().sigMouseClicked.connect(parent.mouse_double_click_on_empty)

    if parent.spectrum_max_plot:
        parent.graphWidget.removeItem(parent.spectrum_max_plot)
    if plotsetting[1]:
        parent.spectrum_max_plot = parent.graphWidget.plot(parent.sp.massaxis, parent.sp.spectrum_max,
                                                       pen=parent.plot_settings["max_spectrum_color"], name="max spectrum")
        parent.spectrum_max_plot.setLogMode(None, True)
    if parent.spectrum_min_plot:
        parent.graphWidget.removeItem(parent.spectrum_min_plot)
    if plotsetting[2]:
        parent.spectrum_min_plot = parent.graphWidget.plot(parent.sp.massaxis, parent.sp.spectrum_min,
                                                       pen=parent.plot_settings["min_spectrum_color"], name="min spectrum")
        parent.spectrum_min_plot.setLogMode(None, True)
    if parent.subspec_plot:
        parent.graphWidget.removeItem(parent.subspec_plot)
    if plotsetting[3]:
        parent.subspec_plot = parent.graphWidget.plot(parent.sp.massaxis, parent.sp.sum_specs[0, :],
                                                  pen=parent.plot_settings["sub_spectrum_color"], name="subspectrum")
        parent.subspec_plot.setLogMode(None, True)

def remove_plot_items(parent,item_list):
    if item_list:
        for item in item_list:
            parent.graphWidget.removeItem(item)
    return []

def remove_all_vlines(parent):
    parent.ml.suggestions.current_lines = remove_plot_items(parent, parent.ml.suggestions.current_lines)
    parent.ml.masslist.current_lines = remove_plot_items(parent, parent.ml.masslist.current_lines)
    parent.ml.isotopes.current_lines = remove_plot_items(parent, parent.ml.isotopes.current_lines)
    parent.sp.current_local_fit_masses = remove_plot_items(parent, parent.sp.current_local_fit)

def remove_all_plot_items(parent):
    # used: https://www.geeksforgeeks.org/pyqtgraph-getting-all-child-items-of-graph-item/
    for item in parent.graphWidget.allChildItems():
        parent.graphWidget.removeItem(item)
def redraw_subspec(parent):
    numbersubspec = int(parent.slider.value())
    if parent.plot_settings["show_plots"][3]:
        parent.graphWidget.removeItem(parent.subspec_plot )
        parent.subspec_plot = parent.graphWidget.plot(parent.sp.massaxis, parent.sp.sum_specs[numbersubspec, :],
                                                  pen=parent.plot_settings["sub_spectrum_color"], name="subspectrum")
        parent.subspec_plot.setLogMode(None, True)


class InfiniteLine_Mass(pg.InfiniteLine):
    """
    A class inheriting the Attributes from pyqtgraph.InfiniteLine and adding the
    ...

    Attributes
    ----------
    says_str : str
        a formatted string to print out what the animal says
    name : str
        the name of the animal
    sound : str
        the sound that the animal makes
    num_legs : int
        the number of legs the animal has (default 4)

    Methods
    -------
    says(sound=None)
        Prints the animals name and what sound it makes
    """
    def __init__(self,Parent,hover=True, deletable = False ,*args,**kwargs):
        """
        Parameters
        ----------
        Parent : object
            Mainwindow object where the Line will be drawn
        hover : True/False
        deletable : True/False
        *args,**kwargs: arguments for pyqtgraph.InfiniteLin
        """
        self.parent = Parent
        super().__init__(*args,**kwargs)
        self.hover = hover
        self.delatable = deletable
        self.vb = self.parent.spectrumplot.getViewBox()
        self.xlims, self.ylims = self.vb.viewRange()


    def hoverEvent(self, ev):
        if (not ev.isExit()) and ev.acceptDrags(QtCore.Qt.MouseButton.LeftButton) and self.hover:
            self.setMouseHover(True)
            if self.delatable:
                self.parent.ml.currently_hovered = self
        else:
            self.setMouseHover(False)
            if self.delatable:
                self.parent.ml.currently_hovered = []

    def mouseClickEvent(self, ev):
        self.sigClicked.emit(self, ev)
        #mod
        if ev.button() == QtCore.Qt.MouseButton.LeftButton and self.hover:
            print("try to add mass", self.value())
            if self.value() not in self.parent.ml.masslist.masses:
                self.parent.ml.add_mass_to_masslist(self.value(), self.parent)
                self.penmasslist = fn.mkPen(self.parent.plot_settings["vert_lines_color_masslist"])
                self.pen = self.penmasslist
                redraw_localfit(self.parent,self.xlims)
                self.update()
            else:
                print("is already in ml")

        if ev.button() == QtCore.Qt.MouseButton.RightButton and self.hover:
            print("try to delete mass", self.value())
            if self.value() in self.parent.ml.masslist.masses :
                self.parent.ml.delete_mass_from_masslist(self.value(),self.parent)
                # self.penmasslist = fn.mkPen(self.parent.plot_settings["vert_lines_color_default"])
                self.pen = fn.mkPen(0.5)
                redraw_localfit(self.parent,self.xlims)
                self.update()
        if ev.button() == QtCore.Qt.MouseButton.RightButton:
            pass


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
                    self.parent.ml.delete_mass_from_masslist(self.startPosX, self.parent)
                #if the new position is close to a suggestion -> add the suggestion to the masslist, otherwise only take the mass (no isotopes posiible)
                close_to_suggestion = self.parent.ml.suggestions.masses[np.isclose(self.value(),self.parent.ml.suggestions.masses, atol = np.diff(self.xlims)*0.0001)]
                if close_to_suggestion.shape[0] > 0:
                    self.parent.ml.add_mass_to_masslist(close_to_suggestion, self.parent)
                else:
                    self.parent.ml.add_mass_to_masslist(self.value(), self.parent)
                redraw_localfit(self.parent, self.xlims)
