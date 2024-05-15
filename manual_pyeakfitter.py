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
import datetime as dt
import configparser

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
        self.setWindowTitle("Manual Pyeakfitter")
        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(1)
        # self.filename = "C://Users//peaq//Uniarbeit//Python//Manual_Pyeakfitter//_result_no_masslist.hdf5"
        self.filename = None
        self.savefilename = None
        self.plot_added = False
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

        # self.slider = QtWidgets.QSlider(Qt.Horizontal)
        self.slider = po.LabeledSlider(0,1,1)
        self.slider.setFocusPolicy(Qt.StrongFocus)
        self.verticalLayout2.addWidget(self.slider)

        # other widgets for the verticalLayout1
        # self.button = QtWidgets.QPushButton("Print suggestions in view range")
        self.button = QtWidgets.QPushButton("Manually add Element")
        self.show_total_masslist_button = QtWidgets.QPushButton("Show total Masslist")
        self.save_button = QtWidgets.QPushButton("Save Masslist to .csv")


        # list of masses
        self.masslist_widget = QtWidgets.QListWidget(self)

        self.label_jump_mass = QtWidgets.QLabel("Jump to mass: ")
        self.jump_to_mass_input = QtWidgets.QLineEdit()
        self.jump_to_mass_input.setValidator(QtGui.QDoubleValidator(0., 500., 4))
        self.label_jump_compound = QtWidgets.QLabel("Jump to compound: ")
        self.jump_to_compound_input = QtWidgets.QLineEdit()
        self.jump_to_compound_button = QtWidgets.QPushButton("OK")
        self.jump_to_mass_layout.addWidget(self.label_jump_mass)
        self.jump_to_mass_layout.addWidget(self.jump_to_mass_input)
        self.jump_to_compound_layout.addWidget(self.label_jump_compound)
        self.jump_to_compound_layout.addWidget(self.jump_to_compound_input)
        # self.jump_to_compound_layout.addWidget(self.jump_to_compound_button)

        # create menu
        menubar = QtWidgets.QMenuBar()
        self.actionFile = menubar.addMenu("File")
        # the po.openfile triggers init_UI_file_loaded() and init_plots()
        openfile = QtWidgets.QAction("Open .hdf5 result file", self)
        openfile.setShortcut("Ctrl+O")
        openfile.triggered.connect(lambda: po.open_file(self))
        self.actionFile.addAction(openfile)

        self.importmasslist = QtWidgets.QAction("Import Masslist from .csv", self)
        self.importmasslist.setShortcut("Ctrl+I")
        self.actionFile.addAction(self.importmasslist)



        self.savecsv = QtWidgets.QAction("Save Masslist to .csv", self)
        self.savecsv.setShortcut("Ctrl+S")
        self.actionFile.addAction(self.savecsv)
        self.saveascsv = QtWidgets.QAction("Save Masslist as new .csv file", self)
        self.saveascsv.setShortcut("Ctrl+Alt+S")
        self.actionFile.addAction(self.saveascsv)

        self.saveashdf5 = QtWidgets.QAction("Save Masslist in new .hdf5 file", self)

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
        self.verticalLayout1.addWidget(self.show_total_masslist_button)

        self.setCentralWidget(self.centralwidget)

    def init_basket_objects(self):
        #those are the "basket" objects, where the data is in sp = all data that has to do with the spectrum, ml = all data to the masslist
        self.sp = mo.Spectrum(self.filename)
        self.ml = mo.read_masslist_from_hdf5_produce_iso_sugg(self.filename)
        self.plot_settings = {"font" : QtGui.QFont('Calibri', 11),
                              "vert_lines_color_suggestions": (97, 99, 102,70),
                              "vert_lines_color_masslist": (38, 135, 20),
                              "vert_lines_color_masslist_without_composition": (13, 110, 184),
                              "vert_lines_color_isotopes": (252, 3, 244, 70), # RGB tubel and last number gives the transparency (from 0 to 255)
                              "vert_lines_width_suggestions": 1.5,
                              "vert_lines_width_masslist": 2.5,
                              "vert_lines_width_isotopes": 1.5,
                              "spectra_width": 1,
                              "average_spectrum_color" : (252, 49, 3),
                              "max_spectrum_color": (51, 10, 84),
                              "min_spectrum_color": (8, 84, 46),
                              "sub_spectrum_color": (13, 99, 5),
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
        #first remove old slider and make anew with new labels etc
        self.slider.deleteLater()
        minslider = 0
        maxslider = self.sp.sum_specs.shape[0]-1
        labels =[ts.astype(dt.datetime).strftime("%Y-%m-%d %H:%M") for ts in self.sp.specs_times]
        self.slider = po.LabeledSlider(minslider, maxslider, 1, orientation=Qt.Horizontal,labels=labels)
        self.verticalLayout2.addWidget(self.slider)
        # self.slider.setTickPosition(QtWidgets.QSlider.TicksBothSides)
        # self.slider.setTickInterval(1)
        # self.label.setText(labels[value])
        # self.slider.setSingleStep(self.sp.sum_specs.shape[0]-1)
        self.slider.sl.valueChanged.connect(lambda: pyqtgraph_objects.redraw_subspec(self))
        # print suggestion list button
        # self.button.clicked.connect(self.printsugg)
        # save masslist button
        self.save_button.clicked.connect(self.save_masslist_to_csv)
        # masslist shown on left
        self.ml.redo_qlist(self.masslist_widget)
        self.masslist_widget.itemClicked.connect(self.jump_to_mass)
        #jump to mass widget
        self.jump_to_mass_input.textChanged.connect(self.jump_to_mass)
        # self.jump_to_compound_button.pressed.connect(lambda: self.jump_to_compound(self.jump_to_compound_input.text()))
        self.jump_to_compound_input.returnPressed.connect(lambda: self.jump_to_compound(self.jump_to_compound_input.text()))
        #menubar stuff
        # change range action in menubar
        changemassrangesWindow = po.SelectMassRangeWindow(self)
        self.changemassranges.triggered.connect(changemassrangesWindow.show)
        # add new element action in menubar
        def show_addnewelem_window():
            addElementWindow = po.AddnewElement(self)
            addElementWindow.show()
        self.button.clicked.connect(show_addnewelem_window)
        def show_totalml_window():
            addElementWindow = po.Show_total_Masslist(self)
            addElementWindow.show()
        self.show_total_masslist_button.clicked.connect(show_totalml_window)
        self.addElement.triggered.connect(show_addnewelem_window)

        self.plotsettings_window = po.PlotSettingsWindow(self)
        self.plotsettings_button.triggered.connect(self.plotsettings_window.show)
        # save to csv in menubar
        self.saveascsv.triggered.connect(lambda: self.save_masslist_to_csv(saveas = True))
        self.savecsv.triggered.connect(lambda: self.save_masslist_to_csv(saveas = False))
        self.importmasslist.triggered.connect(self.importmasslist_fn)


    def printsugg(self):
        xlims, ylims = self.vb.viewRange()
        print(*np.c_[self.ml.suggestions.masses[(xlims[0]< self.ml.suggestions.masses) * (self.ml.suggestions.masses< xlims[1])],
                mo.get_names_out_of_element_numbers(self.ml.suggestions.element_numbers[(xlims[0]< self.ml.suggestions.masses) * (self.ml.suggestions.masses< xlims[1])])], sep="\n")
    def init_plots(self):
        # Enable antialiasing for prettier plots
        pg.setConfigOptions(antialias=True)
        self.graphWidget.setBackground(self.plot_settings["background_color"])
        self.graphWidget.showGrid(y = True)
        self.graphWidget.getAxis('bottom').setPen(pg.mkPen(color='k'))
        self.graphWidget.getAxis('left').setPen(pg.mkPen(color='k'))
        font = self.plot_settings["font"]
        self.graphWidget.getAxis('bottom').setStyle(tickFont=font)  # Set the font for the x-axis ticks
        self.graphWidget.getAxis('left').setStyle(tickFont=font)  # Set the font for the x-axis ticks
        self.graphWidget.getAxis('bottom').setPen('k')
        self.graphWidget.getAxis('left').setPen('k')
        self.graphWidget.getAxis('bottom').setTextPen('k')
        self.graphWidget.getAxis('left').setTextPen('k')
        self.graphWidget.getAxis('left').setLabel(text="Signal [cps]", units=None, unitPrefix=None, **{'color': 'k', 'font-size': '12pt'})
        self.graphWidget.getAxis('bottom').setLabel(text="m/z [Th]", units=None, unitPrefix=None, **{'color': 'k', 'font-size': '12pt'})
        self.graphWidget.setLogMode(y=True)
        self.graphWidget.addLegend()
        # make bg plots
        pyqtgraph_objects.replot_spectra(self,self.plot_settings["show_plots"])
        self.plot_added = True
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
            if self.sp.current_local_fit:
                self.sp.current_local_fit.setData([0], [0])
                self.sp.current_local_fit_masses = np.array([0])
        else:
            pyqtgraph_objects.redraw_vlines(self, xlims)
        if np.diff(xlims) < 0.7:
            # only if we are shure, that we have the influence of only one peak we draw the local fit
            def to_worker():
                pyqtgraph_objects.redraw_localfit(self,xlims)
            worker = Worker(to_worker)
            self.threadpool.start(worker)
    def importmasslist_fn(self):
        print("Import")
        # get filepath of masslist to import
        co = po.Config()
        filepath_lastreadin = co.read_from_config("filepaths", "filepath_last_import_masslist")
        try:
            dialog = QtWidgets.QFileDialog()
            filepath, filter = dialog.getOpenFileName(None, "Window name", filepath_lastreadin, "csv masslist files formatted in the right way (*.csv)")
        except:
            print("Old filepath not reachable")
            dialog = QtWidgets.QFileDialog()
            filepath, filter = dialog.getOpenFileName(None, "Window name", "", "HDF5_files (*.hdf5)")
        co.save_to_config("filepaths", "filepath_last_import_masslist", filepath)
        # filepath = "D:\\Uniarbeit 23_11_09\\CERN\\CLOUD16\\arctic_runs\\2023-11-13\\results\\_result_avg.hdf5"
        print(f"Try to read in Masslist data from {filepath}")
        if filepath:
            # question overwrite or merge
            decision_dialog = QtWidgets.QMessageBox()
            decision_dialog.setWindowTitle('Import Masslist from .csv')
            decision_dialog.setText("How do I handle the old Masslist?")
            decision_dialog.setIcon(QtWidgets.QMessageBox.Question)

            overwrite = decision_dialog.addButton("Overwrite current masslist", QtWidgets.QMessageBox.YesRole)
            merge = decision_dialog.addButton("Merge with current masslist", QtWidgets.QMessageBox.NoRole)

            decision_dialog.exec_()
            merge_with_old_ml = False
            if decision_dialog.clickedButton() == merge:
                merge_with_old_ml = True

            # load the data
            try:
                with open(filepath, 'r') as f:
                    for skip, line in enumerate(f):
                        if 'Masses' in line:
                            break
                df = pd.read_csv(filepath, skiprows=skip+1,sep="\t")
                masslist_read_in = True
            except Exception as error:
                dlg = QtWidgets.QMessageBox(self)
                dlg.setWindowTitle("Error")
                dlg.setText("Masslist is not readable, check whether .csv has the right format")
                dlg.exec()
                print(f"The Exception was {error}")
                masslist_read_in = False
            if masslist_read_in:
                masses_new = df.Mass.values

                # make the elements fit to the proclaimed elements in masslist
                names_elements_proclaimed_masslist = mo.Mass_iso_sugglist.names_elements
                element_numbers_new = np.full([df.shape[0],len(names_elements_proclaimed_masslist)],0)
                for idxcolumn,element, in enumerate(names_elements_proclaimed_masslist):
                    if element in df.columns:
                        element_numbers_new[:,idxcolumn] = df[element].values

                if merge_with_old_ml:
                    # create a mask which n, m entry is whether A[n,:] is same as B[m,:]
                    masksame = np.isclose(masses_new[:, None],self.ml.masslist.masses, atol=0.00001)
                    masksame_new_masses =np.any(masksame,axis=1)
                    masses_merged = np.hstack((self.ml.masslist.masses,masses_new[~masksame_new_masses]))
                    element_numbers_merged = np.vstack((self.ml.masslist.element_numbers,element_numbers_new[~masksame_new_masses,:]))
                    sorted_on_masses = np.argsort(masses_merged)
                    masses_merged = masses_merged[sorted_on_masses]
                    element_numbers_merged = element_numbers_merged[sorted_on_masses,:]
                    masses_new = masses_merged
                    element_numbers_new = element_numbers_merged

                new_masslist = mo._Data(masses_new,element_numbers_new)
                self.ml = mo.Mass_iso_sugglist(new_masslist)
                self.ml.redo_qlist(self.masslist_widget)

    def showmasslist_fn(self):
        print("Show total masslist")
    def save_masslist_to_csv(self, saveas = False):
        if self.savefilename == None or saveas:
            defaultsavefilename = os.path.join(self.filename,"masslist.csv")
            options = QtWidgets.QFileDialog.Options()
            self.savefilename, _ = QtWidgets.QFileDialog.getSaveFileName(self,
                                                                "Save File", defaultsavefilename, "csv_files(*.csv)",
                                                                options=options)
        if self.savefilename:
            head = "# Elements: "
            head += "\n"
            for element in self.ml.names_elements:
                head += f"{element}\t"
            head += "\n\n"
            for mass in self.ml.masses_elements:
                head += f"{mass}\t"
            head += "\n\n"
            head += "#Masses: \n"
            for element in self.ml.names_elements:
                head += f"{element}\t"
            head += "Mass\t"
            head += "Name\n"
            with open(self.savefilename, "w") as file:
                file.write(head)
            element_names = np.empty(self.ml.masslist.masses.size,dtype=object)
            for index, row in enumerate(self.ml.masslist.element_numbers):
                element_names[index] = mo.get_names_out_of_element_numbers(row)
            # problem strings und numbers -> pandas
            data = pd.DataFrame(np.c_[self.ml.masslist.element_numbers, self.ml.masslist.masses])
            data.insert(len(data.columns),"names",element_names)
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
            self.ml.delete_mass_from_masslist(self, self.ml.currently_hovered.value())
            xlims, ylims = self.vb.viewRange()
            pyqtgraph_objects.redraw_localfit(self, xlims)


def main():
    app = QtWidgets.QApplication(sys.argv)
    mainW = MainWindow()
    mainW.show()
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
