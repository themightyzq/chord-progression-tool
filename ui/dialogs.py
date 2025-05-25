from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QRadioButton, QButtonGroup, QGroupBox,
    QComboBox, QDialogButtonBox, QScrollArea, QWidget, QGridLayout, QSizePolicy
)
from PyQt5.QtGui import QFont

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
        ext_layout = QGridLayout()
        ext_layout.setHorizontalSpacing(32)
        ext_layout.setVerticalSpacing(8)
        ext_group.setLayout(ext_layout)
        ext_options = ["None", "+6th", "+7th", "+9th", "sus2", "sus4"]
        self.ext_radios = []
        ext_btn_group = QButtonGroup(self)
        for i, name in enumerate(ext_options):
            btn = QRadioButton(name)
            btn.setFont(font_radio)
            ext_layout.addWidget(btn, i // 2, i % 2)
            ext_btn_group.addButton(btn)
            self.ext_radios.append(btn)
        main_layout.addWidget(ext_group)

        inv_group = QGroupBox("Inversion")
        inv_group.setFont(font_header)
        inv_layout = QVBoxLayout()
        inv_group.setLayout(inv_layout)
        inv_options = ["None", "Root", "1st", "2nd"]
        self.inv_radios = []
        inv_btn_group = QButtonGroup(self)
        for name in inv_options:
            btn = QRadioButton(name)
            btn.setFont(font_radio)
            inv_layout.addWidget(btn)
            inv_btn_group.addButton(btn)
            self.inv_radios.append(btn)
        main_layout.addWidget(inv_group)

        voi_group = QGroupBox("Voicing")
        voi_group.setFont(font_header)
        voi_layout = QVBoxLayout()
        voi_group.setLayout(voi_layout)
        voi_options = ["None", "Root", "Open", "Drop 2", "Custom"]
        self.voi_radios = []
        voi_btn_group = QButtonGroup(self)
        for name in voi_options:
            btn = QRadioButton(name)
            btn.setFont(font_radio)
            voi_layout.addWidget(btn)
            voi_btn_group.addButton(btn)
            self.voi_radios.append(btn)
        main_layout.addWidget(voi_group)

        arp_group = QGroupBox("Arpeggiator")
        arp_group.setFont(font_header)
        arp_layout = QGridLayout()
        arp_layout.setHorizontalSpacing(18)
        arp_layout.setVerticalSpacing(12)
        arp_group.setLayout(arp_layout)

        arp_label = QLabel("Mode:")
        arp_label.setFont(font_radio)
        self.arp_mode_combo = QComboBox()
        self.arp_mode_combo.setFont(font_radio)
        self.arp_mode_combo.addItems([
            "None", "Up", "Down", "Converge", "Diverge", "Random", "Ascending", "Descending"
        ])

        note_len_label = QLabel("Note Length:")
        note_len_label.setFont(font_radio)
        self.arp_length_combo = QComboBox()
        self.arp_length_combo.setFont(font_radio)
        self.arp_length_combo.addItems(["1/16", "1/8", "1/4", "1/2"])

        arp_layout.addWidget(arp_label, 0, 0)
        arp_layout.addWidget(self.arp_mode_combo, 0, 1)
        arp_layout.addWidget(note_len_label, 1, 0)
        arp_layout.addWidget(self.arp_length_combo, 1, 1)
        main_layout.addWidget(arp_group)

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
        self.result = result
        super().accept()
