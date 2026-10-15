import sys
import pandas as pd
from src.metrics import build_metrics
from src.flagging import flag_rows
from src.notes import load_notes
from src.retrieval import NoteRetriever
from src.verdict import decide, build_reason
from src.output import to_record, write_csv

SHIPMENTS = "data/shipment_records.csv"
NOTES = "data/context_notes.csv"
OUTPUT = sys.argv[1] if len(sys.argv) > 1 else "output.csv"

def main():
    flags = flag_rows(build_metrics(SHIPMENTS))
    notes = load_notes(NOTES)
    all_notes = [n for _, n in notes.iterrows()]
    retriever = NoteRetriever(notes)

    records = []
    for _, row in flags.iterrows():
        candidates = retriever.search(row["route"], row["week_of"])
        verdict = decide(row, candidates, all_notes=all_notes)
        records.append(to_record(row, verdict, build_reason(row, verdict)))

    write_csv(records, OUTPUT)
    print(f"{len(flags)} flagged rows written to {OUTPUT}")


if __name__ == "__main__":
    main()