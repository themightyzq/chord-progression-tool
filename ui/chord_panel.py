import math
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFrame, QLabel, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

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
        self.setStyleSheet("background: #ffffff; border-radius: 20px;")
        
        card_frame = QFrame(self)
        card_frame.setMinimumWidth(PANEL_W)
        card_frame.setMaximumWidth(PANEL_W)
        card_frame.setMinimumHeight(PANEL_H)
        card_frame.setMaximumHeight(PANEL_H)
        card_frame.setStyleSheet(PANEL_STYLE)

        card_layout = QVBoxLayout(card_frame)
        card_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        card_layout.setSpacing(0)
        card_layout.setContentsMargins(16, 16, 16, 16)

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

        wheel = QWidget(card_frame)
        wheel.setFixedSize(PANEL_W - 32, PANEL_W - 32)

        wheel_group = QWidget(card_frame)
        wheel_group_layout = QVBoxLayout(wheel_group)
        wheel_group_layout.setContentsMargins(0, 0, 0, 0)
        wheel_group_layout.setSpacing(8)
        wheel_group_layout.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        wheel_group_layout.addWidget(wheel, alignment=Qt.AlignHCenter)

        card_layout.addWidget(header, alignment=Qt.AlignTop | Qt.AlignHCenter)
        card_layout.addWidget(wheel_group, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        self.roman_numerals = ["I", "ii", "iii", "IV", "V", "vi", "vii°"]
        self.btns = []
        degree_colors = {
            "I": "#1976d2", "IV": "#1976d2", "V": "#1976d2",
            "ii": "#388e3c", "iii": "#388e3c", "vi": "#388e3c",
            "vii°": "#d32f2f"
        }
        size = wheel.width()
        center = size / 2
        radius = center - 60

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
            font.setPointSize(38)
            font.setWeight(QFont.Black)
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
                    outline: none;
                    box-shadow: none;
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
        add_chord_center = QPushButton("ADD\nCHORD", wheel)
        add_chord_center.setFixedSize(130, 130)
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

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(card_frame, 1)
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
