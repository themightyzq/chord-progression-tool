import sys
import math
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGridLayout, QGroupBox, QSpinBox, QComboBox, QScrollArea, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt

# Define MODES at the top so it's available globally
MODES = [
    {"label": "Major (Ionian)"},
    {"label": "Dorian"},
    {"label": "Phrygian"},
    {"label": "Lydian"},
    {"label": "Mixolydian"},
    {"label": "Minor (Aeolian)"},
    {"label": "Locrian"},
    {"label": "Gypsy Minor"},
    {"label": "Harmonic Minor"},
    {"label": "Minor Pentatonic"},
    {"label": "Whole Tone"},
    {"label": "Tonic 2nds"},
    {"label": "Tonic 3rds"},
    {"label": "Tonic 4ths"},
    {"label": "Tonic 6ths"},
]

# Define constants for panel dimensions and style
PANEL_W = 400
PANEL_H = 600
PANEL_STYLE = (
    "QFrame {"
    "  background: #fff;"
    "  border-radius: 20px;"
    "  padding: 0;"
    "  border: none;"
    "}"
)

class ChordPanel(QWidget):
    def __init__(self, on_select, on_add, selected_roman):
        super().__init__()
        self.on_select = on_select
        self.on_add = on_add
        self.selected_roman = None
        # ensure the panel background matches the card
        self.setStyleSheet("background: #ffffff; border-radius: 20px;")
        
        # Card container for header + content
        card_frame = QFrame(self)
        card_frame.setMinimumWidth(PANEL_W)
        card_frame.setMaximumWidth(PANEL_W)
        card_frame.setMinimumHeight(PANEL_H)
        card_frame.setMaximumHeight(PANEL_H)
        card_frame.setStyleSheet(PANEL_STYLE)

        # layout inside the card
        card_layout = QVBoxLayout(card_frame)
        card_layout.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
        card_layout.setSpacing(0)
        card_layout.setContentsMargins(16, 16, 16, 16)

        # Header
        header = QLabel("Chord")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet(
            "font-family: Palatino, Georgia, serif;"
            "font-weight: bold;"
            "font-size: 24pt;"
            "margin: 16px 0 0 0;"
            "color: #222;"
        )

        # Chord wheel group (centered with header)
        from PyQt5.QtGui import QFont
        wheel = QWidget(card_frame)
        wheel.setFixedSize(420, 420)

        wheel_container = QVBoxLayout()
        wheel_container.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        wheel_container.setSpacing(0)
        wheel_container.addWidget(header, alignment=Qt.AlignHCenter)
        wheel_container.addSpacing(8)
        wheel_container.addWidget(wheel, alignment=Qt.AlignHCenter)
        card_layout.addLayout(wheel_container)
        card_layout.addStretch(1)
        self.roman_numerals = ["I", "ii", "iii", "IV", "V", "vi", "vii°"]
        self.btns = []
        degree_colors = {
            "I": "#1976d2", "IV": "#1976d2", "V": "#1976d2",
            "ii": "#388e3c", "iii": "#388e3c", "vi": "#388e3c",
            "vii°": "#d32f2f"
        }
        for i, roman in enumerate(self.roman_numerals):
            angle = (i / 7) * 2 * math.pi - (math.pi / 2)
            radius = 120  # Reduced radius for better spacing
            x = 210 + radius * math.cos(angle) - 40  # Adjusted offsets for centering
            y = 210 + radius * math.sin(angle) - 40
            btn = QPushButton(roman, wheel)
            btn.setMinimumSize(90, 90)
            btn.setMaximumSize(90, 90)
            btn.setSizePolicy(btn.sizePolicy().Fixed, btn.sizePolicy().Fixed)
            btn.move(int(x), int(y))
            font = QFont("Palatino")
            if not font.exactMatch():
                font = QFont("Georgia")
            font.setPointSize(38)  # Increased font size for better visibility
            font.setWeight(QFont.Black)  # Use a heavier font weight
            btn.setFont(font)
            color = degree_colors.get(roman, "#1976d2")
            btn.setStyleSheet(
                f"""
                QPushButton {{
                    background: #fff;
                    color: {color};
                    border: 2px solid {color};
                    border-radius: 45px;
                    font-size: 28px;
                    font-weight: bold;
                }}
                QPushButton:focus {{
                    outline: none;      /* remove default focus rectangle */
                    box-shadow: none;   /* ensure no shadow */
                }}
                QPushButton:pressed {{
                    background: #f5faff;
                }}
                QPushButton:hover {{
                    background: #f5faff;
                }}
                """
            )
            btn.setFocusPolicy(Qt.StrongFocus)
            btn.setToolTip(f"{roman} = chord degree (press Enter to select)")
            btn.clicked.connect(lambda checked, r=roman: self.select_roman(r))
            self.btns.append(btn)
        # Central "ADD CHORD" button in the wheel
        add_chord_center = QPushButton("ADD\nCHORD", wheel)
        add_chord_center.setFixedSize(130, 130)
        add_chord_center.move(
            (wheel.width()  - 120) // 2,
            (wheel.height() - 120) // 2
        )
        font_center = QFont("Palatino")
        if not font_center.exactMatch():
            font_center = QFont("Georgia")
        font_center.setPointSize(24)
        font_center.setWeight(QFont.Bold)
        add_chord_center.setFont(font_center)
        add_chord_center.setStyleSheet(
            "QPushButton {"
            "background: #1976d2; color: #fff; border-radius: 65px; font-size: 24px; font-weight: 700;"
            "text-align: center; padding: 0; line-height: 1.2;"
            "}"
            "QPushButton:focus { outline: none; }"
            "QPushButton:pressed { background: #1565c0; }"
        )
        add_chord_center.setFocusPolicy(Qt.StrongFocus)
        add_chord_center.setToolTip("Add selected chord to progression (press Enter)")
        add_chord_center.clicked.connect(self.add_chord)
        self.add_chord_center = add_chord_center

        # outer layout for this widget
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)   # no gap around card_frame
        main_layout.setSpacing(0)
        main_layout.addWidget(card_frame, 1)          # fill full area
        self.setLayout(main_layout)

        self.update_selection(selected_roman)

    def select_roman(self, roman):
        self.selected_roman = roman
        self.update_selection(roman)
        self.on_select(roman)

    def update_selection(self, roman):
        for btn, r in zip(self.btns, self.roman_numerals):
            color = "#1976d2" if r in ["I", "IV", "V"] else "#388e3c" if r in ["ii", "iii", "vi"] else "#d32f2f"
            if r == roman:
                btn.setStyleSheet(
                    f"""
                    QPushButton {{
                        background: {color};
                        color: #fff;
                        border: 2px solid transparent;
                        border-radius: 45px;
                        font-size: 32px;
                        font-weight: bold;
                    }}
                    QPushButton:focus {{
                        outline: none;
                        box-shadow: none;
                        border: 2px solid transparent;
                    }}
                    QPushButton:pressed {{
                        background: #bbdefb;
                    }}
                    """
                )
            else:
                btn.setStyleSheet(
                    f"""
                    QPushButton {{
                        background: #fff;
                        color: {color};
                        border: 2px solid {color};
                        border-radius: 45px;
                        font-size: 32px;
                        font-weight: bold;
                    }}
                    QPushButton:focus {{
                        outline: none;
                        box-shadow: none;
                        border: 2px solid {color};
                    }}
                    QPushButton:pressed {{
                        background: #f5f5f5;
                    }}
                    """
                )

    def add_chord(self):
        if self.selected_roman:
            self.on_add(self.selected_roman)
            self.update_selection(None)

class StructurePanel(QWidget):
    def __init__(self, chords, on_delete):
        super().__init__()
        self.chords = chords
        self.on_delete = on_delete
        # Card container for header + content
        from PyQt5.QtWidgets import QFrame
        card_frame = QFrame(self)
        card_frame.setMinimumWidth(PANEL_W)
        card_frame.setMaximumWidth(PANEL_W)
        card_frame.setMinimumHeight(PANEL_H)
        card_frame.setMaximumHeight(PANEL_H)
        card_frame.setStyleSheet(PANEL_STYLE)
        card_layout = QVBoxLayout(card_frame)
        card_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        card_layout.setSpacing(24)
        card_layout.setContentsMargins(16, 16, 16, 16)

        # Header
        header = QLabel("Chord Structure")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-family: Palatino, Georgia, serif; font-weight: bold; font-size: 28pt; margin: 24px 0 12px 0; color: #222;")
        card_layout.addWidget(header)

        # Chord slots and instructional text
        from PyQt5.QtWidgets import QPushButton
        self.cards_layout = QVBoxLayout()
        self.cards_layout.setSpacing(12)

        # Add Remove All and Randomize buttons
        controls_row = QHBoxLayout()
        controls_row.setSpacing(12)
        self.remove_all_btn = QPushButton("Remove All")
        self.remove_all_btn.setStyleSheet(
            "QPushButton {background: #d32f2f; color: #fff; border-radius: 8px; font-size: 14px; font-weight: bold; padding: 6px 18px;}"
            "QPushButton:pressed {background: #b71c1c;}"
        )
        self.remove_all_btn.setToolTip("Remove all chords from progression")
        self.randomize_btn = QPushButton("Randomize")
        self.randomize_btn.setStyleSheet(
            "QPushButton {background: #1976d2; color: #fff; border-radius: 8px; font-size: 14px; font-weight: bold; padding: 6px 18px;}"
            "QPushButton:pressed {background: #1565c0;}"
        )
        self.randomize_btn.setToolTip("Randomize chord order")
        controls_row.addWidget(self.remove_all_btn)
        controls_row.addWidget(self.randomize_btn)
        card_layout.addLayout(controls_row)
        card_layout.addLayout(self.cards_layout)

        def remove_all_chords():
            self.chords.clear()
            self.update_chords(self.chords)
        def randomize_chords():
            import random
            random.shuffle(self.chords)
            self.update_chords(self.chords)
        self.remove_all_btn.clicked.connect(remove_all_chords)
        self.randomize_btn.clicked.connect(randomize_chords)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(card_frame)
        self.setLayout(main_layout)
        self.update_chords(chords)

    def update_chords(self, chords):
        # Remove old cards
        self.card_widgets = []
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        if not chords:
            # Show 4 empty outlined boxes, centered
            from PyQt5.QtWidgets import QHBoxLayout
            slot_row = QHBoxLayout()
            slot_row.setSpacing(18)
            slot_row.setAlignment(Qt.AlignHCenter)
            for _ in range(4):
                slot = QFrame()
                slot.setFixedSize(56, 56)
                slot.setStyleSheet(
                    "background: #fff; border: 2.5px solid #bbb; border-radius: 10px;"
                )
                slot.setFocusPolicy(Qt.StrongFocus)
                slot.setToolTip("Empty chord slot (Tab to focus)")
                slot_row.addWidget(slot)
            self.cards_layout.addLayout(slot_row)
            # Centered instructional text
            empty = QLabel("Construct your chord progression here.")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet("color: #bbb; font-family: Palatino, Georgia, serif; font-size: 13pt; margin-top: 18px;")
            self.cards_layout.addWidget(empty)
        else:
            # Show each chord as a styled card with play, label, modifiers, and delete
            from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout
            for i, chord in enumerate(chords):
                roman = chord["roman"]
                color = "#1976d2" if roman in ["I", "IV", "V"] else "#388e3c" if roman in ["ii", "iii", "vi"] else "#d32f2f"
                card = QFrame()
                card.setObjectName("chordCard")
                card.setMinimumHeight(110)
                card.setStyleSheet(
                    f"""
                    QFrame#chordCard {{
                        border: 1.5px solid {color};
                        border-radius: 16px;
                        margin-bottom: 16px;
                        background: #fff;
                    }}
                    """
                )
                # Add drop shadow effect
                from PyQt5.QtWidgets import QGraphicsDropShadowEffect
                shadow = QGraphicsDropShadowEffect(card)
                shadow.setBlurRadius(16)
                shadow.setOffset(0, 4)
                shadow.setColor(Qt.gray)
                card.setGraphicsEffect(shadow)
                card.setFocusPolicy(Qt.StrongFocus)
                card.setToolTip(f"Chord: {roman} (hover to preview, drag to reorder)")
                card_layout = QHBoxLayout()
                card_layout.setSpacing(10)
                card_layout.setContentsMargins(12, 8, 12, 8)
                # Play button
                from PyQt5.QtGui import QIcon, QPixmap, QPainter, QBrush, QPolygon
                from PyQt5.QtCore import QPoint

                # Create a small play icon (white triangle)
                small_play_pixmap = QPixmap(24, 24)
                small_play_pixmap.fill(Qt.transparent)
                painter = QPainter(small_play_pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setBrush(QBrush(Qt.white))
                painter.setPen(Qt.NoPen)
                triangle = QPolygon([QPoint(7, 4), QPoint(19, 12), QPoint(7, 20)])
                painter.drawPolygon(triangle)
                painter.end()
                small_play_icon = QIcon(small_play_pixmap)

                play_btn = QPushButton(card)
                play_btn.setIcon(small_play_icon)
                play_btn.setIconSize(small_play_pixmap.size())
                play_btn.setFixedSize(36, 36)
                play_btn.setStyleSheet(
                    """
                    QPushButton {
                        background: #1976d2;
                        border-radius: 10px;
                        border: none;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.10);
                    }
                    QPushButton:pressed {
                        background: #1565c0;
                    }
                    """
                )
                play_btn.setFocusPolicy(Qt.StrongFocus)
                play_btn.setToolTip("Preview this chord")
                def make_play(idx):
                    def play():
                        parent = self.parentWidget()
                        while parent and not hasattr(parent, "key"):
                            parent = parent.parentWidget()
                        if parent and hasattr(parent, "key"):
                            chord = self.chords[idx]
                            freqs = parent.get_chord_frequencies(
                                chord["roman"],
                                chord.get("extension"),
                                chord.get("inversion"),
                                chord.get("voicing"),
                                key=parent.key,
                                mode=parent.mode
                            )
                            parent.play_chord_tone(freqs, duration=0.5)
                    return play
                play_btn.clicked.connect(make_play(i))
                card_layout.addWidget(play_btn)
                # create a vertical stack for label + modifiers
                label_column = QVBoxLayout()
                label_column.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

                # Roman numeral label
                label = QLabel(roman, card)
                label.setAlignment(Qt.AlignCenter)
                font = QFont("Palatino")
                if not font.exactMatch():
                    font = QFont("Georgia")
                font.setPointSize(32)
                font.setWeight(QFont.Bold)
                label.setFont(font)
                label.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {color}; min-width: 60px;")
                label.setWordWrap(False)  # Prevent text wrapping
                label.setMinimumHeight(40)  # Ensure consistent height
                label.setAlignment(Qt.AlignCenter)  # Center-align text
                label_column.addWidget(label)

                # modifiers in a single horizontal row
                mod_row = QHBoxLayout()
                mod_row.setSpacing(8)
                mod_row.setAlignment(Qt.AlignLeft | Qt.AlignBottom)

                if chord.get("extension"):
                    ext_pill = QLabel(chord["extension"])
                    ext_pill.setFixedHeight(30)
                    ext_pill.setMinimumWidth(56)
                    ext_pill.setAlignment(Qt.AlignCenter)
                    ext_pill.setStyleSheet(
                        f"""
                        background: #fff;
                        color: {color};
                        border: 2px solid {color};
                        border-radius: 8px;
                        font-size: 14px;
                        font-weight: bold;
                        padding: 4px 10px;
                        """
                    )
                    mod_row.addWidget(ext_pill)

                if chord.get("inversion"):
                    inv_pill = QLabel(chord["inversion"])
                    inv_pill.setFixedHeight(30)
                    inv_pill.setMinimumWidth(56)
                    inv_pill.setAlignment(Qt.AlignCenter)
                    inv_pill.setStyleSheet(
                        f"""
                        background: #fff;
                        color: {color};
                        border: 2px solid {color};
                        border-radius: 8px;
                        font-size: 14px;
                        font-weight: bold;
                        padding: 4px 10px;
                        """
                    )
                    mod_row.addWidget(inv_pill)

                if chord.get("voicing"):
                    voicing_pill = QLabel(chord["voicing"])
                    voicing_pill.setFixedHeight(30)
                    voicing_pill.setMinimumWidth(56)
                    voicing_pill.setAlignment(Qt.AlignCenter)
                    voicing_pill.setStyleSheet(
                        f"""
                        background: #fff;
                        color: {color};
                        border: 2px solid {color};
                        border-radius: 8px;
                        font-size: 14px;
                        font-weight: bold;
                        padding: 4px 10px;
                        """
                    )
                    mod_row.addWidget(voicing_pill)

                label_column.addLayout(mod_row)
                card_layout.addLayout(label_column, 1)

                # Edit/settings button (distinct)
                edit_btn = QPushButton("✎", card)
                edit_btn.setFixedSize(36, 36)
                edit_btn.setStyleSheet(
                    "QPushButton {background: #fff; color: #1976d2; border: 2px solid #1976d2; font-size: 22px; font-weight: bold; border-radius: 10px;}"
                    "QPushButton:focus { box-shadow: 0 0 0 2px #1976d244; }"
                    "QPushButton:hover { background: #e3f2fd; }"
                )
                edit_btn.setFocusPolicy(Qt.StrongFocus)
                edit_btn.setToolTip("Edit this chord")
                edit_btn.clicked.connect(lambda checked, idx=i: self.show_modifier_popup(idx))
                card_layout.addWidget(edit_btn)
                # Delete button
                del_btn = QPushButton("✕", card)
                del_btn.setFixedSize(36, 36)
                del_btn.setStyleSheet(
                    "QPushButton {background: #fff; color: #888; border: none; font-size: 24px; font-weight: bold; border-radius: 10px;}"
                    "QPushButton:focus { box-shadow: 0 0 0 2px #8884; }"
                    "QPushButton:hover { background: #f0f0f0; }"
                )
                del_btn.setFocusPolicy(Qt.StrongFocus)
                del_btn.setToolTip("Remove this chord from progression")
                del_btn.clicked.connect(lambda checked, idx=i: self.on_delete(idx))
                card_layout.addWidget(del_btn)
                card.setLayout(card_layout)
                self.cards_layout.addWidget(card)
                self.card_widgets.append(card)

    def highlight_card(self, idx):
        for i, card in enumerate(getattr(self, "card_widgets", [])):
            if i == idx:
                card.setFocus()
                card.setStyleSheet(
                    "background: #e3f2fd; border: 2.5px solid #1976d2; border-radius: 10px; "
                    "box-shadow: 0 0 0 3px #1976d288;"
                )
            else:
                card.clearFocus()
                card.setStyleSheet(
                    "background: #fff; border: 2.5px solid #1976d2; border-radius: 10px;"
                )

    def show_modifier_popup(self, idx):
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QRadioButton, QButtonGroup, QDialogButtonBox, QGroupBox, QScrollArea
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Chord Modifiers")
        dialog.setFixedSize(400, 600)
        # Fix: force white background and rounded corners on the dialog
        dialog.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border-radius: 16px;
                padding: 20px;
            }
            QGroupBox {
                background-color: #ffffff;
                border-radius: 12px;
            }
            QRadioButton {
                background-color: #ffffff;
            }
            QWidget {
                background-color: #ffffff;
            }
        """)

        scroll_area = QScrollArea(dialog)
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(8)  # Reduced spacing between group boxes

        # Add extension, inversion, and voicing groups to scrollable content
        ext_groupbox = QGroupBox("Select Extension:")
        ext_layout = QGridLayout()
        ext_group = QButtonGroup(dialog)
        ext_radios = []
        ext_options = ["None", "+6th", "+7th", "+9th", "sus2", "sus4"]
        for i, opt in enumerate(ext_options):
            radio = QRadioButton(opt)
            ext_group.addButton(radio)
            ext_layout.addWidget(radio, i // 2, i % 2)
            ext_radios.append(radio)
        ext_groupbox.setLayout(ext_layout)
        scroll_layout.addWidget(ext_groupbox)

        inv_groupbox = QGroupBox("Select Inversion:")
        inv_layout = QVBoxLayout()
        inv_group = QButtonGroup(dialog)
        inv_radios = []
        inv_options = ["None", "Root", "1st", "2nd"]
        for inv in inv_options:
            radio = QRadioButton(inv)
            inv_group.addButton(radio)
            inv_layout.addWidget(radio)
            inv_radios.append(radio)
        inv_groupbox.setLayout(inv_layout)
        scroll_layout.addWidget(inv_groupbox)

        voicing_groupbox = QGroupBox("Select Voicing:")
        voicing_layout = QVBoxLayout()
        voicing_group = QButtonGroup(dialog)
        voicing_radios = []
        voicing_options = ["None", "Root", "Open", "Drop 2", "Custom"]
        for voicing in voicing_options:
            radio = QRadioButton(voicing)
            if voicing == "Custom":
                radio.setToolTip("Custom voicing is not implemented and has no effect.")
            voicing_group.addButton(radio)
            voicing_layout.addWidget(radio)
            voicing_radios.append(radio)
        voicing_groupbox.setLayout(voicing_layout)
        scroll_layout.addWidget(voicing_groupbox)

        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setStyleSheet(
            "QPushButton { background: #1976d2; color: white; font-size: 16px; font-weight: bold; border-radius: 10px; padding: 6px 24px; }"
            "QPushButton:focus { box-shadow: 0 0 0 3px #1976d244; }"
            "QPushButton:pressed { background: #1565c0; }"
        )
        buttons.button(QDialogButtonBox.Cancel).setStyleSheet(
            "QPushButton { background: #f0f0f0; color: #444; font-size: 16px; font-weight: bold; border-radius: 10px; padding: 6px 24px; }"
            "QPushButton:focus { box-shadow: 0 0 0 3px #8884; }"
            "QPushButton:pressed { background: #e0e0e0; }"
        )

        # Add scroll area and buttons to dialog layout
        dialog_layout = QVBoxLayout(dialog)
        dialog_layout.addWidget(scroll_area)
        dialog_layout.addWidget(buttons)
        dialog.setLayout(dialog_layout)

        # Preselect current values
        chord = self.chords[idx]
        # Handle None as default if not set
        ext_val = chord.get("extension") if chord.get("extension") else "None"
        inv_val = chord.get("inversion") if chord.get("inversion") else "None"
        voicing_val = chord.get("voicing") if chord.get("voicing") else "None"
        if ext_val in ext_options:
            ext_radios[ext_options.index(ext_val)].setChecked(True)
        if inv_val in inv_options:
            inv_radios[inv_options.index(inv_val)].setChecked(True)
        if voicing_val in voicing_options:
            voicing_radios[voicing_options.index(voicing_val)].setChecked(True)

        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        if dialog.exec_() == QDialog.Accepted:
            # Update chord modifiers in the progression
            selected_ext = None
            for r in ext_radios:
                if r.isChecked():
                    selected_ext = r.text()
            if selected_ext == "None":
                selected_ext = None
            print("Applied extension:", selected_ext)
            selected_inv = None
            for r in inv_radios:
                if r.isChecked():
                    selected_inv = r.text()
            if selected_inv == "None":
                selected_inv = None
            selected_voicing = None
            for r in voicing_radios:
                if r.isChecked():
                    selected_voicing = r.text()
            if selected_voicing == "None":
                selected_voicing = None
            self.chords[idx]["extension"] = selected_ext
            self.chords[idx]["inversion"] = selected_inv
            self.chords[idx]["voicing"] = selected_voicing
            print(f"Updated modifiers for {self.chords[idx]['roman']}: {selected_ext}, {selected_inv}, {selected_voicing}")
            self.update_chords(self.chords)

class SettingsPanel(QWidget):
    def __init__(self, on_play, on_stop, is_playing, tempo, set_tempo, on_export_midi, key, set_key, mode, set_mode):
        super().__init__()
        from PyQt5.QtWidgets import QFormLayout, QSizePolicy, QFrame, QPushButton
        # Card container for header + content
        from PyQt5.QtWidgets import QFrame
        card_frame = QFrame(self)
        card_frame.setMinimumWidth(PANEL_W)
        card_frame.setMaximumWidth(PANEL_W)
        card_frame.setMinimumHeight(PANEL_H)
        card_frame.setMaximumHeight(PANEL_H)
        card_frame.setStyleSheet(PANEL_STYLE)
        layout = QVBoxLayout(card_frame)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        layout.setSpacing(24)  # Consistent spacing between elements
        layout.setContentsMargins(16, 16, 16, 16)  # Consistent margins inside the panel

        # Header
        header = QLabel("Session Settings")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-family: Palatino, Georgia, serif; font-weight: bold; font-size: 28pt; margin: 32px 0 16px 0; color: #222;")
        layout.addWidget(header)

        # Form layout for settings
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)  # Change label alignment to left
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(24)  # Reduced spacing for tighter alignment

        # Tempo row
        tempo_label = QLabel("Tempo:")
        tempo_label.setStyleSheet("font-family: Palatino, Georgia, serif; font-size: 16pt; font-weight: bold;")
        self.tempo_spin = QSpinBox()
        self.tempo_spin.setRange(40, 240)
        self.tempo_spin.setValue(tempo)
        self.tempo_spin.setFixedWidth(90)
        self.tempo_spin.setStyleSheet("font-size: 16pt; padding: 2px 8px; border-radius: 6px; border: 1.5px solid #bbb; background: #fff;")
        self.tempo_spin.setFocusPolicy(Qt.StrongFocus)
        self.tempo_spin.setToolTip("Set playback tempo (BPM)")
        self.tempo_spin.valueChanged.connect(set_tempo)
        bpm_label = QLabel("BPM")
        bpm_label.setStyleSheet("font-family: Palatino, Georgia, serif; font-size: 16pt; font-weight: bold;")

        tempo_row = QWidget()
        tempo_row_layout = QHBoxLayout(tempo_row)
        tempo_row_layout.setContentsMargins(0, 0, 0, 0)
        tempo_row_layout.setSpacing(12)
        tempo_row_layout.addWidget(tempo_label)
        tempo_row_layout.addWidget(self.tempo_spin)
        tempo_row_layout.addWidget(bpm_label)
        form.addRow(tempo_row)

        # Play/Stop/Export MIDI buttons row
        from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush, QPolygon
        from PyQt5.QtCore import QPoint

        # Create play icon (white triangle on transparent background)
        play_pixmap = QPixmap(40, 40)
        play_pixmap.fill(Qt.transparent)
        painter = QPainter(play_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(Qt.white))
        painter.setPen(Qt.NoPen)
        triangle = QPolygon([QPoint(12, 8), QPoint(32, 20), QPoint(12, 32)])
        painter.drawPolygon(triangle)
        painter.end()
        play_icon = QIcon(play_pixmap)

        # Create stop icon (white square on transparent background)
        stop_pixmap = QPixmap(40, 40)
        stop_pixmap.fill(Qt.transparent)
        painter = QPainter(stop_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(Qt.white))
        painter.setPen(Qt.NoPen)
        painter.drawRect(12, 12, 16, 16)
        painter.end()
        stop_icon = QIcon(stop_pixmap)

        self.play_btn = QPushButton()
        self.play_btn.setIcon(play_icon)
        self.play_btn.setIconSize(play_pixmap.size())
        self.play_btn.setFixedSize(64, 64)
        self.play_btn.setStyleSheet(
            """
            QPushButton {
                background: #1976d2;
                border-radius: 18px;
                border: none;
                box-shadow: 0 2px 8px rgba(0,0,0,0.10);
            }
            QPushButton:pressed {
                background: #1565c0;
            }
            """
        )
        self.play_btn.setToolTip("Play progression")
        self.play_btn.clicked.connect(on_play)

        self.stop_btn = QPushButton()
        self.stop_btn.setIcon(stop_icon)
        self.stop_btn.setIconSize(stop_pixmap.size())
        self.stop_btn.setFixedSize(64, 64)
        self.stop_btn.setStyleSheet(
            """
            QPushButton {
                background: #d32f2f;
                border-radius: 18px;
                border: none;
                box-shadow: 0 2px 8px rgba(0,0,0,0.10);
            }
            QPushButton:pressed {
                background: #b71c1c;
            }
            """
        )
        self.stop_btn.setToolTip("Stop playback")
        self.stop_btn.clicked.connect(on_stop)

        self.export_btn = QPushButton("Export MIDI")
        self.export_btn.setFixedHeight(44)
        self.export_btn.setStyleSheet("background: #388e3c; color: #fff; border-radius: 12px; font-size: 18px; font-weight: bold;")
        self.export_btn.setToolTip("Export progression as MIDI file")
        self.export_btn.clicked.connect(on_export_midi)

        button_row = QHBoxLayout()
        button_row.addWidget(self.play_btn)
        button_row.addWidget(self.stop_btn)
        layout.addLayout(button_row)  # Add Play/Stop as a horizontal group
        layout.addWidget(self.export_btn)  # Export MIDI as its own row

        # Key row
        key_label = QLabel("Key:")
        key_label.setStyleSheet("font-family: Palatino, Georgia, serif; font-size: 16pt; font-weight: bold;")
        from PyQt5.QtWidgets import QPushButton
        self.key_combo = QComboBox()
        self.key_toggle_btn = QPushButton("Sharp")
        self.key_toggle_btn.setCheckable(True)
        self.key_toggle_btn.setChecked(False)
        self.key_toggle_btn.setFixedWidth(60)
        self.key_toggle_btn.setStyleSheet(
            "QPushButton {font-size: 14px; border-radius: 8px; background: #e0e0e0; color: #222; font-weight: bold;}"
            "QPushButton:checked {background: #1976d2; color: #fff;}"
        )
        self.key_combo.setFixedWidth(90)
        self.key_combo.setStyleSheet(
            "QComboBox {font-size: 16pt; border-radius: 8px; padding: 4px 16px; border: 1.5px solid #bbb; background: #fff;}"
            "QComboBox:focus { border: 2px solid #1976d2; }"
            "QAbstractItemView { background: #fff; }"
        )
        self.key_combo.setFocusPolicy(Qt.StrongFocus)
        self.key_combo.setToolTip("Select key (Tab to focus, arrows to change)")

        # Key options for sharps and flats
        self.key_options_sharps = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        self.key_options_flats = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

        def update_key_options():
            if self.key_toggle_btn.isChecked():
                self.key_toggle_btn.setText("Flat")
                self.key_combo.clear()
                self.key_combo.addItems(self.key_options_flats)
                if key in self.key_options_flats:
                    self.key_combo.setCurrentText(key)
                else:
                    self.key_combo.setCurrentIndex(0)
            else:
                self.key_toggle_btn.setText("Sharp")
                self.key_combo.clear()
                self.key_combo.addItems(self.key_options_sharps)
                if key in self.key_options_sharps:
                    self.key_combo.setCurrentText(key)
                else:
                    self.key_combo.setCurrentIndex(0)

        self.key_toggle_btn.toggled.connect(update_key_options)
        self.key_combo.currentTextChanged.connect(set_key)
        update_key_options()

        key_row = QWidget()
        key_row_layout = QHBoxLayout(key_row)
        key_row_layout.setContentsMargins(0, 0, 0, 0)
        key_row_layout.setSpacing(12)
        key_row_layout.addWidget(key_label)
        key_row_layout.addWidget(self.key_combo)
        key_row_layout.addWidget(self.key_toggle_btn)
        form.addRow(key_row)

        # Mode row
        mode_label = QLabel("Mode:")
        mode_label.setStyleSheet("font-family: Palatino, Georgia, serif; font-size: 16pt; font-weight: bold;")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([m["label"] for m in MODES])
        self.mode_combo.setFixedWidth(180)
        self.mode_combo.setCurrentText(mode)
        self.mode_combo.setStyleSheet(
            "QComboBox {font-size: 16pt; border-radius: 8px; padding: 4px 16px; border: 1.5px solid #bbb; background: #fff;}"
            "QComboBox:focus { border: 2px solid #1976d2; }"
            "QAbstractItemView { background: #fff; }"
        )
        self.mode_combo.setFocusPolicy(Qt.StrongFocus)
        self.mode_combo.setToolTip("Select mode (Tab to focus, arrows to change)")
        self.mode_combo.currentTextChanged.connect(set_mode)

        mode_row = QWidget()
        mode_row_layout = QHBoxLayout(mode_row)
        mode_row_layout.setContentsMargins(0, 0, 0, 0)
        mode_row_layout.setSpacing(12)
        mode_row_layout.addWidget(mode_label)
        mode_row_layout.addWidget(self.mode_combo)
        form.addRow(mode_row)

        layout.addLayout(form)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(card_frame)
        self.setLayout(main_layout)

from functools import partial

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chord Progression Tool")
        self.setStyleSheet("background: #f5f5f5;")
        # Main 3-column layout with styled panels
        main_layout = QHBoxLayout()
        main_layout.setSpacing(40)  # Equal spacing between panels
        main_layout.setContentsMargins(20, 20, 20, 20)  # Add margins around the layout
        main_layout.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        # State for selected chord and progression (must be defined before panel creation)
        self.selected_roman = None
        self.chord_progression = []

        # Handlers for chord selection and add (must be defined before panel creation)
        def on_select(roman):
            self.selected_roman = roman
            self.chord_panel.update_selection(roman)

        def on_add(roman):
            self.chord_progression.append({
                "roman": roman,
                "extension": None,
                "inversion": None
            })
            self.selected_roman = None
            self.chord_panel.update_selection(None)
            self.structure_panel.update_chords(self.chord_progression)

        def on_delete(idx):
            if 0 <= idx < len(self.chord_progression):
                self.chord_progression.pop(idx)
                self.structure_panel.update_chords(self.chord_progression)

        # Playback state and handlers (must be defined before panel creation)
        self.is_playing = False
        self.tempo = 100
        self.key = "C"
        self.mode = "Major (Ionian)"

        import threading
        import time
        import numpy as np
        import sounddevice as sd

        # Add a lock to prevent concurrent audio playback
        self.audio_lock = threading.Lock()

        def play_chord_tone(self, notes, duration=0.5, fs=44100):
            print(f"[DEBUG] play_chord_tone called with notes: {notes}")
            if not notes or not all(isinstance(f, (int, float)) and f > 0 for f in notes):
                print("[DEBUG] Invalid or empty notes passed to play_chord_tone.")
                return
            t = np.linspace(0, duration, int(fs * duration), False)
            audio = np.zeros_like(t)
            for freq in notes:
                print(f"[DEBUG] Generating sine wave for freq: {freq}")
                audio += 0.3 * np.sin(2 * np.pi * freq * t)
            if np.max(np.abs(audio)) == 0:
                print("[DEBUG] Audio buffer is silent (all zeros).")
                return
            audio = audio / np.max(np.abs(audio))
            print("[DEBUG] Playing audio buffer with sounddevice.")
            # Ensure only one playback at a time
            with self.audio_lock:
                sd.play(audio, fs)
                sd.wait()
        setattr(MainWindow, "play_chord_tone", play_chord_tone)

        def on_play():
            self.is_playing = True
            print("Playback started at", self.tempo, "BPM")
            from PyQt5.QtCore import QTimer
            def play_loop():
                print(f"[DEBUG] chord_progression at start of playback: {self.chord_progression}")
                for idx, chord in enumerate(self.chord_progression):
                    if not self.is_playing:
                        break
                    print(f"[DEBUG] chord at idx={idx}: {chord}")
                    # Use QTimer.singleShot with functools.partial to capture idx
                    QTimer.singleShot(0, partial(self.structure_panel.highlight_card, idx))
                    print(f"[DEBUG] Playing chord idx={idx}: {chord}")
                    freqs = self.get_chord_frequencies(
                        chord["roman"],
                        chord.get("extension"),
                        chord.get("inversion"),
                        chord.get("voicing"),
                        key=self.key,
                        mode=self.mode
                    )
                    print(f"[DEBUG] Frequencies for chord: {freqs}")
                    print(f"Playing: {chord['roman']} {chord.get('extension') or ''} {chord.get('inversion') or ''}")
                    self.play_chord_tone(freqs, duration=60/self.tempo)
                # Clear highlight at end
                QTimer.singleShot(0, partial(self.structure_panel.highlight_card, -1))
                self.is_playing = False
            threading.Thread(target=play_loop, daemon=True).start()

        def on_stop():
            self.is_playing = False
            self.structure_panel.highlight_card(-1)
            print("Playback stopped")

        def set_tempo(val):
            self.tempo = val
            print("Tempo set to", val)

        def export_midi():
            from PyQt5.QtWidgets import QFileDialog, QMessageBox
            import mido

            path, _ = QFileDialog.getSaveFileName(self, "Export MIDI", "progression.mid", "MIDI Files (*.mid)")
            if not path:
                return

            note_map = {
                "C": 60, "C#": 61, "D": 62, "D#": 63, "E": 64, "F": 65, "F#": 66,
                "G": 67, "G#": 68, "A": 69, "A#": 70, "B": 71
            }
            def get_midi_notes(roman, extension=None, inversion=None, voicing=None, key="C"):
                roman_map = {
                    "I": ["C", "E", "G"],
                    "ii": ["D", "F", "A"],
                    "iii": ["E", "G", "B"],
                    "IV": ["F", "A", "C"],
                    "V": ["G", "B", "D"],
                    "vi": ["A", "C", "E"],
                    "vii°": ["B", "D", "F"],
                }
                notes = roman_map.get(roman, ["C", "E", "G"])
                if extension == "+7th":
                    notes.append("B")
                elif extension == "+9th":
                    notes.append("D")
                elif extension == "sus2":
                    notes[1] = "D"
                elif extension == "sus4":
                    notes[1] = "F"
                if inversion == "1st":
                    notes = notes[1:] + notes[:1]
                elif inversion == "2nd":
                    notes = notes[2:] + notes[:2]
                if voicing == "Open" and len(notes) >= 3:
                    notes = [notes[0], notes[1], notes[2]]
                elif voicing == "Drop 2" and len(notes) >= 3:
                    notes = [notes[0], notes[2], notes[1]]
                key_offset = note_map.get(key, 60) - 60
                midi_notes = []
                for n in notes:
                    base = n.replace("+8", "").replace("-8", "").replace("°", "")
                    midi = note_map.get(base, 60) + key_offset
                    midi_notes.append(midi)
                return midi_notes

            mid = mido.MidiFile()
            track = mido.MidiTrack()
            mid.tracks.append(track)
            bpm = self.tempo
            tempo = mido.bpm2tempo(bpm)
            track.append(mido.MetaMessage('set_tempo', tempo=tempo))
            ticks_per_beat = mid.ticks_per_beat
            for chord in self.chord_progression:
                notes = get_midi_notes(
                    chord["roman"],
                    chord.get("extension"),
                    chord.get("inversion"),
                    chord.get("voicing"),
                    key=self.key
                )
                for n in notes:
                    track.append(mido.Message('note_on', note=n, velocity=80, time=0))
                for i, n in enumerate(notes):
                    track.append(mido.Message('note_off', note=n, velocity=64, time=ticks_per_beat if i == 0 else 0))
            try:
                mid.save(path)
                QMessageBox.information(self, "Export Complete", f"MIDI file saved to:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Failed to save MIDI file:\n{e}")

        # Chord Panel
        self.chord_panel = ChordPanel(on_select, on_add, self.selected_roman)
        self.chord_panel.setMinimumWidth(340)
        self.chord_panel.setMaximumWidth(420)
        self.chord_panel.setSizePolicy(self.chord_panel.sizePolicy().Expanding, self.chord_panel.sizePolicy().Expanding)

        # Chord Structure Panel
        self.structure_panel = StructurePanel(self.chord_progression, on_delete)
        self.structure_panel.setMinimumWidth(340)
        self.structure_panel.setMaximumWidth(420)
        self.structure_panel.setSizePolicy(self.structure_panel.sizePolicy().Expanding, self.structure_panel.sizePolicy().Expanding)

        # Handlers for key/mode selection (must be defined before panel creation)
        def set_key(val):
            self.key = val
            print("Key set to", val)

        def set_mode(val):
            self.mode = val
            print("Mode set to", val)

        # Session Settings Panel
        self.settings_panel = SettingsPanel(
            on_play, on_stop, self.is_playing, self.tempo, set_tempo, export_midi,
            self.key, set_key, self.mode, set_mode
        )
        self.settings_panel.setMinimumWidth(340)
        self.settings_panel.setMaximumWidth(420)
        self.settings_panel.setSizePolicy(self.settings_panel.sizePolicy().Expanding, self.settings_panel.sizePolicy().Expanding)

        # Add get_chord_frequencies method for StructurePanel play button
        def get_chord_frequencies(self, roman, extension=None, inversion=None, voicing=None, key=None, mode=None):
            print(f"[DEBUG] get_chord_frequencies called with roman={roman}, extension={extension}, inversion={inversion}, voicing={voicing}, key={key}, mode={mode}")
            # Note names and their indices
            note_names_sharp = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
            note_names_flat = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
            note_freqs = [261.63, 277.18, 293.66, 311.13, 329.63, 349.23, 369.99, 392.00, 415.30, 440.00, 466.16, 493.88]
            note_map = {n: f for n, f in zip(note_names_sharp, note_freqs)}
            note_map.update({n: f for n, f in zip(note_names_flat, note_freqs)})

            # Mode intervals (in semitones from root)
            mode_intervals = {
                "Major (Ionian)":      [0, 2, 4, 5, 7, 9, 11],
                "Dorian":              [0, 2, 3, 5, 7, 9, 10],
                "Phrygian":            [0, 1, 3, 5, 7, 8, 10],
                "Lydian":              [0, 2, 4, 6, 7, 9, 11],
                "Mixolydian":          [0, 2, 4, 5, 7, 9, 10],
                "Minor (Aeolian)":     [0, 2, 3, 5, 7, 8, 10],
                "Locrian":             [0, 1, 3, 5, 6, 8, 10],
                "Gypsy Minor":         [0, 2, 3, 6, 7, 8, 11],
                "Harmonic Minor":      [0, 2, 3, 5, 7, 8, 11],
                "Minor Pentatonic":    [0, 3, 5, 7, 10],
                "Whole Tone":          [0, 2, 4, 6, 8, 10],
                "Tonic 2nds":          [0, 2],
                "Tonic 3rds":          [0, 4],
                "Tonic 4ths":          [0, 5],
                "Tonic 6ths":          [0, 9],
            }
            # Chord degree to scale degree index
            roman_to_degree = {
                "I": 0, "ii": 1, "iii": 2, "IV": 3, "V": 4, "vi": 5, "vii°": 6
            }
            # Build scale for key/mode
            key_val = key if key else self.key
            mode_val = mode if mode else self.mode
            if key_val in note_names_sharp:
                key_index = note_names_sharp.index(key_val)
                scale_notes = note_names_sharp
            elif key_val in note_names_flat:
                key_index = note_names_flat.index(key_val)
                scale_notes = note_names_flat
            else:
                key_index = 0
                scale_notes = note_names_sharp
            intervals = mode_intervals.get(mode_val, mode_intervals["Major (Ionian)"])
            scale = [(key_index + i) % 12 for i in intervals]
            scale_note_names = [scale_notes[i] for i in scale]

            # Build triads for each degree
            triads = []
            for i in range(len(scale)):
                root = scale_note_names[i]
                third = scale_note_names[(i + 2) % len(scale)]
                fifth = scale_note_names[(i + 4) % len(scale)]
                triads.append([root, third, fifth])
            roman_map = {
                "I": triads[0],
                "ii": triads[1],
                "iii": triads[2],
                "IV": triads[3],
                "V": triads[4],
                "vi": triads[5],
                "vii°": triads[6] if len(triads) > 6 else triads[0],
            }
            notes = roman_map.get(roman, triads[0])
            # Apply extension, inversion, voicing as in export_midi
            if extension == "+6th":
                # Add 6th degree
                sixth = scale_note_names[(roman_to_degree[roman] + 5) % len(scale_note_names)]
                notes = notes + [sixth]
            elif extension == "+7th":
                # Add 7th degree
                seventh = scale_note_names[(roman_to_degree[roman] + 6) % len(scale_note_names)]
                notes = notes + [seventh]
            elif extension == "+9th":
                ninth = scale_note_names[(roman_to_degree[roman] + 1) % len(scale_note_names)]
                notes = notes + [ninth]
            elif extension == "sus2":
                notes[1] = scale_note_names[(roman_to_degree[roman] + 1) % len(scale_note_names)]
            elif extension == "sus4":
                notes[1] = scale_note_names[(roman_to_degree[roman] + 3) % len(scale_note_names)]
            if inversion == "1st":
                notes = notes[1:] + notes[:1]
            elif inversion == "2nd":
                notes = notes[2:] + notes[:2]
            if voicing == "Open" and len(notes) >= 3:
                notes = [notes[0], notes[1], notes[2]]
            elif voicing == "Drop 2" and len(notes) >= 3:
                notes = [notes[0], notes[2], notes[1]]
            # For "Custom" voicing, do nothing special (user-defined, not implemented)
            # If "Custom" is selected, the voicing is not applied; user can implement their own logic here.
            freqs = [note_map.get(n, 261.63) for n in notes]
            print(f"[DEBUG] get_chord_frequencies returning: {freqs}")
            return freqs
        # Attach as method
        setattr(MainWindow, "get_chord_frequencies", get_chord_frequencies)

        # Add panels to the layout
        main_layout.addWidget(self.chord_panel, 1)
        main_layout.addWidget(self.structure_panel, 1)
        main_layout.addWidget(self.settings_panel, 1)

        self.setLayout(main_layout)
        self.setMinimumSize(1200, 700)  # Adjust window size to fit panels comfortably
        self.setMaximumSize(1400, 900)

        # Set tab order for accessibility (explicitly across panels)
        if hasattr(self.chord_panel, "add_btn"):
            self.setTabOrder(self.chord_panel.add_btn, self.structure_panel)
        if hasattr(self.structure_panel, "card_widgets") and self.structure_panel.card_widgets:
            self.setTabOrder(self.structure_panel.card_widgets[-1], self.settings_panel.tempo_spin)
        self.setTabOrder(self.settings_panel.tempo_spin, self.settings_panel.key_combo)
        self.setTabOrder(self.settings_panel.key_combo, self.settings_panel.mode_combo)
        self.setTabOrder(self.settings_panel.mode_combo, self.settings_panel.play_btn)

    def keyPressEvent(self, event):
        # Space or Enter: Play/Stop toggle (when not in a text field)
        focus_widget = QApplication.focusWidget()
        if event.key() in (Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter):
            if isinstance(focus_widget, QPushButton):
                focus_widget.click()
            elif not self.is_playing:
                self.settings_panel.play_btn.click()
            else:
                self.settings_panel.stop_btn.click()
        # Left/Right: Navigate chord slots in structure panel
        elif event.key() == Qt.Key_Right:
            if hasattr(self.structure_panel, "card_widgets") and self.structure_panel.card_widgets:
                focused = -1
                for i, card in enumerate(self.structure_panel.card_widgets):
                    if card.hasFocus():
                        focused = i
                        break
                next_idx = (focused + 1) % len(self.structure_panel.card_widgets)
                self.structure_panel.card_widgets[next_idx].setFocus()
        elif event.key() == Qt.Key_Left:
            if hasattr(self.structure_panel, "card_widgets") and self.structure_panel.card_widgets:
                focused = -1
                for i, card in enumerate(self.structure_panel.card_widgets):
                    if card.hasFocus():
                        focused = i
                        break
                prev_idx = (focused - 1) % len(self.structure_panel.card_widgets)
                self.structure_panel.card_widgets[prev_idx].setFocus()
        # Up/Down: Move between panels (Chord, Structure, Settings)
        elif event.key() == Qt.Key_Down:
            if focus_widget in self.chord_panel.btns:
                self.structure_panel.setFocus()
            elif focus_widget in getattr(self.structure_panel, "card_widgets", []):
                self.settings_panel.play_btn.setFocus()
        elif event.key() == Qt.Key_Up:
            if focus_widget in getattr(self.structure_panel, "card_widgets", []):
                self.chord_panel.btns[0].setFocus()
            elif focus_widget in [self.settings_panel.play_btn, self.settings_panel.stop_btn, self.settings_panel.export_btn]:
                self.structure_panel.setFocus()
        else:
            super().keyPressEvent(event)

if __name__ == "__main__":
    app = QApplication([])
    # Set global font and stylesheet for professional, accessible look
    from PyQt5.QtGui import QFont, QFontDatabase
    base_font = QFontDatabase.systemFont(QFontDatabase.GeneralFont)
    base_font.setFamily("Palatino" if QFont("Palatino").exactMatch() else "Georgia")
    base_font.setPointSizeF(base_font.pointSizeF() * app.devicePixelRatio())
    app.setFont(base_font)
    app.setStyleSheet("""
        QWidget {
            color: #222;
            background: #faf9f6;
            font-family: Palatino, Georgia, serif;
            font-size: 18px;
        }
        QLabel {
            color: #222;
        }
        QPushButton {
            font-family: Palatino, Georgia, serif;
            font-size: 18px;
            font-weight: bold;
            outline: none;
        }
        QPushButton:focus, QComboBox:focus, QSpinBox:focus {
            outline: 2px solid #1976d2; outline-offset: 2px;
        }
        QComboBox, QSpinBox {
            font-family: Palatino, Georgia, serif;
            font-size: 16px;
            color: #222;
            background: #fff;
        }
        QComboBox:focus, QSpinBox:focus {
            border: 2px solid #1976d2;
        }
        /* Global stylesheet */
        QLabel, QPushButton {
            font-family: "Palatino", "Georgia", serif;
            font-size: 16pt;
            font-weight: bold;
        }
    """)
    window = MainWindow()
    # Remove setTabOrder for add_btn (no longer present)
    # window.setTabOrder(window.chord_panel.add_btn, window.settings_panel.play_btn)
    if hasattr(window.settings_panel, "play_btn") and hasattr(window.settings_panel, "stop_btn") and hasattr(window.settings_panel, "tempo_spin"):
        window.setTabOrder(window.settings_panel.play_btn, window.settings_panel.stop_btn)
        window.setTabOrder(window.settings_panel.stop_btn, window.settings_panel.tempo_spin)
    window.show()
    app.exec_()
