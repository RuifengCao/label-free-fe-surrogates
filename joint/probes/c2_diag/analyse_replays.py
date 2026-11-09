"""Read the CPU replays of G-C2.1's label-free seeds (exploratory, after the verdict).

    python3 -I analyse_replays.py RECORDS_DIR OUT.json seed0.jsonl seed1.jsonl

RECORDS_DIR is the gate's records folder (records/c2/return/records), for the host's history.json of each seed.
Prints, per replayed seed:
- each epoch's mean loss against the host's (the members and displacements of every step are the same in both);
- the medians of the gradient norms before clipping (encoder, decoder, head, all), the share of clipped steps and the
  encoder's median share of the global norm;
- the encoder bursts: steps whose encoder gradient norm exceeds ten times the median of the previous 256 steps, with
  the encoder's share of the global norm and the decoder's and head's norms over their own medians of those steps;
- the collapses: probes at which the encoder's latent diversity (relative variance of the node latents, mean over
  the three probe displacements) fell below a third of its value at the previous probe;
- the steps around each collapse, the latent diversity and e / (D + delta) at every probe, and the last probe.
Writes the same to OUT.json.
"""
import json
import sys
from pathlib import Path

import numpy as np

rec, out_path = Path(sys.argv[1]), Path(sys.argv[2])
CLIP, WINDOW, FACTOR = 1.0, 256, 10.0
summary = {}
for path in sys.argv[3:]:
    rows = [json.loads(l) for l in open(path) if l.strip()]
    seed = next(r for r in rows if "seed" in r)["seed"]
    st = [r for r in rows if "loss" in r]
    assert [r["step"] for r in st] == list(range(1, len(st) + 1)), "steps must run 1, 2, 3, ... once each"
    host = json.loads((rec / "runs" / f"label_free_s{seed}" / "history.json").read_text())["loss"]
    loss = np.array([r["loss"] for r in st])
    g = {k: np.array([r["grad"][k] for r in st]) for k in ("enc", "dec", "head")}
    tot = np.array([r["grad_total"] for r in st])
    epochs = [{"epoch": e + 1, "replay": float(loss[e * 512:(e + 1) * 512].mean()), "host": float(host[e])}
              for e in range(len(loss) // 512)]
    grads = {**{k: float(np.median(v)) for k, v in g.items()}, "all": float(np.median(tot)),
             "share_clipped": float(np.mean(tot > CLIP)), "all_min": float(tot.min()),
             "enc_share_of_all": float(np.median(g["enc"] / tot))}
    bursts = [{"step": i + 1, "enc": float(g["enc"][i]), "median_before": float(np.median(g["enc"][i - WINDOW:i])),
               "lr": st[i]["lr"], "enc_share_of_all": float(g["enc"][i] / tot[i]),
               "dec_over_median_before": float(g["dec"][i] / np.median(g["dec"][i - WINDOW:i])),
               "head_over_median_before": float(g["head"][i] / np.median(g["head"][i - WINDOW:i]))}
              for i in range(WINDOW, len(st)) if g["enc"][i] > FACTOR * np.median(g["enc"][i - WINDOW:i])]
    probes = [(r["step"], r["probe"]) for r in rows if "probe" in r]
    series = [{"step": s, "latent_rel_var": float(np.mean(p["latent_rel_var"])), "e_over_s": float(np.mean(p["e_over_s"])),
               "uy_std_D8": float(p["uy_std"][2])} for s, p in probes]
    collapses = []
    for a, b in zip(series, series[1:]):
        if b["latent_rel_var"] < a["latent_rel_var"] / 3:
            inside = [x for x in bursts if a["step"] < x["step"] <= b["step"]]
            lo, hi = inside[0]["step"] - 3, inside[-1]["step"] + 2
            collapses.append({"between_probes": [a["step"], b["step"]], "before": a, "after": b,
                              "bursts_inside": [x["step"] for x in inside],
                              "steps": [{"step": r["step"], "loss": r["loss"], **r["grad"], "all": r["grad_total"],
                                         "lr": r["lr"]} for r in st[lo - 1:hi]]})
    summary[seed] = {"steps": len(st), "epochs": epochs, "grad_medians": grads, "bursts": bursts,
                     "collapses": collapses, "probes": series, "last_probe": probes[-1][1]}
out_path.write_text(json.dumps(summary, indent=1))
for seed, s in summary.items():
    print(f"=== seed {seed}: {s['steps']} steps replayed")
    for e in s["epochs"]:
        print(f"  epoch {e['epoch']}: replay {e['replay']:.4f}, host {e['host']:.4f}, difference {e['replay'] - e['host']:+.4f}")
    gm = s["grad_medians"]
    print(f"  median gradient norms before clipping: encoder {gm['enc']:.3f}, decoder {gm['dec']:.2f}, head {gm['head']:.2f}, "
          f"all {gm['all']:.2f} (smallest {gm['all_min']:.2f}); steps clipped: {100 * gm['share_clipped']:.1f}%; "
          f"median share of the encoder in the global norm {gm['enc_share_of_all']:.4f}")
    print(f"  encoder bursts (> {FACTOR:g} times the median of the previous {WINDOW} steps): {len(s['bursts'])}")
    for b in s["bursts"]:
        print(f"    step {b['step']}: {b['enc']:.2f} against {b['median_before']:.3f} ({b['enc'] / b['median_before']:.0f} times), "
              f"lr {b['lr']:.2e}; share of the global norm {b['enc_share_of_all']:.3f}; decoder {b['dec_over_median_before']:.2f} "
              f"and head {b['head_over_median_before']:.2f} times their medians before")
    for c in s["collapses"]:
        a, b = c["before"], c["after"]
        print(f"  collapse between probes at steps {c['between_probes'][0]} and {c['between_probes'][1]}, bursts at {c['bursts_inside']}:")
        print(f"    latent diversity {a['latent_rel_var']:.4f} -> {b['latent_rel_var']:.4f}; e/(D+delta) {a['e_over_s']:.4f} -> "
              f"{b['e_over_s']:.4f}; u_y spread at D = 8 mm {a['uy_std_D8']:.2e} -> {b['uy_std_D8']:.2e}")
        for r in c["steps"]:
            print(f"    step {r['step']}: loss {r['loss']:.3f}, encoder {r['enc']:.2f}, decoder {r['dec']:.1f}, head {r['head']:.1f}, "
                  f"all {r['all']:.1f}")
    p = s["probes"]
    print("  latent diversity at probes 0, 64, ...:", [round(x["latent_rel_var"], 3) for x in p])
    print("  e/(D+delta) at probes 0, 64, ...:   ", [round(x["e_over_s"], 3) for x in p])
    lp = s["last_probe"]
    print(f"  last probe (step {p[-1]['step']}): latent diversity {np.round(lp['latent_rel_var'], 4).tolist()}, "
          f"e/(D+delta) {np.round(lp['e_over_s'], 4).tolist()}, u_y spread {np.round(lp['uy_std'], 5).tolist()}")
