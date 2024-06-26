import numpy as np
import math
import h5py
import itertools
import workflows_pyeakfitter.pyqtgraph_objects as pyqtgraph_objects
import workflows_pyeakfitter.pyqt_objects as po
import pyqtgraph as pg
import PyQt5.QtCore as QtCore
import PyQt5.QtWidgets as QtWidgets
import ast
import re

def _load_masslist(Filename, nr_elements_masslistproposed):
    with h5py.File(Filename, "r") as f:
        Masslist = f["MassList"]
        Elemental_compositions = f["ElementalCompositions"]
        Masses = np.array(Masslist[()])
        Element_numbers = np.array(Elemental_compositions[()])
        difference_nr_element_masslistloaded_masslistproposed =  nr_elements_masslistproposed - Element_numbers.shape[1]
        if difference_nr_element_masslistloaded_masslistproposed != 0:
            for i in range(0, difference_nr_element_masslistloaded_masslistproposed):
                Element_numbers = np.c_[Element_numbers, np.zeros(Element_numbers.shape[0])]
        Compound_names = np.array(get_names_out_of_element_numbers(Element_numbers))
        return Masses,Element_numbers, Compound_names

def make_isotope(mass, element_composition, Nr_isotopes, nr_elements_masslistproposed):
    '''Create the Masses, Elemental compositions and Isotopic abundances of isotopes (with 1,2 C13 and O18 right now) dor a given input compound

    Parameters
    ----------
    mass : float
        mass of the compound you want to create the isotopes of
    element_composition : list
        element composition of the compound you want to create the isotopes of (must match the definition in Masslist() with the compound order given in Masslist.names_elements
    Nr_isotopes: int
        Nr of isotopes you want to produce (in this case 3) has to fit to the structure of this function (to add isotopes check the instruction below)
    nr_elements_masslistproposed: int
        In the Masslist() a number of elements in the masslist are proposed (noramlly 8 if you add a new element you want to suggestion it will be one more.

    Returns
    -------
    list of np.arrays:
        1st array: (1,Nr_isotopes)
            Masses of isotopes
        2nd array: (1,Nr_isotopes,nr_elements_masslistproposed)
            Element numbers of the isotopes
    dict:
        keys: "IsotopicAbundance" : array: (1,Nr_isotopes) with isotopic abundances

    to add a new Isotope add another block of the following:
    1) change Nr_isotopes in Masslist() to Nr_isotopes+1
    2) add an Isotope element the same that you would do with a normal element (name it eg. O17)
    3) add the following at the end of this function
    if element_composition[element_composition == x ] > 0:              x = str of the Element you want to add an isotope for
        IsotopeMass[y] = mass - melement + miso  # contains one isotope    y = position of Isotope in list (probaly Nr_isotopes+1 if you add new isotope); melement = mass of element; miso = mass of isotope
        n, k = (element_composition[element_composition == x ], 1)      x = str of the Element you want to add an isotope for
        IsotopicAbundance[0] = math.comb(n,k) * isotopic_abund          isotopic_abund = isotopic Abundance can be taken out of https://www.sisweb.com/mstools/isotope.htm
        Isotope_Elemental_compositions[0,:] = element_composition - [1 if i == x else 0 for i in range(0,nr_elements)] + [1 if i == y else 0 for i in range(0,nr_elements)]
        x = position of element; y = position of isotope Subtract the element (eg. [1, 0, 0, 0, 0, 0, 0, 0] is a C) and add the Isotope (eg. [0, 1, 0, 0, 0, 0, 0, 0] is a C13)

    [IsotopeMasses, Isotope_Elemental_compositions], {"IsotopicAbundance" : IsotopicAbundance}
    '''

    IsotopeMass = np.full(Nr_isotopes, np.nan)
    IsotopicAbundance  = np.full(Nr_isotopes, np.nan)
    Isotope_Elemental_compositions = np.full((Nr_isotopes,nr_elements_masslistproposed), np.nan)
    nr_elements = len(element_composition)#.shape[]
    # make isotopes see: https://www.chem.ualberta.ca/~massspec/atomic_mass_abund.pdf
    if element_composition[0] > 0:  # if the element contains carbons we make an isotope
        IsotopeMass[0] = mass - 12 + 13.003355  # contains one isotope
        n, k = (int(element_composition[0]), 1)
        IsotopicAbundance[0] = math.comb(n,k) * 0.010816  # every C atom has a chance of 1.08% to be an isotope taken out of https://www.sisweb.com/mstools/isotope.htm
        Isotope_Elemental_compositions[0,:] = element_composition - [1 if i == 0 else 0 for i in range(0,nr_elements)] + [1 if i == 1 else 0 for i in range(0,nr_elements)]  # the composition is one less C atom, on more C13

    if element_composition[0] > 1:  # if it contains more than carobons there is a likelyhood, that the molecule contains 2 C13
        IsotopeMass[1] = IsotopeMass[0] - 12 + 13.003355
        n, k = (int(element_composition[0]), 2)
        IsotopicAbundance[1] = math.comb(n,k) * 0.010816 ** 2  # binomial coeficient since we have bin(n,2) possibilities to of 2 out n C atoms atoms to be C13
        Isotope_Elemental_compositions[1,:] = element_composition - [2 if i == 0 else 0 for i in range(0,nr_elements)] + [2 if i == 1 else 0 for i in range(0,nr_elements)]  # the composition is 2 less C atom, 2 more C13
    # if it contains an oxygen
    if element_composition[5] > 0:
        IsotopeMass[2] = mass - 15.99492 + 17.99916
        n, k = (int(element_composition[5]), 1)
        IsotopicAbundance[2] = math.comb(n, k) * 0.00205      #abundance out of https://en.wikipedia.org/wiki/Isotopes_of_oxygen
        Isotope_Elemental_compositions[2, :] = element_composition - [1 if i == 5 else 0 for i in range(0,nr_elements)] + [1 if i == 6 else 0 for i in range(0,nr_elements)]
    # if it contains sulfur
    if element_composition[7] > 0:
        IsotopeMass[3] = mass -	31.9720711 + 33.96786
        # n, k = (element_composition[7], 1)# because it is only one S we donot need it
        IsotopicAbundance[3] = element_composition[7] * 0.0425          #out of https://en.wikipedia.org/wiki/Isotopes_of_sulfur
        Isotope_Elemental_compositions[3,:] = element_composition - [1 if i == 7 else 0 for i in range(0,nr_elements)] + [1 if i == 8 else 0 for i in range(0,nr_elements)]

    Isotope_compound_names = np.array([get_names_out_of_element_numbers(isotope) for isotope in Isotope_Elemental_compositions])
    return IsotopeMass, IsotopicAbundance, Isotope_Elemental_compositions, Isotope_compound_names

def _load_isotopes(masslist, Nr_isotopes,nr_elements_masslistproposed):
    # here it is important, that the index in the isotopes is always the same as the index in the masslist
    Isotope_Elemental_compositions = np.full((masslist.masses.shape[0], Nr_isotopes, masslist.element_numbers.shape[1]), np.nan)
    IsotopeMasses = np.full((masslist.masses.shape[0], Nr_isotopes), np.nan)
    IsotopicAbundance = np.full((masslist.masses.shape[0], Nr_isotopes), np.nan)
    Compound_names =  np.full((masslist.masses.shape[0], Nr_isotopes), '',dtype='U20')

    for i, (mass, element_composition) in enumerate(zip(masslist.masses, masslist.element_numbers)):
        IsotopeMasses[i,:],IsotopicAbundance[i,:],Isotope_Elemental_compositions[i,:,:], Compound_names[i, :]= make_isotope(mass, element_composition, Nr_isotopes, nr_elements_masslistproposed)

    return [IsotopeMasses, Isotope_Elemental_compositions,Compound_names], {"IsotopicAbundance" : IsotopicAbundance}


#
def _load_suggestions(Mass_suggestions_range_numbers, masses_elements, filtersanemasses = True):
    Masses_elements = masses_elements
    Listofranges = [Mass_suggestions_range_numbers[key] for key in Mass_suggestions_range_numbers]
    Element_numbers = np.array(list(itertools.product(*Listofranges)))
    Masses = np.sum(
        Element_numbers * Masses_elements, axis=1)
    sortperm = np.argsort(Masses)
    Masses = Masses[sortperm]
    Element_numbers = np.array(Element_numbers)[sortperm]
    H_to_C_lower = 1.3
    H_to_C_upper = 3.3
    O_to_C_upper = 2
    if filtersanemasses:
        #0 = C, 2 = H, 4 = N, 5 = 0, 7 = S
        selMasses_mask = np.full(Masses.shape, True)
        selMasses_mask = selMasses_mask & ((Element_numbers[:, 2] > H_to_C_lower * Element_numbers[:, 0]) | (Masses <40)) # H:C > 1.3 for masses over 40
        including_NH4 = (Element_numbers[:, 4] >= 1) & (Element_numbers[:, 2] >= 3)
        including_NH4_H_number_sub_4 = including_NH4 & (Element_numbers[:, 2] - 3 < H_to_C_upper * Element_numbers[:, 0])
        selMasses_mask = selMasses_mask & (Element_numbers[:, 3] == 1) # only include compounds which have a H+ in it
        selMasses_mask = selMasses_mask & ((Element_numbers[:, 2] < H_to_C_upper * Element_numbers[:, 0]) | (Masses <40) | including_NH4_H_number_sub_4) # H:C <  3.3 for masses over 40 or H-3:C <  3.3 for compound including NH3H+
        selMasses_mask = selMasses_mask & ((Element_numbers[:, 5] < O_to_C_upper * Element_numbers[:, 0]) | (Masses <40)) # O:C < 1.5 # 2
        Masses = Masses[selMasses_mask]
        Element_numbers = Element_numbers[selMasses_mask,:]
        # Masses_thrown = Masses[~selMasses_mask]
        # Element_numbers_thrown = Element_numbers[~selMasses_mask,:]
        Compound_names = np.array(get_names_out_of_element_numbers(Element_numbers))


    return [Masses,Element_numbers,Compound_names],{"Mass_suggestions_ranges" : Mass_suggestions_range_numbers}


class _Data():
    '''
    Basket object for Suggestions, Masslist and Isotopes (suggisomass) and all functions that alter these
    -to add a new element to suggest, change the variables names_elements masses_elements mass_suggestions_ranges with the information on the compound
    -to change sane mass rules, go to load_suggestions function (which compounds are suggested depending on some ratio eg. C:O ratio)
    -to add a new isotope, follow the recipe in the make_isotope function

    Parameters
    ----------
    Filename : str
        The filepath of the _result file where the masslist is in

    Attributes
    ----------
    element_numbers : np.array (-, Masslist.nr_elements)
        Element numbers of suggisomass entries
    masses: np.array (-)
        masses of suggisomass entries. If the Data are isotopes the dimensions have to fit to (len(Masslist.masslist.masses),Nr_isotopes )
    mass_suggestions_ranges: list of tuples (1,nr_elements)
        For each element give a range of which number you want to include in the suggestions. Only filled suggestions
    isotopic_abundance: np.array (len(Masslist.masslist.masses), Masslist.Nr_isotopes)
        Isotopic abundances
    mass_coefficients: np.array (len(Masslist.masslist.masses))
        holds the mass coefficients calculated by the local fits
    current_lines: list
        Holds all InfiniteLine_Mass objects that are currently plotted
    current_element_names: list
        Element numbers of current InfiniteLine_Mass objects

    '''


    def __init__(self,Masses,Element_numbers,Compound_names,Mass_suggestions_ranges = [], IsotopicAbundance = []):
        # initialize masslist
        self.element_numbers = Element_numbers
        self.masses = Masses
        self.compound_names = Compound_names
        # self.current_element_names = []
        self.current_lines = []
        self.mass_coefficients = np.full(Masses.shape[0],1.)
        self.isotopic_abundance = IsotopicAbundance
        self.mass_suggestions_ranges = Mass_suggestions_ranges
def read_masslist_from_hdf5_produce_iso_sugg(Filename):
    '''disentagle masslist read in from .hdf5 and production of sugg and iso so that import of ml is possible'''
    names_elements = Mass_iso_sugglist.names_elements #iodine, silizium
    nr_elements = len(names_elements)
    masslist = _Data(*_load_masslist(Filename, nr_elements))

    ml = Mass_iso_sugglist(masslist)
    return ml

class Mass_iso_sugglist():
    '''
    Basket object for Suggestions, Masslist and Isotopes and all functions that alter these
    -to add a new element to suggest, change the variables names_elements masses_elements mass_suggestions_ranges with the information on the compound
    -to change sane mass rules, go to load_suggestions function (which compounds are suggested depending on some ratio eg. C:O ratio)
    -to add a new isotope, follow the recipe in the make_isotope function

    Parameters
    ----------
    Filename : str
        The filepath of the _result file where the masslist is in

    Attributes (only the most important)
    ----------
    suggestions : _Data
        _Data object with all information on masssuggestions
    masslist: _Data
        _Data object with all information on masslist masses
    isotopes: _Data
        _Data object with all information on isotopes
    names_elements: list (1,nr_elements)
        names of elements you want to suggest
    masses_elements: list (1,nr_elements)
        Masses of elements defined in names_elements in the same order
    order_of_letters: list (1,nr_elements)
        When giving a name string you define here how the letter of names_elements is reordered in the name string
    mass_suggestions_ranges: list of tuples (1,nr_elements)
        For each element give a range of which number you want to include in the suggestions
    isotopes_range_back: int
        For the calculation of the mass coefficients for the local fit define here how many unit masses back you want to include isotopes
    nr_isotopes: int
        How many isotopes do you incorporate
    currently_hovered: list
        holds the InfiniteLineMass objects when you hover over them


    Methods
    ----------
    reinit
    add_suggestion_to_sugglist
    add_mass_to_masslist
    delete_mass_from_masslist
    redo_qlist

    '''

    names_elements = ["C", "C(13)", "H", "H+", "N", "O", "O(18)", "S","S(34)", "I", "Si"] #iodine, silizium
    isotopes_to_include = ["C(13)","2C(13)","O(18)","S(34)"]
    order_of_letters = [0, 1, 2, 9, 4, 5, 6, 7 ,8 , 10 ,3]
    masses_elements = np.array([12,
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
    mass_suggestions_ranges = [(0, 10), (0, 0), (0, 20), (1, 1), (0, 1), (0, 5), (0, 0), (0, 1),(0, 0), (0, 1), (0, 0)]  # always in the order C C13 H H+ N O, O18 S in the first place would be C number of 0 to 10
    co = po.Config()
    old_mass_suggestions_numbers = co.read_from_config("ranges", "lastrangesettings")
    try:
        old_mass_suggestions_numbers = ast.literal_eval(old_mass_suggestions_numbers)
        mass_suggestions_numbers = old_mass_suggestions_numbers
    except:
        mass_suggestions_numbers = {}
        for i,key in enumerate(names_elements):
            mass_suggestions_numbers[key] = list(range(mass_suggestions_ranges[i][0],mass_suggestions_ranges[i][1]+1))
        # order ["C", "C13", "H", "H+", "N", "O", "O18", "S", ]
    isotopes_range_back = 2 # isotopes range 2 Masses further (important for mass coefficients)
    nr_isotopes = len(isotopes_to_include)  #right now we consider 3 isotopes: Isotope with 1 or 2 C13 and Isotope with 1 O18
    nr_elements = len(names_elements)
    def __init__(self, masslist):
        #try it with old suggestion numbers, if this doesnot work go to default
        try:
            args, kwargs = _load_suggestions(self.mass_suggestions_numbers, masses_elements = self.masses_elements)
        except Exception as error:
            mass_suggestions_numbers = {}
            for i, key in enumerate(self.names_elements):
                self.mass_suggestions_numbers[key] = list(
                    range(self.mass_suggestions_ranges[i][0], self.mass_suggestions_ranges[i][1] + 1))
            args, kwargs = _load_suggestions(self.mass_suggestions_numbers, masses_elements = self.masses_elements)
            print(f"Old suggestion numbers yielded an error {error}")
        self.suggestions = _Data(*args, **kwargs)
        self.masslist = masslist
        args, kwargs = _load_isotopes(self.masslist, self.nr_isotopes,self.nr_elements)
        self.isotopes = _Data(*args, **kwargs)
        self.currently_hovered = []
    def reinit_old_sugg_ranges(self):
        self.mass_suggestions_numbers = {}
        for i, key in enumerate(self.names_elements):
            self.mass_suggestions_numbers[key] = list(
                range(self.mass_suggestions_ranges[i][0], self.mass_suggestions_ranges[i][1] + 1))
        self.reinit_suggestions()
    def reinit_suggestions(self):
        '''Reinitiate the basket object

        Parameters
        ----------
        Filename : str
            The filepath of the _result file where the masslist is in

        Returns
        -------
        None
        '''
        args, kwargs = _load_suggestions(self.mass_suggestions_numbers, masses_elements = self.masses_elements)
        self.suggestions = _Data(*args, **kwargs)

    def add_suggestion_to_sugglist(self, parent, compoundelements):
        '''Add a new compound to the suggestion _Data object, redraw the InfinitLineMass objects, so that it will be shown on the plot and zoom to the mass of the compound

        Parameters
        ----------
        parent : object
            Mainwindow object where the Line will be drawn
        compoundelements : list
            Has to fit the notation established in Masslist()

        Returns
        -------
        None
        '''


        if len(compoundelements) == len(self.names_elements):
            mass = np.sum(np.array(compoundelements) * self.masses_elements)
            xlims, ylims = parent.vb.viewRange()
            parent.vb.setXRange(xlims[0], xlims[0] + 0.2)
            parent.jump_to_mass(float(mass))

            if not (self.suggestions.element_numbers == compoundelements).all(axis=1).any():
                # add to suggestion list
                self.suggestions.element_numbers = np.vstack([self.suggestions.element_numbers,compoundelements])
                self.suggestions.masses = np.append(self.suggestions.masses,mass)
                this_compound_name = get_names_out_of_element_numbers(compoundelements)
                self.suggestions.compound_names = np.append(self.suggestions.compound_names,this_compound_name)
                compound_name = get_names_out_of_element_numbers(compoundelements)
                print("add mass ", mass, ",", compound_name ,this_compound_name, "to suggestionslist")

                sortperm = np.argsort(self.suggestions.masses)
                self.suggestions.masses = self.suggestions.masses[sortperm]
                self.suggestions.element_numbers = self.suggestions.element_numbers[sortperm]
                self.suggestions.compound_names = self.suggestions.compound_names[sortperm]

                pyqtgraph_objects.redraw_vlines(parent,parent.graphWidget, xlims)

                pyqtgraph_objects.highlight_mass_vline(parent,mass,compound_name)



    def add_mass_to_masslist(self, parent, mass):
        '''Add the given mass to the masslist _Data object delete the corresponding mass in the suggestion _Data object and redraw the InfinitLineMass objects, so that it will be shown on the plot.

        Parameters
        ----------
        parent : object
            Mainwindow object where the Line will be drawn
        mass : float
            mass of the compound you want to add. If the mass is also in the suggestions you will also get element numbers

        Returns
        -------
        None
        '''

        if mass not in self.masslist.masses:
            self.masslist.masses = np.append(self.masslist.masses,mass)
            if mass in self.suggestions.masses:
                element_numbers_this = self.suggestions.element_numbers[np.where(self.suggestions.masses == mass)]
                self.masslist.element_numbers = np.append(self.masslist.element_numbers, element_numbers_this, axis=0)
                self.masslist.compound_names = np.append(self.masslist.compound_names,get_names_out_of_element_numbers(element_numbers_this))
                isotope_mass_this, isotopic_abundance_this, isotope_element_numbers_this, isotope_compound_names = make_isotope(mass, element_numbers_this.flatten(), self.nr_isotopes, self.nr_elements)
                self.isotopes.masses = np.vstack([self.isotopes.masses, isotope_mass_this])
                self.isotopes.isotopic_abundance = np.vstack([self.isotopes.isotopic_abundance, isotopic_abundance_this])
                self.isotopes.element_numbers = np.vstack([self.isotopes.element_numbers, np.expand_dims(isotope_element_numbers_this, axis= 0)])
                self.isotopes.compound_names = np.vstack([self.isotopes.compound_names, isotope_compound_names])

                print("add mass ", mass, ",", get_names_out_of_element_numbers(element_numbers_this.flatten()) ,
                      "with isotpes ", isotope_mass_this, [get_names_out_of_element_numbers(x) for x in isotope_element_numbers_this], "to masslist")

            else: # if it is not in the suggestions we cannot show isotopes
                self.masslist.element_numbers = np.append(self.masslist.element_numbers, [[0]*len(self.names_elements)], axis=0)
                self.masslist.compound_names = np.append(self.masslist.compound_names, '')
                self.isotopes.masses = np.vstack([self.isotopes.masses, [np.nan]*self.nr_isotopes])
                self.isotopes.isotopic_abundance = np.vstack([self.isotopes.isotopic_abundance, [np.nan]*self.nr_isotopes])
                self.isotopes.element_numbers = np.vstack([self.isotopes.element_numbers, [[[np.nan]*self.nr_elements]*self.nr_isotopes]])
                self.isotopes.compound_names = np.vstack([self.isotopes.compound_names, ['']*self.nr_isotopes])
                print("add mass ", mass, "to masslist")


            sortperm = np.argsort(self.masslist.masses)
            self.masslist.masses = self.masslist.masses[sortperm]
            self.masslist.element_numbers = self.masslist.element_numbers[sortperm]
            self.masslist.compound_names = self.masslist.compound_names[sortperm]

            self.isotopes.masses = self.isotopes.masses[sortperm]
            self.isotopes.isotopic_abundance = self.isotopes.isotopic_abundance[sortperm]
            self.isotopes.element_numbers = self.isotopes.element_numbers[sortperm]
            self.isotopes.compound_names = self.isotopes.compound_names[sortperm]


            #delete in suggetions -> Problem danach ist es ganz weg
            index_of_deletion = np.where(self.suggestions.masses == mass)
            self.suggestions.masses = np.delete(self.suggestions.masses, index_of_deletion)
            self.suggestions.element_numbers = np.delete(self.suggestions.element_numbers, index_of_deletion, axis = 0)
            self.suggestions.compound_names = np.delete(self.suggestions.compound_names, index_of_deletion)
            xlims, ylims = parent.vb.viewRange()
            pyqtgraph_objects.redraw_vlines(parent,parent.graphWidget, xlims)
            self.redo_qlist(parent.masslist_widget)

    def delete_mass_from_masslist(self, parent, mass):
        '''Delete the given mass in the masslist _Data object, add the corresponding mass to the suggestion _Data object, if there are any element number attached to it and redraw the InfinitLineMass objects, so that it will be shown on the plot.

        Parameters
        ----------
        parent : object
            Mainwindow object where the Line will be drawn
        mass : float
            mass of the compound you want to delete

        Returns
        -------
        None
        '''
        print(f"Try to delete Mass {mass} in masslist")
        if np.any(np.isclose(self.masslist.masses, mass, atol=0.000001)):
            #delete in masses
            index_of_deletion = np.where(self.masslist.masses == mass)

            #first append it to suggestions only if we have a compound formual attached to it
            if np.any(self.masslist.element_numbers[index_of_deletion]):
                if mass not in self.suggestions.masses:
                    self.suggestions.masses = np.append(self.suggestions.masses, mass)
                    self.suggestions.element_numbers = np.append(self.suggestions.element_numbers, self.masslist.element_numbers[index_of_deletion], axis=0)
                    self.suggestions.compound_names = np.append(self.suggestions.compound_names, self.masslist.compound_names[index_of_deletion])
                    sortperm = np.argsort(self.suggestions.masses)
                    self.suggestions.masses = self.suggestions.masses[sortperm]
                    self.suggestions.element_numbers = self.suggestions.element_numbers[sortperm]
                    self.suggestions.compound_names = self.suggestions.compound_names[sortperm]

            print("delete mass ", mass, ",", get_names_out_of_element_numbers(self.masslist.element_numbers[index_of_deletion].flatten()) ,"from masslist")
            self.masslist.masses = np.delete(self.masslist.masses, index_of_deletion)
            self.masslist.element_numbers = np.delete(self.masslist.element_numbers, index_of_deletion, axis = 0)
            self.masslist.compound_names = np.delete(self.masslist.compound_names, index_of_deletion)
            self.isotopes.masses = np.delete(self.isotopes.masses,index_of_deletion,axis = 0)
            self.isotopes.isotopic_abundance = np.delete(self.isotopes.isotopic_abundance,index_of_deletion,axis = 0)
            self.isotopes.element_numbers = np.delete(self.isotopes.element_numbers,index_of_deletion,axis = 0)
            self.isotopes.compound_names = np.delete(self.isotopes.compound_names, index_of_deletion,axis = 0)
            print("Redraw")
            xlims, ylims = parent.vb.viewRange()
            pyqtgraph_objects.redraw_vlines(parent,parent.graphWidget,xlims)
            self.redo_qlist(parent.masslist_widget)
        else:
            print("not found in masslist")

    def redo_qlist(self,qlist):
        '''Update the List on the right side of the Plot

        Parameters
        ----------
        qlist : QtWidgets.QListWidget

        Returns
        -------
        None
        '''
        qlist.clear()
        for mass,compound_name in zip(self.masslist.masses, self.masslist.compound_names):
            qlist.addItem(str(round(mass,6)) + "  " + compound_name)
    def check_whether_suggmass_nearby(self,mass,suggestions,threshold_closeness):
        differences_suggmasses_to_value = np.abs(suggestions.masses - mass)
        close_suggmasses_differences = differences_suggmasses_to_value[differences_suggmasses_to_value < threshold_closeness]
        close_suggmasses = suggestions.masses[differences_suggmasses_to_value < threshold_closeness]
        print(f"Close suggestions:{close_suggmasses}")
        if close_suggmasses.shape[0] > 0:
            closest_suggmass = close_suggmasses[np.argmin(close_suggmasses_differences)]
            print(f"close to suggestion {closest_suggmass}")
            return closest_suggmass
        else:
            print("No suggestion Mass near")
            return mass

class Spectrum():
    '''
    Basket object for the meanspectrum, min and max spectrum, subspectra, the local fits and all function that alter these.

    Parameters
    ----------
    Filename : str
        The filepath of the _result file where the spectra are in

    Attributes (only the most important)
    ----------
    sum_specs: np.array(number of timestamps in _result file, nr of subspectra)
        Baseline corrected Subspectra
    spectrum: np.array(number of timestamps in _result file)
        Baseline corrected mean spectrum
    spectrum_max: np.array(number of timestamps in _result file)
        Baseline corrected maximum spectrum
    spectrum_max: np.array(number of timestamps in _result file)
        Baseline corrected minimum spectrum
    massaxis: np.array(number of massaxis points in _result file)

    peakshape: np.array(nr of mean peakshapes, 401)
        average peakshapes over some massrange out of _result file
    peakshapemiddle: np.array(nr of mean peakshapes)
        middle of massrange for the peakshapes
    peakshapeborders: np.array(nr of mean peakshapes+ 1)
        boarders of massranges for the peakshapes
    current_local_fit: list of PlotItem
        current Local fit
    current_local_fit_masses: list
        masses influencing the current local fit


    Methods
    ----------
    make_singlepeak
    get_mass_coefficients

    '''

    def __init__(self, filename):
        subspectra_limit=50
        with h5py.File(filename, "r") as f:
            self.sum_specs_ds = f["SumSpecs"]
            self.specs_times = f["AvgStickCpsTimes"]
            if self.sum_specs_ds.shape[0] > subspectra_limit:
                n = int(round(self.sum_specs_ds.shape[0]/subspectra_limit))
                print(f"Too many subspectra {self.sum_specs_ds.shape[0]}, take only {subspectra_limit}")
                nthrow = slice(None, None, n)
                self.sum_specs = self.sum_specs_ds[nthrow,:]
                self.specs_times = self.specs_times[nthrow]
            else:
                self.sum_specs = self.sum_specs_ds[()]
                self.specs_times = self.specs_times[()]
            self.specs_times = np.array([np.datetime64(int(ts), 's') for ts in self.specs_times])

            self._baselines_ds = f["BaseLines"][()]
            if self._baselines_ds.shape[0] > subspectra_limit:
                n = int(round(self._baselines_ds.shape[0]/subspectra_limit))
                nthrow = slice(None, None, n)
                self._baselines = self._baselines_ds[nthrow,:]
            else:
                self._baselines = self._baselines_ds[()]
            self.sum_specs = self.sum_specs - self._baselines
            self.spectrum = f["AvgSpectrum"][()]
            self._avg_baseline = f["AvgBaseline"][()]
            self.spectrum = self.spectrum - self._avg_baseline
            self.spectrum_max = f["SumSpecMax"][()]
            self.spectrum_max = self.spectrum_max- self._avg_baseline
            self.spectrum_min = f["SumSpecMin"][()]
            self.spectrum_min = self.spectrum_min- self._avg_baseline
            self.massaxis = f["MassAxis"][()]
            self.peakshape = f["MassDepPeakshape"][()]
            self.peakshapemiddle = f["MassDepPeakshapeCenterMasses"][()]#
        self.peakshapeborders = self._init_peakshapeborders()
        self.current_local_fit = []
        self.current_local_fit_init = False
        self.current_local_fit_masses = []
        self.current_subspectrum_time = self.specs_times[0]
    def make_singlepeak(self, mass, massaxis_this_zoom):
        '''Make a single peak around a given mass with given massaxis points and interpolated peakshape to the given mass

        Parameters
        ----------
        mass: float
            Mass the maximum of the peakshape is around
        massaxis_this_zoom: np.array()
            Massaxis points to interpolate the single peak to

        Returns
        -------
        massaxis_this_zoom: np.array()
            same as input
        peakshape_interpolated: np.array(massaxis_this_zoom.shape)
            new peakshape around mass

        '''
        # print("make single peak")
        peakshape_index_low = min(range(len(self.peakshapemiddle)), key=lambda i: abs(self.peakshapemiddle[i] - mass) if self.peakshapemiddle[i] < mass else float('inf'))
        ind_peak, deviation = self._find_nearest(self.massaxis, mass)
        lowind = ind_peak - 200
        highind = ind_peak + 201
        peakshape_massaxis_this_mass = self.massaxis[lowind:highind] -deviation
        if mass < self.peakshapemiddle[0] or mass > self.peakshapemiddle[-1]:
            peakshape_this = self.peakshape[peakshape_index_low]
        else:
            # the mass is between peakshape_index and peakshape_index + 1
            dx = mass - self.peakshapemiddle[peakshape_index_low]
            d = self.peakshapemiddle[peakshape_index_low + 1] - self.peakshapemiddle[peakshape_index_low]
            fact = dx/d #this factor is 0 if mass is near the lower bound and 1 if it is near the higher bound
            # print(f"fact {fact} between {self.peakshapemiddle[peakshape_index_low]}, {self.peakshapemiddle[peakshape_index_low +1]}")
            peakshape_this = self.peakshape[peakshape_index_low] * (1-fact) + self.peakshape[peakshape_index_low + 1] * fact
        if peakshape_massaxis_this_mass.shape[0] < peakshape_this.shape[0]:
        # if the massaxis is to short (at the end of the spectum) extend the massaxis
            initial_length = peakshape_massaxis_this_mass.shape[0]
            elements_needed = peakshape_this.shape[0] - initial_length
            step_size = peakshape_massaxis_this_mass[-1] - peakshape_massaxis_this_mass[-2]
            additional_elements = np.arange(peakshape_massaxis_this_mass[-1]+step_size,
                                            peakshape_massaxis_this_mass[-1]+ (elements_needed + 1) * step_size,
                                            step_size)
            extended_list = np.concatenate((peakshape_massaxis_this_mass, additional_elements))
            peakshape_massaxis_this_mass = extended_list

        peakshape_interpolated = np.interp(massaxis_this_zoom, peakshape_massaxis_this_mass, peakshape_this,left= 0, right= 0)

        return massaxis_this_zoom, peakshape_interpolated

    def _find_nearest(self, array, value):
        array = np.asarray(array)
        idx = (np.abs(array - value)).argmin()
        deviation = array[idx] - value
        return idx, deviation

    def _init_peakshapeborders(self):
        peakshapeborders= [(self.peakshapemiddle[i] + self.peakshapemiddle[i + 1]) / 2 for i in range(len(self.peakshapemiddle) - 1)]
        peakshapeborders.insert(-1, self.massaxis[-1])
        peakshapeborders.insert(0, 0)
        return peakshapeborders

    def get_mass_coefficients(self, range, ml):
        '''Make singlepeaks for all masslist masses and isotopes in range, recalculate the coefficient for the best fit

        Parameters
        ----------
        range: tupel
            X- range of current view
        ml: Masslist object
            The Masslist object defined in MainWindow

        Returns
        -------
        massaxis_in_range: tupel
            same as input
        local_fit: np.array()
            summed up all singlepeaks of masslist masses and isotopes scaled by their coefficients
        coefficients: np.array(nr_of_masses_in_range)
            All coefficients influencing the current view
        A: np.array(local_fit,nr_of_masses_in_range)
            All single peak fits => A*coefficient gives a matrix which has all scaled single peaks in its columns

        '''

        isotopes_range = ml.isotopes_range_back  # how many isotopes back we want to include
        margin = 0.5
        massaxis_range = [range[0] - isotopes_range - margin,
                          range[1] + margin]  # in this range we consider other peaks to influence the peakshape (-2.3 because of isotopes)
        massaxis_mask = (self.massaxis > massaxis_range[0]) & (self.massaxis < massaxis_range[1])
        massaxis_in_range = self.massaxis[massaxis_mask]
        spectrum_in_range = self.spectrum[massaxis_mask]

        masslist_mask = (ml.masslist.masses > massaxis_range[0]) & (ml.masslist.masses < massaxis_range[1])
        masslist_masses_in_range = ml.masslist.masses[masslist_mask]
        isotopes_in_range = ml.isotopes.masses[masslist_mask]
        isotopicabundance_in_range = ml.isotopes.isotopic_abundance[masslist_mask]
        # print("isotopes in range", isotopes_in_range)

        list_isotopes_in_range = np.hstack([masslist_masses_in_range[:, np.newaxis], isotopes_in_range])
        # print("mass and isotope in range", list_isotopes_in_range)
        A = np.empty((massaxis_in_range.size, masslist_masses_in_range.size))

        for i, iso_list_mass in enumerate(list_isotopes_in_range):
            peakshape = np.full(spectrum_in_range.shape, 0)  # added up peakshape for the mass and its isotopes
            for j, mass in enumerate(iso_list_mass):
                if not np.isnan(mass):
                    massaxis, peakshape_one_mass = self.make_singlepeak(mass, massaxis_in_range)
                    if j == 0:  # if the mass is a non isotope
                        peakshape = peakshape + peakshape_one_mass
                    else:
                        peakshape = peakshape + peakshape_one_mass * isotopicabundance_in_range[i, j - 1]

            A[:, i] = peakshape
        coefficients, *otherinfo = np.linalg.lstsq(A, spectrum_in_range,rcond=None)
        #problem hier: größe der mass coefficient ändet sich, wenn man eine masses hinzufügt
        # ml.masslist.mass_coefficients[masslist_mask] = coefficients
        # ml.isotopes.mass_coefficients[masslist_mask] = coefficients
        local_fit = np.sum(A*coefficients, axis = 1)
        return massaxis_in_range, local_fit,coefficients, A




def get_names_out_of_element_numbers(compound_array):
    # only if any compounds are in compound array give a string
    '''Get the compound name out of a compound array

    Parameters
    ----------
    compound_array : np.array (nr_elements, nr_compounds)
        corresponding to the rules used in Masslist object

    Returns
    -------
    compoundname_list:
        str if compound_array is (nr_elements, 1)
            compound name
        list if (nr_elements, nr_compounds)
            compound names
    '''

    compoundname_list = []
    names_elements = Mass_iso_sugglist.names_elements
    # modify the input array
    single_compound = False
    if len(compound_array.shape) == 1:
        single_compound = True
        compound_array = compound_array.reshape(1, compound_array.shape[0])
    compound_array_copy = compound_array.copy()

    if compound_array_copy.shape[1] < 9:
        # if we still donot have iodine etc take the reduce name list
        names_elements = np.array(["C", "C(13)", "H", "H+", "N", "O", "O(18)", "S"])
        order_of_letters = [0, 1, 2, 4, 5, 6, 7, 3]
    else:
        order_of_letters = Mass_iso_sugglist.order_of_letters
        names_elements = np.array(Mass_iso_sugglist.names_elements)

    for compound in compound_array_copy:
        if np.any(compound):
            compoundletters = ""
            including_NH4 = False
            if compound[names_elements == "H"].item() >= 3 and compound[names_elements == "N"].item() >= 1 and compound[names_elements == "H+"].item() == 1:
                including_NH4 = True
                compound[names_elements == "H"] = compound[names_elements == "H"].item()-3
                compound[names_elements == "N"] = compound[names_elements == "N"].item()-1
            for index, order in enumerate(order_of_letters):
                # before the last letter (H+) add a " "
                if index == len(order_of_letters)-1:
                    if including_NH4: #if the compound includes a NH3 add a NH4+ instead of H+
                        compoundletters += " NH3"
                    else:
                        compoundletters += " " #add a " " before the H+
                if compound[order] == 0:
                    pass
                if compound[order] == 1:
                    compoundletters += names_elements[order]
                if compound[order] > 1:
                    compoundletters += names_elements[order] + str(round(compound[order]))
            compoundname_list.append(compoundletters)
            if single_compound:
                return compoundletters
        else:
            if single_compound:
                return ""
            compoundname_list.append("")

    return compoundname_list


def get_element_numbers_out_of_names(namestring):
    '''Get the compound name out of a compound array

    Parameters
    ----------
    namestring : str characters and numbers in any order

    Returns
    -------
    mass: float
        mass of the compound
    element_numbers: np.array (nr_elemets)


    '''
    # first take out Si to not change exchange with S&I
    si_pattern = r'Si(\d+)?'
    numbers_si = re.findall(si_pattern, namestring)
    numbers_si = [1 if match == '' else int(match) for match in numbers_si]
    number_si = 0
    for x in numbers_si:
        number_si += x

    namestring = re.sub(si_pattern, "",namestring) # remove Si_x out of namestring
    namestring = namestring.lower()

    # if the namestring has + make it an ion
    ion = False
    if "+" in namestring:
        ion = True
        namestring = namestring.replace("+","")

    # prepare the namestring as a list of element and elementnumbers (eg. c3c(13)c to elements = [c,c(13)], numbers = [4,1]
    el_iso_pattern = r'([a-zA-Z](\(\d+\))?)(\d+)?'
    pattern_find = re.findall(el_iso_pattern, namestring) # gives out a list of tuples the first entry of the tuple is the element, the second the isotopenr and the third the number of this element
    el_numb_duplicates = [(entry[0],int(entry[2])) if entry[2] else (entry[0],1) for entry in pattern_find]
    el_numb = {}
    for entry in el_numb_duplicates:
        element,number = entry
        if element not in el_numb:
            el_numb[element] = number
        else:
            el_numb[element] += number
    elements = np.array(list(el_numb.keys()))
    numbers = np.array(list(el_numb.values()))

    # make the array out of the names Mass_iso_sugglist.names_elements
    names_elements = Mass_iso_sugglist.names_elements
    names_elements = np.array([x.lower() for x in names_elements])
    compound_array = np.array([0] * len(names_elements))
    for index,element in enumerate(names_elements):
        #make it lower, so that we have more freedom in writing
        if np.any(element == elements):
            compound_array[index] = numbers[element == elements][0]

    # if there is a Si add this
    compound_array[names_elements == "si"] = number_si

    # if there is + remove one H and add a H+
    # add a H+ and delete a H if it is ion
    if ion:
        compound_array[names_elements == "h"] = compound_array[names_elements == "h"] -1
        compound_array[names_elements == "h+"] = compound_array[names_elements == "h+"] + 1


    mass = np.sum(compound_array*Mass_iso_sugglist.masses_elements)
    return mass, compound_array


# ml = read_masslist_from_hdf5_produce_iso_sugg(r"D:\Uniarbeit 23_11_09\CERN\CLOUD16\arctic_runs\2023-11-09to2023-11-12\results\_result_avg.hdf5")
# sp = Spectrum(r"D:\Uniarbeit 23_11_09\CERN\CLOUD16\arctic_runs\2023-11-09to2023-11-12\results\_result_avg.hdf5")