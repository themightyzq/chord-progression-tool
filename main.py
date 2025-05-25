import threading
import time
import numpy as np
from functools import partial
from pattern_editor_panel import PatternEditorPanel

import sounddevice as sd
# --- SustainedSynth class for real-time note on/off audio playback ---
class SustainedSynth:
    """
    Simple polyphonic synthesizer supporting sustained notes (note on/off, all_notes_off).
    Uses a background audio callback and maintains active notes.
    """
    def __init__(self, fs=44100):
        self.fs = fs
        self.active_notes = {}  # frequency -> count
        self.lock = threading.Lock()
        self.stream = None
        self.phase = {}
        self.running = False

    def start(self):
        if self.stream is not None:
            return
        self.running = True
        self.stream = sd.OutputStream(
            samplerate=self.fs,
            channels=1,
            dtype="float32",
            callback=self._callback,
            blocksize=0,
            finished_callback=self._on_stream_finished
        )
        self.stream.start()

    def stop(self):
        self.running = False
        self.all_notes_off()
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        self.phase = {}

    def note_on(self, freqs):
        with self.lock:
            for f in freqs:
                self.phase[f] = self.phase.get(f, 0.0)
                self.active_notes[f] = self.active_notes.get(f, 0) + 1

    def note_off(self, freqs):
        with self.lock:
            for f in freqs:
                if f in self.active_notes:
                    self.active_notes[f] -= 1
                    if self.active_notes[f] <= 0:
                        del self.active_notes[f]
                        self.phase.pop(f, None)

    def all_notes_off(self):
        with self.lock:
            self.active_notes.clear()
            self.phase = {}

    def _callback(self, outdata, frames, time_info, status):
        t = np.arange(frames) / self.fs
        chunk = np.zeros(frames, dtype=np.float32)
        with self.lock:
            notes = list(self.active_notes)
            for f in notes:
                ph = self.phase.get(f, 0.0)
                s = np.sin(2 * np.pi * f * t + ph)
                chunk += 0.2 * s
                # Update phase for next chunk
                self.phase[f] = (ph + 2 * np.pi * f * frames / self.fs) % (2 * np.pi)
        # Normalize and output
        if len(self.active_notes) > 0:
            chunk = chunk / max(1, len(self.active_notes))
        outdata[:] = chunk.reshape(-1, 1)

    def _on_stream_finished(self):
        pass

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
        card_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        card_layout.setSpacing(0)
        card_layout.setContentsMargins(16, 16, 16, 16)

        # Header
        header = QLabel("Chord")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet(
            "font-family: Palatino, Georgia, serif;"
            "font-weight: bold;"
            "font-size: 28pt;"
            "margin-top: 0px;"
            "margin-bottom: 12px;"
            "color: #222;"
        )

        # Chord wheel group (centered with header)
        from PyQt5.QtGui import QFont
        wheel = QWidget(card_frame)
        # make it exactly as wide as the panel minus margins (16px each side)
        wheel.setFixedSize(PANEL_W - 32, PANEL_W - 32)

        # Create a container widget for wheel only (no header)
        wheel_group = QWidget(card_frame)
        wheel_group_layout = QVBoxLayout(wheel_group)
        wheel_group_layout.setContentsMargins(0, 0, 0, 0)
        wheel_group_layout.setSpacing(8)
        wheel_group_layout.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        # Only the wheel in the group (header will be placed outside)
        wheel_group_layout.addWidget(wheel, alignment=Qt.AlignHCenter)

        # Place header at the top of the card (outside wheel_group)
        card_layout.addWidget(header, alignment=Qt.AlignTop | Qt.AlignHCenter)
        card_layout.addWidget(wheel_group, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        self.roman_numerals = ["I", "ii", "iii", "IV", "V", "vi", "vii°"]
        self.btns = []
        degree_colors = {
            "I": "#1976d2", "IV": "#1976d2", "V": "#1976d2",
            "ii": "#388e3c", "iii": "#388e3c", "vi": "#388e3c",
            "vii°": "#d32f2f"
        }
        # compute center & radius based on the actual wheel size
        size = wheel.width()
        center = size / 2
        radius = center - 60   # bring the roman‐numeral buttons in closer to center

        for i, roman in enumerate(self.roman_numerals):
            angle = (i / len(self.roman_numerals)) * 2 * math.pi - (math.pi / 2)
            x = center + radius * math.cos(angle) - 40
            y = center + radius * math.sin(angle) - 40
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
        # Center the button exactly in the wheel, with a small nudge for visual centering
        add_chord_center.move(
            (wheel.width() - add_chord_center.width()) // 2 + 1,
            (wheel.height() - add_chord_center.height()) // 2 + 2
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
        # Standardize panel height to match others
        self.setMinimumHeight(PANEL_H)
        self.setMaximumHeight(PANEL_H)
        card_layout = QVBoxLayout(card_frame)
        card_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        card_layout.setSpacing(12)
        card_layout.setContentsMargins(12, 12, 12, 12)

        # Header
        header = QLabel("Chord Structure")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet(
            "font-family: Palatino, Georgia, serif;"
            "font-weight: bold;"
            "font-size: 28pt;"
            "margin-top: 0px;"
            "margin-bottom: 12px;"
            "color: #222;"
        )
        card_layout.addWidget(header, alignment=Qt.AlignTop | Qt.AlignHCenter)

        # Chord slots and instructional text
        from PyQt5.QtWidgets import QPushButton
        self.cards_layout = QVBoxLayout()
        self.cards_layout.setSpacing(3)

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
        from PyQt5.QtWidgets import QFrame
        chords = chords[:8]  # Limit to 8 chords max
        # Reserve space for up to 8 cards, matching panel height
        self.setFixedHeight(PANEL_H)
        # Remove old cards/layouts
        self.card_widgets = []
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            else:
                # If item is a layout, delete all its widgets/layouts recursively
                sublayout = item.layout() if hasattr(item, "layout") else None
                if sublayout:
                    while sublayout.count():
                        subitem = sublayout.takeAt(0)
                        subwidget = subitem.widget()
                        if subwidget:
                            subwidget.deleteLater()
        if not chords:
            # Centered instructional text
            empty = QLabel("Construct your chord progression here.")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet("color: #bbb; font-family: Palatino, Georgia, serif; font-size: 13pt; margin-top: 18px;")
            self.cards_layout.addWidget(empty)
            # Show 4 empty outlined boxes, centered
            from PyQt5.QtWidgets import QHBoxLayout
            slot_row = QHBoxLayout()
            slot_row.setSpacing(18)
            slot_row.setAlignment(Qt.AlignHCenter)
            for _ in range(4):
                slot = QFrame()
                slot.setFixedSize(48, 48)
                slot.setStyleSheet(
                    "background: #fff; border: 2.5px solid #bbb; border-radius: 10px;"
                )
                slot.setFocusPolicy(Qt.StrongFocus)
                slot.setToolTip("Empty chord slot (Tab to focus)")
                slot_row.addWidget(slot)
            self.cards_layout.addLayout(slot_row)
        else:
            # Always reserve 8 vertical slots, never overlap
            from PyQt5.QtWidgets import QVBoxLayout, QFrame
            for i in range(8):
                slot_container = QVBoxLayout()
                slot_container.setContentsMargins(0, 0, 0, 0)
                slot_container.setSpacing(2)
                if i < len(chords):
                    card = self.create_card(chords[i], i)
                    slot_container.addWidget(card)
                    self.card_widgets.append(card)
                else:
                    spacer = QFrame()
                    spacer.setFixedHeight(52)
                    slot_container.addWidget(spacer)
                self.cards_layout.addLayout(slot_container)

    def create_card(self, chord, idx):
        from PyQt5.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QWidget, QSpacerItem, QSizePolicy
        from PyQt5.QtGui import QFont, QIcon, QPixmap, QPainter, QBrush, QPolygon
        from PyQt5.QtCore import Qt, QPoint
        roman = chord["roman"]
        color = "#1976d2" if roman in ["I", "IV", "V"] else "#388e3c" if roman in ["ii", "iii", "vi"] else "#d32f2f"
        card = QFrame()
        card.setObjectName("chordCard")
        card.setFixedHeight(52)
        card.setStyleSheet(
            f"""
            QFrame#chordCard {{
                border: 1.5px solid {color};
                border-radius: 16px;
                margin-bottom: 8px;
                background: #fff;
            }}
            """
        )
        from PyQt5.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(16)
        shadow.setOffset(0, 4)
        shadow.setColor(Qt.gray)
        card.setGraphicsEffect(shadow)
        card.setFocusPolicy(Qt.StrongFocus)
        card.setToolTip(f"Chord: {roman} (hover to preview, drag to reorder)")
        card_layout = QHBoxLayout()
        # Consistent margins and spacing for card layout
        card_layout.setContentsMargins(8, 6, 8, 6)
        card_layout.setSpacing(6)
        card_layout.setAlignment(Qt.AlignVCenter)

        # Uniform button/label size
        btn_size = 28

        # Helper to strictly vertically & horizontally center a widget
        def center_wrap(widget):
            container = QWidget()
            layout = QVBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setAlignment(Qt.AlignCenter)
            layout.addWidget(widget)
            return container

        # Play button (uniform size)
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
        play_btn.setFixedSize(btn_size, btn_size)
        play_btn.setStyleSheet(
            """
            QPushButton {
                background: #1976d2;
                border-radius: 8px;
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
        play_btn.clicked.connect(make_play(idx))
        play_btn_container = center_wrap(play_btn)
        play_btn_container.layout().setAlignment(Qt.AlignCenter)
        card_layout.addWidget(play_btn_container)

        # Roman numeral label (uniform size to buttons)
        label = QLabel(roman, card)
        label.setAlignment(Qt.AlignCenter)
        font = QFont("Palatino")
        if not font.exactMatch():
            font = QFont("Georgia")
        font.setPointSize(14)
        font.setWeight(QFont.Bold)
        label.setFont(font)
        label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: {color};
            border: 2px solid {color};
            border-radius: 10px;
            padding: 0px 0px;
        """)
        label.setWordWrap(False)
        label.setFixedSize(btn_size, btn_size)
        label.setAlignment(Qt.AlignCenter)
        label_container = center_wrap(label)
        # Remove any extra setContentsMargins offsets
        label_container.setContentsMargins(0, 0, 0, 0)
        label_container.layout().setAlignment(Qt.AlignCenter)
        card_layout.addWidget(label_container)

        # Add spacing between Roman numeral and modifier row
        card_layout.addSpacing(6)

        # Modifier row (modifiers, centered vertically, with spacers on both sides)
        mod_row = QHBoxLayout()
        mod_row.setSpacing(8)
        mod_row.setContentsMargins(0, 0, 0, 0)
        mod_row.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        # Left spacer
        mod_row.addItem(QSpacerItem(4, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        if chord.get("extension"):
            ext_pill = QLabel(chord["extension"])
            ext_pill.setFixedHeight(22)
            ext_pill.setMinimumHeight(22)
            ext_pill.setMinimumWidth(44)
            ext_pill.setAlignment(Qt.AlignCenter)
            ext_pill.setStyleSheet(
                f"""
                background: #fff;
                color: {color};
                border: 2px solid {color};
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
                padding: 0px 6px;
                """
            )
            mod_row.addWidget(center_wrap(ext_pill))
        if chord.get("inversion"):
            inv_pill = QLabel(chord["inversion"])
            inv_pill.setFixedHeight(22)
            inv_pill.setMinimumHeight(22)
            inv_pill.setMinimumWidth(44)
            inv_pill.setAlignment(Qt.AlignCenter)
            inv_pill.setStyleSheet(
                f"""
                background: #fff;
                color: {color};
                border: 2px solid {color};
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
                padding: 0px 6px;
                """
            )
            mod_row.addWidget(center_wrap(inv_pill))
        if chord.get("voicing"):
            voicing_pill = QLabel(chord["voicing"])
            voicing_pill.setFixedHeight(22)
            voicing_pill.setMinimumHeight(22)
            voicing_pill.setMinimumWidth(44)
            voicing_pill.setAlignment(Qt.AlignCenter)
            voicing_pill.setStyleSheet(
                f"""
                background: #fff;
                color: {color};
                border: 2px solid {color};
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
                padding: 0px 6px;
                """
            )
            mod_row.addWidget(center_wrap(voicing_pill))
        # Right spacer
        mod_row.addItem(QSpacerItem(4, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        # Wrap mod_row in a QWidget for vertical centering
        mod_row_container = QWidget()
        mod_row_container.setLayout(mod_row)
        mod_row.layout().setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        card_layout.addWidget(mod_row_container)

        # Edit/settings button (uniform size)
        edit_btn = QPushButton("✎", card)
        edit_btn.setFixedSize(btn_size, btn_size)
        edit_btn.setStyleSheet(
            "QPushButton {background: #fff; color: #1976d2; border: 2px solid #1976d2; font-size: 22px; font-weight: bold; border-radius: 8px;}"
            "QPushButton:focus { box-shadow: 0 0 0 2px #1976d244; }"
            "QPushButton:hover { background: #e3f2fd; }"
        )
        edit_btn.setFocusPolicy(Qt.StrongFocus)
        edit_btn.setToolTip("Edit this chord")
        edit_btn.clicked.connect(lambda checked, idx=idx: self.show_modifier_popup(idx))
        edit_btn_container = center_wrap(edit_btn)
        edit_btn_container.layout().setAlignment(Qt.AlignCenter)
        card_layout.addWidget(edit_btn_container)

        # Delete button (uniform size)
        del_btn = QPushButton("✕", card)
        del_btn.setFixedSize(btn_size, btn_size)
        del_btn.setStyleSheet(
            "QPushButton {background: #fff; color: #888; border: none; font-size: 24px; font-weight: bold; border-radius: 8px;}"
            "QPushButton:focus { box-shadow: 0 0 0 2px #8884; }"
            "QPushButton:hover { background: #f0f0f0; }"
        )
        del_btn.setFocusPolicy(Qt.StrongFocus)
        del_btn.setToolTip("Remove this chord from progression")
        del_btn.clicked.connect(lambda checked, idx=idx: self.on_delete(idx))
        del_btn_container = center_wrap(del_btn)
        del_btn_container.layout().setAlignment(Qt.AlignCenter)
        card_layout.addWidget(del_btn_container)

        # Ensure all widgets are vertically centered in the card
        card_layout.setAlignment(Qt.AlignVCenter)

        card.setLayout(card_layout)
        return card

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
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QRadioButton, QButtonGroup, QDialogButtonBox, QGroupBox

        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Chord Modifiers")
        dialog.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border-radius: 16px;
                padding: 20px;
            }
            QGroupBox {
                margin-top: 24px;
                padding-top: 16px;
                font-family: Palatino, Georgia, serif;
                font-size: 18pt;
                font-weight: bold;
                color: #222;
                border: 1.5px solid #bbb;
                border-radius: 10px;
                background: #fff;
            }
            QGroupBox:title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                margin-top: -16px;
                font-size: 18pt;
                font-weight: bold;
                color: #222;
                background: transparent;
            }
            QRadioButton {
                background-color: #ffffff;
            }
            QWidget {
                background-color: #ffffff;
            }
        """)

        dialog_layout = QVBoxLayout(dialog)
        dialog_layout.setContentsMargins(24, 24, 24, 24)
        dialog_layout.setSpacing(20)

        # Add extension, inversion, and voicing groups with large QLabel headers and border-only QGroupBox

        from PyQt5.QtGui import QFont

        # --- Extension Section ---
        ext_label = QLabel("Select Extension:")
        ext_label_font = QFont("Palatino" if QFont("Palatino").exactMatch() else "Georgia")
        ext_label_font.setPointSize(20)
        ext_label_font.setWeight(QFont.Bold)
        ext_label.setFont(ext_label_font)
        ext_label.setStyleSheet("margin-top: 25px; margin-bottom: 25px;")
        ext_label.setMinimumHeight(25)
        dialog_layout.addWidget(ext_label)

        ext_groupbox = QGroupBox()
        ext_groupbox.setStyleSheet("QGroupBox { border: 2px solid #bbb; border-radius: 14px; margin-bottom: 10px; background: #fff; }")
        ext_layout = QGridLayout()
        ext_layout.setHorizontalSpacing(16)
        ext_layout.setVerticalSpacing(5)
        ext_group = QButtonGroup(dialog)
        ext_radios = []
        ext_options = ["None", "+6th", "+7th", "+9th", "sus2", "sus4"]
        for i, opt in enumerate(ext_options):
            radio = QRadioButton(opt)
            ext_group.addButton(radio)
            ext_layout.addWidget(radio, i // 2, i % 2)
            ext_radios.append(radio)
        ext_groupbox.setLayout(ext_layout)
        dialog_layout.addWidget(ext_groupbox)

        # --- Inversion Section ---
        inv_label = QLabel("Select Inversion:")
        inv_label_font = QFont("Palatino" if QFont("Palatino").exactMatch() else "Georgia")
        inv_label_font.setPointSize(20)
        inv_label_font.setWeight(QFont.Bold)
        inv_label.setFont(inv_label_font)
        inv_label.setStyleSheet("margin-top: 25px; margin-bottom: 25px;")
        inv_label.setMinimumHeight(25)
        dialog_layout.addWidget(inv_label)

        inv_groupbox = QGroupBox()
        inv_groupbox.setStyleSheet("QGroupBox { border: 2px solid #bbb; border-radius: 14px; margin-bottom: 18px; background: #fff; }")
        inv_layout = QVBoxLayout()
        inv_layout.setSpacing(5)
        inv_group = QButtonGroup(dialog)
        inv_radios = []
        inv_options = ["None", "Root", "1st", "2nd"]
        for inv in inv_options:
            radio = QRadioButton(inv)
            inv_group.addButton(radio)
            inv_layout.addWidget(radio)
            inv_radios.append(radio)
        inv_groupbox.setLayout(inv_layout)
        dialog_layout.addWidget(inv_groupbox)

        # --- Voicing Section ---
        voicing_label = QLabel("Select Voicing:")
        voicing_label_font = QFont("Palatino" if QFont("Palatino").exactMatch() else "Georgia")
        voicing_label_font.setPointSize(20)
        voicing_label_font.setWeight(QFont.Bold)
        voicing_label.setFont(voicing_label_font)
        voicing_label.setStyleSheet("margin-top: 25px; margin-bottom: 25px;")
        voicing_label.setMinimumHeight(25)
        dialog_layout.addWidget(voicing_label)

        voicing_groupbox = QGroupBox()
        voicing_groupbox.setStyleSheet("QGroupBox { border: 2px solid #bbb; border-radius: 14px; margin-bottom: 18px; background: #fff; }")
        voicing_layout = QVBoxLayout()
        voicing_layout.setSpacing(5)
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
        dialog_layout.addWidget(voicing_groupbox)

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
        dialog_layout.addWidget(buttons)
        dialog.setLayout(dialog_layout)

        # Let Qt compute the required size for all content, then fix the dialog size
        dialog.adjustSize()
        dialog.setFixedSize(dialog.size())

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
    def __init__(self, on_play, on_stop, is_playing, tempo, set_tempo, on_export_midi, key, set_key, mode, set_mode, pattern_bars, set_pattern_bars, quantization, set_quantization):
        super().__init__()
        from PyQt5.QtWidgets import QFormLayout, QSizePolicy, QFrame, QPushButton
        # Card container for header + content
        card_frame = QFrame(self)
        card_frame.setMinimumWidth(PANEL_W)
        card_frame.setMaximumWidth(PANEL_W)
        card_frame.setMinimumHeight(PANEL_H)
        card_frame.setMaximumHeight(PANEL_H)
        card_frame.setStyleSheet(PANEL_STYLE)
        layout = QVBoxLayout(card_frame)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Header
        header = QLabel("Session Settings")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet(
            "font-family: Palatino, Georgia, serif;"
            "font-weight: bold;"
            "font-size: 28pt;"
            "margin-top: 16px;"
            "margin-bottom: 24px;"
            "color: #222;"
        )
        layout.addWidget(header, alignment=Qt.AlignTop | Qt.AlignHCenter)

        # Form layout for settings
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(24)

        # (Bars and quantization controls removed)


        # Standard label width for alignment
        label_width = 60

        # Tempo row
        tempo_label = QLabel("Tempo:")
        tempo_label.setStyleSheet(
            "font-family: Palatino, Georgia, serif;"
            "font-size: 18px;"
            "font-weight: 600;"
            "color: #222;"
        )
        tempo_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        tempo_label.setFixedWidth(label_width)

        self.tempo_spin = QSpinBox()
        self.tempo_spin.setRange(40, 240)
        self.tempo_spin.setValue(tempo)
        self.tempo_spin.setStyleSheet(
            "font-size: 16px;"
            "font-family: Palatino, Georgia, serif;"
            "padding: 4px 10px;"
            "border-radius: 6px;"
            "border: 1.5px solid #bbb;"
            "background-color: #f5f5f5;"
        )
        self.tempo_spin.setFocusPolicy(Qt.StrongFocus)
        self.tempo_spin.setToolTip("Set playback tempo (BPM)")
        self.tempo_spin.setPrefix("")
        self.tempo_spin.setSuffix(" BPM")
        self.tempo_spin.valueChanged.connect(set_tempo)
        # --- Uniform width for all input widgets ---
        uniform_input_width = 180
        self.tempo_spin.setFixedWidth(uniform_input_width)
        # Align tempo_spin to right in a layout
        from PyQt5.QtWidgets import QWidget, QHBoxLayout
        tempo_container = QWidget()
        tempo_layout = QHBoxLayout(tempo_container)
        tempo_layout.setContentsMargins(0, 0, 0, 0)
        tempo_layout.setAlignment(Qt.AlignRight)
        tempo_layout.addWidget(self.tempo_spin)
        form.addRow(tempo_label, tempo_container)

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
        layout.addLayout(button_row)
        layout.addWidget(self.export_btn)

        from PyQt5.QtWidgets import QCheckBox

        self.click_checkbox = QCheckBox("Enable Click Track")
        self.click_checkbox.setChecked(False)
        self.click_checkbox.setStyleSheet("font-size: 14pt; margin: 4px 0px 0px 12px; font-family: Palatino, Georgia, serif; background: transparent;")
        layout.addWidget(self.click_checkbox)

        def on_click_checkbox_changed(state):
            parent = self.parentWidget()
            while parent and not hasattr(parent, "click_enabled"):
                parent = parent.parentWidget()
            if parent:
                parent.click_enabled = (state == Qt.Checked)
        self.click_checkbox.stateChanged.connect(on_click_checkbox_changed)

        # Add loop playback checkbox
        self.loop_checkbox = QCheckBox("Loop Playback")
        self.loop_checkbox.setChecked(False)
        self.loop_checkbox.setStyleSheet("font-size: 14pt; margin: 4px 0px 0px 12px; font-family: Palatino, Georgia, serif; background: transparent;")
        layout.addWidget(self.loop_checkbox)

        def on_loop_checkbox_changed(state):
            parent = self.parentWidget()
            while parent and not hasattr(parent, "loop_enabled"):
                parent = parent.parentWidget()
            if parent:
                parent.loop_enabled = (state == Qt.Checked)
        self.loop_checkbox.stateChanged.connect(on_loop_checkbox_changed)

        # Key row
        key_label = QLabel("Key:")
        key_label.setStyleSheet(
            "font-family: Palatino, Georgia, serif;"
            "font-size: 18px;"
            "font-weight: 600;"
            "color: #222;"
        )
        key_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        key_label.setFixedWidth(label_width)

        self.key_combo = QComboBox()
        self.key_toggle_btn = QPushButton("Sharp")
        self.key_toggle_btn.setCheckable(True)
        self.key_toggle_btn.setChecked(False)
        self.key_toggle_btn.setFixedWidth(60)
        self.key_toggle_btn.setStyleSheet(
            "QPushButton {"
            "    font-size: 14px;"
            "    border-radius: 6px;"
            "    background: #e0e0e0;"
            "    color: #333;"
            "    font-weight: 600;"
            "    padding: 4px 10px;"
            "}"
            "QPushButton:checked {"
            "    background: #1976d2;"
            "    color: #fff;"
            "}"
        )
        self.key_combo.setStyleSheet(
            "font-size: 16px;"
            "font-family: Palatino, Georgia, serif;"
            "padding: 4px 10px;"
            "border-radius: 6px;"
            "border: 1.5px solid #bbb;"
            "background-color: #f5f5f5;"
        )
        self.key_combo.setFocusPolicy(Qt.StrongFocus)
        self.key_combo.setToolTip("Select key")

        self.key_options_sharps = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        self.key_options_flats = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

        def update_key_options():
            if self.key_toggle_btn.isChecked():
                self.key_toggle_btn.setText("♭")
                self.key_combo.clear()
                self.key_combo.addItems(self.key_options_flats)
                if key in self.key_options_flats:
                    self.key_combo.setCurrentText(key)
                else:
                    self.key_combo.setCurrentIndex(0)
            else:
                self.key_toggle_btn.setText("#")
                self.key_combo.clear()
                self.key_combo.addItems(self.key_options_sharps)
                if key in self.key_options_sharps:
                    self.key_combo.setCurrentText(key)
                else:
                    self.key_combo.setCurrentIndex(0)

        self.key_toggle_btn.toggled.connect(update_key_options)
        self.key_combo.currentTextChanged.connect(set_key)
        update_key_options()

        # --- Uniform width for key_combo ---
        self.key_combo.setFixedWidth(uniform_input_width)
        key_widget = QWidget()
        key_layout = QHBoxLayout(key_widget)
        key_layout.setContentsMargins(0, 0, 0, 0)
        key_layout.setSpacing(18)
        # Add key_combo first, then key_toggle_btn (toggle button to the right)
        key_layout.addWidget(self.key_combo)
        key_layout.addWidget(self.key_toggle_btn)
        # Wrap in a right-aligned layout
        key_container = QWidget()
        key_row_layout = QHBoxLayout(key_container)
        key_row_layout.setContentsMargins(0, 0, 0, 0)
        key_row_layout.setAlignment(Qt.AlignRight)
        key_row_layout.addWidget(key_widget)
        form.addRow(key_label, key_container)

        # Mode row
        mode_label = QLabel("Mode:")
        mode_label.setStyleSheet(
            "font-family: Palatino, Georgia, serif;"
            "font-size: 18px;"
            "font-weight: 600;"
            "color: #222;"
        )
        mode_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        mode_label.setFixedWidth(label_width)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems([m["label"] for m in MODES])
        self.mode_combo.setStyleSheet(
            "font-size: 16px;"
            "font-family: Palatino, Georgia, serif;"
            "padding: 4px 10px;"
            "border-radius: 6px;"
            "border: 1.5px solid #bbb;"
            "background-color: #f5f5f5;"
        )
        self.mode_combo.setFocusPolicy(Qt.StrongFocus)
        self.mode_combo.setToolTip("Select mode")
        self.mode_combo.currentTextChanged.connect(set_mode)
        self.mode_combo.setFixedWidth(uniform_input_width)
        # Align mode_combo to right in a layout
        mode_container = QWidget()
        mode_layout = QHBoxLayout(mode_container)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        mode_layout.setAlignment(Qt.AlignRight)
        mode_layout.addWidget(self.mode_combo)
        form.addRow(mode_label, mode_container)

        layout.addLayout(form)

        # Random Block Placement Section
        random_block_label = QLabel("Random Block Placement")
        random_block_label.setStyleSheet(
            "font-family: Palatino, Georgia, serif;"
            "font-size: 18px;"
            "font-weight: 600;"
            "color: #222;"
        )
        random_block_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # Min spin box
        min_spin = QSpinBox()
        min_spin.setRange(1, 32)
        min_spin.setValue(1)
        min_spin.setFixedWidth(uniform_input_width)
        min_spin.setStyleSheet(
            "font-size: 16px;"
            "font-family: Palatino, Georgia, serif;"
            "padding: 4px 10px;"
            "border-radius: 6px;"
            "border: 1.5px solid #bbb;"
            "background-color: #f5f5f5;"
        )
        min_spin.setFocusPolicy(Qt.StrongFocus)
        min_spin.setToolTip("Minimum number of blocks to generate")
        min_spin.valueChanged.connect(lambda val: setattr(self.parentWidget().pattern_panel, "max_blocks_min", val))

        # Max spin box
        max_spin = QSpinBox()
        max_spin.setRange(1, 32)
        max_spin.setValue(6)
        max_spin.setFixedWidth(uniform_input_width)
        max_spin.setStyleSheet(
            "font-size: 16px;"
            "font-family: Palatino, Georgia, serif;"
            "padding: 4px 10px;"
            "border-radius: 6px;"
            "border: 1.5px solid #bbb;"
            "background-color: #f5f5f5;"
        )
        max_spin.setFocusPolicy(Qt.StrongFocus)
        max_spin.setToolTip("Maximum number of blocks to generate")
        max_spin.valueChanged.connect(lambda val: setattr(self.parentWidget().pattern_panel, "max_blocks_max", val))

        # Add to form layout
        form.addRow(random_block_label)
        form.addRow(QLabel("Min:"), min_spin)
        form.addRow(QLabel("Max:"), max_spin)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(card_frame)
        self.setLayout(main_layout)

# ==========================
# PatternEditorPanel (NEW UI SECTION)
# This widget adds a horizontal sequencer bar below the three main panels.
# It replicates the NDLR pattern editor: a grid where each chord has a row of step toggles.
# Each chord can trigger specific beats in a 16-step sequence.
# Playback uses the session tempo and division (quarter, eighth, sixteenth).
# This is the fourth "layer" in the UI, full-width, anchored under Chord, Structure, and Settings panels.
# ==========================
from PyQt5.QtWidgets import QScrollArea, QComboBox, QCheckBox, QSizePolicy
from PyQt5.QtCore import Qt

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chord Progression Tool")
        self.setStyleSheet("background: #f5f5f5;")
        # Main 3-column layout with styled panels
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(24)  # Reduced spacing between panels
        columns_layout.setContentsMargins(20, 20, 20, 20)  # Add margins around the layout
        columns_layout.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

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
            # Update pattern editor grid immediately when a chord is added
            if hasattr(self, "pattern_panel"):
                self.pattern_panel.set_chords(self.chord_progression)
                pass  # Removed automatic randomization on chord add

        def on_delete(idx):
            if 0 <= idx < len(self.chord_progression):
                self.chord_progression.pop(idx)
                self.structure_panel.update_chords(self.chord_progression)

        # Playback state and handlers (must be defined before panel creation)
        self.is_playing = False
        self.tempo = 100
        self.key = "C"
        self.mode = "Major (Ionian)"
        self.synth = SustainedSynth()
        self.playback_thread = None
        self.click_enabled = False
        self.loop_enabled = False

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
            sd.play(audio, fs)
            sd.wait()
        setattr(MainWindow, "play_chord_tone", play_chord_tone)

        def on_play():
            if self.is_playing:
                on_stop()
                time.sleep(0.1)  # Ensure cleanup
            self.is_playing = True
            self.synth.start()
            print("Playback started at", self.tempo, "BPM")
            from PyQt5.QtCore import QTimer

            pattern_panel = getattr(self, "pattern_panel", None)
            pattern_length = 32  # Always 32 steps
            bpm = self.tempo
            step_duration = 60 / bpm / 4  # Sixteenth notes

            def play_loop():
                step_idx = 0
                while self.is_playing:
                    if pattern_panel:
                        QTimer.singleShot(0, partial(pattern_panel.highlight_step, step_idx))

                    if self.click_enabled:
                        fs = 44100
                        duration = 0.05
                        freq = 1760 if step_idx % 16 == 0 else 1200
                        t = np.linspace(0, duration, int(fs * duration), False)
                        click = 0.5 * np.sin(2 * np.pi * freq * t)
                        fade = np.linspace(1, 0, int(fs * duration))
                        click = click * fade
                        sd.play(click, fs, blocking=False)

                    blocks = pattern_panel.blocks if pattern_panel else []
                    print(f"[DEBUG] Blocks at step {step_idx}: {blocks}")
                    blocks_starting = [b for b in blocks if b["start"] == step_idx]
                    print(f"[DEBUG] Blocks starting at step {step_idx}: {blocks_starting}")
                    blocks_ending = [b for b in blocks if b["start"] + b["length"] == step_idx]

                    for block in blocks_starting:
                        chord_idx = block["chord_idx"]
                        if 0 <= chord_idx < len(self.chord_progression):
                            chord = self.chord_progression[chord_idx]
                            freqs = self.get_chord_frequencies(
                                chord["roman"],
                                chord.get("extension"),
                                chord.get("inversion"),
                                chord.get("voicing"),
                                key=self.key,
                                mode=self.mode
                            )
                            self.synth.note_on(freqs)

                    for block in blocks_ending:
                        chord_idx = block["chord_idx"]
                        if 0 <= chord_idx < len(self.chord_progression):
                            chord = self.chord_progression[chord_idx]
                            freqs = self.get_chord_frequencies(
                                chord["roman"],
                                chord.get("extension"),
                                chord.get("inversion"),
                                chord.get("voicing"),
                                key=self.key,
                                mode=self.mode
                            )
                            self.synth.note_off(freqs)

                    time.sleep(step_duration)
                    step_idx += 1
                    if step_idx >= pattern_length:
                        if self.loop_enabled:
                            step_idx = 0
                        else:
                            break

                if pattern_panel:
                    QTimer.singleShot(0, partial(pattern_panel.highlight_step, -1))
                self.synth.all_notes_off()
                self.is_playing = False

            self.playback_thread = threading.Thread(target=play_loop, daemon=True)
            self.playback_thread.start()

        def on_stop():
            self.is_playing = False
            if self.playback_thread is not None and self.playback_thread.is_alive():
                self.playback_thread.join(timeout=1.0)
                self.playback_thread = None
            self.structure_panel.highlight_card(-1)
            if hasattr(self, "pattern_panel"):
                self.pattern_panel.highlight_step(-1)
            self.synth.stop()

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
                "G": 67, "G#": 68, "A": 69, "A#": 70, "B": 71,
                "Db": 61, "Eb": 63, "Gb": 66, "Ab": 68, "Bb": 70
            }
            def get_midi_notes(roman, extension=None, inversion=None, voicing=None, key="C"):
                # This function should match the get_chord_frequencies logic as close as possible
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

            # Use pattern editor blocks for MIDI, reflecting all overlapping chords and durations
            pattern_panel = getattr(self, "pattern_panel", None)
            bars = getattr(pattern_panel, "pattern_bars", 1) if pattern_panel else 1
            quant = getattr(pattern_panel, "quantization", "Sixteenth") if pattern_panel else "Sixteenth"
            quant_to_steps = {"Whole": 1, "Half": 2, "Quarter": 4, "Eighth": 8, "Sixteenth": 16}
            grid_steps = bars * 16
            if pattern_panel:
                blocks = list(pattern_panel.blocks)
            else:
                blocks = []
            # Each step is a time point; for each block, schedule note_on at start, note_off at end
            # Build a list of note events: (step, onoff, midi_note, block)
            events = []
            for block in blocks:
                chord_idx = block["chord_idx"]
                if 0 <= chord_idx < len(self.chord_progression):
                    chord = self.chord_progression[chord_idx]
                    notes = get_midi_notes(
                        chord["roman"],
                        chord.get("extension"),
                        chord.get("inversion"),
                        chord.get("voicing"),
                        key=self.key
                    )
                    start = block["start"]
                    end = block["start"] + block["length"]
                    for n in notes:
                        events.append((start, "on", n))
                        events.append((end, "off", n))
            # Sort events by step, with note_off before note_on at same step
            events.sort(key=lambda e: (e[0], 0 if e[1] == "off" else 1))
            # Calculate ticks per step
            # Each quantization step is a fraction of a quarter note
            if quant == "Whole":
                steps_per_bar = 1
                ticks_per_step = ticks_per_beat * 4
            elif quant == "Half":
                steps_per_bar = 2
                ticks_per_step = ticks_per_beat * 2
            elif quant == "Quarter":
                steps_per_bar = 4
                ticks_per_step = ticks_per_beat
            elif quant == "Eighth":
                steps_per_bar = 8
                ticks_per_step = ticks_per_beat // 2
            elif quant == "Sixteenth":
                steps_per_bar = 16
                ticks_per_step = ticks_per_beat // 4
            else:
                steps_per_bar = 16
                ticks_per_step = ticks_per_beat // 4
            # Write all events in order, keeping track of time since last event
            last_step = 0
            last_event_time = 0
            notes_on = set()
            for i, event in enumerate(events):
                step, onoff, n = event
                delta_steps = step - last_step
                delta_ticks = delta_steps * ticks_per_step
                # For simultaneous events, only advance time for the first event at a new step
                time_val = delta_ticks if i == 0 or step != last_step else 0
                if onoff == "on":
                    track.append(mido.Message('note_on', note=n, velocity=80, time=time_val))
                    notes_on.add(n)
                else:
                    track.append(mido.Message('note_off', note=n, velocity=64, time=time_val))
                    notes_on.discard(n)
                last_step = step
            # Ensure all notes are turned off at the end
            for n in notes_on:
                track.append(mido.Message('note_off', note=n, velocity=64, time=0))
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

        # Pattern editor state for bars and quantization
        self.pattern_bars = 2
        self.quantization = "Sixteenth"
        def set_pattern_bars(val):
            self.pattern_bars = int(val)
            if hasattr(self, "pattern_panel"):
                self.pattern_panel.set_bars(val)
        def set_quantization(val):
            self.quantization = val
            if hasattr(self, "pattern_panel"):
                self.pattern_panel.set_quant(val)

        # Session Settings Panel
        self.settings_panel = SettingsPanel(
            on_play, on_stop, self.is_playing, self.tempo, set_tempo, export_midi,
            self.key, set_key, self.mode, set_mode,
            self.pattern_bars, set_pattern_bars, self.quantization, set_quantization
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
            print(f"[DEBUG] Frequencies to play: {freqs}")
            print(f"[DEBUG] get_chord_frequencies returning: {freqs}")
            return freqs
        # Attach as method
        setattr(MainWindow, "get_chord_frequencies", get_chord_frequencies)

        # Add panels to the columns layout
        columns_layout.addWidget(self.chord_panel, 1)
        columns_layout.addWidget(self.structure_panel, 1)
        columns_layout.addWidget(self.settings_panel, 1)

        # Pattern editor panel (full width, below columns)
        self.pattern_panel = PatternEditorPanel(self.chord_progression)
        # Snap toggle: removed; quantization is always used for rounding only
        # Wrap pattern editor in a scroll area for safe rendering
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.pattern_panel)

        # Main vertical layout for the window
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addLayout(columns_layout, 3)
        main_layout.addWidget(scroll, 1)

        self.setLayout(main_layout)
        self.setMinimumSize(1200, 800)  # Adjust window size to fit panels comfortably
        self.setMaximumSize(1600, 1200)

        # Set tab order for accessibility (explicitly across panels)
        if hasattr(self.chord_panel, "add_btn"):
            self.setTabOrder(self.chord_panel.add_btn, self.settings_panel.play_btn)
        if hasattr(self.settings_panel, "play_btn") and hasattr(self.settings_panel, "stop_btn") and hasattr(self.settings_panel, "tempo_spin"):
            self.setTabOrder(self.settings_panel.play_btn, self.settings_panel.stop_btn)
            self.setTabOrder(self.settings_panel.stop_btn, self.settings_panel.tempo_spin)
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
    window.setTabOrder(window.settings_panel.tempo_spin, window.settings_panel.key_combo)
    window.setTabOrder(window.settings_panel.key_combo, window.settings_panel.mode_combo)
    window.setTabOrder(window.settings_panel.mode_combo, window.settings_panel.play_btn)

    window.show()
    app.exec_()
