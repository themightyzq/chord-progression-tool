import threading
import time
import numpy as np
from functools import partial
from pattern_editor_panel import PatternEditorPanel
from audio.synth import SustainedSynth
from ui.chord_panel import ChordPanel

import sys
import math
import sounddevice as sd
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

# --- Modern, grid-aligned, scrollable EditChordModifiersDialog ---
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QRadioButton, QButtonGroup, QGroupBox,
    QComboBox, QDialogButtonBox, QScrollArea, QWidget, QGridLayout, QSizePolicy
)
from PyQt5.QtGui import QFont
from ui.dialogs import EditChordModifiersDialog
from ui.structure_panel import StructurePanel
from ui.settings_panel import SettingsPanel
from core.arpeggiator import get_arpeggio_sequence

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chord Progression Tool")
        self.setStyleSheet("background: #f5f5f5;")
        # Main 3-column layout with styled panels
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(24)  # Reduced spacing between panels
        columns_layout.setContentsMargins(20, 20, 20, 20)  # Add margins around the layout
        # Removed setAlignment to allow panels to expand and fill space naturally

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

        def play_chord_tone(self, notes, duration=0.5, fs=44100, chord=None):
            print(f"[DEBUG] play_chord_tone called with notes: {notes}")
            if not notes or not all(isinstance(f, (int, float)) and f > 0 for f in notes):
                print("[DEBUG] Invalid or empty notes passed to play_chord_tone.")
                return

            # If chord has arpeggiator settings, play as arpeggio
            if chord and chord.get("arp_mode") and chord.get("arp_mode") != "None":
                arp_mode = chord.get("arp_mode")
                arp_length = chord.get("arp_length", "1/16")
                sequence = get_arpeggio_sequence(notes, arp_mode)
                duration_map = {"1/16": 0.125, "1/8": 0.25, "1/4": 0.5, "1/2": 1.0}
                note_duration = duration_map.get(arp_length, 0.125)
                # Scale note_duration by tempo (120 = default)
                note_duration *= (120 / self.tempo)
                for note in sequence:
                    t = np.linspace(0, note_duration, int(fs * note_duration), False)
                    audio = 0.3 * np.sin(2 * np.pi * note * t)
                    audio = audio / np.max(np.abs(audio)) if np.max(np.abs(audio)) != 0 else audio
                    print(f"[DEBUG] Playing arpeggiated note {note} for {note_duration}s")
                    sd.play(audio, samplerate=fs, blocking=True)
                return

            # Otherwise, play all notes in unison
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
                        click_audio = click.astype(np.float32)
                        try:
                            with sd.OutputStream(
                                samplerate=fs,
                                channels=1,
                                dtype='float32',
                                device=None  # Auto-select
                            ) as stream:
                                stream.write(click_audio)
                        except Exception as e:
                            print(f"[ERROR] Click track stream failed: {e}")

                    blocks = pattern_panel.blocks if pattern_panel else []
                    print(f"[DEBUG] Blocks at step {step_idx}: {blocks}")
                    blocks_starting = [b for b in blocks if b["start"] == step_idx]
                    print(f"[DEBUG] Blocks starting at step {step_idx}: {blocks_starting}")
                    blocks_ending = [b for b in blocks if b["start"] + b["length"] == step_idx]

                    # For each active block at this step, play arpeggiator note or chord
                    active_blocks = [b for b in blocks if b["start"] <= step_idx < b["start"] + b["length"]]
                    for block in active_blocks:
                        chord_idx = block["chord_idx"]
                        if 0 <= chord_idx < len(self.chord_progression):
                            base_chord = self.chord_progression[chord_idx]
                            modifiers = block.get("modifiers", {})
                            merged_chord = dict(base_chord)
                            merged_chord.update(modifiers)
                            freqs = self.get_chord_frequencies(
                                merged_chord["roman"],
                                merged_chord.get("extension"),
                                merged_chord.get("inversion"),
                                merged_chord.get("voicing"),
                                key=self.key,
                                mode=self.mode,
                                custom_voicing=merged_chord.get("custom_voicing")
                            )
                            arp_mode = merged_chord.get("arp_mode", "None")
                            arp_length = merged_chord.get("arp_length", "1/16")
                            if arp_mode and arp_mode != "None":
                                # Step-synchronized arpeggiator: sustain each note for the correct number of steps
                                # Use the same merged_chord as above
                                notes = self.get_chord_frequencies(
                                    merged_chord["roman"],
                                    merged_chord.get("extension"),
                                    merged_chord.get("inversion"),
                                    merged_chord.get("voicing"),
                                    self.key, self.mode,
                                    custom_voicing=merged_chord.get("custom_voicing")
                                )
                                sequence = get_arpeggio_sequence(notes, arp_mode)
                                if not hasattr(self, "_arpeggio_positions"):
                                    self._arpeggio_positions = {}
                                if not hasattr(self, "_arpeggio_last_notes"):
                                    self._arpeggio_last_notes = {}
                                block_id = (block["start"], block["chord_idx"])
                                step_offset = step_idx - block["start"]
                                arp_length_map = {"1/16": 1, "1/8": 2, "1/4": 4, "1/2": 8}
                                steps_per_arp_note = arp_length_map.get(arp_length, 1)
                                # Only advance arpeggio note at the start of each arp note duration
                                if step_offset % steps_per_arp_note == 0:
                                    # Turn off previous note if any
                                    last_note = self._arpeggio_last_notes.get(block_id)
                                    if last_note is not None:
                                        self.synth.note_off([last_note])
                                    pos = self._arpeggio_positions.get(block_id, 0)
                                    note = sequence[pos % len(sequence)]
                                    self.synth.note_on([note])
                                    self._arpeggio_positions[block_id] = pos + 1
                                    self._arpeggio_last_notes[block_id] = note
                            else:
                                # Only play chord on the first step of the block
                                if step_idx == block["start"]:
                                    self.synth.note_on(freqs)

                    for block in blocks_ending:
                        chord_idx = block["chord_idx"]
                        if 0 <= chord_idx < len(self.chord_progression):
                            base_chord = self.chord_progression[chord_idx]
                            modifiers = block.get("modifiers", {})
                            merged_chord = dict(base_chord)
                            merged_chord.update(modifiers)
                            freqs = self.get_chord_frequencies(
                                merged_chord["roman"],
                                merged_chord.get("extension"),
                                merged_chord.get("inversion"),
                                merged_chord.get("voicing"),
                                key=self.key,
                                mode=self.mode,
                                custom_voicing=merged_chord.get("custom_voicing")
                            )
                            arp_mode = merged_chord.get("arp_mode", "None")
                            if arp_mode and arp_mode != "None":
                                # Step-synchronized arpeggiator: turn off last note and reset position for this block
                                notes = self.get_chord_frequencies(
                                    merged_chord["roman"],
                                    merged_chord.get("extension"),
                                    merged_chord.get("inversion"),
                                    merged_chord.get("voicing"),
                                    self.key, self.mode,
                                    custom_voicing=merged_chord.get("custom_voicing")
                                )
                                sequence = get_arpeggio_sequence(notes, arp_mode)
                                block_id = (block["start"], block["chord_idx"])
                                if hasattr(self, "_arpeggio_last_notes"):
                                    last_note = self._arpeggio_last_notes.get(block_id)
                                    if last_note is not None:
                                        self.synth.note_off([last_note])
                                    self._arpeggio_last_notes.pop(block_id, None)
                                if hasattr(self, "_arpeggio_positions"):
                                    if block_id in self._arpeggio_positions:
                                        del self._arpeggio_positions[block_id]
                            else:
                                self.synth.note_off(freqs)

                    time.sleep(step_duration)
                    step_idx += 1
                    if step_idx >= pattern_length:
                        if self.loop_enabled:
                            # Before looping, turn off any notes that should end at or after the pattern boundary
                            if pattern_panel:
                                blocks = pattern_panel.blocks
                                for block in blocks:
                                    block_end = block["start"] + block["length"]
                                    if block_end >= pattern_length:
                                        chord_idx = block["chord_idx"]
                                        if 0 <= chord_idx < len(self.chord_progression):
                                            base_chord = self.chord_progression[chord_idx]
                                            modifiers = block.get("modifiers", {})
                                            merged_chord = dict(base_chord)
                                            merged_chord.update(modifiers)
                                            freqs = self.get_chord_frequencies(
                                                merged_chord["roman"],
                                                merged_chord.get("extension"),
                                                merged_chord.get("inversion"),
                                                merged_chord.get("voicing"),
                                                key=self.key,
                                                mode=self.mode,
                                                custom_voicing=merged_chord.get("custom_voicing")
                                            )
                                            arp_mode = merged_chord.get("arp_mode", "None")
                                            if arp_mode and arp_mode != "None":
                                                # For arpeggiator, turn off last note if held
                                                block_id = (block["start"], block["chord_idx"])
                                                if hasattr(self, "_arpeggio_last_notes"):
                                                    last_note = self._arpeggio_last_notes.get(block_id)
                                                    if last_note is not None:
                                                        self.synth.note_off([last_note])
                                                    self._arpeggio_last_notes.pop(block_id, None)
                                                if hasattr(self, "_arpeggio_positions"):
                                                    if block_id in self._arpeggio_positions:
                                                        del self._arpeggio_positions[block_id]
                                            else:
                                                self.synth.note_off(freqs)
                            # Wait for any running arpeggiator threads to finish before looping
                            if hasattr(self, "_arpeggio_threads"):
                                for t in self._arpeggio_threads:
                                    t.join(timeout=2.0)
                                self._arpeggio_threads.clear()
                            step_idx = 0
                        else:
                            break

                if pattern_panel:
                    QTimer.singleShot(0, partial(pattern_panel.highlight_step, -1))
                # Clear arpeggio positions and turn off any held arpeggiator notes at end of playback
                if hasattr(self, "_arpeggio_last_notes"):
                    for note in self._arpeggio_last_notes.values():
                        self.synth.note_off([note])
                    self._arpeggio_last_notes.clear()
                if hasattr(self, "_arpeggio_positions"):
                    self._arpeggio_positions.clear()
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
            def get_midi_notes(roman, extension=None, inversion=None, voicing=None, key="C", custom_voicing=None):
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
                # Convert note names to MIDI numbers
                key_offset = note_map.get(key, 60) - 60
                midi_notes = []
                for n in notes:
                    base = n.replace("+8", "").replace("-8", "").replace("°", "")
                    midi = note_map.get(base, 60) + key_offset
                    midi_notes.append(midi)
                # Apply voicing
                if custom_voicing:
                    num_notes = custom_voicing.get("num_notes", len(midi_notes))
                    position = custom_voicing.get("position", 3)
                    spread = custom_voicing.get("spread", 0)
                    center = 12 * (position + 1)
                    midi_notes = sorted(midi_notes)
                    if num_notes <= 4 or spread == 0:
                        base = center - 2 * (num_notes // 2)
                        midi_notes = [base + 2 * i for i in range(num_notes)]
                    else:
                        if spread == 1:
                            midi_notes = [center - 24] + [center - 12 + 4 * i for i in range(num_notes - 2)] + [center + 12]
                        elif spread == 2:
                            midi_notes = [center - 24] + [center + i for i in range(num_notes - 1)]
                        elif spread == 3:
                            import random
                            midi_notes = [n for n in range(center - 12, center + 12) if random.random() < 0.7][:num_notes]
                        elif spread == 4:
                            midi_notes = [center - 24] + [center + 7 * i for i in range(1, num_notes)]
                        elif spread == 5:
                            midi_notes = [center - 24] + [center + 4 * i for i in range(1, num_notes)]
                    midi_notes = midi_notes[:num_notes]
                elif voicing == "Open" and len(midi_notes) >= 3:
                    midi_notes = midi_notes[:]
                    midi_notes[1] += 12
                elif voicing == "Drop 2" and len(midi_notes) >= 3:
                    midi_notes = midi_notes[:]
                    sorted_idx = sorted(range(len(midi_notes)), key=lambda i: midi_notes[i], reverse=True)
                    idx_2nd_highest = sorted_idx[1]
                    midi_notes[idx_2nd_highest] -= 12
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
                    base_chord = self.chord_progression[chord_idx]
                    modifiers = block.get("modifiers", {})
                    merged_chord = dict(base_chord)
                    merged_chord.update(modifiers)
                    notes = get_midi_notes(
                        merged_chord["roman"],
                        merged_chord.get("extension"),
                        merged_chord.get("inversion"),
                        merged_chord.get("voicing"),
                        key=self.key,
                        custom_voicing=merged_chord.get("custom_voicing")
                    )
                    start = block["start"]
                    end = block["start"] + block["length"]
                    arp_mode = merged_chord.get("arp_mode", "None")
                    arp_length = merged_chord.get("arp_length", "1/16")
                    if arp_mode and arp_mode != "None":
                        # Arpeggiated export: only one note on at a time, matching playback
                        from core.arpeggiator import get_arpeggio_sequence
                        sequence = get_arpeggio_sequence(notes, arp_mode)
                        arp_length_map = {"1/16": 1, "1/8": 2, "1/4": 4, "1/2": 8}
                        steps_per_arp_note = arp_length_map.get(arp_length, 1)
                        num_notes = len(sequence)
                        total_steps = end - start
                        prev_note = None
                        for step_offset in range(0, total_steps, steps_per_arp_note):
                            pos = step_offset // steps_per_arp_note
                            note_idx = pos % num_notes
                            n = sequence[note_idx]
                            note_on_step = start + step_offset
                            note_off_step = min(note_on_step + steps_per_arp_note, end)
                            # Turn off previous note before turning on the next
                            if prev_note is not None:
                                events.append((note_on_step, "off", prev_note))
                            events.append((note_on_step, "on", n))
                            events.append((note_off_step, "off", n))
                            prev_note = n
                        # At the end of the block, ensure the last note is turned off (if not already)
                        # (Handled by the above loop, but this is a safety net)
                        # No need to turn off prev_note here, as it's handled at note_off_step
                    else:
                        # Block chord export
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
        self.chord_panel.setSizePolicy(self.chord_panel.sizePolicy().Expanding, self.chord_panel.sizePolicy().Expanding)

        # Chord Structure Panel
        self.structure_panel = StructurePanel(self.chord_progression, on_delete)
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
        self.settings_panel.setSizePolicy(self.settings_panel.sizePolicy().Expanding, self.settings_panel.sizePolicy().Expanding)

        # Add get_chord_frequencies method for StructurePanel play button
        def get_chord_frequencies(self, roman, extension=None, inversion=None, voicing=None, key=None, mode=None, custom_voicing=None):
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
            # Convert note names to MIDI numbers (C4 = 60)
            note_to_midi = {
                "C": 60, "C#": 61, "Db": 61, "D": 62, "D#": 63, "Eb": 63, "E": 64, "F": 65, "F#": 66, "Gb": 66,
                "G": 67, "G#": 68, "Ab": 68, "A": 69, "A#": 70, "Bb": 70, "B": 71
            }
            midi_notes = []
            for n in notes:
                base = n.replace("+8", "").replace("-8", "").replace("°", "")
                midi = note_to_midi.get(base, 60)
                # Handle octave shifts
                if "+8" in n:
                    midi += 12
                if "-8" in n:
                    midi -= 12
                midi_notes.append(midi)
            # Apply voicing
            if custom_voicing:
                # Custom voicing logic
                num_notes = custom_voicing.get("num_notes", len(midi_notes))
                position = custom_voicing.get("position", 3)
                note_range = custom_voicing.get("range", len(midi_notes))
                spread = custom_voicing.get("spread", 0)
                # Center note is at MIDI octave (position), so center = 12 * (position + 1)
                center = 12 * (position + 1)
                # Spread notes around the center, within the allowed range
                midi_notes = sorted(midi_notes)
                # Stack in thirds for <=4 notes, otherwise apply spread logic
                if num_notes <= 4 or spread == 0:
                    # Stack in thirds, centered
                    base = center - 2 * (num_notes // 2)
                    midi_notes = [base + 2 * i for i in range(num_notes)]
                else:
                    # For spread > 0, implement basic open/closed voicing logic as a placeholder
                    # (Full spread logic can be expanded as needed)
                    if spread == 1:
                        # Root in bass, open mid, closed high, root high
                        midi_notes = [center - 24] + [center - 12 + 4 * i for i in range(num_notes - 2)] + [center + 12]
                    elif spread == 2:
                        # Root in bass, closed 4th octave
                        midi_notes = [center - 24] + [center + i for i in range(num_notes - 1)]
                    elif spread == 3:
                        # 70% chance for any pad note
                        import random
                        midi_notes = [n for n in range(center - 12, center + 12) if random.random() < 0.7][:num_notes]
                    elif spread == 4:
                        # Root in bass, root+5ths above
                        midi_notes = [center - 24] + [center + 7 * i for i in range(1, num_notes)]
                    elif spread == 5:
                        # Root in bass, 3rds or 7ths above
                        midi_notes = [center - 24] + [center + 4 * i for i in range(1, num_notes)]
                midi_notes = midi_notes[:num_notes]
            elif voicing == "Open" and len(midi_notes) >= 3:
                midi_notes = midi_notes[:]
                midi_notes[1] += 12
            elif voicing == "Drop 2" and len(midi_notes) >= 3:
                midi_notes = midi_notes[:]
                sorted_idx = sorted(range(len(midi_notes)), key=lambda i: midi_notes[i], reverse=True)
                idx_2nd_highest = sorted_idx[1]
                midi_notes[idx_2nd_highest] -= 12
            # Convert MIDI numbers to frequencies
            freqs = [440.0 * (2 ** ((m - 69) / 12.0)) for m in midi_notes]
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
        self.setSizePolicy(self.sizePolicy().Expanding, self.sizePolicy().Expanding)

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
    # Enable high-DPI scaling for better cross-platform and resolution independence
    import os
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QApplication
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication([])
    # Set global font and stylesheet for professional, accessible look
    from PyQt5.QtGui import QFont, QFontDatabase
    base_font = QFontDatabase.systemFont(QFontDatabase.GeneralFont)
    base_font.setFamily("Palatino" if QFont("Palatino").exactMatch() else "Georgia")
    base_font.setPointSizeF(base_font.pointSizeF() * app.devicePixelRatio())
    app.setFont(base_font)
    # Load and apply external stylesheet for all visual settings
    try:
        with open("style.qss", "r") as f:
            app.setStyleSheet(f.read())
    except Exception as e:
        print(f"Failed to load stylesheet: {e}")
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
