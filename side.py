self.parent = parent
self.setWindowTitle("Select Mass Ranges")

# self.gridlayout.addWidget(QtWidgets.QLabel("Lower Limit"), 0, 1)
# self.gridlayout.addWidget(QtWidgets.QLabel("Upper Limit"), 0, 2)
self.labels = []
self.inputs = []
# self.mass_suggestions_ranges = parent.ml.mass_suggestions_ranges
names_elements = ["C", "C(13)", "H", "H+", "N", "O", "O(18)", "S", "I", "Si"]
mass_suggestions_ranges = [(0, 10), (0, 0), (0, 20), (1, 1), (0, 1), (0, 5), (0, 0), (0, 1), (0, 1), (
    0, 0)]  # always in the order C C13 H H+ N O, O18 S in the first place would be C number of 0 to 10
patternfindall = re.compile(r'(\d+)\s*-?\s*(\d+)?\s*&?\s*')
patternmatch = r'((\d+)\s*-?\s*(\d+)?\s*&?\s*)*'

regex_validator = RegExpValidator(r'^[A-Za-z0-9_]*$', self)