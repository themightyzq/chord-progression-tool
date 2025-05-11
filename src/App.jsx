import { useState } from 'react';
import * as Tone from 'tone';
import './App.css';

const CHROMATIC_KEYS_SHARP = [
  "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"
];
const CHROMATIC_KEYS_FLAT = [
  "C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"
];
const MODES = [
  { label: "Major (Ionian)", value: "major" },
  { label: "Dorian", value: "dorian" },
  { label: "Phrygian", value: "phrygian" },
  { label: "Lydian", value: "lydian" },
  { label: "Mixolydian", value: "mixolydian" },
  { label: "Minor (Aeolian)", value: "minor" },
  { label: "Locrian", value: "locrian" },
  { label: "Gypsy Minor", value: "gypsy_minor" },
  { label: "Harmonic Minor", value: "harmonic_minor" },
  { label: "Minor Pentatonic", value: "minor_pentatonic" },
  { label: "Whole Tone", value: "whole_tone" },
  { label: "Tonic 2nds", value: "tonic_2nds" },
  { label: "Tonic 3rds", value: "tonic_3rds" },
  { label: "Tonic 4ths", value: "tonic_4ths" },
  { label: "Tonic 6ths", value: "tonic_6ths" },
  // Add more as needed
];

const ROMAN_NUMERALS = [
  'I', 'ii', 'iii', 'IV', 'V', 'vi', 'vii°'
];

const EXTENSIONS = [
  { label: '+7th', value: '7' },
  { label: '+9th', value: '9' },
  { label: 'sus2', value: 'sus2' },
  { label: 'sus4', value: 'sus4' }
];

function App() {
  // Key, accidental display, and mode state
  const [key, setKey] = useState("C");
  const [useSharps, setUseSharps] = useState(true);
  const [mode, setMode] = useState(MODES[0].value);
  // Track the order of selected chords with extensions
  const [previewChords, setPreviewChords] = useState([]);
  const [chordExtensions, setChordExtensions] = useState({});

  // Selected chord for add button
  const [selectedRoman, setSelectedRoman] = useState(null);

  // Add a chord (with its extensions) to the preview list
  const addChordToPreview = (roman) => {
    const extensions = chordExtensions[roman] || [];
    setPreviewChords((prev) => [
      ...prev,
      { roman, extensions }
    ]);
    setSelectedRoman(null); // Deselect after adding
  };

  // Toggle extension for a chord (UI only)
  const toggleExtension = (roman, ext) => {
    setChordExtensions((prev) => {
      const prevExts = prev[roman] || [];
      return {
        ...prev,
        [roman]: prevExts.includes(ext)
          ? prevExts.filter((e) => e !== ext)
          : [...prevExts, ext]
      };
    });
  };

  // Remove a chord from the preview list by index
  const removePreviewChord = (idx) => {
    setPreviewChords((prev) => prev.filter((_, i) => i !== idx));
  };

  // Render chord label with extensions
  const renderChordLabel = (chord) => {
    let label = chord.roman;
    if (chord.extensions.length > 0) {
      label += chord.extensions.map(e => {
        if (e === '7') return '7';
        if (e === '9') return '9';
        if (e === 'sus2') return 'sus2';
        if (e === 'sus4') return 'sus4';
        return e;
      }).join('');
    }
    return label;
  };

  // Generate scale for the selected key and mode
  const getScale = (tonic, mode) => {
    // Semitone intervals for common modes
    const modeIntervals = {
      major:        [2, 2, 1, 2, 2, 2, 1], // Ionian
      minor:        [2, 1, 2, 2, 1, 2, 2], // Aeolian
      dorian:       [2, 1, 2, 2, 2, 1, 2],
      phrygian:     [1, 2, 2, 2, 1, 2, 2],
      lydian:       [2, 2, 2, 1, 2, 2, 1],
      mixolydian:   [2, 2, 1, 2, 2, 1, 2],
      locrian:      [1, 2, 2, 1, 2, 2, 2],
      harmonic_minor: [2, 1, 2, 2, 1, 3, 1],
      gypsy_minor:  [2, 1, 3, 1, 1, 3, 1],
      minor_pentatonic: [3, 2, 2, 3, 2],
      whole_tone:   [2, 2, 2, 2, 2, 2],
      tonic_2nds:   [2, 2, 2, 2, 2, 2, 2], // placeholder
      tonic_3rds:   [3, 3, 2, 2, 2], // placeholder
      tonic_4ths:   [5, 2, 2, 3], // placeholder
      tonic_6ths:   [6, 1, 2, 3], // placeholder
    };
    // Use sharps or flats for chromatic scale
    const chromatic = useSharps ? CHROMATIC_KEYS_SHARP : CHROMATIC_KEYS_FLAT;
    const startIdx = chromatic.indexOf(tonic);
    let intervals = modeIntervals[mode] || modeIntervals["major"];
    let scale = [tonic];
    let idx = startIdx;
    for (let i = 0; i < intervals.length; i++) {
      idx = (idx + intervals[i]) % chromatic.length;
      scale.push(chromatic[idx]);
    }
    return scale;
  };

  // Map Roman numeral + extensions to notes in selected key/mode
  const getChordNotes = (chord) => {
    // Roman numeral to scale degree (0-based)
    const romanToDegree = {
      "I": 0, "ii": 1, "iii": 2, "IV": 3, "V": 4, "vi": 5, "vii°": 6,
    };
    const scale = getScale(key, mode);
    const degree = romanToDegree[chord.roman];
    if (degree === undefined) return [];
    // Triad: root, 3rd, 5th
    let root = scale[degree];
    let third = scale[(degree + 2) % scale.length];
    let fifth = scale[(degree + 4) % scale.length];
    // Octave numbers (for C4 as root)
    const baseOctave = 4;
    const noteWithOctave = (n, offset) => {
      // Offset is 0 for root, 1 for 3rd, 2 for 5th, etc.
      // Wraps at C
      let chromatic = useSharps ? CHROMATIC_KEYS_SHARP : CHROMATIC_KEYS_FLAT;
      let idx = chromatic.indexOf(n.replace(/[#b]/, ""));
      let octave = baseOctave + (idx < chromatic.indexOf(key.replace(/[#b]/, "")) ? 1 : 0) + offset;
      return n + octave;
    };
    let notes = [
      noteWithOctave(root, 0),
      noteWithOctave(third, 0),
      noteWithOctave(fifth, 0),
    ];
    // Extensions
    if (chord.extensions.includes("7")) {
      let seventh = scale[(degree + 6) % scale.length];
      notes.push(noteWithOctave(seventh, 0));
    }
    if (chord.extensions.includes("9")) {
      let ninth = scale[(degree + 1) % scale.length];
      notes.push(noteWithOctave(ninth, 1));
    }
    // Suspended chords
    if (chord.extensions.includes("sus2")) {
      // Replace 3rd with 2nd
      let second = scale[(degree + 1) % scale.length];
      notes[1] = noteWithOctave(second, 0);
    }
    if (chord.extensions.includes("sus4")) {
      // Replace 3rd with 4th
      let fourth = scale[(degree + 3) % scale.length];
      notes[1] = noteWithOctave(fourth, 0);
    }
    return notes;
  };

  // Play the chord using Tone.js
  const playChord = async (chord) => {
    const notes = getChordNotes(chord);
    if (notes.length === 0) return;
    const synth = new Tone.PolySynth(Tone.Synth).toDestination();
    await Tone.start();
    synth.triggerAttackRelease(notes, "1.2");
  };

  return (
    <div
      className="main-layout"
      style={{
        background: "#f5f5f5",
        minHeight: "100vh",
        width: "100%",
        maxWidth: 1120,
        margin: "0 auto",
        display: "flex",
        justifyContent: "center",
        alignItems: "flex-start",
        gap: 24,
        fontFamily: "Inter, Arial, sans-serif",
        padding: "48px 0",
        boxSizing: "border-box",
      }}
    >
      {/* Left Column: Chord Selector */}
      <div
        className="panel chord-panel"
        style={{
          width: 340,
          minWidth: 340,
          maxWidth: 340,
          minHeight: 640,
          background: "#fff",
          borderRadius: 12,
          boxShadow: "0 2px 6px rgba(0,0,0,0.08)",
          padding: 28,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          marginTop: 0,
          minHeight: 640,
        }}
      >
        {/* Column Heading */}
        <h2
          className="panel-title"
          style={{
            width: "100%",
            textAlign: "center",
            fontWeight: 800,
            fontSize: 32,
            fontFamily: "Inter, Arial, sans-serif",
            letterSpacing: 0.5,
            marginBottom: 18,
            marginTop: 0,
            color: "#232526",
          }}
        >
          Chord
        </h2>
        {/* Chord Wheel and Add Button (centered, block layout) */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            width: "100%",
            margin: "32px 0 0 0",
            flex: 1,
          }}
        >
          <div
            className="chord-wheel"
            style={{
              width: 240,
              height: 240,
              aspectRatio: "1",
              display: "grid",
              placeItems: "center",
              position: "relative",
              background: "#f7f7f7",
              borderRadius: "50%",
              boxShadow: "0 4px 32px #0002",
              marginBottom: 24,
            }}
          >
            {/* Chord buttons */}
            {ROMAN_NUMERALS.map((roman, i) => {
              // Color-code by chord type
              const chordType =
                roman === "I" || roman === "IV" || roman === "V"
                  ? "major"
                  : roman === "vii°"
                  ? "diminished"
                  : "minor";
              const colorMap = {
                major: "#1976d2",
                minor: "#43a047",
                diminished: "#d32f2f",
              };
              const bgMap = {
                major: "#e3f2fd",
                minor: "#e8f5e9",
                diminished: "#ffebee",
              };
              const angle =
                (i / ROMAN_NUMERALS.length) * 2 * Math.PI - Math.PI / 2;
              const radius = 110;
              const x = 120 + radius * Math.cos(angle) - 36;
              const y = 120 + radius * Math.sin(angle) - 36;
              const isSelected = selectedRoman === roman;
              return (
                <div
                  key={roman}
                  draggable
                  tabIndex={0}
                  aria-label={`Drag or preview ${roman} chord`}
                  style={{
                    position: "absolute",
                    left: x,
                    top: y,
                    width: 72,
                    height: 72,
                    borderRadius: "50%",
                    background:
                      isSelected
                        ? "#fff"
                        : "radial-gradient(circle at 60% 40%, " +
                          bgMap[chordType] +
                          " 80%, #fff 100%)",
                    color: colorMap[chordType],
                    fontWeight: 800,
                    fontSize: 32,
                    border: isSelected
                      ? `4px solid ${colorMap[chordType]}`
                      : `2px solid ${colorMap[chordType]}`,
                    boxShadow: isSelected
                      ? `0 0 0 4px ${colorMap[chordType]}33`
                      : "0 2px 8px #0001",
                    cursor: "grab",
                    zIndex: 2,
                    transition:
                      "background 0.2s, box-shadow 0.2s, border 0.2s",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    textAlign: "center",
                    lineHeight: "1",
                    outline: "none",
                    filter: "drop-shadow(0 2px 8px #0002)",
                    userSelect: "none",
                  }}
                  title={`Preview or drag ${roman} chord`}
                  onClick={() => {
                    playChord({ roman, extensions: [] });
                    setSelectedRoman(roman);
                  }}
                  onKeyDown={e => {
                    if (e.key === "Enter" || e.key === " ") {
                      playChord({ roman, extensions: [] });
                      setSelectedRoman(roman);
                    }
                  }}
                  onDragStart={e => {
                    e.dataTransfer.setData("text/plain", roman);
                    e.currentTarget.style.opacity = 0.5;
                  }}
                  onDragEnd={e => {
                    e.currentTarget.style.opacity = 1;
                  }}
                  onMouseOver={e => (e.currentTarget.style.background = "#fff")}
                  onMouseOut={e =>
                    (e.currentTarget.style.background =
                      isSelected
                        ? "#fff"
                        : "radial-gradient(circle at 60% 40%, " +
                          bgMap[chordType] +
                          " 80%, #fff 100%)")
                  }
                  onFocus={e =>
                    (e.currentTarget.style.boxShadow = `0 0 0 4px ${colorMap[chordType]}33`)
                  }
                  onBlur={e =>
                    (e.currentTarget.style.boxShadow = isSelected
                      ? `0 0 0 6px ${colorMap[chordType]}33`
                      : "0 2px 8px #0001")
                  }
                >
                  {roman}
                </div>
              );
            })}
            {/* Add to Structure Button (centered in circle) */}
            <button
              id="add-chord-button"
              style={{
                position: "absolute",
                left: "50%",
                top: "50%",
                transform: "translate(-50%,-50%)",
                width: 110,
                height: 110,
                borderRadius: "50%",
                background: "#1976d2",
                color: "#fff",
                border: "none",
                fontWeight: 800,
                fontSize: 22,
                cursor: selectedRoman ? "pointer" : "not-allowed",
                boxShadow: "0 2px 8px #0002",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                zIndex: 10,
                opacity: selectedRoman ? 1 : 0.5,
                pointerEvents: selectedRoman ? "auto" : "none",
                transition: "background 0.2s, box-shadow 0.2s",
                letterSpacing: 0.5,
                textAlign: "center",
                textTransform: "uppercase",
              }}
              onClick={() => {
                if (selectedRoman) {
                  addChordToPreview(selectedRoman);
                }
              }}
              title="Add selected chord to structure"
              aria-label="Add selected chord to structure"
              tabIndex={0}
            >
              Add Chord
            </button>
          </div>
        </div>
      </div>
      {/* Center Column: Chord Structure (Vertical, Rearrangeable) */}
      <div
        style={{
          width: 340,
          minWidth: 340,
          maxWidth: 340,
          minHeight: 640,
          background: "#fff",
          borderRadius: 12,
          boxShadow: "0 2px 6px rgba(0,0,0,0.08)",
          padding: 28,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "flex-start",
          minHeight: 640,
        }}
      >
        {/* Column Heading */}
        <div
          style={{
            width: "100%",
            textAlign: "center",
            fontWeight: 800,
            fontSize: 32,
            fontFamily: "Inter, Arial, sans-serif",
            letterSpacing: 0.5,
            marginBottom: 18,
            marginTop: 0,
            color: "#232526",
          }}
        >
          Chord Structure
        </div>
        <div
          style={{
            width: "80%",
            minHeight: 60,
            display: "flex",
            flexDirection: "column",
            alignItems: "stretch",
            gap: 18,
            margin: "0 auto",
            paddingBottom: 8,
            justifyContent: "flex-start",
            transition: "min-width 0.2s, max-width 0.2s",
          }}
        >
          {previewChords.length === 0 ? (
            <div
              style={{
                color: "#bbb",
                fontWeight: 600,
                fontSize: 22,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                height: "100%",
                width: "100%",
                textAlign: "center",
                gap: 24,
              }}
            >
              {/* Faded progression line/placeholder boxes */}
              <div style={{ display: "flex", gap: 16, marginBottom: 18, opacity: 0.3 }}>
                {[0, 1, 2, 3].map((i) => (
                  <div
                    key={i}
                    style={{
                      width: 80,
                      height: 56,
                      borderRadius: 12,
                      background: "#e3e3e3",
                      border: "2px dashed #bbb",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  />
                ))}
              </div>
              {/* Ghost chord card if a chord is selected */}
              {selectedRoman && (
                <div
                  style={{
                    width: 140,
                    minHeight: 56,
                    borderRadius: 16,
                    background: "#f7f7f7",
                    border: "2.5px dashed #1976d2",
                    color: "#1976d2",
                    fontWeight: 800,
                    fontSize: 28,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    margin: "0 auto 18px auto",
                    opacity: 0.7,
                    boxShadow: "0 2px 8px #0001",
                  }}
                  aria-label={`Preview: ${selectedRoman} chord`}
                  title={`Preview: ${selectedRoman} chord`}
                >
                  {selectedRoman}
                </div>
              )}
              Construct your chord progression here.
            </div>
          ) : (
            <RearrangeableChordList
              chords={previewChords}
              setChords={setPreviewChords}
              playChord={playChord}
              removePreviewChord={removePreviewChord}
              chordExtensions={chordExtensions}
              setChordExtensions={setChordExtensions}
            />
          )}
        </div>
      </div>
      {/* Right Column: Session Controls */}
      <div
        style={{
          width: 340,
          minWidth: 340,
          maxWidth: 340,
          minHeight: 640,
          background: "#fff",
          borderRadius: 12,
          boxShadow: "0 2px 6px rgba(0,0,0,0.08)",
          padding: 28,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          minHeight: 640,
        }}
      >
        {/* Column Heading */}
        <div
          style={{
            width: "100%",
            textAlign: "center",
            fontWeight: 800,
            fontSize: 32,
            fontFamily: "Inter, Arial, sans-serif",
            letterSpacing: 0.5,
            marginBottom: 18,
            marginTop: 0,
            color: "#232526",
          }}
        >
          Session Settings
        </div>
        {/* Tempo Control */}
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 18 }}>
          <label htmlFor="tempo-input" style={{ fontWeight: 700, fontSize: 18, marginRight: 6, color: "#232526" }}>
            Tempo:
          </label>
          <input
            id="tempo-input"
            type="number"
            min={40}
            max={240}
            value={tempo}
            onChange={e => setTempo(Number(e.target.value))}
            style={{
              fontSize: 22,
              width: 80,
              borderRadius: 8,
              border: "1.5px solid #bbb",
              background: "#fff",
              fontWeight: 700,
              color: "#222",
              boxShadow: "0 2px 8px #0001",
              textAlign: "center",
              outline: "none",
              marginRight: 8,
            }}
            aria-label="Tempo (BPM)"
          />
          <span style={{ fontWeight: 600, fontSize: 18, color: "#232526" }}>BPM</span>
        </div>
        {/* Play/Stop Buttons */}
        <div style={{ display: "flex", gap: 16, marginBottom: 24 }}>
          <button
            style={{
              background: "#1976d2",
              color: "#fff",
              border: "none",
              borderRadius: 8,
              padding: "8px 28px",
              fontWeight: 700,
              fontSize: 20,
              cursor: isPlaying ? "not-allowed" : "pointer",
              opacity: isPlaying ? 0.6 : 1,
              boxShadow: "0 1px 4px #0001",
              transition: "background 0.2s, box-shadow 0.2s",
            }}
            onClick={handlePlay}
            disabled={isPlaying}
            aria-label="Play progression"
          >
            Play
          </button>
          <button
            style={{
              background: "#eee",
              color: "#888",
              border: "none",
              borderRadius: 8,
              padding: "8px 28px",
              fontWeight: 700,
              fontSize: 20,
              cursor: isPlaying ? "pointer" : "not-allowed",
              opacity: isPlaying ? 1 : 0.6,
              boxShadow: "0 1px 4px #0001",
              transition: "background 0.2s, box-shadow 0.2s",
            }}
            onClick={handleStop}
            disabled={!isPlaying}
            aria-label="Stop playback"
          >
            Stop
          </button>
        </div>
        {/* Key Dropdown */}
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 18 }}>
          <label htmlFor="key-dropdown" style={{ fontWeight: 700, fontSize: 18, marginRight: 6, color: "#232526" }}>
            Key:
          </label>
          <select
            id="key-dropdown"
            style={{
              fontSize: 22,
              padding: "10px 18px",
              borderRadius: 12,
              border: "1.5px solid #bbb",
              background: "#fff",
              fontWeight: 700,
              color: "#222",
              boxShadow: "0 2px 8px #0001",
              zIndex: 10,
              minWidth: 90,
              textAlign: "center",
              appearance: "none",
              outline: "none",
              letterSpacing: 0.5,
            }}
            value={key}
            onChange={(e) => setKey(e.target.value)}
          >
            {(useSharps ? CHROMATIC_KEYS_SHARP : CHROMATIC_KEYS_FLAT).map((k) => (
              <option key={k} value={k}>
                {k}
              </option>
            ))}
          </select>
          <button
            style={{
              marginLeft: 6,
              background: "#f5f5f5",
              color: "#1976d2",
              border: "1.5px solid #bbb",
              borderRadius: 8,
              padding: "4px 10px",
              cursor: "pointer",
              fontWeight: 600,
              fontSize: 16,
            }}
            onClick={() => setUseSharps((s) => !s)}
            title="Toggle sharp/flat"
          >
            {useSharps ? "♯" : "♭"}
          </button>
        </div>
        {/* Mode Dropdown */}
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 24 }}>
          <label htmlFor="mode-dropdown" style={{ fontWeight: 700, fontSize: 18, marginRight: 6, color: "#232526" }}>
            Mode:
          </label>
          <select
            id="mode-dropdown"
            style={{
              fontSize: 22,
              padding: "10px 18px",
              borderRadius: 12,
              border: "1.5px solid #bbb",
              background: "#fff",
              fontWeight: 700,
              color: "#222",
              boxShadow: "0 2px 8px #0001",
              zIndex: 10,
              minWidth: 180,
              textAlign: "center",
              appearance: "none",
              outline: "none",
              letterSpacing: 0.5,
            }}
            value={mode}
            onChange={(e) => setMode(e.target.value)}
          >
            {MODES.map((m) => (
              <option key={m.value} value={m.value}>
                {m.label}
              </option>
            ))}
          </select>
        </div>
        {/* Pattern, Tempo, Export (placeholders) */}
        <div style={{ marginTop: 24, width: "100%" }}>
          <h3 style={{ fontWeight: 700, fontSize: 18, marginBottom: 10, color: "#232526" }}>Pattern Generation</h3>
          <div style={{ marginBottom: 18, color: "#888" }}>[Pattern controls coming soon]</div>
          <h3 style={{ fontWeight: 700, fontSize: 18, marginBottom: 10, color: "#232526" }}>Tempo</h3>
          <div style={{ marginBottom: 18, color: "#888" }}>[Tempo controls coming soon]</div>
          <h3 style={{ fontWeight: 700, fontSize: 18, marginBottom: 10, color: "#232526" }}>Export</h3>
          <div style={{ color: "#888" }}>[Export options coming soon]</div>
        </div>
      </div>
    </div>
  );
}

function ChordWidget({
  chord,
  idx,
  playChord,
  removePreviewChord,
  chordExtensions,
  setChordExtensions,
}) {
  const [showOptions, setShowOptions] = useState(false);
  const [selectedExts, setSelectedExts] = useState(chord.extensions || []);
  const [selectedInv, setSelectedInv] = useState(null);

  // Color-code by chord type
  const chordType =
    chord.roman === "I" || chord.roman === "IV" || chord.roman === "V"
      ? "major"
      : chord.roman === "vii°"
      ? "diminished"
      : "minor";
  const colorMap = {
    major: "#1976d2",
    minor: "#43a047",
    diminished: "#d32f2f",
  };
  const bgMap = {
    major: "#e3f2fd",
    minor: "#e8f5e9",
    diminished: "#ffebee",
  };

  // Save options to parent state
  const saveOptions = () => {
    setChordExtensions((prev) => ({
      ...prev,
      [chord.roman]: selectedExts,
    }));
    setShowOptions(false);
  };

  // Pill modifiers for extension/inversion with spacing, tooltips, and dismissibility
  const getModifierPills = () => {
    const pills = [];
    const extLabels = {
      "7": "+7th",
      "9": "+9th",
      "sus2": "Suspended 2nd",
      "sus4": "Suspended 4th",
    };
    const pillStyle = {
      display: "inline-flex",
      alignItems: "center",
      borderRadius: 12,
      padding: "2px 10px",
      fontWeight: 700,
      fontSize: 16,
      marginRight: 6,
      marginLeft: 0,
      marginBottom: 2,
      letterSpacing: 0.5,
      boxShadow: "0 1px 4px #0001",
      cursor: "pointer",
      outline: "none",
      border: "none",
      transition: "background 0.2s, color 0.2s",
      gap: 4,
    };
    if (selectedExts.length > 0) {
      const ext = selectedExts[0];
      const pillText = ext === "7" ? "+7th" : ext === "9" ? "+9th" : ext;
      pills.push(
        <span
          key={ext}
          className="modifier-pill"
          tabIndex={0}
          aria-label={extLabels[ext] || ext}
          title={extLabels[ext] || ext}
          style={{
            ...pillStyle,
            background: colorMap[chordType],
            color: "#fff",
          }}
          onClick={() => setSelectedExts([])}
          onKeyDown={e => {
            if (e.key === "Enter" || e.key === " ") setSelectedExts([]);
          }}
        >
          {pillText}
          <span
            style={{
              marginLeft: 6,
              fontWeight: 900,
              fontSize: 18,
              cursor: "pointer",
              color: "#fff",
              opacity: 0.7,
            }}
            aria-label="Remove modifier"
            title="Remove modifier"
          >
            ×
          </span>
        </span>
      );
    }
    if (selectedInv) {
      const invLabels = {
        "Root": "Root Position",
        "1st": "First Inversion",
        "2nd": "Second Inversion",
      };
      pills.push(
        <span
          key={selectedInv}
          className="modifier-pill"
          tabIndex={0}
          aria-label={invLabels[selectedInv] || selectedInv}
          title={invLabels[selectedInv] || selectedInv}
          style={{
            ...pillStyle,
            background: "#fff",
            color: colorMap[chordType],
            border: `2px solid ${colorMap[chordType]}`,
          }}
          onClick={() => setSelectedInv(null)}
          onKeyDown={e => {
            if (e.key === "Enter" || e.key === " ") setSelectedInv(null);
          }}
        >
          {selectedInv}
          <span
            style={{
              marginLeft: 6,
              fontWeight: 900,
              fontSize: 18,
              cursor: "pointer",
              color: colorMap[chordType],
              opacity: 0.7,
            }}
            aria-label="Remove inversion"
            title="Remove inversion"
          >
            ×
          </span>
        </span>
      );
    }
    return (
      <div
        className="modifier-pill-group"
        style={{
          display: "flex",
          gap: 6,
          flexWrap: "wrap",
          alignItems: "center",
        }}
      >
        {pills}
      </div>
    );
  };

  return (
    <div
      style={{
        background: bgMap[chordType],
        border: `3px solid ${colorMap[chordType]}`,
        borderRadius: 16,
        boxShadow: "0 2px 8px #0001",
        minWidth: 140,
        maxWidth: 220,
        marginRight: 0,
        marginBottom: 0,
        padding: "14px 18px 10px 18px",
        display: "flex",
        flexDirection: "column",
        alignItems: "stretch",
        justifyContent: "center",
        position: "relative",
        transition: "box-shadow 0.2s, border 0.2s",
      }}
      tabIndex={0}
      aria-label={`Chord: ${chord.roman}`}
    >
      {/* Top row: Chord label */}
      <div
        style={{
          fontWeight: 800,
          fontSize: 28,
          color: colorMap[chordType],
          letterSpacing: 0.5,
          textAlign: "center",
          marginBottom: 8,
        }}
        title={`Chord: ${chord.roman}`}
      >
        {chord.roman}
      </div>
      {/* Second row: Controls */}
      <div
        style={{
          display: "flex",
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "center",
          gap: 8,
          marginBottom: 2,
          minHeight: 44,
        }}
      >
        <button
          style={{
            background: "#1976d2",
            color: "#fff",
            border: "none",
            borderRadius: 8,
            padding: "4px 14px",
            cursor: "pointer",
            fontWeight: 700,
            fontSize: 20,
            boxShadow: "0 1px 4px #0001",
            marginRight: 2,
            minWidth: 44,
            minHeight: 44,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
          onClick={() => playChord({ ...chord, extensions: selectedExts })}
          title="Preview chord"
          aria-label="Preview chord"
        >
          ▶
        </button>
        <button
          style={{
            background: "#eee",
            color: "#888",
            border: "none",
            borderRadius: 8,
            padding: "4px 10px",
            cursor: "pointer",
            fontWeight: 700,
            fontSize: 20,
            marginRight: 2,
            minWidth: 44,
            minHeight: 44,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            position: "absolute",
            top: 10,
            right: 10,
          }}
          onClick={() => removePreviewChord(idx)}
          title="Remove chord"
          aria-label="Remove chord"
        >
          ✕
        </button>
        <button
          style={{
            background: "#f5f5f5",
            color: colorMap[chordType],
            border: `2px solid ${colorMap[chordType]}`,
            borderRadius: 8,
            padding: "4px 10px",
            cursor: "pointer",
            fontWeight: 700,
            fontSize: 18,
            marginLeft: 2,
            minWidth: 44,
            minHeight: 44,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
          onClick={() => setShowOptions((v) => !v)}
          title="Advanced chord options"
          aria-label="Advanced chord options"
        >
          ⚙️
        </button>
      </div>
      {/* Third row: Modifiers (always present for alignment) */}
      <div
        style={{
          minHeight: 32,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          marginTop: 4,
        }}
      >
        {getModifierPills()}
      </div>
      {/* Popup for extensions/inversions */}
      {showOptions && (
        <div
          style={{
            position: "absolute",
            top: 60,
            left: "50%",
            transform: "translateX(-50%)",
            background: "#fff",
            border: `2px solid ${colorMap[chordType]}`,
            borderRadius: 14,
            boxShadow: "0 4px 24px #0003",
            padding: 22,
            zIndex: 10,
            minWidth: 260,
            minHeight: 140,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
          }}
        >
          <div
            style={{
              fontWeight: 800,
              fontSize: 20,
              color: colorMap[chordType],
              marginBottom: 10,
              letterSpacing: 0.5,
              textAlign: "center",
              textTransform: "uppercase",
            }}
          >
            Extensions
          </div>
          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              gap: 12,
              marginBottom: 18,
              justifyContent: "center",
            }}
          >
            {EXTENSIONS.map((ext) => (
              <label
                key={ext.value}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                  fontWeight: 700,
                  fontSize: 16,
                  color: colorMap[chordType],
                  background: selectedExts[0] === ext.value
                    ? colorMap[chordType]
                    : "#fff",
                  border: `2px solid ${colorMap[chordType]}`,
                  borderRadius: 16,
                  padding: "4px 14px",
                  cursor: "pointer",
                  margin: 2,
                  transition: "background 0.2s, color 0.2s",
                  userSelect: "none",
                }}
                title={ext.label}
              >
                <input
                  type="radio"
                  name={`ext-radio-${idx}`}
                  checked={selectedExts[0] === ext.value}
                  onChange={() =>
                    setSelectedExts(
                      selectedExts[0] === ext.value ? [] : [ext.value]
                    )
                  }
                  style={{
                    accentColor: colorMap[chordType],
                    marginRight: 4,
                  }}
                  aria-label={ext.label}
                />
                <span
                  style={{
                    color: selectedExts[0] === ext.value
                      ? "#fff"
                      : colorMap[chordType],
                  }}
                >
                  {ext.label}
                </span>
              </label>
            ))}
          </div>
          <div
            style={{
              fontWeight: 800,
              fontSize: 18,
              color: colorMap[chordType],
              marginBottom: 8,
              letterSpacing: 0.5,
              textAlign: "center",
              textTransform: "uppercase",
            }}
          >
            Inversion
          </div>
          <div style={{ display: "flex", gap: 12, marginBottom: 18 }}>
            {["Root", "1st", "2nd"].map((inv) => (
              <label
                key={inv}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 4,
                  fontWeight: 700,
                  fontSize: 15,
                  color: colorMap[chordType],
                  background: selectedInv === inv ? colorMap[chordType] : "#fff",
                  border: `2px solid ${colorMap[chordType]}`,
                  borderRadius: 16,
                  padding: "4px 14px",
                  cursor: "pointer",
                  userSelect: "none",
                  transition: "background 0.2s, color 0.2s",
                }}
                title={inv}
              >
                <input
                  type="checkbox"
                  checked={selectedInv === inv}
                  onChange={() =>
                    setSelectedInv(selectedInv === inv ? null : inv)
                  }
                  style={{
                    accentColor: colorMap[chordType],
                    marginRight: 2,
                  }}
                  aria-label={inv}
                />
                <span
                  style={{
                    color: selectedInv === inv ? "#fff" : colorMap[chordType],
                  }}
                >
                  {inv}
                </span>
              </label>
            ))}
          </div>
          <button
            style={{
              marginTop: 10,
              background: colorMap[chordType],
              color: "#fff",
              border: "none",
              borderRadius: 10,
              padding: "10px 28px",
              fontWeight: 800,
              fontSize: 18,
              cursor: "pointer",
              boxShadow: "0 1px 4px #0001",
              letterSpacing: 0.5,
            }}
            onClick={saveOptions}
            aria-label="Save chord options"
          >
            Save
          </button>
        </div>
      )}
    </div>
  );
}

function RearrangeableChordList({
  chords,
  setChords,
  playChord,
  removePreviewChord,
  chordExtensions,
  setChordExtensions,
}) {
  const [dragIdx, setDragIdx] = useState(null);
  const [dragOverIdx, setDragOverIdx] = useState(null);

  const handleDragStart = (idx) => setDragIdx(idx);
  const handleDragEnter = (idx) => setDragOverIdx(idx);
  const handleDragEnd = () => {
    if (dragIdx !== null && dragOverIdx !== null && dragIdx !== dragOverIdx) {
      const newChords = [...chords];
      const [removed] = newChords.splice(dragIdx, 1);
      newChords.splice(dragOverIdx, 0, removed);
      setChords(newChords);
    }
    setDragIdx(null);
    setDragOverIdx(null);
  };

  return (
    <>
      {chords.map((chord, idx) => (
        <div
          key={idx}
          draggable
          onDragStart={() => handleDragStart(idx)}
          onDragEnter={() => dragIdx !== null && handleDragEnter(idx)}
          onDragEnd={handleDragEnd}
          onDragOver={(e) => e.preventDefault()}
          style={{
            opacity: dragIdx === idx ? 0.5 : 1,
            border: dragOverIdx === idx && dragIdx !== null ? "2px dashed #1976d2" : undefined,
            background: dragOverIdx === idx && dragIdx !== null ? "#e3f2fd" : undefined,
            transition: "background 0.2s, border 0.2s, opacity 0.2s",
            cursor: "grab",
          }}
        >
          <ChordWidget
            chord={chord}
            idx={idx}
            playChord={playChord}
            removePreviewChord={removePreviewChord}
            chordExtensions={chordExtensions}
            setChordExtensions={setChordExtensions}
          />
        </div>
      ))}
    </>
  );
}

export default App;
