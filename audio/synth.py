import threading
import numpy as np
import sounddevice as sd

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

    def note_on(self, freqs, duration=None):
        with self.lock:
            for f in freqs:
                self.phase[f] = self.phase.get(f, 0.0)
                self.active_notes[f] = self.active_notes.get(f, 0) + 1
        if duration is not None:
            threading.Timer(duration, lambda: self.note_off(freqs)).start()

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
