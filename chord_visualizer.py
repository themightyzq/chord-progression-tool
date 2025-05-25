from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor
from PyQt5.QtCore import Qt, QRectF

# MIDI note numbers for C4 (middle C) = 60
NOTE_POSITIONS = {
    # MIDI note: (line index, is_on_line)
    60: (4, False),  # C4, below staff
    61: (4, True),   # C#4/Db4
    62: (3, False),  # D4
    63: (3, True),   # D#4/Eb4
    64: (2, False),  # E4
    65: (2, True),   # F4
    66: (1, False),  # F#4/Gb4
    67: (1, True),   # G4
    68: (0, False),  # G#4/Ab4
    69: (0, True),   # A4
    70: (-1, False), # A#4/Bb4
    71: (-1, True),  # B4
    72: (-2, False), # C5, above staff
}

def note_name_to_midi(note):
    # Accepts note names like "C", "C#", "Db", etc. (octave 4 assumed)
    base = {"C": 60, "C#": 61, "Db": 61, "D": 62, "D#": 63, "Eb": 63, "E": 64, "F": 65, "F#": 66, "Gb": 66,
            "G": 67, "G#": 68, "Ab": 68, "A": 69, "A#": 70, "Bb": 70, "B": 71}
    return base.get(note, 60)

class ChordVisualizer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(120)
        self.setMaximumHeight(150)
        self.setSizePolicy(self.sizePolicy().Expanding, self.sizePolicy().Fixed)
        self.notes = []  # List of note names or MIDI numbers

    def set_notes(self, notes):
        """Set notes to display (as MIDI numbers or note names)."""
        self.notes = []
        for n in notes:
            if isinstance(n, int):
                self.notes.append(n)
            elif isinstance(n, str):
                self.notes.append(note_name_to_midi(n))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = self.height()
        margin = 20
        staff_top = margin
        staff_height = h - 2 * margin
        line_spacing = staff_height / 4

        # Draw 5 staff lines
        pen = QPen(QColor("#222"), 2)
        painter.setPen(pen)
        for i in range(5):
            y = staff_top + i * line_spacing
            painter.drawLine(int(margin), int(y), int(w - margin), int(y))

        # Draw notes as filled circles
        note_radius = 14
        if self.notes:
            # Spread notes horizontally
            n_notes = len(self.notes)
            x_spacing = (w - 2 * margin) / (n_notes + 1)
            for idx, midi in enumerate(self.notes):
                # Map MIDI to staff position (C4 = 60, E4 = 64, G4 = 67, etc.)
                rel = (midi - 60) % 12
                # Find closest staff position
                pos = NOTE_POSITIONS.get(60 + rel, (4, False))
                line_idx, is_on_line = pos
                y = staff_top + (4 - line_idx) * line_spacing
                x = margin + (idx + 1) * x_spacing
                painter.setBrush(QBrush(QColor("#1976d2")))
                painter.setPen(QPen(QColor("#1976d2")))
                painter.drawEllipse(QRectF(x - note_radius, y - note_radius, 2 * note_radius, 2 * note_radius))
                # Optionally, draw note name
                painter.setPen(QPen(Qt.white))
                painter.setFont(self.font())
                painter.drawText(QRectF(x - note_radius, y - note_radius, 2 * note_radius, 2 * note_radius),
                                 Qt.AlignCenter, "")

        painter.end()
