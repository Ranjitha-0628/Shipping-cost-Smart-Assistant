import numpy as np
import pandas as pd
from src.metrics import HISTORY_WINDOW

MIN_RISE_VS_OWN = 0.07
MIN_Z_SCORE = 2.0
MIN_HISTORY_FOR_Z = 4

RECENT_WEEKS = 12     
def add_z_score(weekly):
    stds = []
    for _, grp in weekly.groupby("route", sort=False):
        values = grp["cpt"].tolist()
        for i in range(len(values)):
            past = values[max(0, i - HISTORY_WINDOW):i]
            stds.append(np.std(past, ddof=1) if len(past) >= MIN_HISTORY_FOR_Z else np.nan)
    weekly["own_std"] = stds
    weekly["z_score"] = (weekly["cpt"] - weekly["own_base"]) / weekly["own_std"]
    return weekly

def flag_rows(weekly):
   
    weekly = add_z_score(weekly.copy())
    rising = weekly["own_pct"] >= MIN_RISE_VS_OWN
    unusual = weekly["z_score"] >= MIN_Z_SCORE
    dearer_than_peers = weekly["peer_pct"] > 0
    flagged = weekly[rising & unusual & dearer_than_peers].reset_index(drop=True)
    flagged["recent_flags"] = [
        int(((flagged["route"] == r.route)
             & (flagged["week_of"] <= r.week_of)
             & (flagged["week_of"] > r.week_of - pd.Timedelta(weeks=RECENT_WEEKS))).sum())
        for r in flagged.itertuples()
    ]
    return flagged