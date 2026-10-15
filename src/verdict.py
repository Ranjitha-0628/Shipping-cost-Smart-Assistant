import pandas as pd

from src.notes import NOTE_SUMMARY, check_note

NOTE_MAGNITUDE = {"N003": (0.05, 0.07)}


def _closest_relevant(week_of, route, all_notes):
    """Nearest note that is at least about this route (or all routes).
    Route-specific notes are preferred over 'All Routes' ones."""
    best = None
    for note in all_notes:
        if note["route"] not in ("ALL", route):
            continue
        key = (0 if note["route"] == route else 1,
               abs((pd.Timestamp(note["date"]) - week_of).days),
               note["note_id"])
        if best is None or key < best[0]:
            best = (key, note)
    return best[1] if best else None


def decide(flag_row, candidates, all_notes=None):
    """candidates: retrieved notes, best match first. all_notes (optional) is
    used only to pick which rejected note to mention in an unexplained reason."""
    for note in candidates:
        ok, _ = check_note(note, flag_row["route"], flag_row["week_of"])
        if ok:
            return {"justified": True, "note": note, "why_rejected": None}
    closest = _closest_relevant(flag_row["week_of"], flag_row["route"],
                                candidates if all_notes is None else all_notes)
    why = check_note(closest, flag_row["route"], flag_row["week_of"])[1] if closest is not None else None
    return {"justified": False, "note": closest, "why_rejected": why}


def _ordinal(n):
    return {2: "2nd", 3: "3rd"}.get(n, f"{n}th")


def build_reason(flag_row, verdict):
    note = verdict["note"]
    if verdict["justified"]:
        text = (f"Matches note {note['note_id']} dated {note['date']}: "
                f"{NOTE_SUMMARY[note['note_id']]}. The cost rise has a clear explanation.")
        low_high = NOTE_MAGNITUDE.get(note["note_id"])
        if low_high and flag_row["own_pct"] > low_high[1]:
            text += (f" The note cites roughly {low_high[0]:.0%}-{low_high[1]:.0%}, but the "
                     f"observed rise is {flag_row['own_pct']:+.1%}, so part of it is not covered.")
        return text
    if note is None:
        return ("No matching note found for this route or date range. "
                "Cost rise looks unexplained and worth a human review.")
    text = (f"The closest note ({note['note_id']}, {note['date']}) says {NOTE_SUMMARY[note['note_id']]}; "
            f"it does not explain this rise because {verdict['why_rejected']}. "
            f"No genuine justification found; flagged for review.")
    repeats = flag_row.get("recent_flags", 1)
    if repeats >= 2:
        text += (f" This is the {_ordinal(repeats)} flagged week on this route in the last 12 weeks, "
                 f"so it looks like a sustained rise rather than a one-off.")
    return text