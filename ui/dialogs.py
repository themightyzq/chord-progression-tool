from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QRadioButton, QButtonGroup, QGroupBox,
    QComboBox, QDialogButtonBox, QScrollArea, QWidget, QGridLayout, QSizePolicy, QPushButton
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

class EditChordModifiersDialog(QDialog):
    """
    Modern, well-aligned, scrollable dialog for editing chord modifiers.
    Extension, Inversion, Voicing, Arpeggiator Mode, and Note Length.
    """
    def __init__(self, parent, chord):
        super().__init__(parent)
        self.setWindowTitle("Edit Chord Modifiers")
        self.setModal(True)
        self.setMinimumWidth(540)
        self.setMaximumWidth(640)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.result = None

        font_header = QFont("Palatino" if QFont("Palatino").exactMatch() else "Georgia", 14, QFont.Bold)
        font_radio = QFont("Palatino" if QFont("Palatino").exactMatch() else "Georgia", 12)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll_contents = QWidget()
        main_layout = QVBoxLayout(scroll_contents)
        main_layout.setContentsMargins(32, 24, 32, 12)
        main_layout.setSpacing(18)

        ext_group = QGroupBox("Extension")
        ext_group.setFont(font_header)
        ext_group.setToolTip("Select a chord extension to add additional color or tension to the chord.")
        ext_layout = QGridLayout()
        ext_layout.setHorizontalSpacing(32)
        ext_layout.setVerticalSpacing(8)
        ext_group.setLayout(ext_layout)
        ext_options = ["None", "+6th", "+7th", "+9th", "sus2", "sus4"]
        ext_tooltips = [
            "No extension.",
            "Add a 6th interval to the chord.",
            "Add a 7th interval to the chord.",
            "Add a 9th interval to the chord.",
            "Suspend the 3rd and use the 2nd instead (sus2).",
            "Suspend the 3rd and use the 4th instead (sus4)."
        ]
        self.ext_radios = []
        ext_btn_group = QButtonGroup(self)
        for i, name in enumerate(ext_options):
            btn = QRadioButton(name)
            btn.setFont(font_radio)
            btn.setToolTip(ext_tooltips[i])
            ext_layout.addWidget(btn, i // 2, i % 2)
            ext_btn_group.addButton(btn)
            self.ext_radios.append(btn)
        main_layout.addWidget(ext_group)

        inv_group = QGroupBox("Inversion")
        inv_group.setFont(font_header)
        inv_group.setToolTip("Select a chord inversion to change which note is in the bass.")
        inv_layout = QVBoxLayout()
        inv_group.setLayout(inv_layout)
        inv_options = ["None", "Root", "1st", "2nd"]
        inv_tooltips = [
            "No inversion (root position).",
            "Root position (root note in the bass).",
            "1st inversion (third in the bass).",
            "2nd inversion (fifth in the bass)."
        ]
        self.inv_radios = []
        inv_btn_group = QButtonGroup(self)
        for i, name in enumerate(inv_options):
            btn = QRadioButton(name)
            btn.setFont(font_radio)
            btn.setToolTip(inv_tooltips[i])
            inv_layout.addWidget(btn)
            inv_btn_group.addButton(btn)
            self.inv_radios.append(btn)
        main_layout.addWidget(inv_group)

        voi_group = QGroupBox("Voicing")
        voi_group.setFont(font_header)
        voi_group.setToolTip("Select a voicing style to determine how the chord notes are distributed.")
        voi_layout = QVBoxLayout()
        voi_group.setLayout(voi_layout)
        voi_options = ["None", "Root", "Open", "Drop 2", "Custom"]
        voi_tooltips = [
            "No special voicing (default stack).",
            "Root position voicing.",
            "Open voicing (spreads notes further apart).",
            "Drop 2 voicing (lowers the second highest note by an octave).",
            "Custom voicing (set your own note count, position, and spread)."
        ]
        self.voi_radios = []
        voi_btn_group = QButtonGroup(self)
        for i, name in enumerate(voi_options):
            btn = QRadioButton(name)
            btn.setFont(font_radio)
            btn.setToolTip(voi_tooltips[i])
            voi_layout.addWidget(btn)
            voi_btn_group.addButton(btn)
            self.voi_radios.append(btn)
        main_layout.addWidget(voi_group)

        # --- Custom Voicing Controls ---
        from PyQt5.QtWidgets import QSpinBox

        self.custom_voicing_group = QGroupBox("Custom Voicing")
        self.custom_voicing_group.setFont(font_header)
        custom_voicing_layout = QGridLayout()
        self.custom_voicing_group.setLayout(custom_voicing_layout)

        # Number of notes
        num_notes_label = QLabel("Number of Notes:")
        num_notes_label.setToolTip("How many notes will be played in the chord.")
        custom_voicing_layout.addWidget(num_notes_label, 0, 0)
        self.num_notes_spin = QSpinBox()
        self.num_notes_spin.setRange(1, 22)
        self.num_notes_spin.setValue(3)
        self.num_notes_spin.setToolTip("How many notes will be played in the chord.")
        custom_voicing_layout.addWidget(self.num_notes_spin, 0, 1)

        # Position (center note, MIDI octave 0-7)
        position_label = QLabel("Position (Octave):")
        position_label.setToolTip("The center octave for the chord voicing (0 = C0, 7 = C7).")
        custom_voicing_layout.addWidget(position_label, 1, 0)
        self.position_spin = QSpinBox()
        self.position_spin.setRange(0, 7)
        self.position_spin.setValue(3)
        self.position_spin.setToolTip("The center octave for the chord voicing (0 = C0, 7 = C7).")
        custom_voicing_layout.addWidget(self.position_spin, 1, 1)


        # Spread (ComboBox with 6 types)
        spread_label = QLabel("Spread Type:")
        spread_label.setToolTip("How the notes are distributed across the keyboard. Hover each option for details.")
        custom_voicing_layout.addWidget(spread_label, 3, 0)
        self.spread_combo = QComboBox()
        spread_titles = [
            "Stacked Thirds",
            "Layered Voicing",
            "Closed Voicing Above Root Bass",
            "Note Variability",
            "Root + Fifth Spread",
            "Root + Guide Tones"
        ]
        spread_tooltips = [
            "Standard closed voicing with intervals in thirds.",
            "Root in bass, open voicing in low-mids, closed voicing in upper-mids or root in upper register.",
            "Root in bass, closed triad or 7th chord in 4th octave.",
            "Each note has a 70% chance to trigger.",
            "Root in bass, root and fifths layered above.",
            "Root in bass, upper voices favor 3rds or 7ths."
        ]
        for i, title in enumerate(spread_titles):
            self.spread_combo.addItem(title)
            self.spread_combo.setItemData(i, spread_tooltips[i], role=Qt.ToolTipRole)
        custom_voicing_layout.addWidget(self.spread_combo, 3, 1)

        # Load saved custom voicing if present
        custom_voicing = chord.get("custom_voicing")
        if custom_voicing:
            self.num_notes_spin.setValue(custom_voicing.get("num_notes", 3))
            self.position_spin.setValue(custom_voicing.get("position", 3))
            self.range_spin.setValue(custom_voicing.get("range", 3))
            self.spread_combo.setCurrentIndex(custom_voicing.get("spread", 0))

        self.custom_voicing_group.setVisible(False)
        main_layout.addWidget(self.custom_voicing_group)

        # Show/hide custom voicing controls based on selection
        def update_custom_voicing_visibility():
            custom_selected = self.voi_radios[-1].isChecked()
            self.custom_voicing_group.setVisible(custom_selected)
        for btn in self.voi_radios:
            btn.toggled.connect(update_custom_voicing_visibility)
        update_custom_voicing_visibility()

        arp_group = QGroupBox("Arpeggiator")
        arp_group.setFont(font_header)
        arp_group.setToolTip("Configure the arpeggiator to play the chord notes in a sequence instead of all at once.")
        arp_layout = QGridLayout()
        arp_layout.setHorizontalSpacing(18)
        arp_layout.setVerticalSpacing(12)
        arp_group.setLayout(arp_layout)

        arp_label = QLabel("Mode:")
        arp_label.setFont(font_radio)
        arp_label.setToolTip("Select the arpeggiator pattern for playing the chord notes.")
        self.arp_mode_combo = QComboBox()
        self.arp_mode_combo.setFont(font_radio)
        self.arp_mode_combo.addItems([
            "None", "Up", "Down", "Converge", "Diverge", "Random", "Ascending", "Descending"
        ])
        self.arp_mode_combo.setToolTip("Select the arpeggiator pattern for playing the chord notes.")

        note_len_label = QLabel("Note Length:")
        note_len_label.setFont(font_radio)
        note_len_label.setToolTip("Set the duration of each arpeggiated note.")
        self.arp_length_combo = QComboBox()
        self.arp_length_combo.setFont(font_radio)
        self.arp_length_combo.addItems(["1/16", "1/8", "1/4", "1/2"])
        self.arp_length_combo.setToolTip("Set the duration of each arpeggiated note.")

        arp_layout.addWidget(arp_label, 0, 0)
        arp_layout.addWidget(self.arp_mode_combo, 0, 1)
        arp_layout.addWidget(note_len_label, 1, 0)
        arp_layout.addWidget(self.arp_length_combo, 1, 1)
        main_layout.addWidget(arp_group)

        import random
        # Randomize button
        randomize_btn = QPushButton("Randomize")
        randomize_btn.setStyleSheet(
            "QPushButton { background: #388e3c; color: white; font-size: 15px; font-weight: bold; border-radius: 10px; padding: 6px 24px; }"
            "QPushButton:pressed { background: #256029; }"
        )
        def randomize_modifiers():
            # Extension
            ext_choice = random.choice(ext_options)
            for btn in self.ext_radios:
                btn.setChecked(btn.text() == ext_choice)
            # Inversion
            inv_choice = random.choice(inv_options)
            for btn in self.inv_radios:
                btn.setChecked(btn.text() == inv_choice)
            # Voicing
            voi_choice = random.choice(voi_options)
            for btn in self.voi_radios:
                btn.setChecked(btn.text() == voi_choice)
            # Arp mode
            arp_mode_count = self.arp_mode_combo.count()
            self.arp_mode_combo.setCurrentIndex(random.randint(0, arp_mode_count - 1))
            # Arp length
            arp_len_count = self.arp_length_combo.count()
            self.arp_length_combo.setCurrentIndex(random.randint(0, arp_len_count - 1))
            # Custom voicing randomization
            self.num_notes_spin.setValue(random.randint(self.num_notes_spin.minimum(), self.num_notes_spin.maximum()))
            self.position_spin.setValue(random.randint(self.position_spin.minimum(), self.position_spin.maximum()))
            self.spread_combo.setCurrentIndex(random.randint(0, self.spread_combo.count() - 1))
        randomize_btn.clicked.connect(randomize_modifiers)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.button(QDialogButtonBox.Ok).setStyleSheet(
            "QPushButton { background: #1976d2; color: white; font-size: 15px; font-weight: bold; border-radius: 10px; padding: 6px 24px; }"
            "QPushButton:pressed { background: #1565c0; }"
        )
        btn_box.button(QDialogButtonBox.Cancel).setStyleSheet(
            "QPushButton { background: #f0f0f0; color: #444; font-size: 15px; font-weight: bold; border-radius: 10px; padding: 6px 24px; }"
            "QPushButton:pressed { background: #e0e0e0; }"
        )

        main_layout.addStretch()
        main_layout.addWidget(randomize_btn)
        main_layout.addWidget(btn_box)

        scroll.setWidget(scroll_contents)
        dialog_layout = QVBoxLayout(self)
        dialog_layout.addWidget(scroll)
        self.setLayout(dialog_layout)

        ext_val = chord.get("extension") or "None"
        inv_val = chord.get("inversion") or "None"
        voi_val = chord.get("voicing") or "None"
        arp_val = chord.get("arp_mode") or "None"
        arp_len_val = chord.get("arp_length") or "1/16"
        for btn, name in zip(self.ext_radios, ext_options):
            btn.setChecked(name == ext_val)
        for btn, name in zip(self.inv_radios, inv_options):
            btn.setChecked(name == inv_val)
        for btn, name in zip(self.voi_radios, voi_options):
            btn.setChecked(name == voi_val)
        self.arp_mode_combo.setCurrentText(arp_val)
        self.arp_length_combo.setCurrentText(arp_len_val)

        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)

        self.adjustSize()
        self.setFixedSize(self.size().width(), min(self.size().height() + 24, 700))

    def accept(self):
        ext = next((btn.text() for btn in self.ext_radios if btn.isChecked()), "None")
        inv = next((btn.text() for btn in self.inv_radios if btn.isChecked()), "None")
        voi = next((btn.text() for btn in self.voi_radios if btn.isChecked()), "None")
        result = {
            "extension": None if ext == "None" else ext,
            "inversion": None if inv == "None" else inv,
            "voicing": None if voi == "None" else voi,
            "arp_mode": self.arp_mode_combo.currentText(),
            "arp_length": self.arp_length_combo.currentText()
        }
        # Add custom voicing parameters if "Custom" is selected
        if voi == "Custom":
            result["custom_voicing"] = {
                "num_notes": self.num_notes_spin.value(),
                "position": self.position_spin.value(),
                "spread": self.spread_combo.currentIndex()
            }
        self.result = result
        super().accept()
