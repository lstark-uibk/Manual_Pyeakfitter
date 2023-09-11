import numpy as np
import math
import h5py
import itertools
import workflows.pyqtgraph_objects as pyqtgraph_objects
import timeit

def load_masslist(Filename):
    with h5py.File(Filename, "r") as f:
        Masslist = f["MassList"]
        Elemental_compositions = f["ElementalCompositions"]
        Masses = np.array(Masslist[()])
        Element_numbers = np.array(Elemental_compositions[()])

        return Masses,Element_numbers

# masslist = data(*load_masslist(filename))

def make_isotope(mass, element_composition):
    IsotopeMass = np.full(2, np.nan)
    IsotopicAbundance  = np.full(2, np.nan)
    Isotope_Elemental_compositions = np.full((2,8), np.nan)
    # make isotopes see: https://www.chem.ualberta.ca/~massspec/atomic_mass_abund.pdf
    if element_composition[0] > 0:  # if the element contains carbons we make an isotope
        IsotopeMass[0] = mass - 12 + 13.003355  # contains one isotope
        n, k = (element_composition[0], 1)
        IsotopicAbundance[0] = math.comb(n,k) * 0.010816  # every C atom has a chance of 1.08% to be an isotope taken out of https://www.sisweb.com/mstools/isotope.htm
        Isotope_Elemental_compositions[0,:] = element_composition - [1, 0, 0, 0, 0, 0, 0, 0] + [0, 1, 0, 0, 0, 0, 0,0]  # the composition is one less C atom, on more C13

    if element_composition[0] > 1:  # if it contains more than carobons there is a likelyhood, that the molecule contains 2 C13
        IsotopeMass[1] = IsotopeMass[0] - 12 + 13.003355
        n, k = (element_composition[0], 2)
        IsotopicAbundance[1] = math.comb(n,k) * 0.010816 ** 2  # binomial coeficient since we have bin(n,2) possibilities to of 2 out n C atoms atoms to be C13
        Isotope_Elemental_compositions[1,:] = element_composition - [2, 0, 0, 0, 0, 0, 0, 0] + [0, 2, 0, 0, 0, 0, 0,0]  # the composition is one less C atom, on more C13

    return IsotopeMass, IsotopicAbundance, Isotope_Elemental_compositions

def load_isotopes(masslist):
    # here it is important, that the index in the isotopes is always the same as the index in the masslist
    Isotope_Elemental_compositions = np.full((masslist.masses.shape[0], 2, masslist.element_numbers.shape[1]), np.nan)
    IsotopeMasses = np.full((masslist.masses.shape[0], 2), np.nan)
    IsotopicAbundance = np.full((masslist.masses.shape[0], 2), np.nan)

    for i, (mass, element_composition) in enumerate(zip(masslist.masses, masslist.element_numbers)):
        IsotopeMasses[i,:],IsotopicAbundance[i,:],Isotope_Elemental_compositions[i,:,:] = make_isotope(mass, element_composition)
    return [IsotopeMasses, Isotope_Elemental_compositions], {"IsotopicAbundance" : IsotopicAbundance}


#
# Mass_suggestions_ranges = [(0, 10), (0, 0), (0, 20), (1, 1), (0, 3), (0, 3), (0, 0), (0, 2)]  # always in the order C C13 H H+ N O, O18 S in the first place would be C number of 0 to 10
def load_suggestions(Mass_suggestions_ranges, filtersanemasses = True):
    Masses_elements = np.array([12,
                                13.00335,
                                1.00783,
                                1.007276,
                                14.00307,
                                15.99492,
                                17.99916,
                                31.97207
                                ]),

    Listofranges = [list(range(A[0], A[1] + 1)) for A in Mass_suggestions_ranges]
    Element_numbers = np.array(list(itertools.product(*Listofranges)))
    Masses = np.sum(
        Element_numbers * Masses_elements, axis=1)
    sortperm = np.argsort(Masses)
    Masses = Masses[sortperm]
    Element_numbers = np.array(Element_numbers)[sortperm]

    if filtersanemasses:
        selMasses_mask = np.full(Masses.shape, True)
        selMasses_mask = selMasses_mask & (Element_numbers[:, 2] > 1.3 * Element_numbers[:, 0]) | (Masses <40) # H:C > 1.3
        selMasses_mask = selMasses_mask & (Element_numbers[:, 2] < 2.2 * Element_numbers[:, 0]) | (Masses <40) # H:C < 2.2
        selMasses_mask = selMasses_mask & (Element_numbers[:, 5] < 2 * Element_numbers[:, 0]) | (Masses <40) # O:C < 1.5 # 2
        # selMasses_mask = selMasses_mask or (Element_numbers[:, 5] < 2 * Element_numbers[:, 0])    # O:C < 1.5 # 2
        Masses = Masses[selMasses_mask]
        Element_numbers = Element_numbers[selMasses_mask,:]


    return [Masses,Element_numbers],{"Mass_suggestions_ranges" : Mass_suggestions_ranges}


class Data():
    def __init__(self,Masses,Element_numbers,Mass_suggestions_ranges = [], IsotopicAbundance = []):
        # initialize masslist
        self.element_numbers = Element_numbers
        self.masses = Masses
        self.current_element_names = []
        self.current_lines = []
        self.mass_coefficients = np.full(Masses.shape[0],1.)
        self.isotopic_abundance = IsotopicAbundance
        self.mass_suggestions_ranges = Mass_suggestions_ranges


class Masslist():
    names_elements = ["C", "C13", "H", "H+", "N", "O", "O18", "S", ]
    order_of_letters = [0, 1, 2, 4, 5, 6, 7, 3]
    masses_elements = np.array([12,
                                13.00335,
                                1.00783,
                                1.007276,
                                14.00307,
                                15.99492,
                                17.99916,
                                31.97207
                                ]),
    isotopes_range_back = 2 # isotopes range 2 Masses further (important for mass coefficients)
    def __init__(self,Mass_suggestions_ranges, Filename):
        self.filename = Filename
        args, kwargs = load_suggestions(Mass_suggestions_ranges)
        self.suggestions = Data(*args, **kwargs)
        self.masslist = Data(*load_masslist(Filename))
        args, kwargs = load_isotopes(self.masslist)
        self.isotopes = Data(*args, **kwargs)
        self.currently_hovered = []

    def reinit(self, Mass_suggestions_ranges, Filename):
        self.__init__(Mass_suggestions_ranges, Filename)

    def add_mass_to_masslist(self, mass, parent):
        # add to masslist
        if mass not in self.masslist.masses:
            self.masslist.masses = np.append(self.masslist.masses,mass)
            if mass in self.suggestions.masses:
                element_numbers_this = self.suggestions.element_numbers[np.where(self.suggestions.masses == mass)]
                self.masslist.element_numbers = np.append(self.masslist.element_numbers, element_numbers_this, axis=0)
                isotope_mass_this, isotopic_abundance_this, isotope_element_numbers_this = make_isotope(mass, element_numbers_this.flatten())
                self.isotopes.masses = np.vstack([self.isotopes.masses, isotope_mass_this])
                self.isotopes.isotopic_abundance = np.vstack([self.isotopes.isotopic_abundance, isotopic_abundance_this])
                self.isotopes.element_numbers = np.vstack([self.isotopes.element_numbers, np.expand_dims(isotope_element_numbers_this, axis= 0)])

                print("add mass ", mass, ",", get_names_out_of_element_numbers(element_numbers_this.flatten()) ,
                      "with isotpes ", isotope_mass_this, [get_names_out_of_element_numbers(x) for x in isotope_element_numbers_this], "to masslist")

            else: # if it is not in the suggestions we cannot show isotopes
                self.masslist.element_numbers = np.append(self.masslist.element_numbers, [[0]*len(self.names_elements)], axis=0)
                self.isotopes.masses = np.vstack([self.isotopes.masses, [np.nan]*2])
                self.isotopes.isotopic_abundance = np.vstack([self.isotopes.isotopic_abundance, [np.nan]*2])
                self.isotopes.element_numbers = np.vstack([self.isotopes.element_numbers, [[[np.nan]*8]*2]])
                print("add mass ", mass, "to masslist")

            sortperm = np.argsort(self.masslist.masses)
            self.masslist.masses = self.masslist.masses[sortperm]
            self.masslist.element_numbers = self.masslist.element_numbers[sortperm]
            self.isotopes.masses = self.isotopes.masses[sortperm]
            self.isotopes.isotopic_abundance = self.isotopes.isotopic_abundance[sortperm]
            self.isotopes.element_numbers = self.isotopes.element_numbers[sortperm]

            xlims, ylims = parent.spectrumplot.getViewBox().viewRange()
            pyqtgraph_objects.redraw_vlines(parent)
            self.redo_qlist(parent.masslist_widget)

    def delete_mass_from_masslist(self, mass, parent):
        if mass in self.masslist.masses:
            #delete in masses
            index_of_deletion = np.where(self.masslist.masses == mass)
            print("delete mass ", mass, ",", get_names_out_of_element_numbers(self.masslist.element_numbers[index_of_deletion].flatten()) ,"from masslist")
            self.masslist.masses = np.delete(self.masslist.masses, index_of_deletion)
            self.masslist.element_numbers = np.delete(self.masslist.element_numbers, index_of_deletion, axis = 0)
            self.isotopes.masses = np.delete(self.isotopes.masses,index_of_deletion,axis = 0)
            self.isotopes.isotopic_abundance = np.delete(self.isotopes.isotopic_abundance,index_of_deletion,axis = 0)
            self.isotopes.element_numbers = np.delete(self.isotopes.element_numbers,index_of_deletion,axis = 0)

            xlims, ylims = parent.spectrumplot.getViewBox().viewRange()
            pyqtgraph_objects.redraw_vlines(parent)

    def redo_qlist(self,qlist):
        qlist.clear()
        for mass,element_numbers in zip(self.masslist.masses, self.masslist.element_numbers):
            qlist.addItem(str(round(mass,6)) + "  " + get_names_out_of_element_numbers(element_numbers))

class Spectrum():
    def __init__(self, filename):
        with h5py.File(filename, "r") as f:
            self.sum_specs = f["SumSpecs"][()]
            self.baselines = f["BaseLines"][()]
            self.sum_specs = self.sum_specs - self.baselines
            self.spectrum = f["AvgSpectrum"][()]
            self.avg_baseline = f["AvgBaseline"][()]
            self.spectrum = self.spectrum - self.avg_baseline
            self.spectrum_max = f["SumSpecMax"][()]
            self.spectrum_min = f["SumSpecMin"][()]
            self.massaxis = f["MassAxis"][()]
            self.peakshape = f["MassDepPeakshape"][()]
            self.peakshapemiddle = f["MassDepPeakshapeCenterMasses"][()]#
        self.peakshapeborders = self._init_peakshapeborders()
        self.current_local_fit = []
        self.current_local_fit_masses = []

    def make_singlepeak(self, mass, massaxis_this_zoom):
        peakshape_index = int(
            [i for i in range(len(self.peakshapeborders) - 1) if self.peakshapeborders[i] < mass < self.peakshapeborders[i + 1]][0])
        ind_peak, deviation = self._find_nearest(self.massaxis, mass)
        lowind = ind_peak - 200
        highind = ind_peak + 201
        peakshape_massaxis_this_mass = self.massaxis[lowind:highind] -deviation
        if mass < self.peakshapeborders[0] or self.peakshapeborders[-1]:
            peakshape_this = self.peakshape[peakshape_index]
        else:
            # the mass is between peakshape_index and peakshape_index + 1
            dx = mass - self.peakshapeborders[peakshape_index]
            d = self.peakshapeborders[peakshape_index] - self.peakshapeborders[peakshape_index + 1]
            fact = dx/d #this factor is 0 if mass is near the lower bound and 1 if it is near the lower bound
            peakshape_this = np.empty(self.peakshape[peakshape_index].shape)
            for i in range(peakshape_this.size):
                peakshape_this =np.append(peakshape_this, self.peakshape[i] * fact + self.peakshape[i+1] * (1 - fact))
                print("interpolate the peakshape, between")
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
        print("recalculate local fit")
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

        list_isotopes_in_range = np.hstack([masslist_masses_in_range[:, np.newaxis], isotopes_in_range])
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
    order_of_letters = Masslist.order_of_letters
    names_elements = Masslist.names_elements
    compoundletters = ""
    for order in order_of_letters:
        if compound_array[order] == 0:
            pass
        if compound_array[order] == 1:
            compoundletters += names_elements[order]
        if compound_array[order] > 1:
            compoundletters += names_elements[order] + str(round(compound_array[order]))
    return compoundletters



