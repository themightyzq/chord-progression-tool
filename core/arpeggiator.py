import random

def get_arpeggio_sequence(notes, mode):
    """
    Returns a sequence of notes based on the arpeggiator mode.
    Supported modes: Up, Down, Random, Converge, Diverge, Ascending, Descending, None.
    """
    if not notes or mode is None or mode == "None":
        return notes
    if mode == "Up":
        return notes
    if mode == "Down":
        return list(reversed(notes))
    if mode == "Random":
        return random.sample(notes, len(notes))
    if mode == "Converge":
        if len(notes) < 2:
            return notes
        return [notes[0], notes[-1]] + notes[1:-1]
    if mode == "Diverge":
        if len(notes) < 2:
            return notes
        mid = len(notes) // 2
        left = notes[:mid][::-1]
        right = notes[mid+1:]
        return [notes[mid]] + left + right
    if mode == "Ascending":
        return sorted(notes)
    if mode == "Descending":
        return sorted(notes, reverse=True)
    return notes


# Utility function to get note duration in seconds based on arp_length and tempo
def get_note_duration(arp_length, tempo):
    """
    Returns note duration in seconds for a given arp length and tempo (in BPM).
    """
    duration_map = {
        "1/16": 0.25,
        "1/8": 0.5,
        "1/4": 1.0,
        "1/2": 2.0,
    }
    beats_per_second = tempo / 60.0
    beat_duration = 1.0 / beats_per_second
    multiplier = duration_map.get(arp_length, 0.25)  # Default to 1/16
    return multiplier * beat_duration
