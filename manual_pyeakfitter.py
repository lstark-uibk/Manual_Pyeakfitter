import numpy as np
import pandas as pd
import pyqtgraph as pg
import os
from PyQt5.QtCore import *
from PyQt5 import QtWidgets, QtGui, QtCore
import sys
import workflows.masslist_objects as mo
import workflows.pyqtgraph_objects as pyqtgraph_objects
import workflows.pyqt_objects as po


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
        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(1)
        # self.filename = "C://Users//peaq//Uniarbeit//Python//Manual_Pyeakfitter//_result_no_masslist.hdf5"
        self.filename = None
        self.savefilename = None
        self.file_loaded = False
        self.init_Ui_file_not_loaded()



    def init_Ui_file_not_loaded(self):
        self.centralwidget = QtWidgets.QWidget(self)
        # main layout setup
        self.overallverticallayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.verticalLayout1 = QtWidgets.QVBoxLayout()  #layout on the left with the masslist, and other stuff
        self.verticalLayout2 = QtWidgets.QVBoxLayout()  #laout on the right with the graph
        self.jump_to_mass_layout = QtWidgets.QHBoxLayout()
        self.jump_to_compound_layout = QtWidgets.QHBoxLayout()


        self.horizontalLayout.addLayout(self.verticalLayout1)
        self.horizontalLayout.addLayout(self.verticalLayout2)
        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(1,7)
        self.verticalLayout1.addLayout(self.jump_to_mass_layout)
        self.verticalLayout1.addLayout(self.jump_to_compound_layout)

        # plot widget for the verticalLayout2
        self.graphWidget = pg.PlotWidget()


        self.verticalLayout2.addWidget(self.graphWidget)

        self.slider = QtWidgets.QSlider(Qt.Horizontal)
        self.slider.setFocusPolicy(Qt.StrongFocus)
        self.verticalLayout2.addWidget(self.slider)

        # other widgets for the verticalLayout1
        # self.button = QtWidgets.QPushButton("Print suggestions in view range")
        self.button = QtWidgets.QPushButton("Manually add Element")

        self.save_button = QtWidgets.QPushButton("Save Masslist to .csv")


        # list of masses
        self.masslist_widget = QtWidgets.QListWidget(self)

        self.label_jump_mass = QtWidgets.QLabel("Jump to mass: ")
        self.jump_to_mass_input = QtWidgets.QLineEdit()
        self.jump_to_mass_input.setValidator(QtGui.QDoubleValidator(0., 500., 4))
        self.label_jump_compound = QtWidgets.QLabel("Jump to compound: ")
        self.jump_to_compound_input = QtWidgets.QLineEdit()
        self.jump_to_mass_layout.addWidget(self.label_jump_mass)
        self.jump_to_mass_layout.addWidget(self.jump_to_mass_input)
        self.jump_to_compound_layout.addWidget(self.label_jump_compound)
        self.jump_to_compound_layout.addWidget(self.jump_to_compound_input)


        # create menu
        menubar = QtWidgets.QMenuBar()
        self.actionFile = menubar.addMenu("File")
        # the po.openfile triggers init_UI_file_loaded() and init_plots()
        openfile = QtWidgets.QAction("Open", self)
        openfile.setShortcut("Ctrl+O")
        openfile.triggered.connect(lambda: po.open_file(self))
        self.actionFile.addAction(openfile)

        self.savecsv = QtWidgets.QAction("Save Masslist", self)
        self.savecsv.setShortcut("Ctrl+S")
        self.actionFile.addAction(self.savecsv)
        self.saveascsv = QtWidgets.QAction("Save Masslist as new file", self)
        self.saveascsv.setShortcut("Ctrl+Alt+S")
        self.actionFile.addAction(self.saveascsv)

        self.actionFile.addSeparator()
        quit = QtWidgets.QAction("Quit", self)
        quit.setShortcut("Alt+F4")
        quit.triggered.connect(lambda: sys.exit(0))
        self.actionFile.addAction(quit)

        self.settingsMenubar = menubar.addMenu("Settings")
        self.plotsettings_button = QtWidgets.QAction("Plot Settings", self)
        self.settingsMenubar.addAction(self.plotsettings_button)


        self.changemassranges = QtWidgets.QAction("Change Element ranges", self)
        self.settingsMenubar.addAction(self.changemassranges)
        self.addElement = QtWidgets.QAction("Manually add Element", self)
        self.manually_add_element = menubar.addAction(self.addElement)

        helpwindow = po.HelpWindow(self)
        helpaction = QtWidgets.QAction("Help", self)
        helpaction.triggered.connect(helpwindow.show)
        menubar.addAction(helpaction)


        self.overallverticallayout.addWidget(menubar)
        self.overallverticallayout.addLayout(self.horizontalLayout)
        self.verticalLayout1.addWidget(self.masslist_widget)
        self.verticalLayout1.addWidget(self.button)
        self.verticalLayout1.addWidget(self.save_button)

        self.setCentralWidget(self.centralwidget)

    def init_basket_objects(self):
        #those are the "basket" objects, where the data is in sp = all data that has to do with the spectrum, ml = all data to the masslist
        self.sp = mo.Spectrum(self.filename)
        self.ml = mo.Masslist(self.filename)
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
                              "sub_spectrum_color": (103, 42, 201, 80),
                              "local_fit": (0,0,210),
                              "background_color": "w",
                              "show_plots": [True,False,False,False] #plots corresponding to [avg spectrum, min spec, max spect, subspectr]
                              }
        self.spectrumplot = []
        self.spectrum_max_plot = []
        self.spectrum_min_plot = []
        self.subspec_plot = []
        self.jumping_possible = True


    def init_UI_file_loaded(self):
        #add functionality to:
        #slider
        self.slider.setMinimum(0)
        self.slider.setMaximum(self.sp.sum_specs.shape[0]-1)
        self.slider.setTickPosition(QtWidgets.QSlider.TicksBothSides)
        self.slider.setTickInterval(1)
        self.slider.setSingleStep(self.sp.sum_specs.shape[0]-1)
        self.slider.valueChanged.connect(lambda: pyqtgraph_objects.redraw_subspec(self))
        # print suggestion list button
        # self.button.clicked.connect(self.printsugg)
        # save masslist button
        self.save_button.clicked.connect(self.save_masslist_to_csv)
        # masslist shown on left
        self.ml.redo_qlist(self.masslist_widget)
        self.masslist_widget.itemClicked.connect(self.jump_to_mass)
        #jump to mass widget
        self.jump_to_mass_input.textChanged.connect(self.jump_to_mass)
        self.timer_textchange = QtCore.QTimer()
        self.timer_textchange.setSingleShot(True)
        self.timer_textchange.setInterval(500)
        def timerstart(event):
            self.timer_textchange.timeout.connect(lambda: self.jump_to_compound(event))
            self.timer_textchange.start()

        self.jump_to_compound_input.textChanged.connect(timerstart)


        #menubar stuff
        # change range action in menubar
        changemassrangesWindow = po.SelectMassRangeWindow(self)
        self.changemassranges.triggered.connect(changemassrangesWindow.show)
        # add new element action in menubar
        addElementWindow = po.AddnewElement(self)
        # print add elements
        self.button.clicked.connect(addElementWindow.show)
        self.addElement.triggered.connect(addElementWindow.show)

        self.plotsettings_window = po.PlotSettingsWindow(self)
        self.plotsettings_button.triggered.connect(self.plotsettings_window.show)
        # save to csv in menubar
        self.saveascsv.triggered.connect(lambda: self.save_masslist_to_csv(saveas = True))
        self.savecsv.triggered.connect(lambda: self.save_masslist_to_csv(saveas = False))

    def printsugg(self):
        xlims, ylims = self.vb.viewRange()
        print(*np.c_[self.ml.suggestions.masses[(xlims[0]< self.ml.suggestions.masses) * (self.ml.suggestions.masses< xlims[1])],
                mo.get_names_out_of_element_numbers(self.ml.suggestions.element_numbers[(xlims[0]< self.ml.suggestions.masses) * (self.ml.suggestions.masses< xlims[1])])], sep="\n")
    def init_plots(self):
        # Enable antialiasing for prettier plots
        pg.setConfigOptions(antialias=True)
        self.graphWidget.setBackground(self.plot_settings["background_color"])
        self.graphWidget.setLabel('bottom', "m/z [Th]")
        self.graphWidget.setLabel('left', "Signal [cps]")
        self.graphWidget.setLogMode(y=True)
        self.graphWidget.addLegend()
        # make bg plots
        pyqtgraph_objects.replot_spectra(self,self.plot_settings["show_plots"])

        # set the restrictions on the movement
        self.vb = self.spectrumplot.getViewBox()
        self.vb.setXRange(1,20)
        self.vb.setMenuEnabled(False)
        self.vb.setAspectLocked(lock=False)
        self.vb.setAutoVisible(y=1.0)
        self.vb.setMouseEnabled(x=True, y=False)   # restric movement
        self.vb.enableAutoRange(axis='y', enable=True)
        # when xrange changed make the following
        # to signals and slots: https://www.tutorialspoint.com/pyqt/pyqt_signals_and_slots.htm#:~:text=Each%20PyQt%20widget%2C%20which%20is,%27%20to%20a%20%27slot%27.
        self.vb.sigXRangeChanged.connect(lambda: self.on_xlims_changed(self.vb))



    def on_xlims_changed(self, viewbox):
        # for a similar examples look at:
        # import pyqtgraph.examples
        # pyqtgraph.examples.run()
        # InfiniteLine Example
        #documentation https://pyqtgraph.readthedocs.io/en/latest/api_reference/graphicsItems/infiniteline.html

        xlims, ylims = viewbox.viewRange()
        # print("xlims changed ", xlims, np.diff(xlims))

        if np.diff(xlims) > 1.1:
            pyqtgraph_objects.remove_all_vlines(self)
        else:
            pyqtgraph_objects.redraw_vlines(self, xlims)
        if np.diff(xlims) < 0.7:
            # only if we are shure, that we have the influence of only one peak we draw the local fit
            def to_worker():
                print("because I scrolled I redraw local fit")
                pyqtgraph_objects.redraw_localfit(self,xlims)
            worker = Worker(to_worker)
            self.threadpool.start(worker)
    def save_masslist_to_csv(self, saveas = False):
        if self.savefilename == None or saveas:
            defaultsavefilename = os.path.join(self.filename,"masslist.csv")
            options = QtWidgets.QFileDialog.Options()
            self.savefilename, _ = QtWidgets.QFileDialog.getSaveFileName(self,
                                                                "Save File", defaultsavefilename, "csv_files(*.csv)",
                                                                options=options)

        head = "# Elements: \nC	C(13)	H	H+	N	O	O(18)	S\n	C					O\n12	13.003355	1.007825	1.007276	14.003074	15.994915	17.99916	31.97207\n\n# Masses: \nC	C(13)	H	H+	N	O	O(18)	S	Mass	Name\n"
        with open(self.savefilename, "w") as file:
            file.write(head)
        element_names = np.empty(self.ml.masslist.masses.size,dtype=object)
        for index, row in enumerate(self.ml.masslist.element_numbers):
            element_names[index] = mo.get_names_out_of_element_numbers(row)
        # problem strings und numbers -> pandas
        data = pd.DataFrame(np.c_[self.ml.masslist.element_numbers, self.ml.masslist.masses])
        data.insert(9,"names",element_names)
        data.to_csv(self.savefilename, mode='a', sep='\t', index=False, header=False)

        print("Saved Masslist to", self.savefilename)

    def jump_to_mass(self, event):
        if type(event) is str:
            mass = float(event)
        elif type(event) is float:
            mass = event
        else:
            mass, compoundstr = event.text().rsplit('  ', 1)
            mass = float(mass)
        print("jump to mass: ", mass)
        xlims, ylims = self.vb.viewRange()
        xrange = xlims[1] - xlims[0]
        target_mass = mass
        newxlims = (target_mass - xrange/2 , target_mass + xrange/2)
        self.vb.setXRange(*newxlims, padding = 0)

    def jump_to_compound(self,compoundstring):
        print(compoundstring)
        mass, compound = mo.get_element_numbers_out_of_names(compoundstring)
        self.jump_to_mass(float(mass))
        if not (self.ml.suggestions.element_numbers == compound).all(axis=1).any():
            self.ml.add_suggestion_to_sugglist(self, compound)

    def mouse_double_click_on_empty(self, ev):
        # ev pos is the position of the mouseclick in pixel relative to the window, map it onto the view values
        xlims, ylims = self.vb.viewRange()
        if ev.double() and np.diff(xlims) < 1.1:
            xpos = self.vb.mapToView(ev.pos()).x()
            self.ml.add_mass_to_masslist(self, xpos)
            pyqtgraph_objects.redraw_localfit(self,xlims)


    def keyPressEvent(self, event):
        if event.key() == Qt.Key_D:
            xlims, ylims = self.vb.viewRange()
            self.vb.setXRange(xlims[0] +1 , xlims[1] + 1, padding = 0)
        if event.key() == Qt.Key_A:
            xlims, ylims = self.vb.viewRange()
            self.vb.setXRange(xlims[0] - 1, xlims[1] - 1, padding = 0)
        if event.key() == Qt.Key_Delete:
            print(self.ml.currently_hovered.value())
            self.ml.delete_mass_from_masslist(self, self.ml.currently_hovered.value())
            xlims, ylims = self.vb.viewRange()
            pyqtgraph_objects.redraw_localfit(self, xlims)


def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
