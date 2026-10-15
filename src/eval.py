import os
import tempfile

import pandas as pd

from src.metrics import build_metrics
from src.flagging import flag_rows
from src.notes import load_notes
from src.verdict import decide

SHIPMENTS = "data/shipment_records.csv"
NOTES = "data/context_notes.csv"

LABELS = {
    ("Ahmedabad-Mumbai", "2025-01-20"): "N002",
    ("Chennai-Bangalore", "2025-02-24"): "N001",
    ("Chennai-Bangalore", "2025-03-03"): "N001",
    ("Mumbai-Delhi", "2025-05-12"): "N003",
    ("Delhi-Chennai", "2024-02-05"): None,
    ("Delhi-Jaipur", "2024-11-11"): None,
    ("Delhi-Jaipur", "2024-11-18"): None,
    ("Kolkata-Bhubaneswar", "2025-05-26"): None,
    ("Mumbai-Pune", "2025-09-15"): None,
    ("Mumbai-Pune", "2025-10-20"): None,
    ("Mumbai-Pune", "2025-11-03"): None,
    ("Mumbai-Pune", "2025-11-17"): None,
    ("Mumbai-Pune", "2025-12-01"): None,
}

ADVERSARIAL = [
    ("flood note, wrong route",             "Delhi-Jaipur",      "2025-02-24", ["N001"], None),
    ("flood note, week after its window",   "Chennai-Bangalore", "2025-03-10", ["N001"], None),
    ("flood note, week before its window",  "Chennai-Bangalore", "2025-02-17", ["N001"], None),
    ("'not significantly affected' note",   "Mumbai-Delhi",      "2024-07-29", ["N005"], None),
    ("road-improvement note",               "Delhi-Jaipur",      "2024-05-20", ["N007"], None),
    ("toll note for routes not in dataset", "Ahmedabad-Mumbai",  "2024-03-11", ["N004"], None),
    ("'stable demand' note",                "Mumbai-Pune",       "2025-09-22", ["N006"], None),
    ("'returned to normal' note",           "Chennai-Bangalore", "2025-03-17", ["N009"], None),
    ("'no rate change' note",               "Mumbai-Pune",       "2025-10-27", ["N010"], None),
    ("diesel note, months too late",        "Mumbai-Pune",       "2025-09-15", ["N003"], None),
    ("all-routes note, right week (control)", "Kolkata-Bhubaneswar", "2025-05-12", ["N003"], "N003"),
    ("wrong note ranked first, right second", "Chennai-Bangalore", "2025-02-24", ["N005", "N001"], "N001"),
]

INJECTED = [("Kolkata-Bhubaneswar", "2024-09-09", 1.25), ("Delhi-Chennai", "2025-08-04", 1.20)]


def run_pipeline(shipments_path, notes, retriever):
    results = []
    for _, row in flag_rows(build_metrics(shipments_path)).iterrows():
        results.append((row, decide(row, retriever.search(row["route"], row["week_of"]))))
    return results


def _key(row):
    return (row["route"], row["week_of"].strftime("%Y-%m-%d"))


def check_labels(results):
    got = {_key(r): (v["note"]["note_id"] if v["justified"] else None) for r, v in results}
    tp = sum(1 for k, n in LABELS.items() if n and got.get(k) == n)
    wrong_note = sum(1 for k, n in got.items() if n and LABELS.get(k) != n)
    pred_just = sum(1 for n in got.values() if n)
    actual_just = sum(1 for n in LABELS.values() if n)
    print(f"[labels] flagged {len(got)} rows, labelled {len(LABELS)}; "
          f"missing={set(LABELS)-set(got)}, unlabelled={set(got)-set(LABELS)}")
    print(f"[labels] justified precision {tp}/{pred_just}, recall {tp}/{actual_just}, "
          f"fabricated (justified with a wrong note) = {wrong_note}")
    return tp == pred_just == actual_just and wrong_note == 0 and set(got) == set(LABELS)


def check_adversarial(notes):
    by_id = notes.set_index("note_id", drop=False)
    ok = True
    for desc, route, week, ids, expected in ADVERSARIAL:
        row = {"route": route, "week_of": pd.Timestamp(week), "own_pct": 0.10}
        v = decide(row, [by_id.loc[i] for i in ids])
        got = v["note"]["note_id"] if v["justified"] else None
        passed = got == expected
        ok &= passed
        print(f"[adversarial] {'PASS' if passed else 'FAIL'}: {desc} -> {got}")
    return ok


def check_injected_spikes(notes, retriever):
    df = pd.read_csv(SHIPMENTS, parse_dates=["shipment_date"])
    df["route"] = df["origin"] + "-" + df["destination"]
    df["week_of"] = df["shipment_date"] - pd.to_timedelta(df["shipment_date"].dt.weekday, unit="D")
    df["freight_cost_inr"] = df["freight_cost_inr"].astype(float)   # allow scaled values
    for route, week, mult in INJECTED:
        mask = (df["route"] == route) & (df["week_of"] == pd.Timestamp(week))
        df.loc[mask, "freight_cost_inr"] *= mult
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "spiked.csv")
        df.drop(columns=["route", "week_of"]).to_csv(path, index=False)
        got = {_key(r): v["justified"] for r, v in run_pipeline(path, notes, retriever)}
    ok = True
    for route, week, mult in INJECTED:
        passed = got.get((route, week)) is False      # flagged AND unexplained
        ok &= passed
        print(f"[injected] {'PASS' if passed else 'FAIL'}: x{mult} on {route} {week} "
              f"-> {'flagged, unexplained' if passed else got.get((route, week), 'not flagged')}")
    original_still_flagged = set(LABELS) <= set(got)
    print(f"[injected] original flags all still present: {original_still_flagged}")
    return ok and original_still_flagged


def check_retrieval_recall(retriever, k):
    ok = True
    for (route, week), note_id in LABELS.items():
        if not note_id:
            continue
        top = [n["note_id"] for n in retriever.search(route, pd.Timestamp(week), k)]
        passed = note_id in top
        ok &= passed
        print(f"[retrieval] {'PASS' if passed else 'FAIL'}: {note_id} in top {k} for {route} {week}: {top}")
    return ok


def main():
    from src.retrieval import NoteRetriever, TOP_K
    notes = load_notes(NOTES)
    retriever = NoteRetriever(notes)
    results = [
        check_labels(run_pipeline(SHIPMENTS, notes, retriever)),
        check_adversarial(notes),
        check_injected_spikes(notes, retriever),
        check_retrieval_recall(retriever, TOP_K),
    ]
    print("ALL CHECKS PASSED" if all(results) else "SOME CHECKS FAILED")


if __name__ == "__main__":
    main()