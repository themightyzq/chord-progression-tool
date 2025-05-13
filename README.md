# 🎹 Chord Progression Tool

A desktop application for constructing, previewing and exporting chord progressions.  
Built with Python and PyQt5, it provides:

- A **chord wheel** to select Roman‐numeral degrees in any key/mode  
- A **structure panel** to build, reorder, preview and edit chord modifiers  
- A **settings panel** to play/stop, set tempo, choose key & mode, and export MIDI  

---

## 🔧 Requirements

- Python 3.7+  
- macOS: [PortAudio](http://portaudio.com/) (for `sounddevice`)  
- pip packages:
  - PyQt5  
  - numpy  
  - sounddevice  
  - mido  

---

## ⚙️ Installation

1. Clone the repo:
   ````bash
   git clone https://github.com/<YOU>/<REPO>.git
   cd chord-progression-tool

(Optional) Create & activate a virtualenv:
"python3 -m venv venv
source venv/bin/activate"

Install PortAudio (macOS):
"brew install portaudio"

Install Python deps:
"pip install PyQt5 numpy sounddevice mido"

▶️ Running the App
"python main.py"

💾 Exporting as MIDI
Build your progression in the UI
Click Export MIDI
Save as e.g. progression.mid

📝 License
This project is MIT-licensed. See LICENSE for details.