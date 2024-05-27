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
        self.overallverticallayout = QtWidgets.QVBoxLayout(self.centralwidget) # all with bar for files and interaction laout
        self.horizontal_splitter = QtWidgets.QSplitter(Qt.Horizontal)
        # self.horizontal_splitter.setSizes([1000, 2000])
        # self.horizontal_splitter.setMinimumSize(100, 100)
        # self.horizontal_splitter.setMaximumSize(400, 1000)
        # self.horizontalLayout = QtWidgets.QHBoxLayout() # overall horizontallayout with left column and plot

        self.left_splitter_masslist_info = QtWidgets.QSplitter(Qt.Vertical)
        self.horizontal_splitter.addWidget(self.left_splitter_masslist_info)
        # self.horizontal_splitter.addWidget(QtWidgets.QLabel("ji"))
        self.masslist_frame = po.Masslist_Frame()
        self.left_splitter_masslist_info.addWidget(self.masslist_frame)
        self.splitter_selected_peak = QtWidgets.QSplitter(Qt.Horizontal)
        self.left_splitter_masslist_info.addWidget(self.splitter_selected_peak)

        self.masses_selected_frame = po.SelectedMassesFrame()
        self.splitter_selected_peak.addWidget(self.masses_selected_frame)

        self.plot_peak_frame = po.Peak_Frame()
        self.splitter_selected_peak.addWidget(self.plot_peak_frame)
        # self.left_column_layout = QtWidgets.QVBoxLayout() #layout on the left with the masslist, and other stuff
        # self.infoonmasses_layout = QtWidgets.QHBoxLayout()
        # self.masses_selected_layout = QtWidgets.QVBoxLayout()
        # self.peak_info_layout = QtWidgets.QVBoxLayout()
        # self.masslists_layout = QtWidgets.QVBoxLayout()
        # self.left_column_layout.addLayout(self.masslists_layout)
        # self.left_column_layout.addLayout(self.infoonmasses_layout)
        # self.left_column_layout.setStretch(0,2)
        # self.left_column_layout.setStretch(1,1)
        # self.plot_layout = QtWidgets.QVBoxLayout()  #laout on the right with the graph
        # self.jump_to_mass_layout = QtWidgets.QHBoxLayout()
        # self.jump_to_compound_layout = QtWidgets.QHBoxLayout()
        # self.multiple_check_layout = QtWidgets.QHBoxLayout()
        # self.sorting_layout = QtWidgets.QHBoxLayout()


        # self.horizontalLayout.addLayout(self.left_column_layout)
        # self.horizontalLayout.addLayout(self.plot_layout)
        # self.horizontalLayout.setStretch(0, 2)
        # self.horizontalLayout.setStretch(1,3)
        # self.masslists_layout.addLayout(self.multiple_check_layout)
        # self.masslists_layout.addLayout(self.jump_to_mass_layout)
        # self.masslists_layout.addLayout(self.jump_to_compound_layout)
        # self.masslists_layout.addLayout(self.sorting_layout)

        # plot widget for the plot_layout
        self.graphWidget = pg.PlotWidget()
        axis = pg.DateAxisItem()
        self.graphWidget.setAxisItems({'bottom': axis})
        self.horizontal_splitter.addWidget(self.graphWidget)


        # #show peak info
        # self.peak_info_layout_header = QtWidgets.QHBoxLayout()
        # self.peak_info_layout_header.addWidget(QtWidgets.QLabel("Peak of selected Mass"))
        # self.peakmasslabel = QtWidgets.QLabel("")
        # self.peak_info_layout_header.addWidget(self.peakmasslabel)
        # self.peakmasscolor = po.ColorField((0,0,0))
        # self.peak_info_layout_header.addWidget(self.peakmasscolor)
        # # self.peak_info_deselectall_button = QtWidgets.QPushButton("Deselect")
        # # self.peak_info_layout_header.addWidget(self.peak_info_deselectall_button)
        # self.plot_peak_layout = QtWidgets.QVBoxLayout()
        # self.graph_peak_Widget = pg.PlotWidget()
        # axis = pg.DateAxisItem()
        # self.graph_peak_Widget.setAxisItems({'bottom': axis})
        # self.plot_peak_layout.addWidget(self.graph_peak_Widget)
        #
        # self.horizontal_splitter.addWidget(self.left_splitter_masslist_info)
        # self.left_splitter_masslist_info.addWidget(self.graphWidget)
        #
        # # list of masses
        # self.masslist_widget = to.QlistWidget_Masslist(self,[],[])
        # regex = QRegExp(r'^-?\d+(-\d+)?$')
        # # Create a validator based on the regular expression
        # self.multiple_check = QtWidgets.QLineEdit()
        # validator = QRegExpValidator(regex, self.multiple_check)
        # self.multiple_check.setValidator(validator)
        # multiple_check_label = QtWidgets.QLabel("Select traces (e.g. 1-10)")
        # self.multiple_check_OK_Button = QtWidgets.QPushButton("OK")
        # self.multiple_check_layout.addWidget(multiple_check_label)
        # self.multiple_check_layout.addWidget(self.multiple_check)
        # # self.multiple_check_layout.addWidget(self.multiple_check_OK_Button)
        #
        #
        #
        #
        #
        # self.label_jump_mass = QtWidgets.QLabel("Select masses (e.g. 69.420-70): ")
        # self.jump_to_mass_input = QtWidgets.QLineEdit()
        # regexmass = QRegExp(r'^\d+(\.\d*)?(-(\d+)(\.\d*)?)?$')
        # validator = QRegExpValidator(regexmass, self.jump_to_mass_input)
        # self.jump_to_mass_input.setValidator(validator)
        # self.jump_to_mass_layout.addWidget(self.label_jump_mass)
        # self.jump_to_mass_layout.addWidget(self.jump_to_mass_input)
        #
        # self.label_jump_compound = QtWidgets.QLabel("Select compound (e.g. H3O+): ")
        # self.jump_to_compound_input = QtWidgets.QLineEdit()
        # regexcomp = QRegExp(r'^(([a-zA-Z]+)(\d+)?)+\+$')
        # validatorcomp = QRegExpValidator(regexcomp, self.jump_to_compound_input)
        # self.jump_to_compound_input.setValidator(validatorcomp)
        # self.jump_to_compound_button = QtWidgets.QPushButton("OK")
        # self.jump_to_mass_layout.addWidget(self.label_jump_mass)
        # self.jump_to_mass_layout.addWidget(self.jump_to_mass_input)
        # self.jump_to_compound_layout.addWidget(self.label_jump_compound)
        # self.jump_to_compound_layout.addWidget(self.jump_to_compound_input)
        # # self.jump_to_compound_layout.addWidget(self.jump_to_compound_button)
        #
        # def sort_on_mass(masses):
        #     sorted = np.argsort(masses)
        #     return sorted
        # self.sort_mass = to.Sorting(self,self.sorting_layout, sort_on_mass, "Sort masses")
        #
        # def sort_biggest_relative_difference(traces):
        #     if traces.ndim == 3:
        #         traces = traces[0]
        #     rel_diffs = np.empty(traces.shape[0])
        #     for i, trace in enumerate(traces):
        #         if np.mean(trace) > 0.7 * np.std(trace):
        #             #preselect for noise
        #             biggestdiff = np.ptp(trace)
        #             mean = np.mean(trace)
        #             rel_diff = biggestdiff / mean
        #             rel_diffs[i] = rel_diff
        #         else: rel_diffs[i] = 0
        #     sorted = np.argsort(rel_diffs)[::-1]
        #     return sorted
        # self.sort_rel = to.Sorting(self, self.sorting_layout, sort_biggest_relative_difference, "Sorting on highest rel diff")
        #
        # def sorting_max(traces):
        #     if traces.ndim == 3:
        #         traces = traces[0]
        #     means = np.mean(traces, axis=1)
        #     sorted = np.argsort(means)
        #     sorted = sorted[::-1]
        #     return sorted
        # self.sort_max = to.Sorting(self,self.sorting_layout,sorting_max, "Sorting on highest trace")
        #
        # create menu
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
        self.overallverticallayout.addWidget(self.horizontal_splitter,stretch = 40)
        # self.masses_selected_layout.addLayout(self.masses_selected_layout_header, stretch = 10)
        # self.masses_selected_layout.addWidget(self.masses_selected_widget, stretch = 10)
        #
        # self.peak_info_layout.addLayout(self.peak_info_layout_header)
        # self.peak_info_layout.addLayout(self.plot_peak_layout)
        # self.infoonmasses_layout.addLayout(self.masses_selected_layout,stretch = 3)
        # self.infoonmasses_layout.addLayout(self.peak_info_layout,stretch = 2)
        #
        #
        # self.masslists_layout.addWidget(QtWidgets.QLabel("Masslist"),stretch = 1)
        # self.masslists_layout.addWidget(self.masslist_widget,stretch = 40)


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
        self.masslist_widget.redo_qlist(self.tr.MasslistMasses, self.tr.MasslistCompositions)
        # self.masslist_widget.itemClicked.connect(self.jump_to_mass)
        self.masslist_widget.itemClicked.connect(lambda item,button: self.masses_selected_widget.add_item_to_selected_masses(item,button,self))
        self.masses_selected_widget.itemClicked.connect(lambda item,button: self.masses_selected_widget.clicked_on_item(item,button,self))
        self.masses_selected_deselectall_button.clicked.connect(lambda: self.masses_selected_widget.deselect_all(self))
        self.masses_selected_export_button.clicked.connect(self.export_currently_selected_masses_to_csv)
        # self.masslist_widget.itemDoubleClicked.connect(lambda item: self.masslist_widget.handle_double_click(item, parent=self))

        #jump to mass widget
        self.jump_to_mass_input.returnPressed.connect(lambda: self.masses_selected_widget.add_mass_to_selected_masses(self.jump_to_mass_input.text(),self))
        self.jump_to_compound_button.pressed.connect(lambda: self.masslist_widget.jump_to_compound(self.jump_to_compound_input.text(),self))
        self.jump_to_compound_input.returnPressed.connect(lambda: self.masslist_widget.jump_to_compound(self.jump_to_compound_input.text(),self))
        self.multiple_check_OK_Button.pressed.connect(self.multiple_check_pressed)
        self.multiple_check.returnPressed.connect(self.multiple_check_pressed)

        # #sorting widgets - give sorting function define sorting object,
        self.sort_max.sortingbutton.pressed.connect(lambda: self.sort_max.sort_qlist(self.masslist_widget,self.tr.load_Traces("all")))
        self.sort_rel.sortingbutton.pressed.connect(lambda : self.sort_rel.sort_qlist(self.masslist_widget,self.tr.load_Traces("all")))
        self.sort_mass.sortingbutton.pressed.connect(lambda: self.sort_mass.sort_qlist(self.masslist_widget,self.tr.MasslistMasses) )
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
        self.vb.setAutoVisible(y=1.0)
        self.vb.setMouseEnabled(x=True, y=False)   # restric movement
        self.vb.enableAutoRange(axis='y', enable=True)
        # when xrange changed make the following
        # to signals and slots: https://www.tutorialspoint.com/pyqt/pyqt_signals_and_slots.htm#:~:text=Each%20PyQt%20widget%2C%20which%20is,%27%20to%20a%20%27slot%27.
        self.vb.sigXRangeChanged.connect(lambda: self.on_xlims_changed(self.vb))
        self.update_plots()

        self.graph_peak_Widget.setBackground(self.plot_settings["background_color"])
        self.graph_peak_Widget.showGrid(y = True)
        self.graph_peak_Widget.getAxis('bottom').setPen(pg.mkPen(color='k'))
        self.graph_peak_Widget.getAxis('left').setPen(pg.mkPen(color='k'))
        # font = self.plot_settings["font"]
        # self.graph_peak_Widget.getAxis('bottom').setStyle(tickFont=font)  # Set the font for the x-axis ticks
        # self.graph_peak_Widget.getAxis('left').setStyle(tickFont=font)  # Set the font for the x-axis ticks
        # self.graph_peak_Widget.getAxis('bottom').setPen('k')
        # self.graph_peak_Widget.getAxis('left').setPen('k')
        # self.graph_peak_Widget.getAxis('bottom').setTextPen('k')
        # self.graph_peak_Widget.getAxis('left').setTextPen('k')
        # self.graph_peak_Widget.getAxis('left').setLabel(text="Signal", units=None, unitPrefix=None, **{'color': 'k', 'font-size': '12pt'})
        # self.graph_peak_Widget.getAxis('bottom').setLabel(text="m/z [Th]", units=None, unitPrefix=None, **{'color': 'k', 'font-size': '12pt'})
        self.graph_peak_Widget.setLogMode(y=True)
        self.graph_peak_Widget.addLegend()

        self.plot_added = True
        # set the restrictions on the movement
        self.vb_peak = self.graph_peak_Widget.getViewBox()
        self.vb_peak.setXRange(0,1)
        self.vb_peak.setMenuEnabled(False)
        self.vb_peak.setAspectLocked(lock=False)
        self.vb_peak.setAutoVisible(y=1.0)
        self.vb_peak.setMouseEnabled(x=True, y=False)   # restric movement
        self.vb_peak.enableAutoRange(axis='y', enable=True)
        pyqto.replot_spectra(self, self.graph_peak_Widget, self.plot_settings["show_plots"], alterable_plot=False)

        # when xrange changed make the following
        # to signals and slots: https://www.tutorialspoint.com/pyqt/pyqt_signals_and_slots.htm#:~:text=Each%20PyQt%20widget%2C%20which%20is,%27%20to%20a%20%27slot%27.
        # self.vb_peak.sigXRangeChanged.connect(lambda: self.on_xlims_changed(self.vb))

    def export_currently_selected_masses_to_csv(self):
        print(f"Export {self.masses_selected_widget.selectedmasses}")
        if self.masses_selected_widget.selectedmasses.shape[0] > 0:
            defaultsavefilename = os.path.join(self.filename,"Selected_traces.csv")
            options = QtWidgets.QFileDialog.Options()
            savefilename, _ = QtWidgets.QFileDialog.getSaveFileName(self,
                                                                "Save File", defaultsavefilename, "csv_files(*.csv)",
                                                                options=options)
            if savefilename:
                print(self.tr.Traces)
                print(f"{self.masses_selected_widget.selectedcompositions}")
                compnames = to.get_names_out_of_element_numbers(self.masses_selected_widget.selectedcompositions)
                print(compnames)
                header = [f"{round(mass,6)}-{compname}" for mass,compname in zip(self.masses_selected_widget.selectedmasses,compnames)]
                print(header)
                export_df = pd.DataFrame(self.tr.Traces.T,columns=header,index=self.tr.Times)
                print(export_df)
                export_df.to_csv(savefilename)


    def multiple_check_pressed(self):
        print(f"Input: {self.multiple_check.text()}")
        borders = self.multiple_check.text().split("-")
        if len(borders) == 1:
            index = int(borders[0]) -1
            self.masses_selected_widget.add_index_to_selected_masses(index, self)
        if len(borders) == 2:
            lower, upper = borders
            lower,upper = int(lower),int(upper)
            if lower < 0:
                lower = 0
            else:
                lower = lower -1
            upper = upper -1
            if lower < upper:
                print(lower, upper)
                self.masses_selected_widget.add_index_to_selected_masses(lower,self,upper_index=upper)
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
        print(self.tr.Traces.shape, self.masses_selected_widget.selectedcompositions)
        for (trace,mass,composition,color) in zip(self.tr.Traces,self.masses_selected_widget.selectedmasses,self.masses_selected_widget.selectedcompositions,self.masses_selected_widget.defaultcolorcycle):
            print(mass,self.masses_selected_widget.current_clicked_mass)
            if mass==self.masses_selected_widget.current_clicked_mass:
                width = 3
            else:width = 1
            self.tracesplot = self.graphWidget.plot(self.tr.Times, trace,
                                                  pen=pg.mkPen(color, width=width),
                                                  name=f"m/z {round(mass,6)} - {to.get_names_out_of_element_numbers(composition)}")
            self.tracesplot.scene().sigMouseClicked.connect(self.mouse_double_click_on_empty)
        self.vb.autoRange()


        # if type(event) is str:
        #     mass = float(event)
        # elif type(event) is float:
        #     mass = event
        # else:
        #     mass, compoundstr = event.text().rsplit('  ', 1)
        #     mass = float(mass)
        # print("jump to mass: ", mass)
        # xlims, ylims = self.vb.viewRange()
        # xrange = xlims[1] - xlims[0]
        # target_mass = mass
        # newxlims = (target_mass - xrange/2 , target_mass + xrange/2)
        # self.vb.setXRange(*newxlims, padding = 0)

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
