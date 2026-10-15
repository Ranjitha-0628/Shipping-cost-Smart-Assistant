import pandas as pd

NOTE_FACTS = {
    "N001": ("2025-02-24", "2025-03-08", "raises", "Feb 24 to Mar 8"),
    "N002": ("2025-01-20", "2025-01-26", "raises", "festival week"),
    "N003": ("2025-05-05", "2025-05-18", "raises", "starting this week"),
    "N004": ("2024-03-11", "2024-03-17", "none",   "not part of this dataset"),
    "N005": ("2024-07-29", "2024-08-04", "none",   "not significantly affected"),
    "N006": ("2025-09-22", "2025-09-28", "none",   "no major disruptions"),
    "N007": ("2024-05-20", "2024-05-26", "reduces", "improved road conditions"),
    "N008": ("2025-06-09", "2025-06-15", "none",   "No significant disruptions"),
    "N009": ("2025-03-17", "2025-03-23", "none",   "returned to normal"),
    "N010": ("2025-10-27", "2025-11-02", "none",   "without a rate change"),
}

NOTE_SUMMARY = {
    "N001": "flooding on the Chennai-Bangalore highway from Feb 24 to Mar 8 forced longer detours and higher trip costs",
    "N002": "a regional festival week led transporters to add a temporary surcharge on this corridor",
    "N003": "a nationwide diesel price rise pushed freight costs up by roughly 5-7% on all routes",
    "N004": "a new toll plaza was commissioned, but on routes that are not in this dataset",
    "N005": "highway maintenance caused minor delays but costs were not significantly affected",
    "N006": "freight demand stayed stable with no major disruptions",
    "N007": "road conditions improved after resurfacing work was completed",
    "N008": "no significant disruptions were reported and freight movement stayed normal",
    "N009": "the route returned to normal conditions after flood repairs were completed",
    "N010": "a vehicle tracking mandate was introduced, but transporters absorbed the cost with no rate change",
}


def load_notes(path):
    notes = pd.read_csv(path)
    notes["route"] = notes["applies_to"].replace({"All Routes": "ALL"})
    for i, row in notes.iterrows():
        start, end, effect, phrase = NOTE_FACTS[row["note_id"]]
        if phrase.lower() not in row["note"].lower():          
            raise ValueError(f"{row['note_id']}: expected phrase not found in note text")
        if pd.Timestamp(start) < pd.Timestamp(row["date"]):
            raise ValueError(f"{row['note_id']}: window starts before the note date")
        notes.loc[i, ["window_start", "window_end", "effect"]] = [
            pd.Timestamp(start), pd.Timestamp(end), effect]
    notes["window_start"] = pd.to_datetime(notes["window_start"])
    notes["window_end"] = pd.to_datetime(notes["window_end"])
    return notes


def failed_checks(note, route, week_of):
    failed = []
    if note["route"] not in ("ALL", route):
        failed.append("it is about a different route")
    week_start, week_end = week_of, week_of + pd.Timedelta(days=6)
    if not (note["window_start"] <= week_end and note["window_end"] >= week_start):
        failed.append("its dates do not cover this week")
    if note["effect"] != "raises":
        failed.append("it does not describe a cost rise")
    return failed


def check_note(note, route, week_of):
    failed = failed_checks(note, route, week_of)
    if failed:
        return False, " and ".join(failed)
    return True, "route, dates and direction all match"