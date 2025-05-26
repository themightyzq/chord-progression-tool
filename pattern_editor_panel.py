from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QMenu, QDialog
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush
from PyQt5.QtCore import Qt, QTimer
import numpy as np
class PatternEditorPanel(QWidget):
    """
    Piano roll style sequencer for chords.
    Users can click and drag to create, move, and resize colored blocks representing chord events of arbitrary length.
    Multiple chords can overlap in time.
    """
    def __init__(self, chords):
        super().__init__()
        self.chords = chords
        self.blocks = []  # Each block: {"chord_idx": int, "start": int, "length": int, "color": QColor}
        self.selected_block = None
        self.dragging = False
        self.drag_start = None
        self.resizing = False
        self.resize_dir = None
        self.setMinimumHeight(320)
        self.setMouseTracking(True)
        self.colors = [
            "#1976d2", "#388e3c", "#d32f2f", "#fbc02d", "#7b1fa2", "#0288d1", "#c2185b"
        ]
        # Fixed grid: 32 steps, always integer step grid
        self.grid_steps = 32
        self.grid_height = 30
        self.header_height = 30
        self.left_margin = 60
        self.right_margin = 20
        self.top_margin = 10
        self.bottom_margin = 10
        self.block_min_length = 1
        self.setLayout(QVBoxLayout(self))
        # --- Max blocks for randomization ---
        self.max_blocks_min = 1
        self.max_blocks_max = 8
        # --- Animated playhead state ---
        self.playhead_anim = 0.0
        self.playhead_anim_target = 0.0
        from PyQt5.QtCore import QTimer
        self.anim_timer = QTimer(self)
        self.anim_timer.setInterval(16)
        self.anim_timer.timeout.connect(self.update_playhead_anim)
        self.anim_timer.start()
        # --- Pulse for active (playing) blocks ---
        import numpy as np
        self.pulse_phase = 0.0
        self.pulse_timer = QTimer(self)
        self.pulse_timer.setInterval(32)
        def update_pulse():
            self.pulse_phase = (self.pulse_phase + 0.08) % (2 * np.pi)
            self.update()
        self.pulse_timer.timeout.connect(update_pulse)
        self.pulse_timer.start()

    def set_bars(self, val):
        self.update()
    def set_quant(self, val):
        self.update()
    def set_chords(self, chords):
        self.chords = chords
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            x, y = event.x(), event.y()
            col, row = self.xy_to_grid(x, y)
            if row is not None and col is not None:
                col = int(round(col))
                col = max(0, min(self.grid_steps - 1, col))
                cell_w = self.cell_width()
                grid_left = self.left_margin
                grid_top = self.header_height + self.top_margin
                # Check if clicking on an existing block
                for block in reversed(self.blocks):
                    if block["chord_idx"] == row and block["start"] <= col < block["start"] + block["length"]:
                        # Compute pixel x-coordinates for block edges
                        block_x_left = grid_left + block["start"] * cell_w
                        block_x_right = grid_left + (block["start"] + block["length"]) * cell_w
                        # Mouse x relative to grid
                        mouse_x = x
                        # Detect edge proximity (6px threshold)
                        if abs(mouse_x - block_x_left) <= 6:
                            self.resizing = True
                            self.resize_dir = "left"
                        elif abs(mouse_x - block_x_right) <= 6:
                            self.resizing = True
                            self.resize_dir = "right"
                        else:
                            self.resizing = False
                            self.resize_dir = None
                        self.selected_block = block
                        self.dragging = True
                        self.drag_start = (col, row, block["start"], block["length"])
                        self.update()
                        return
                # Otherwise, create a new block (length 1)
                color = self.colors[row % len(self.colors)]
                new_block = {"chord_idx": row, "start": col, "length": 1, "color": color}
                self.blocks.append(new_block)
                self.selected_block = new_block
                self.dragging = True
                self.drag_start = (col, row, col, 1)
                self.resizing = False
                self.resize_dir = None
                self.update()
    def mouseMoveEvent(self, event):
        x, y = event.x(), event.y()
        # Resizing/moving logic if dragging
        if self.dragging and self.selected_block:
            col, row = self.xy_to_grid(x, y)
            if col is not None and row == self.selected_block["chord_idx"]:
                col = int(round(col))
                col = max(0, min(self.grid_steps - 1, col))
                if self.resizing:
                    # Resize block (snap to integer steps)
                    if self.resize_dir == "right":
                        new_length = max(self.block_min_length, col - self.selected_block["start"] + 1)
                        self.selected_block["length"] = min(new_length, self.grid_steps - self.selected_block["start"])
                        # Clamp to max 32
                        self.selected_block["length"] = min(self.selected_block["length"], 32)
                    elif self.resize_dir == "left":
                        end = self.selected_block["start"] + self.selected_block["length"]
                        new_start = min(max(0, col), end - self.block_min_length)
                        self.selected_block["length"] = end - new_start
                        self.selected_block["start"] = new_start
                        # Clamp to min 1, max 32
                        if self.selected_block["length"] < 1:
                            self.selected_block["length"] = 1
                        if self.selected_block["length"] > 32:
                            self.selected_block["length"] = 32
                else:
                    # Move block (snap to integer steps)
                    offset = col - self.drag_start[0]
                    new_start = min(max(0, self.drag_start[2] + offset), self.grid_steps - self.selected_block["length"])
                    self.selected_block["start"] = new_start
            self.update()
        else:
            # Cursor feedback for resizing
            col, row = self.xy_to_grid(x, y)
            cell_w = self.cell_width()
            grid_left = self.left_margin
            grid_top = self.header_height + self.top_margin
            found_edge = False
            if row is not None and col is not None:
                mouse_x = x
                for block in reversed(self.blocks):
                    if block["chord_idx"] == row and block["start"] <= col < block["start"] + block["length"]:
                        block_x_left = grid_left + block["start"] * cell_w
                        block_x_right = grid_left + (block["start"] + block["length"]) * cell_w
                        if abs(mouse_x - block_x_left) <= 6:
                            self.setCursor(Qt.SizeHorCursor)
                            found_edge = True
                            break
                        elif abs(mouse_x - block_x_right) <= 6:
                            self.setCursor(Qt.SizeHorCursor)
                            found_edge = True
                            break
            if not found_edge:
                self.setCursor(Qt.ArrowCursor)
    def contextMenuEvent(self, event):
        # Right-click context menu for deleting/clearing/randomizing a row, editing, or deleting a block
        x, y = event.x(), event.y()
        col, row = self.xy_to_grid(x, y)
        if row is not None and col is not None:
            from PyQt5.QtWidgets import QMenu
            menu = QMenu(self)
            randomize_action = menu.addAction("Randomize This Row")
            clear_action = menu.addAction("Clear This Row")

            edit_modifiers_action = None
            delete_action = None
            block_to_edit = None
            for block in reversed(self.blocks):
                if block["chord_idx"] == row and block["start"] <= col < block["start"] + block["length"]:
                    edit_modifiers_action = menu.addAction("Edit Block Modifiers...")
                    delete_action = menu.addAction("Delete Block")
                    block_to_edit = block
                    break

            action = menu.exec_(self.mapToGlobal(event.pos()))
            if action == randomize_action:
                self.randomize_patterns(only_row=row)
                return
            elif action == clear_action:
                self.blocks = [b for b in self.blocks if b["chord_idx"] != row]
                self.update()
                return
            elif edit_modifiers_action and action == edit_modifiers_action and block_to_edit is not None:
                # Open chord modifier dialog for this block
                from ui.dialogs import EditChordModifiersDialog
                # Use the base chord as a starting point, but allow overrides
                chord = self.chords[row].copy()
                if "modifiers" in block_to_edit and block_to_edit["modifiers"]:
                    chord.update(block_to_edit["modifiers"])
                dialog = EditChordModifiersDialog(self, chord)
                if dialog.exec_() == QDialog.Accepted and dialog.result:
                    # Save only the modifiers that are set (not the roman)
                    block_to_edit["modifiers"] = {k: v for k, v in dialog.result.items() if k != "roman"}
                self.update()
                return
            elif action and action.text() == "Delete Block":
                for block in reversed(self.blocks):
                    if block["chord_idx"] == row and block["start"] <= col < block["start"] + block["length"]:
                        self.blocks.remove(block)
                        self.selected_block = None
                        self.update()
                        break
    def mouseReleaseEvent(self, event):
        self.dragging = False
        self.resizing = False
        self.resize_dir = None
        self.update()
    def xy_to_grid(self, x, y):
        # Convert pixel x/y to grid col/row
        grid_top = self.header_height + self.top_margin
        grid_left = self.left_margin
        row = (y - grid_top) // self.grid_height
        col = (x - grid_left) // self.cell_width()
        if 0 <= row < len(self.chords) and 0 <= col < self.grid_steps:
            return int(round(col)), int(row)
        return None, None
    def cell_width(self):
        w = max(1, (self.width() - self.left_margin - self.right_margin) // max(1, self.grid_steps))
        return w
    def paintEvent(self, event):
        from PyQt5.QtGui import QPainter, QColor, QPen, QBrush
        import numpy as np
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setClipRect(self.rect())
        grid_top = self.header_height + self.top_margin
        grid_left = self.left_margin
        cell_w = self.cell_width()
        playhead = int(round(self.playhead_anim))
        # Draw grid
        for row in range(len(self.chords)):
            y = grid_top + row * self.grid_height
            painter.setPen(QColor("#222"))
            painter.setFont(self.font())
            painter.drawText(8, y + self.grid_height // 2 + 8, self.chords[row]["roman"])
            for col in range(self.grid_steps):
                x = grid_left + col * cell_w
                painter.setPen(QPen(QColor("#bbb"), 1))
                painter.setBrush(QBrush(QColor("#fafafa")))
                painter.drawRect(x, y, cell_w, self.grid_height)
        # Duration value map for musical terms
        value_map = {1: "1/16", 2: "1/8", 4: "1/4", 8: "1/2", 16: "1"}
        # Draw blocks
        for block in self.blocks:
            row = block["chord_idx"]
            x = grid_left + block["start"] * cell_w
            y = grid_top + row * self.grid_height
            w = block["length"] * cell_w
            h = self.grid_height
            # Highlight block if playhead is within its range (legacy playhead_step for compatibility)
            is_playing = playhead is not None and block["start"] <= playhead < block["start"] + block["length"]
            length = block['length']
            label = value_map.get(length, f"{length}/16")
            if is_playing:
                # Block is filled with half transparency, solid black border, black label.
                base_color = QColor(block["color"])
                base_color.setAlpha(128)  # half transparency
                painter.setPen(QPen(Qt.black, 3))
                painter.setBrush(base_color)
                painter.drawRect(int(x), int(y), int(w), int(h))
                painter.setPen(QColor(Qt.black))
                painter.setFont(self.font())
                painter.drawText(int(x) + 6, int(y) + 24, label)
            else:
                color = QColor(block["color"])
                painter.setPen(QPen(color.darker(150), 2))
                painter.setBrush(QBrush(color.lighter(120)))
                painter.drawRect(int(x), int(y), int(w), int(h))
                painter.setPen(QColor("#333"))
                painter.drawText(int(x) + 6, int(y) + 24, label)
            # Draw selection
            if block is self.selected_block:
                painter.setPen(QPen(QColor("#ff9800"), 3))
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(int(x), int(y), int(w), int(h))
        # Draw timeline header
        painter.setPen(QPen(QColor("#888"), 1))
        painter.setBrush(QBrush(QColor("#eee")))
        painter.drawRect(grid_left, self.top_margin, self.grid_steps * cell_w, self.header_height)
        for col in range(self.grid_steps):
            x = grid_left + col * cell_w
            painter.setPen(QPen(QColor("#bbb"), 1))
            painter.drawLine(x, self.top_margin, x, self.top_margin + self.header_height + len(self.chords) * self.grid_height)
            painter.setPen(QColor("#444"))
            painter.drawText(x + 2, self.top_margin + 18, str(col + 1))
        # Draw playhead as a semi-transparent line ON TOP of blocks
        if (
            self.playhead_anim is not None
            and self.playhead_anim >= 0
            and self.playhead_anim < self.grid_steps
        ):
            x = grid_left + self.playhead_anim * cell_w
            from PyQt5.QtGui import QColor, QPen
            painter.setPen(QPen(QColor(255, 152, 0, 160), 4, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(
                int(x),
                int(self.top_margin),
                int(x),
                int(self.top_margin + self.header_height + len(self.chords) * self.grid_height)
            )
        painter.end()
    def highlight_step(self, step_idx):
        # Animate playhead to the new step (can be float for animation)
        self.playhead_anim_target = float(step_idx if step_idx is not None else -1)
        self.update()

    def update_playhead_anim(self):
        # Smoothly animate playhead position toward target (LERP)
        speed = 0.33
        self.playhead_anim += (self.playhead_anim_target - self.playhead_anim) * speed
        if abs(self.playhead_anim - self.playhead_anim_target) < 0.01:
            self.playhead_anim = self.playhead_anim_target
        self.update()
    def get_active_blocks(self, step_idx):
        # Return all blocks active at this step
        active = [block for block in self.blocks if block["start"] <= step_idx < block["start"] + block["length"]]
        print(f"Active blocks at step {step_idx}:",
              [b for b in self.blocks if b["start"] <= step_idx < b["start"] + b["length"]])
        return active

    def get_blocks_starting_at(self, step_idx):
        # Return all blocks that start at this step
        blocks = [block for block in self.blocks if block["start"] == step_idx]
        print(f"Getting blocks at step {step_idx}:",
              [b for b in self.blocks if b["start"] == step_idx])
        return blocks


    # ---- Move randomize_patterns as a method of PatternEditorPanel ----

    from functools import partial

    # Add the method inside the PatternEditorPanel class:

    # (inserted above End of File, at class scope)

    # ... at the end of the PatternEditorPanel class:

    def randomize_patterns(self, only_row=None):
        import random
        if only_row is not None:
            self.blocks = [b for b in self.blocks if b["chord_idx"] != only_row]
        else:
            self.blocks = []
        duration_options = [1, 2, 4, 6, 8]  # durations in 16th-note steps

        for row_idx, chord in enumerate(self.chords):
            if only_row is not None and row_idx != only_row:
                continue

            attempts = 0
            blocks_to_place = random.randint(self.max_blocks_min, self.max_blocks_max)
            placed_blocks = 0
            max_attempts = 100

            while placed_blocks < blocks_to_place and attempts < max_attempts:
                duration = random.choice(duration_options)
                start = random.randint(0, self.grid_steps - duration)
                conflict = any(
                    b for b in self.blocks
                    if b["chord_idx"] == row_idx and
                       not (start + duration <= b["start"] or start >= b["start"] + b["length"])
                )
                if not conflict:
                    color = self.colors[row_idx % len(self.colors)]
                    self.blocks.append({
                        "chord_idx": row_idx,
                        "start": start,
                        "length": duration,
                        "color": color
                    })
                    for i in range(start, start + duration):
                        pass  # Could remove from an available set if tracking space more carefully
                    print(f"Added block: row={row_idx}, start={start}, length={duration}, color={color}")
                    placed_blocks += 1
                attempts += 1

        self.playhead_anim = -1  # Reset animation state
        self.playhead_anim_target = 0
        self.update()
