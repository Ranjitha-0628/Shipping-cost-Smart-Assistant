from src.metrics import build_metrics
from src.flagging import add_z_score

m = add_z_score(build_metrics("data/shipment_records.csv"))
print(f"weeks with an own-history baseline: {m['own_pct'].notna().sum()}")
print(f"typical weekly change vs own history: std {m['own_pct'].std():.1%}")
for rise, z in [(0.05, 2), (0.05, 3), (0.07, 2), (0.08, 2)]:
    n = ((m.own_pct >= rise) & (m.z_score >= z) & (m.peer_pct > 0)).sum()
    print(f"rise >= {rise:.0%} and z >= {z}: {n} rows")
print(f"rise >= 10% alone: {(m.own_pct >= 0.10).sum()} rows")