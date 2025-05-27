from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QPushButton, QLabel, QSpacerItem, QSizePolicy, QGraphicsDropShadowEffect, QDialog
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

class StructurePanel(QWidget):
    def __init__(self, chords, on_delete):
        super().__init__()
        self.chords = chords
        self.on_delete = on_delete
        from PyQt5.QtWidgets import QSizePolicy

        card_frame = QFrame(self)
        card_frame.setMinimumWidth(PANEL_W)
        card_frame.setMinimumHeight(PANEL_H)
        card_frame.setStyleSheet(PANEL_STYLE)
        card_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(PANEL_H)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        card_layout = QVBoxLayout(card_frame)
        card_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        card_layout.setSpacing(12)
        card_layout.setContentsMargins(12, 12, 12, 12)

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

        self.cards_layout = QVBoxLayout()
        self.cards_layout.setSpacing(3)

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
        chords = chords[:8]
        self.setFixedHeight(PANEL_H)
        self.card_widgets = []
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            else:
                sublayout = item.layout() if hasattr(item, "layout") else None
                if sublayout:
                    while sublayout.count():
                        subitem = sublayout.takeAt(0)
                        subwidget = subitem.widget()
                        if subwidget:
                            subwidget.deleteLater()
        if not chords:
            empty = QLabel("Construct your chord progression here.")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet("color: #bbb; font-family: Palatino, Georgia, serif; font-size: 13pt; margin-top: 18px;")
            self.cards_layout.addWidget(empty)
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
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(16)
        shadow.setOffset(0, 4)
        shadow.setColor(Qt.gray)
        card.setGraphicsEffect(shadow)
        card.setFocusPolicy(Qt.StrongFocus)
        card.setToolTip(f"Chord: {roman} (hover to preview, drag to reorder)")
        card_layout = QHBoxLayout()
        card_layout.setContentsMargins(8, 6, 8, 6)
        card_layout.setSpacing(6)
        card_layout.setAlignment(Qt.AlignVCenter)

        btn_size = 28

        def center_wrap(widget):
            container = QWidget()
            layout = QVBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setAlignment(Qt.AlignCenter)
            layout.addWidget(widget)
            return container

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
                        mode=parent.mode,
                        custom_voicing=chord.get("custom_voicing")
                    )
                    parent.play_chord_tone(freqs, duration=0.5, chord=chord)
            return play
        play_btn.clicked.connect(make_play(idx))
        play_btn_container = center_wrap(play_btn)
        play_btn_container.layout().setAlignment(Qt.AlignCenter)
        card_layout.addWidget(play_btn_container)

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
        label_container.setContentsMargins(0, 0, 0, 0)
        label_container.layout().setAlignment(Qt.AlignCenter)
        card_layout.addWidget(label_container)

        card_layout.addSpacing(6)

        mod_row = QHBoxLayout()
        mod_row.setSpacing(8)
        mod_row.setContentsMargins(0, 0, 0, 0)
        mod_row.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
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
        if chord.get("arp_mode") and chord.get("arp_mode") != "None":
            arp_pill = QLabel("ARP")
            arp_pill.setFixedHeight(22)
            arp_pill.setMinimumHeight(22)
            arp_pill.setMinimumWidth(44)
            arp_pill.setAlignment(Qt.AlignCenter)
            arp_pill.setStyleSheet(
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
            mod_row.addWidget(center_wrap(arp_pill))
        mod_row.addItem(QSpacerItem(4, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        mod_row_container = QWidget()
        mod_row_container.setLayout(mod_row)
        mod_row.layout().setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        card_layout.addWidget(mod_row_container)

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
        from ui.dialogs import EditChordModifiersDialog
        chord = self.chords[idx]
        dialog = EditChordModifiersDialog(self, chord)
        if dialog.exec_() == QDialog.Accepted and dialog.result:
            self.chords[idx]["extension"] = dialog.result.get("extension")
            self.chords[idx]["inversion"] = dialog.result.get("inversion")
            self.chords[idx]["voicing"] = dialog.result.get("voicing")
            self.chords[idx]["arp_mode"] = dialog.result.get("arp_mode")
            self.chords[idx]["arp_length"] = dialog.result.get("arp_length")
            # Store custom voicing parameters if present
            if "custom_voicing" in dialog.result:
                self.chords[idx]["custom_voicing"] = dialog.result["custom_voicing"]
            else:
                self.chords[idx].pop("custom_voicing", None)
            self.update_chords(self.chords)
