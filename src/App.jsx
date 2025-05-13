import { useState, useRef } from 'react';
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
  const [key, setKey] = useState("C");
  const [useSharps, setUseSharps] = useState(true);
  const [mode, setMode] = useState(MODES[0].value);
  const [tempo, setTempo] = useState(100);
  const [previewChords, setPreviewChords] = useState([]);
  const [chordExtensions, setChordExtensions] = useState({});
  const [selectedRoman, setSelectedRoman] = useState(null);

  // Playback state
  const [isPlaying, setIsPlaying] = useState(false);
  const playIndexRef = useRef(0);
  const stopPlaybackRef = useRef(false);

  // Add a chord (with its extensions) to the preview list
  const addChordToPreview = (roman) => {
    const extensions = chordExtensions[roman] || [];
    setPreviewChords((prev) => [
      ...prev,
      { roman, extensions }
    ]);
    setSelectedRoman(null);
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
    const modeIntervals = {
      major:        [2, 2, 1, 2, 2, 2, 1],
      minor:        [2, 1, 2, 2, 1, 2, 2],
      dorian:       [2, 1, 2, 2, 2, 1, 2],
      phrygian:     [1, 2, 2, 2, 1, 2, 2],
      lydian:       [2, 2, 2, 1, 2, 2, 1],
      mixolydian:   [2, 2, 1, 2, 2, 1, 2],
      locrian:      [1, 2, 2, 1, 2, 2, 2],
      harmonic_minor: [2, 1, 2, 2, 1, 3, 1],
      gypsy_minor:  [2, 1, 3, 1, 1, 3, 1],
      minor_pentatonic: [3, 2, 2, 3, 2],
      whole_tone:   [2, 2, 2, 2, 2, 2],
      tonic_2nds:   [2, 2, 2, 2, 2, 2, 2],
      tonic_3rds:   [3, 3, 2, 2, 2],
      tonic_4ths:   [5, 2, 2, 3],
      tonic_6ths:   [6, 1, 2, 3],
    };
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

  // Map Roman numeral + extensions + inversion to notes in selected key/mode
  const getChordNotes = (chord, inversion = null) => {
    const romanToDegree = {
      "I": 0, "ii": 1, "iii": 2, "IV": 3, "V": 4, "vi": 5, "vii°": 6,
    };
    const scale = getScale(key, mode);
    const degree = romanToDegree[chord.roman];
    if (degree === undefined) return [];
    let root = scale[degree];
    let third = scale[(degree + 2) % scale.length];
    let fifth = scale[(degree + 4) % scale.length];
    const baseOctave = 4;
    const noteWithOctave = (n, offset) => {
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
    if (chord.extensions.includes("7")) {
      let seventh = scale[(degree + 6) % scale.length];
      notes.push(noteWithOctave(seventh, 0));
    }
    if (chord.extensions.includes("9")) {
      let ninth = scale[(degree + 1) % scale.length];
      notes.push(noteWithOctave(ninth, 1));
    }
    if (chord.extensions.includes("sus2")) {
      let second = scale[(degree + 1) % scale.length];
      notes[1] = noteWithOctave(second, 0);
    }
    if (chord.extensions.includes("sus4")) {
      let fourth = scale[(degree + 3) % scale.length];
      notes[1] = noteWithOctave(fourth, 0);
    }
    // Handle inversion
    if (inversion === "1st") {
      notes.push(notes.shift());
    } else if (inversion === "2nd") {
      notes.push(notes.shift());
      notes.push(notes.shift());
    }
    return notes;
  };

  // Play the chord using Tone.js
  const playChord = async (chord, inversion = null) => {
    const notes = getChordNotes(chord, inversion);
    if (notes.length === 0) return;
    const synth = new Tone.PolySynth(Tone.Synth).toDestination();
    await Tone.start();
    synth.triggerAttackRelease(notes, "1.2");
  };

  // Sequential playback of previewChords
  const handlePlay = async () => {
    if (previewChords.length === 0) return;
    setIsPlaying(true);
    stopPlaybackRef.current = false;
    playIndexRef.current = 0;
    const beatDuration = 60 / tempo;
    for (let i = 0; i < previewChords.length; i++) {
      if (stopPlaybackRef.current) break;
      const chord = previewChords[i];
      // Get inversion if present in chordExtensions
      let inversion = null;
      if (chordExtensions && chordExtensions[chord.roman] && chordExtensions[chord.roman].inversion) {
        inversion = chordExtensions[chord.roman].inversion;
      }
      await playChord(chord, inversion);
      playIndexRef.current = i + 1;
      // Wait for the duration of a beat (or chord)
      await new Promise(res => setTimeout(res, beatDuration * 1000 * 1.2));
    }
    setIsPlaying(false);
  };

  const handleStop = () => {
    stopPlaybackRef.current = true;
    setIsPlaying(false);
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
      {/* ... (unchanged) ... */}
      {/* Center Column: Chord Structure (Vertical, Rearrangeable) */}
      {/* ... (unchanged) ... */}
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
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 8,
            }}
            onClick={handlePlay}
            disabled={isPlaying}
            aria-label="Play progression"
          >
            <svg width="22" height="22" viewBox="0 0 22 22" style={{ display: "block" }}>
              <polygon points="5,3 19,11 5,19" fill="white" />
            </svg>
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
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 8,
            }}
            onClick={handleStop}
            disabled={!isPlaying}
            aria-label="Stop playback"
          >
            <svg width="22" height="22" viewBox="0 0 22 22" style={{ display: "block" }}>
              <rect x="5" y="5" width="12" height="12" fill="#888" />
            </svg>
            Stop
          </button>
        </div>
        {/* ... (rest unchanged) ... */}
      </div>
    </div>
  );
}

// ChordWidget and RearrangeableChordList remain mostly unchanged, except for the following updates:
// - ChordWidget: play/stop icons use SVG and are centered
// - ChordWidget: all backgrounds in the modifiers window are white, regardless of selection
// - ChordWidget: inversion is saved to chordExtensions for playback

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
  const [selectedInv, setSelectedInv] = useState(
    chordExtensions && chordExtensions[chord.roman] && chordExtensions[chord.roman].inversion
      ? chordExtensions[chord.roman].inversion
      : null
  );

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
      [chord.roman]: {
        extensions: selectedExts,
        inversion: selectedInv,
      },
    }));
    setShowOptions(false);
  };

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
            background: "#fff",
            color: colorMap[chordType],
            border: `2px solid ${colorMap[chordType]}`,
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
              color: colorMap[chordType],
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
          onClick={() => playChord({ ...chord, extensions: selectedExts }, selectedInv)}
          title="Preview chord"
          aria-label="Preview chord"
        >
          <svg width="22" height="22" viewBox="0 0 22 22" style={{ display: "block" }}>
            <polygon points="5,3 19,11 5,19" fill="white" />
          </svg>
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
          <svg width="18" height="18" viewBox="0 0 18 18" style={{ display: "block" }}>
            <line x1="4" y1="4" x2="14" y2="14" stroke="#888" strokeWidth="2.5"/>
            <line x1="14" y1="4" x2="4" y2="14" stroke="#888" strokeWidth="2.5"/>
          </svg>
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
                  background: "#fff",
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
                    color: colorMap[chordType],
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
                  background: "#fff",
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
                    color: colorMap[chordType],
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
