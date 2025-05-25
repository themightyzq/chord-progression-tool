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

```bash
# Install Python (if not already installed)
brew install python

# Install PortAudio (required for playback)
brew install portaudio

# Clone and enter the project folder
git clone https://github.com/<yourname>/chord-progression-tool.git
cd chord-progression-tool

# (Optional) Create and activate virtualenv
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Run the app
python main.py
```

### ✅ Windows

1. Install Python 3.9+ from https://python.org
2. Download and install PortAudio from http://www.portaudio.com/download.html (or install via Chocolatey: `choco install portaudio`)
3. Clone the project or download ZIP
4. Open Command Prompt:

```cmd
cd path\to\chord-progression-tool

# (Optional) Create and activate virtualenv
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python main.py
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
- Right-click blocks for more options (delete, randomize, clear row).
- Up to 32 steps total.
- Up to 8 unique chords can be sequenced.

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

**(Optional)** You can use these shell scripts to install everything automatically:

### macOS - `install_mac.sh`
```bash
#!/bin/bash
brew install python portaudio
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Windows - `install_win.bat`
```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

## 📝 License

This project is MIT-licensed. See LICENSE for full terms.