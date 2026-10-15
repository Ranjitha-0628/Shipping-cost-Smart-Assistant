import pandas as pd

HISTORY_WINDOW = 8 

def load_shipments(path):
    df = pd.read_csv(path, parse_dates=["shipment_date"])

    needed = ["origin", "destination", "route_type", "quantity_tonnes",
              "distance_km", "freight_cost_inr", "shipment_date"] 
    if df[needed].isna().any().any():
        raise ValueError("Missing values found in shipment data")
    if (df[["quantity_tonnes", "distance_km", "freight_cost_inr"]] <= 0).any().any():
        raise ValueError("Non-positive quantity, distance or cost found")

    df["route"] = df["origin"] + "-" + df["destination"]

    df["week_of"] = df["shipment_date"] - pd.to_timedelta(df["shipment_date"].dt.weekday, unit="D")
    df["tonne_km"] = df["quantity_tonnes"] * df["distance_km"]
    return df

def weekly_cost(df):
    """Total cost / total tonne-km per route per week.

    Pooling (instead of averaging each shipment's own ratio) makes big,
    long shipments count for more, which matches how the money is spent.
    """
    weekly = (
        df.groupby(["route", "route_type", "week_of"], as_index=False)
          .agg(total_cost=("freight_cost_inr", "sum"),
               total_tonne_km=("tonne_km", "sum"),
               n_shipments=("shipment_id", "count"))
    )
    weekly["cpt"] = weekly["total_cost"] / weekly["total_tonne_km"]
    return weekly.sort_values(["route", "week_of"]).reset_index(drop=True)


def add_own_history(weekly):
    """Average of up to 8 earlier weeks, never including the current one."""
    bases, counts = [], []
    for _, grp in weekly.groupby("route", sort=False):
        values = grp["cpt"].tolist()
        for i in range(len(values)):
            past = values[max(0, i - HISTORY_WINDOW):i]  
            counts.append(len(past))
            bases.append(sum(past) / len(past) if past else float("nan"))
    weekly["own_base"] = bases
    weekly["n_hist"] = counts
    return weekly


def add_peer_baseline(weekly):
    """Mean cpt of the other routes with the same route_type in the same week."""
    grp = weekly.groupby(["route_type", "week_of"])["cpt"]
    total, count = grp.transform("sum"), grp.transform("count")
    others = (count - 1).where(count > 1)
    others = (count - 1).where(count > 1)  
    weekly["peer_base"] = (total - weekly["cpt"]) / others
    return weekly


def build_metrics(path):
    weekly = weekly_cost(load_shipments(path))
    weekly = add_own_history(weekly)
    weekly = add_peer_baseline(weekly)
    weekly["own_pct"] = weekly["cpt"] / weekly["own_base"] - 1
    weekly["peer_pct"] = weekly["cpt"] / weekly["peer_base"] - 1
    return weekly

