import numpy as np
import pandas as pd
import pyqtgraph as pg
import os
from PyQt5.QtCore import *
from PyQt5 import QtWidgets, QtGui, QtCore
import sys
import workflows_ptg.trace_objects as to
import workflows_ptg.pyqt_objects_ptg as po
import workflows_pyeakfitter.masslist_objects as mo
import workflows_pyeakfitter.pyqtgraph_objects as pyqto
from PyQt5.QtGui import QRegExpValidator



class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        self.fn(*self.args, **self.kwargs)



class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        print("Initializing Window")
        self.setWindowTitle("PlottingTracesGui")
        self.setGeometry(300, 100, 1500, 800)
        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(1)
        self.filename = None
        self.savefilename = None
        self.file_loaded = False
        self.init_Ui_file_not_loaded()

        # to not load file everytime uncomment here
        # self.filename = r"D:\Uniarbeit 23_11_09\CERN\CLOUD16\arctic_runs\2023-11-09to2023-11-12\results\_result_avg.hdf5"
        # self.init_basket_objects()
        # self.init_UI_file_loaded()
        # self.init_plots()
        # self.file_loaded = True



    def init_Ui_file_not_loaded(self):
        self.centralwidget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.centralwidget)
        # main layout setup
        self.overallverticallayout = QtWidgets.QVBoxLayout(self.centralwidget) # all with menubar and interaction layout

        #menubar
        menubar = QtWidgets.QMenuBar()
        self.actionFile = menubar.addMenu("File")
        # the po.openfile triggers init_UI_file_loaded() and init_plots()
        openfile = QtWidgets.QAction("Open", self)
        openfile.setShortcut("Ctrl+O")
        openfile.triggered.connect(self.open_file)
        self.actionFile.addAction(openfile)


        self.actionFile.addSeparator()
        quit = QtWidgets.QAction("Quit", self)
        quit.setShortcut("Alt+F4")
        quit.triggered.connect(lambda: sys.exit(0))
        self.actionFile.addAction(quit)

        self.settingsMenubar = menubar.addMenu("Settings")
        self.plotsettings_button = QtWidgets.QAction("Plot Settings", self)
        self.settingsMenubar.addAction(self.plotsettings_button)

        self.overallverticallayout.addWidget(menubar,stretch = 1)
        self.horizontal_splitter = QtWidgets.QSplitter(Qt.Horizontal) # first horizontal splitter with masslist on left and traces on right
        self.overallverticallayout.addWidget(self.horizontal_splitter,stretch = 40)

        self.left_splitter_masslist_info = QtWidgets.QSplitter(Qt.Vertical) # vertical splitter with masslist on top and selected masses at bottom
        self.masslist_frame = po.Masslist_Frame()
        self.left_splitter_masslist_info.addWidget(self.masslist_frame)
        self.horizontal_splitter.addWidget(self.left_splitter_masslist_info)

        # plot widget for the plot_layout
        self.graphWidget = pg.PlotWidget()
        axis = pg.DateAxisItem()
        self.graphWidget.setAxisItems({'bottom': axis})
        self.horizontal_splitter.addWidget(self.graphWidget)

        self.splitter_selected_peak = QtWidgets.QSplitter(Qt.Horizontal) # horizontal splitter with selected masses left and peak on right
        self.masses_selected_frame = po.SelectedMassesFrame()
        self.splitter_selected_peak.addWidget(self.masses_selected_frame)
        self.plot_peak_frame = po.Peak_Frame()
        self.splitter_selected_peak.addWidget(self.plot_peak_frame)
        self.left_splitter_masslist_info.addWidget(self.splitter_selected_peak)


        self.horizontal_splitter.setSizes([500, 1000])
        self.left_splitter_masslist_info.setSizes([500, 300])
        self.splitter_selected_peak.setSizes([50, 300])


    def open_file(self):
        # show the dialog
        dialog = QtWidgets.QFileDialog()
        filepath, filter = dialog.getOpenFileName(None, "Window name", "", "HDF5_files (*.hdf5)")
        self.filename = filepath
        # if self.file_loaded:
        #     print("remove old plot stuff")
        #     pyqtgraph_objects.remove_all_plot_items(parent)
        if self.filename:
            self.init_basket_objects()
            self.init_UI_file_loaded()
            self.init_plots()
            self.file_loaded = True

    def init_basket_objects(self):
        #those are the "basket" objects, where the data is in sp = all data that has to do with the spectrum, ml = all data to the masslist

        self.plot_settings = {"vert_lines_color_suggestions": (97, 99, 102,70),
                              "vert_lines_color_masslist": (38, 135, 20),
                              "vert_lines_color_masslist_without_composition": (13, 110, 184),
                              "vert_lines_color_isotopes": (252, 3, 244, 70), # RGB tubel and last number gives the transparency (from 0 to 255)
                              "vert_lines_width_suggestions": 1,
                              "vert_lines_width_masslist": 2,
                              "vert_lines_width_isotopes": 1.5,
                              "average_spectrum_color" : (252, 49, 3),
                              "max_spectrum_color": (122, 72, 6, 80),
                              "min_spectrum_color": (11, 125, 191, 80),
                              "local_fit": (0, 0, 210),
                              "color_cycle": ['r', 'g', 'b', 'c', 'm', 'y'],
                              "current_color": 0,
                              "current_color_fixed": 0,
                              "background_color": "w",
                              "spectra_width": 1,
                              "show_plots": [True,False,False,False], #plots corresponding to [avg spectrum, min spec, max spect, subspectr]
                              "avg": False,
                              "raw": True,
                              "font": QtGui.QFont('Calibri', 11),
                              }
        self.tr = to.Traces(self.filename,useAveragesOnly=self.plot_settings["avg"], Raw=self.plot_settings["raw"])
        self.sp = mo.Spectrum(self.filename)
        self.ml = mo.read_masslist_from_hdf5_produce_iso_sugg(self.filename)
        self.tracesplot = []
        self.spectrumplot = []
        self.spectrum_max_plot = []
        self.spectrum_min_plot = []
        self.subspec_plot = []



    def init_UI_file_loaded(self):
        #add functionality to:
        #slider
        # masslist shown on left
        self.masslist_frame.masslist_widget.redo_qlist(self.tr.MasslistMasses, self.tr.MasslistCompositions)
        # self.masslist_widget.itemClicked.connect(self.jump_to_mass)
        self.masslist_frame.masslist_widget.itemClicked.connect(lambda item,button: self.masses_selected_frame.masses_selected_widget.add_item_to_selected_masses(item,button,self))
        self.masses_selected_frame.masses_selected_widget.itemClicked.connect(lambda item,button: self.masses_selected_frame.masses_selected_widget.clicked_on_item(item,button,self))
        self.masses_selected_frame.deselectall_button.clicked.connect(lambda: self.masses_selected_frame.masses_selected_widget.deselect_all(self))
        self.masses_selected_frame.export_button.clicked.connect(self.export_currently_selected_masses_to_csv)
        # self.masslist_widget.itemDoubleClicked.connect(lambda item: self.masslist_widget.handle_double_click(item, parent=self))

        #jump to mass widget
        self.masslist_frame.jump_to_mass_input.returnPressed.connect(lambda: self.masses_selected_frame.masses_selected_widget.add_mass_to_selected_masses(self.masslist_frame.jump_to_mass_input.text(),self))
        self.masslist_frame.jump_to_compound_button.pressed.connect(lambda: self.masses_selected_frame.masses_selected_widget.add_compound(self.masslist_frame.jump_to_compound_input.text(),self))
        self.masslist_frame.jump_to_compound_input.returnPressed.connect(lambda: self.masses_selected_frame.masses_selected_widget.add_compound(self.masslist_frame.jump_to_compound_input.text(),self))
        self.masslist_frame.multiple_check_OK_Button.pressed.connect(self.multiple_check_pressed)
        self.masslist_frame.multiple_check.returnPressed.connect(self.multiple_check_pressed)

        # #sorting widgets - give sorting function define sorting object,
        self.masslist_frame.sort_max.sortingbutton.pressed.connect(lambda: self.masslist_frame.sort_max.sort_qlist(self.masslist_frame.masslist_widget,self.tr.load_Traces("all")))
        self.masslist_frame.sort_rel.sortingbutton.pressed.connect(lambda : self.masslist_frame.sort_rel.sort_qlist(self.masslist_frame.masslist_widget,self.tr.load_Traces("all")))
        self.masslist_frame.sort_mass.sortingbutton.pressed.connect(lambda: self.masslist_frame.sort_mass.sort_qlist(self.masslist_frame.masslist_widget,self.tr.MasslistMasses) )
        #menubar stuff

        self.plotsettings_window = po.PlotSettingsWindow(self)
        self.plotsettings_button.triggered.connect(self.plotsettings_window.show)



    def init_plots(self):
        # first big plot
        # Enable antialiasing for prettier plots
        pg.setConfigOptions(antialias=True)
        self.graphWidget.setBackground(self.plot_settings["background_color"])
        self.graphWidget.setLabel('bottom', "Time")
        self.graphWidget.setLabel('left', "Signal [cps]")
        self.graphWidget.setLogMode(y=True)
        self.graphWidget.showGrid(y = True)
        self.graphWidget.showGrid(x = True)
        self.graphWidget.addLegend()
        # make bg plots
        # pyqtgraph_objects.replot_spectra(self,self.plot_settings["show_plots"])

        # set the restrictions on the movement
        self.vb = self.graphWidget.getViewBox()
        self.vb.autoRange()
        self.vb.setMenuEnabled(False)
        self.vb.setAspectLocked(lock=False)
        self.vb.enableAutoRange(axis='y', enable=True)
        # when xrange changed make the following
        # to signals and slots: https://www.tutorialspoint.com/pyqt/pyqt_signals_and_slots.htm#:~:text=Each%20PyQt%20widget%2C%20which%20is,%27%20to%20a%20%27slot%27.
        self.vb.sigXRangeChanged.connect(lambda: self.on_xlims_changed(self.vb))
        self.update_plots()

        self.plot_peak_frame.graph_peak_Widget.setBackground(self.plot_settings["background_color"])
        self.plot_peak_frame.graph_peak_Widget.showGrid(y = True)
        self.plot_peak_frame.graph_peak_Widget.getAxis('bottom').setPen(pg.mkPen(color='k'))
        self.plot_peak_frame.graph_peak_Widget.getAxis('left').setPen(pg.mkPen(color='k'))
        # font = self.plot_settings["font"]
        # self.graph_peak_Widget.getAxis('bottom').setStyle(tickFont=font)  # Set the font for the x-axis ticks
        # self.graph_peak_Widget.getAxis('left').setStyle(tickFont=font)  # Set the font for the x-axis ticks
        # self.graph_peak_Widget.getAxis('bottom').setPen('k')
        # self.graph_peak_Widget.getAxis('left').setPen('k')
        # self.graph_peak_Widget.getAxis('bottom').setTextPen('k')
        # self.graph_peak_Widget.getAxis('left').setTextPen('k')
        # self.graph_peak_Widget.getAxis('left').setLabel(text="Signal", units=None, unitPrefix=None, **{'color': 'k', 'font-size': '12pt'})
        # self.graph_peak_Widget.getAxis('bottom').setLabel(text="m/z [Th]", units=None, unitPrefix=None, **{'color': 'k', 'font-size': '12pt'})
        self.plot_peak_frame.graph_peak_Widget.setLogMode(y=True)
        self.plot_peak_frame.graph_peak_Widget.addLegend()

        # set the restrictions on the movement
        self.vb_peak = self.plot_peak_frame.graph_peak_Widget.getViewBox()
        self.vb_peak.setXRange(0,1)
        self.vb_peak.setMenuEnabled(False)
        self.vb_peak.setAspectLocked(lock=False)
        self.vb_peak.setAutoVisible(y=1.0)
        self.vb_peak.setMouseEnabled(x=True, y=False)   # restric movement
        self.vb_peak.enableAutoRange(axis='y', enable=True)
        pyqto.replot_spectra(self, self.plot_peak_frame.graph_peak_Widget, self.plot_settings["show_plots"], alterable_plot=False)

        # when xrange changed make the following
        # to signals and slots: https://www.tutorialspoint.com/pyqt/pyqt_signals_and_slots.htm#:~:text=Each%20PyQt%20widget%2C%20which%20is,%27%20to%20a%20%27slot%27.
        # self.vb_peak.sigXRangeChanged.connect(lambda: self.on_xlims_changed(self.vb))

    def export_currently_selected_masses_to_csv(self):
        selected_masses = self.masses_selected_frame.masses_selected_widget.selectedmasses
        selected_compositions = self.masses_selected_frame.masses_selected_widget.selectedcompositions
        print(f"Export {selected_masses}")
        if selected_masses.shape[0] > 0:
            defaultsavefilename = os.path.join(self.filename,"Selected_traces.csv")
            options = QtWidgets.QFileDialog.Options()
            savefilename, _ = QtWidgets.QFileDialog.getSaveFileName(self,
                                                                "Save File", defaultsavefilename, "csv_files(*.csv)",
                                                                options=options)
            if savefilename:
                print(self.tr.Traces)
                print(f"{selected_compositions}")
                compnames = mo.get_names_out_of_element_numbers(selected_compositions)
                order_of_masses = np.argsort(selected_masses)
                print(compnames)
                header = [f"{round(mass,6)}-{compname}" for mass,compname in zip(selected_masses,compnames)]
                print(header)
                export_df = pd.DataFrame(self.tr.Traces.T,columns=header,index=self.tr.Times)
                export_df = export_df[export_df.columns[order_of_masses]]
                print(export_df)
                export_df.to_csv(savefilename)


    def multiple_check_pressed(self):
        print(f"Input: {self.masslist_frame.multiple_check.text()}")
        input = self.masslist_frame.multiple_check.text()
        first,sep,second = input.rpartition('-')
        print(first,second)
        if first:
            lower, upper = first,second
            lower,upper = int(lower)-1,int(upper)
            if lower < 0:
                lower = 0
            upper = upper
            if lower < upper:
                print(lower, upper)
                self.masses_selected_frame.masses_selected_widget.add_index_to_selected_masses(lower,self,upper_index=upper)
        else:
            # if first is empty -> only one input
            index = int(second) - 1
            if index >= 0:
                print(second)
                self.masses_selected_frame.masses_selected_widget.add_index_to_selected_masses([index], self)

    def remove_all_plot_items(self):
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
        for item in self.graphWidget.allChildItems():
            self.graphWidget.removeItem(item)

    def on_xlims_changed(self, viewbox):
        # for a similar examples look at:
        # import pyqtgraph.examples
        # pyqtgraph.examples.run()
        # InfiniteLine Example
        #documentation https://pyqtgraph.readthedocs.io/en/latest/api_reference/graphicsItems/infiniteline.html
        pass
    #     xlims, ylims = viewbox.viewRange()
    #     # print("xlims changed ", xlims, np.diff(xlims))
    #
    #     if np.diff(xlims) > 1.1:
    #         pyqtgraph_objects.remove_all_vlines(self)
    #     else:
    #         pyqtgraph_objects.redraw_vlines(self, xlims)
    #     if np.diff(xlims) < 0.7:
    #         # only if we are shure, that we have the influence of only one peak we draw the local fit
    #         def to_worker():
    #             pyqtgraph_objects.redraw_localfit(self,xlims)
    #         worker = Worker(to_worker)
    #         self.threadpool.start(worker)

    def update_plots(self):
        # set the restrictions on the movement
        self.remove_all_plot_items()
        traces = self.tr.Traces#[self.tr.MasslistMasses]
        masses = self.masses_selected_frame.masses_selected_widget.selectedmasses
        compositions = self.masses_selected_frame.masses_selected_widget.selectedcompositions
        colors = self.masses_selected_frame.masses_selected_widget.defaultcolorcycle
        currentmass = self.masses_selected_frame.masses_selected_widget.current_clicked_mass
        for (trace,mass,composition,color) in zip(traces,masses,compositions,colors):
            print(mass,color)
            if mass==currentmass:
                width = 3
            else:width = 1
            self.tracesplot = self.graphWidget.plot(self.tr.Times, trace,
                                                  pen=pg.mkPen(color, width=width),
                                                  name=f"m/z {round(mass,6)} - {mo.get_names_out_of_element_numbers(composition)}")
            # self.tracesplot.scene().sigMouseClicked.connect(self.mouse_double_click_on_empty)
        self.vb.autoRange()



    def mouse_double_click_on_empty(self,ev):
        if ev.double():
            xpos = self.vb.mapToView(ev.pos()).x()
            print(xpos)



    def keyPressEvent(self, event):
        if event.key() == Qt.Key_D:
            xlims, ylims = self.vb.viewRange()
            self.vb.setXRange(xlims[0] +1 , xlims[1] + 1, padding = 0)
        if event.key() == Qt.Key_A:
            xlims, ylims = self.vb.viewRange()
            self.vb.setXRange(xlims[0] - 1, xlims[1] - 1, padding = 0)


def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys._excepthook = sys.excepthook

    def exception_hook(exctype, value, traceback):
        print("silent error")
        print(exctype, value, traceback)
        sys._excepthook(exctype, value, traceback)
        sys.exit(1)

    sys.excepthook = exception_hook
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
