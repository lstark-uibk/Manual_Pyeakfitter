# Manual_Pyeakfitter
Anaylze TOF spectra averaged by TOF-Tracer (https://github.com/lukasfischer83/TOF-Tracer2) to generate masslists. 

Rewritten Python version of Manual Peak Fitter by Lukas Fischer (https://github.com/lukasfischer83/peakFit) using PyQt5 (https://www.riverbankcomputing.com/software/pyqt/) and pyqtgraph (https://pyqtgraph.readthedocs.io/en/latest/)

## Installation with .exe file
It is possible to run the program from a .exe file from windows. This is most often not the newest Version and the current development is done in the python files of this repository. 

To run Manual Pyeakfitter with a .exe file:
- download the manual_pyeakfitter_distribution_windows.zip file. 
- Unzip it
- Run the manual_pyeakfitter.exe application

## Installation with Python
Running the Manual Pyeakfitter from Python give acces to the latest developments and makes it able to contribute.

### Requirements
Latest running on Python  3.11.4 

Needs packages:
PyQt5, pyqtgraph, pandas, numpy, h5py

Latest running versions:
- Pyqt   5.15.9 
- h5py   3.9.0 
- pyqtgraph 0.13.1

### Installation
On Pycharm with Git installed, add this project by Git -> Clone... -> Repository URL.
Insert the url: https://github.com/lstark-uibk/Manual_Pyeakfitter and select the directory you want to save it in.

Without PyCharm just download the repository and run it with your favourite Python interpreter.

To install the packages run in your anaconda prompt or python command line:
```
pip install pyqt5 pyqtgraph pandas numpy h5py
```
## License

[![CC BY-NC-SA 4.0][cc-by-nc-sa-shield]][cc-by-nc-sa]

This work is licensed under a
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License][cc-by-nc-sa].

[![CC BY-NC-SA 4.0][cc-by-nc-sa-image]][cc-by-nc-sa]

[cc-by-nc-sa]: http://creativecommons.org/licenses/by-nc-sa/4.0/
[cc-by-nc-sa-image]: https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png
[cc-by-nc-sa-shield]: https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg

2023, Leander Stark 


