import csv

COLUMNS = ["route", "week_of", "cost_per_tonne_km", "vs_own_history",
           "vs_similar_routes", "flagged", "matched_note_id", "reason"]


def to_record(flag_row, verdict, reason):
    return {
        "route": flag_row["route"],
        "week_of": flag_row["week_of"].strftime("%Y-%m-%d"),
        "cost_per_tonne_km": f"{flag_row['cpt']:.2f}",
        "vs_own_history": f"{flag_row['own_pct']:+.1%} vs this route's past average",
        "vs_similar_routes": f"{flag_row['peer_pct']:+.1%} vs similar-length routes this week",
        "flagged": "No (justified)" if verdict["justified"] else "Yes",
        "matched_note_id": verdict["note"]["note_id"] if verdict["justified"] else "",
        "reason": reason,
    }


def write_csv(records, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(records)