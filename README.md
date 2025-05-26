# 🎹 Chord Progression Tool

The Chord Progression Tool is a desktop application for composing, previewing, and exporting chord-based MIDI phrases.  
Designed for composers and producers, it blends traditional music theory with modern sequencing flexibility—ideal for prototyping ideas or building dynamic chord systems for games, film, and personal music projects.

Built with **Python + PyQt5**, this app supports:

- A powerful **Chord Wheel** to select any scale degree across keys/modes.
- A **Chord Structure Panel** to preview and customize chords with modifiers (extensions, inversions, voicings, arpeggiators).
- A **Pattern Editor** for drawing rhythmic patterns with full control over note length and step timing.
- A **Session Settings Panel** to control tempo, key, mode, and export options.
- **Sustained Synth Playback** with optional click track.
- Support for advanced **Arpeggiator Modes** (Up, Down, Random, Converge, Diverge, etc.)
- MIDI Export functionality.

---

## 🔧 Requirements

- Python 3.9+
- macOS or Windows
- PortAudio (required for `sounddevice` module)

Python dependencies:
- `PyQt5`
- `numpy`
- `sounddevice`
- `mido`

---

## 💻 Installation

### ✅ macOS

1. Open Terminal and navigate to the project folder.
2. Run the setup script:
   ```bash
   ./install_mac.sh
   ```
   This will install Python, PortAudio, create a virtual environment, and install all required Python packages.
3. To run the app after setup, use:
   ```bash
   ./run_mac.sh
   ```

**Troubleshooting:**  
If you get a "permission denied" error when running `./run_mac.sh`, you may need to make the script executable:
```bash
chmod +x run_mac.sh
```
This step is usually handled automatically by the installer, but if you encounter issues, run the above command and try again.

### ✅ Windows

1. Open Command Prompt and navigate to the project folder.
2. Run the setup script:
   ```cmd
   install_win.bat
   ```
   This will check for Python, install PortAudio (if Chocolatey is available), create a virtual environment, and install all required Python packages.
3. To run the app after setup, use:
   ```cmd
   run_win.bat
   ```

---

## ▶️ How to Use

### 🎼 Chord Wheel Panel
- Select a **key** and **mode** in the session settings.
- Click a Roman numeral to add a chord to your structure.
- Hover over a chord button to see its scale degree and function.

### 🧱 Chord Structure Panel
- Shows your chord sequence.
- Click the **play** button to preview any chord.
- Use **Options** to:
  - Add extensions (7th, 9th, etc.)
  - Set inversions and voicings
  - Choose arpeggiator mode and note value

### 🎛 Pattern Editor
- Each chord becomes a horizontal row.
- Click and drag blocks to place notes.
- Drag sides of blocks to set note length (snap to grid).
- Right-click blocks for more options (delete, randomize, clear row, **edit block modifiers**).
- Up to 32 steps total.
- Up to 8 unique chords can be sequenced.

#### Per-Block Chord Modifier Overrides
- You can override chord modifiers (extension, inversion, voicing, custom voicing, arpeggiator, etc.) for any block in the pattern editor.
- Right-click a block and select **Edit Block Modifiers...** to open the chord modifier dialog for that block.
- Any changes made here will apply only to that block, overriding the base chord's settings for playback and MIDI export.
- If no block-specific modifiers are set, the chord's global modifiers are used.

### ⚙️ Session Settings
- Set tempo (BPM), key, and mode.
- Export your chord patterns to a MIDI file.
- Optionally enable a click track for timing.

---

## 🎹 MIDI Export
1. Build your pattern in the structure and editor panels.
2. Press **Export MIDI** in the settings panel.
3. Save your file and import into your DAW or game engine.

---

## 🔁 Arpeggiator Modes

- **Up / Down**: Ascending or descending order
- **Converge**: From outer to inner
- **Diverge**: From inner to outer
- **Random**: Random shuffle each cycle
- **Ascending/Descending**: Repeats across entire block duration

Note duration is calculated based on tempo and block length.

---

## 🛠 Automation

For convenience, use the provided scripts for setup and running the app:

- **macOS:**
  - `install_mac.sh` — Installs all dependencies and sets up the environment.
  - `run_mac.sh` — Activates the environment and runs the app.

- **Windows:**
  - `install_win.bat` — Installs all dependencies and sets up the environment.
  - `run_win.bat` — Activates the environment and runs the app.

No manual installation steps are required—just use the scripts above!

---

## 📝 License

This project is MIT-licensed. See LICENSE for full terms.
