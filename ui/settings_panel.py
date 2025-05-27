from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QSizePolicy, QFrame, QPushButton, QLabel, QSpinBox, QComboBox, QHBoxLayout, QCheckBox
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPainter, QBrush, QPolygon
from PyQt5.QtCore import Qt, QPoint

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

class SettingsPanel(QWidget):
    def __init__(self, on_play, on_stop, is_playing, tempo, set_tempo, on_export_midi, key, set_key, mode, set_mode, pattern_bars, set_pattern_bars, quantization, set_quantization):
        super().__init__()
        card_frame = QFrame(self)
        card_frame.setMinimumWidth(PANEL_W)
        card_frame.setMinimumHeight(PANEL_H)
        card_frame.setStyleSheet(PANEL_STYLE)
        card_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout = QVBoxLayout(card_frame)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

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

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(24)

        label_width = 60

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
        uniform_input_width = 180
        self.tempo_spin.setFixedWidth(uniform_input_width)
        tempo_container = QWidget()
        tempo_layout = QHBoxLayout(tempo_container)
        tempo_layout.setContentsMargins(0, 0, 0, 0)
        tempo_layout.setAlignment(Qt.AlignRight)
        tempo_layout.addWidget(self.tempo_spin)
        form.addRow(tempo_label, tempo_container)

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

        self.key_combo.setFixedWidth(uniform_input_width)
        key_widget = QWidget()
        key_layout = QHBoxLayout(key_widget)
        key_layout.setContentsMargins(0, 0, 0, 0)
        key_layout.setSpacing(18)
        key_layout.addWidget(self.key_combo)
        key_layout.addWidget(self.key_toggle_btn)
        key_container = QWidget()
        key_row_layout = QHBoxLayout(key_container)
        key_row_layout.setContentsMargins(0, 0, 0, 0)
        key_row_layout.setAlignment(Qt.AlignRight)
        key_row_layout.addWidget(key_widget)
        form.addRow(key_label, key_container)

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
        self.mode_combo.addItems([
            "Major (Ionian)", "Dorian", "Phrygian", "Lydian", "Mixolydian", "Minor (Aeolian)",
            "Locrian", "Gypsy Minor", "Harmonic Minor", "Minor Pentatonic", "Whole Tone",
            "Tonic 2nds", "Tonic 3rds", "Tonic 4ths", "Tonic 6ths"
        ])
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
        mode_container = QWidget()
        mode_layout = QHBoxLayout(mode_container)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        mode_layout.setAlignment(Qt.AlignRight)
        mode_layout.addWidget(self.mode_combo)
        form.addRow(mode_label, mode_container)

        layout.addLayout(form)

        random_block_label = QLabel("Random Block Placement")
        random_block_label.setStyleSheet(
            "font-family: Palatino, Georgia, serif;"
            "font-size: 18px;"
            "font-weight: 600;"
            "color: #222;"
        )
        random_block_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

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

        form.addRow(random_block_label)
        form.addRow(QLabel("Min:"), min_spin)
        form.addRow(QLabel("Max:"), max_spin)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(card_frame)
        self.setLayout(main_layout)

        # Expose a method to get the current tempo value
        self.get_tempo = lambda: self.tempo_spin.value()
