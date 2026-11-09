"""The starting field's loss against the host's epoch means (exploratory, after the G-C2.1 verdict).

    python3 -I compare_start.py RECORDS_DIR HOST_ADJUSTED.json OUT.json start_field_s0.json start_field_s1.json

For each epoch that start_field.py evaluated: the host's mean loss over the epoch, the starting field's mean over the
same members and displacements, and their difference; then both adjusted for the draws with the adjustment of
analyse_host.py (the host's raw mean minus its adjusted mean is the epoch's adjustment, the same for both).
"""
import json
import sys
from pathlib import Path

rec, adj_path, out_path = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
adj = json.loads(adj_path.read_text())["adjusted"]
rows = []
for path in sys.argv[4:]:
    sf = json.loads(Path(path).read_text())
    s = sf["seed"]
    hist = json.loads((rec / "runs" / f"label_free_s{s}" / "history.json").read_text())["loss"]
    for ep, v in sorted(sf["epochs"].items(), key=lambda kv: int(kv[0])):
        e = int(ep)
        assert v["steps"] == 512
        host_raw, host_adj = hist[e - 1], adj[str(s)]["epochs"][e - 1]
        shift = host_raw - host_adj
        rows.append({"seed": s, "epoch": e, "host": host_raw, "start": v["mean"], "difference": host_raw - v["mean"],
                     "host_adjusted": host_adj, "start_adjusted": v["mean"] - shift})
out_path.write_text(json.dumps(rows, indent=1))
for r in rows:
    print(f"seed {r['seed']}, epoch {r['epoch']}: host {r['host']:.4f}, starting field {r['start']:.4f}, "
          f"host minus starting field {r['difference']:+.4f}; adjusted: host {r['host_adjusted']:.4f}, "
          f"starting field {r['start_adjusted']:.4f}")
