import numpy as np
import pyqtgraph as pg
import os
from PyQt5.QtCore import *
from PyQt5 import QtWidgets, QtGui
import sys
import workflows.masslist_objects as mf
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

        self.filename = r"C:\Users\peaq\Desktop\manualPeakFitter\_result.hdf5"
        self.savefilename =   r"C:\Users\peaq\Desktop\manualPeakFitter"

        #those are the "basket" objects, where the data is in sp = all data that has to do with the spectrum, ml = all data to the masslist
        self.sp = mf.Spectrum(self.filename)
        self.mass_suggestions_ranges = [(0, 10), (0, 0), (0, 20), (1, 1), (0, 1), (0, 5), (0, 0), (0, 0)]  # always in the order C C13 H H+ N O, O18 S in the first place would be C number of 0 to 10
        # order ["C", "C13", "H", "H+", "N", "O", "O18", "S", ]
        self.ml = mf.Masslist(self.mass_suggestions_ranges, self.filename)
        self.plot_settings = {"vert_lines_color_default": 0.5,
                              "vert_lines_color_masslist": "r",
                              "vert_lines_color_isotopes": (0,210,0,100), # RGB tubel and last number gives the transparency (from 0 to 255)
                              "average_spectrum_color" : (150,0,200),
                              "max_spectrum_color": (120, 40, 200, 100),
                              "min_spectrum_color": (30, 150, 40, 100),
                              "sub_spectrum_color": (30, 70, 230, 100),
                              "local_fit": (0,0,210),
                              "background_color": "w",
                              "show_plots": [True,False,False,False] #plots corresponding to [avg spectrum, min spec, max spect, subspectr]
                              }
        self.spectrumplot = []
        self.spectrum_max_plot = []
        self.spectrum_min_plot = []
        self.subspec_plot = []

        self.init_Ui()
        self.init_plots()



    def init_Ui(self):
        self.centralwidget = QtWidgets.QWidget(self)
        # main layout setup
        self.overallverticallayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.verticalLayout1 = QtWidgets.QVBoxLayout()  #layout on the left with the masslist, and other stuff
        self.verticalLayout2 = QtWidgets.QVBoxLayout()  #laout on the right with the graph
        self.jump_to_mass_layout = QtWidgets.QHBoxLayout()

        self.horizontalLayout.addLayout(self.verticalLayout1)
        self.horizontalLayout.addLayout(self.verticalLayout2)
        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(1,7)
        self.verticalLayout1.addLayout(self.jump_to_mass_layout)

        # plot widget for the verticalLayout2
        self.graphWidget = pg.PlotWidget()
        self.verticalLayout2.addWidget(self.graphWidget)

        self.slider = QtWidgets.QSlider(Qt.Horizontal)
        self.slider.setFocusPolicy(Qt.StrongFocus)
        self.slider.setMinimum(0)
        self.slider.setMaximum(self.sp.sum_specs.shape[0]-1)
        self.slider.setTickPosition(QtWidgets.QSlider.TicksBothSides)
        self.slider.setTickInterval(1)
        self.slider.setSingleStep(self.sp.sum_specs.shape[0]-1)
        self.slider.valueChanged.connect(lambda: pyqtgraph_objects.redraw_subspec(self))
        self.verticalLayout2.addWidget(self.slider)

        # other widgets for the verticalLayout1
        self.button = QtWidgets.QPushButton("Print Masslist")
        self.button.clicked.connect(lambda: print(self.ml.masslist.masses))

        save_button = QtWidgets.QPushButton("Save Masslist to .csv")
        save_button.clicked.connect(self.save_masslist_to_csv)

        # list of masses
        self.masslist_widget = QtWidgets.QListWidget(self)
        self.masslist_widget.itemClicked.connect(self.jump_to_mass)
        # this functions redraws the qlist with the current masses in the masslist
        self.ml.redo_qlist(self.masslist_widget)

        self.label_jump_mass = QtWidgets.QLabel("Jump to mass: ")
        self.jump_to_mass_input = QtWidgets.QLineEdit()
        self.jump_to_mass_input.setValidator(QtGui.QDoubleValidator(0., 500., 4))
        self.jump_to_mass_input.textChanged.connect(self.jump_to_mass)
        self.jump_to_mass_layout.addWidget(self.label_jump_mass)
        self.jump_to_mass_layout.addWidget(self.jump_to_mass_input)


        # create menu
        menubar = QtWidgets.QMenuBar()
        actionFile = menubar.addMenu("File")
        openfile = QtWidgets.QAction("Open", self)
        openfile.setShortcut("Ctrl+O")
        openfile.triggered.connect(lambda: po.open_file(self))
        actionFile.addAction(openfile)
        savecsv = QtWidgets.QAction("Save Masslist to .cvs", self)
        savecsv.setShortcut("Ctrl+Shift+S")
        savecsv.triggered.connect(self.save_masslist_to_csv)
        actionFile.addAction(savecsv)

        actionFile.addSeparator()
        quit = QtWidgets.QAction("Quit", self)
        quit.setShortcut("Alt+F5")
        quit.triggered.connect(lambda: sys.exit(0))
        actionFile.addAction(quit)

        changemassrangesWindow = po.SelectMassRangeWindow(self)
        changemassranges = QtWidgets.QAction("Change Element ranges", self)
        changemassranges.triggered.connect(changemassrangesWindow.show)
        actionFile.addAction(changemassranges)

        settingswindow = po.SettingsWindow(self)
        settings = QtWidgets.QAction("Settings", self)
        settings.triggered.connect(settingswindow.show)
        menubar.addAction(settings)

        helpwindow = po.HelpWindow(self)
        helpaction = QtWidgets.QAction("Help", self)
        helpaction.triggered.connect(helpwindow.show)
        menubar.addAction(helpaction)


        self.overallverticallayout.addWidget(menubar)
        self.overallverticallayout.addLayout(self.horizontalLayout)
        self.verticalLayout1.addWidget(self.masslist_widget)
        self.verticalLayout1.addWidget(self.button)
        self.verticalLayout1.addWidget(save_button)


        self.setCentralWidget(self.centralwidget)

    def init_plots(self):
        # Enable antialiasing for prettier plots
        pg.setConfigOptions(antialias=True)
        self.graphWidget.setBackground(self.plot_settings["background_color"])
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

        # whens scrolling through there comes a point where nothing is shown anymore
        xlims, ylims = viewbox.viewRange()

        if np.diff(xlims) > 1.1:
            pyqtgraph_objects.remove_all_vlines(self)
        else:
            pyqtgraph_objects.redraw_vlines(self)
        if np.diff(xlims) < 0.7:
            # only if we are shure, that we have the influence of only one peak we draw the local fit
            def to_worker():
                pyqtgraph_objects.redraw_localfit(self,xlims)
            worker = Worker(to_worker)
            self.threadpool.start(worker)
    def save_masslist_to_csv(self):
        dialog = QtWidgets.QFileDialog()
        filepath = dialog.getExistingDirectory(None, "Save .csv")
        self.savefilename = filepath
        np.savetxt(os.path.join(self.savefilename,"masslist.csv") , self.ml.masslist.masses, delimiter=",")
        np.savetxt(os.path.join(self.savefilename, "compounds.csv") , self.ml.masslist.element_numbers, delimiter=",")
        print("Saved Masslist to", self.savefilename)

    def jump_to_mass(self, event):
        print(event)
        if type(event) is str:
            mass = float(event)
        else:
            mass, compoundstr = event.text().rsplit('  ', 1)
            mass = float(mass)
        xlims, ylims = self.vb.viewRange()
        xrange = xlims[1] - xlims[0]
        target_mass = mass
        newxlims = (target_mass - xrange/2 , target_mass + xrange/2)
        self.vb.setXRange(*newxlims)

    def mouse_double_click_on_empty(self, ev):
        # ev pos is the position of the mouseclick in pixel relative to the window, map it onto the view values
        xlims, ylims = self.vb.viewRange()
        if ev.double() and np.diff(xlims) < 1.1:
            print(ev.pos())
            xpos = self.vb.mapToView(ev.pos()).x()
            self.ml.add_mass_to_masslist(xpos,self)
            pyqtgraph_objects.redraw_localfit(self,xlims)


    def keyPressEvent(self, event):
        if event.key() == Qt.Key_D:
            xlims, ylims = self.vb.viewRange()
            self.vb.setXRange(xlims[0] +1 , xlims[1] + 1)
        if event.key() == Qt.Key_A:
            xlims, ylims = self.vb.viewRange()
            self.vb.setXRange(xlims[0] - 1, xlims[1] - 1)
        if event.key() == Qt.Key_Delete:
            print(self.ml.currently_hovered)
            self.ml.currently_hovered.delete_vline()



def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
