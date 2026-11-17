"""Audit of gate G-C2.2, item 2: did the run keep to the pre-specification and the runbook? Checks made from the
return package and the export of the stamped commit, with the auditor's own code.

  configuration   the returned c22_config.json against the stamped configuration (bytes and canonical SHA-256); the
                  hash carried by the manifest, the three histories and verdict.json;
  code            the stamped hash lists against the stamped files, the table of the pre-specification, and the
                  hashes that the configuration command printed on the laptop;
  sample          the manifest: 644 members; the family parameters of each set against a draw made here with a
                  sampler written here (numpy generator, the family's ranges and rejection rules); no member
                  shared between sets; the times of generation and of the labels;
  labels          the ledger: 132 members once each, levels, convergence, iterations, residual limits, force
                  readings, hashes of the label files;
  training        the histories: seeds, steps, epochs, betas, cap settings, cap events and bursts; the epoch lines of
                  the queue's logs against the histories; attempts.log; times of a step;
  queue           the commands that ran against the runbook's commands; exit codes; the order of events;
  smoke           the host check's report against the runbook's conditions.

Nothing is imported from the gate's evaluation code or from the author's audit scripts. The stamped configuration is
obtained by importing c22.config from the export of the stamped commit.

Usage:  python -I a4_run_checks.py STAMP RECORDS [--out OUT.json]
"""
import argparse
import hashlib
import json
import os
import re
import statistics
import sys

import numpy as np

RANGES = {"t_f": (8.0, 20.0), "t_w": (6.0, 12.0), "r": (8.0, 18.0), "w": (70.0, 110.0), "n": (20.0, 40.0),
          "fy": (235.0, 460.0), "rho": (0.0, 0.9)}      # the family of the pre-specification of G-C2.1
SHA = "ef5376a4d6c3cc98d7888121439c8d959ee817d332958dd6b1141b25e78734bb"
LEVELS = [0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0]


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def draw(n, seed):
    """The family's sampler written again: uniform draws in the order of the keys, rejected where the bearing patch
    (radius 12 mm, clearance 2 mm) reaches the root or the flange tip, or the web is more than 2 mm thicker than
    the flange."""
    rng = np.random.default_rng(seed)
    out = []
    while len(out) < n:
        q = {k: float(rng.uniform(*RANGES[k])) for k in RANGES}
        if q["w"] / 2 - 12.0 < q["t_w"] / 2 + q["r"] + 2.0:
            continue
        if q["n"] < 12.0 + 2.0:
            continue
        if q["t_w"] > q["t_f"] + 2.0:
            continue
        out.append(q)
    return out


def text(path):
    return open(path, "rb").read().decode("utf-8").replace("\r\n", "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stamp"); ap.add_argument("records"); ap.add_argument("--out")
    a = ap.parse_args()
    R, J = a.records, os.path.join(a.stamp, "joint")
    res = {}

    # ---- configuration
    sys.path.insert(0, J)
    from c22.config import config
    cfg = config()
    stamped_bytes = json.dumps(cfg, indent=1, sort_keys=True).encode("ascii")
    got = open(os.path.join(R, "c22_config.json"), "rb").read()
    canon = hashlib.sha256(json.dumps(json.loads(got), sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    man = json.load(open(os.path.join(R, "manifest.json")))
    ver = json.load(open(os.path.join(R, "verdict.json")))
    hist = {s: json.load(open(os.path.join(R, "run_files", f"label_free_s{s}", "history.json"))) for s in (5, 6, 7)}
    res["configuration"] = {
        "returned_file_equals_stamped_bytes": got == stamped_bytes, "returned_file_sha256": hashlib.sha256(got).hexdigest(),
        "canonical_sha256_of_returned": canon, "equals_prespecified": canon == SHA,
        "manifest": man["config_sha256"] == SHA, "verdict": ver["config_sha256"] == SHA,
        "histories": [hist[s]["config_sha256"] == SHA for s in hist],
        "prespec_names_it": SHA in open(os.path.join(J, "docs", "PRESPEC_G-C2.2.md")).read(),
        "runbook_names_it": open(os.path.join(J, "RUNBOOK_C22.md")).read().count(SHA)}

    # ---- code hashes
    code = {}
    for name in ("G-C2.2_code.sha256", "G-C2.1_code.sha256"):
        lines = [l.split() for l in open(os.path.join(J, "docs", name)).read().splitlines() if l.strip()]
        bad = [f for h, f in lines if sha(os.path.join(J, f.lstrip("*"))) != h]
        code[name] = {"lines": len(lines), "files_differing": bad}
    lines22 = {f.lstrip("*"): h for h, f in (l.split() for l in open(os.path.join(J, "docs", "G-C2.2_code.sha256")).read().splitlines() if l.strip())}
    log = text(os.path.join(R, "queue", "71_c22_config.log")).splitlines()
    printed = {}
    for l in log:
        m = re.match(r"^(?:repository )?(\S+\.py) ([0-9a-f]{64})(?: checked)?$", l)
        if m:
            printed[m.group(1)] = m.group(2)
    def stamped_hash(f):
        for k, h in lines22.items():
            if k == f or k.endswith("/" + f) or k.endswith(f):
                return h
        return None
    code["config_log"] = {"first_line_is_hash": log[1] == "config sha256 " + SHA, "hashes_printed": len(printed),
                          "repository_lines": sum(l.startswith("repository ") and l.endswith(" checked") for l in log),
                          "differing_from_hash_list": [f for f, h in printed.items() if stamped_hash(f) != h]}
    pres = open(os.path.join(J, "docs", "PRESPEC_G-C2.2.md")).read()
    table = dict(re.findall(r"\| `(c22/\S+?)` \| `([0-9a-f]{64})` \|", pres))
    code["prespec_table"] = {"rows": len(table), "differing_from_files": [f for f, h in table.items() if sha(os.path.join(J, f)) != h]}
    res["code"] = code

    # ---- sample
    inst = man["instances"]
    by_split = {}
    for r in inst:
        by_split.setdefault(r["split"], []).append(r)
    samp = {"n": man["n"], "instances": len(inst), "sizes": {k: len(v) for k, v in by_split.items()}}
    for split, seed, n in (("train", 20261106, 512), ("eval", 20261113, 64), ("former", 20261107, 64)):
        mine = draw(n, seed)
        samp[f"{split}_equals_draw_seed_{seed}"] = [r["params"] for r in by_split[split]] == mine
        samp[f"{split}_ids_in_order"] = [r["id"] for r in by_split[split]] == [f"{split}_{i:04d}" for i in range(n)]
    samp["tested_equal_configuration"] = {r["id"]: r["params"] for r in by_split["tested"]} == {"tested_" + k: v for k, v in cfg["data"]["tested"].items()}
    keyset = {}
    for r in inst:
        keyset.setdefault(json.dumps(r["params"], sort_keys=True), []).append(r["id"])
    samp["members_with_the_same_parameters"] = [v for v in keyset.values() if len(v) > 1]
    samp["eval_fy_below_300"] = sum(r["params"]["fy"] < 300 for r in by_split["eval"])
    samp["configured_seeds"] = {k: cfg["data"][k] for k in ("train_seed", "eval_seed", "former_eval_seed", "seeds_seen_before_stamp")}
    res["sample"] = samp

    # ---- labels
    led = json.load(open(os.path.join(R, "ledger.json")))
    ids = [r["id"] for r in inst if r["split"] in ("eval", "former", "tested")]
    msha = {r["id"]: r["sha256"] for r in inst}
    lim = cfg["data"]["kkt_limits"]
    worst = {k: (min if op == ">=" else max)(e["kkt_worst"][k] for e in led) for k, (op, _) in lim.items()}
    lab = {"entries": len(led), "distinct": len({e["id"] for e in led}), "exactly_the_labelled_sets": sorted(e["id"] for e in led) == sorted(ids),
           "levels_ok": all(e["levels"] == LEVELS for e in led), "all_converged": all(all(e["converged"]) for e in led),
           "max_iterations": max(max(e["iterations"]) for e in led), "worst": worst,
           "within_limits": {k: bool(worst[k] >= v if op == ">=" else worst[k] <= v) for k, (op, v) in lim.items()},
           "max_F_vs_F_sigma": max(e["F_vs_F_sigma"] for e in led), "solvers": sorted({e["solver"] for e in led}),
           "inst_sha_equal_manifest": all(e["inst_sha256"] == msha[e["id"]] for e in led),
           "label_files_with_ledger_sha": sum(sha(os.path.join(R, "labels", e["id"] + ".npz")) == e["label_sha256"] for e in led),
           "label_files_in_package": len([f for f in os.listdir(os.path.join(R, "labels")) if f.endswith(".npz")]),
           "first_time": min(e["time"][:19] for e in led), "last_time": max(e["time"][:19] for e in led),
           "seconds_min_median_max": [min(e["seconds"] for e in led), statistics.median(e["seconds"] for e in led), max(e["seconds"] for e in led)]}
    for split in ("eval", "former", "tested"):
        t = [e["time"][:19] for e in led if e["id"].startswith(split)]
        lab[f"times_{split}"] = [min(t), max(t)]
        lg = text(os.path.join(R, "queue", {"eval": "73a_c22_label_eval.log", "former": "73b_c22_label_former.log", "tested": "73c_c22_label_tested.log"}[split])).splitlines()
        lab[f"log_{split}"] = {"converged_lines": sum(l.endswith(" converged") for l in lg), "not_converged_lines": sum("NOT CONVERGED" in l for l in lg),
                               "labelled_line": [l for l in lg if l.startswith("labelled")]}
    lab["check_labels_line"] = [l for l in text(os.path.join(R, "queue", "73d_c22_check_labels.log")).splitlines() if l.startswith("{")][0][:80]
    res["labels"] = lab

    # ---- training
    tr = {}
    logs = {5: ["74_c22_train_s5.log", "74_c22_train_s5_c.log"], 6: ["75_c22_train_s6.log"], 7: ["76_c22_train_s7.log"]}
    all_sec = []
    for s, h in hist.items():
        ep = np.array(h["epoch_seconds"]); loss = np.array(h["loss"])
        ce, bu = h["cap_events"], h["bursts"]
        steps_c = [c[0] for c in ce]; steps_b = [b[0] for b in bu]
        lines, warn, starts, finals = [], 0, 0, []
        for name in logs[s]:
            for l in text(os.path.join(R, "queue", name)).splitlines():
                m = re.match(r"^epoch (\d+) loss (\S+) (\S+) s; cap events (\d+), bursts (\d+)$", l)
                if m:
                    lines.append((int(m.group(1)), m.group(2), float(m.group(3)), int(m.group(4)), int(m.group(5))))
                warn += "UserWarning" in l
                starts += l.startswith("start label_free_s")
                if l.startswith('{"status"'):
                    finals.append(l)
        mism = []
        for k, (e, lo, sec, nc, nb) in enumerate(lines):
            ok = (e == k + 1 and lo == f"{loss[k]:.6g}" and sec == float(ep[k])
                  and nc == sum(x <= 512 * e for x in steps_c) and nb == sum(x <= 512 * e for x in steps_b))
            if not ok:
                mism.append(e)
        per_step = ep / 512.0
        all_sec.append(per_step)
        tr[s] = {"seed": h["seed"], "arm": h["arm"], "total_steps": h["total_steps"], "steps": h["steps"], "epochs": len(loss), "status": h["status"],
                 "betas": h["betas"], "cap": h["cap"], "torch": h["torch"], "gpu": h["gpu"], "device": h["device"], "matmul": h["matmul_precision"],
                 "resumes": h["resumes"], "resumed_from_epoch": h["resumed_from_epoch"], "peak_memory_GiB": round(h["peak_memory_GiB"], 4),
                 "cap_events": len(ce), "bursts": len(bu), "first_cap_step": steps_c[0], "cap_steps_increasing": steps_c == sorted(set(steps_c)),
                 "cap_ratios_all_above_5": all(c[1] > 5 or c[1] is None for c in ce), "min_cap_ratio": min(c[1] for c in ce), "max_cap_ratio": max(c[1] for c in ce),
                 "bursts_all_above_10": all(b[1] > 10 for b in bu), "bursts_subset_of_cap_events": set(map(tuple, bu)) <= set(map(tuple, ce)),
                 "cap_events_with_ratio_above_10": sum(c[1] > 10 for c in ce), "last_step_of_event": max(steps_c),
                 "share_of_steps_capped": len(ce) / h["steps"],
                 "log_epoch_lines": len(lines), "log_lines_differing_from_history": mism, "warnings_in_logs": warn, "start_lines": starts, "final_lines": finals,
                 "loss_first": float(loss[0]), "loss_mean_1_10": float(loss[:10].mean()), "loss_mean_191_200": float(loss[-10:].mean()),
                 "loss_last10_min_max": [float(loss[-10:].min()), float(loss[-10:].max())], "loss_max": float(loss.max()), "loss_max_epoch": int(loss.argmax()) + 1,
                 "loss_min": float(loss.min()), "loss_all_finite": bool(np.isfinite(loss).all()),
                 "hours": float(ep.sum() / 3600), "seconds_per_step_min_median_max": [float(per_step.min()), float(np.median(per_step)), float(per_step.max())],
                 "epochs_below_0.38": int((per_step < 0.38).sum()), "epochs_above_0.8": int((per_step > 0.8).sum()),
                 "attempts": text(os.path.join(R, "run_files", f"label_free_s{s}", "attempts.log")).splitlines()}
        if s == 5:
            tr[s]["median_step_before_pause"] = float(np.median(per_step[:75])); tr[s]["median_step_after_pause"] = float(np.median(per_step[75:]))
            tr[s]["hours_before"] = float(ep[:75].sum() / 3600); tr[s]["hours_after"] = float(ep[75:].sum() / 3600)
        # where the slow epochs lie (more than 0.6 s a step): runs of consecutive epochs
        slow = per_step > 0.6
        runs, k = [], 0
        while k < 200:
            if slow[k]:
                j = k
                while j + 1 < 200 and slow[j + 1]:
                    j += 1
                runs.append([k + 1, j + 1]); k = j + 1
            else:
                k += 1
        tr[s]["runs_of_epochs_above_0.6_s_a_step"] = runs
    allp = np.concatenate(all_sec)
    tr["all"] = {"epochs": int(allp.size), "min": float(allp.min()), "max": float(allp.max()), "below_0.38": int((allp < 0.38).sum()),
                 "above_0.8": int((allp > 0.8).sum()), "hours": float(sum(float(np.sum(x)) for x in all_sec) * 512 / 3600)}
    res["training"] = tr

    # ---- queue
    q = {}
    Q = os.path.join(R, "queue")
    runbook = open(os.path.join(J, "RUNBOOK_C22.md")).read()
    cmds = re.findall(r"^PY (gate/joint/c22/\S+) (.*)$", runbook, flags=re.M)
    want = [[c[0]] + c[1].split() for c in cmds]
    jobs = {}
    for f in sorted(os.listdir(Q)):
        if f.endswith(".job.json"):
            j = json.loads(text(os.path.join(Q, f)))
            jobs[f[:-9]] = [j["script"]] + [str(x) for x in j["args"]]
    done = {f[:-10]: json.loads(text(os.path.join(Q, f))) for f in sorted(os.listdir(Q)) if f.endswith(".done.json")}
    ran = [v for k, v in jobs.items() if v[0].startswith("gate/joint/c22/")]
    q["runbook_commands"] = len(want)
    q["runbook_commands_not_run_as_written"] = [" ".join(w) for w in want if w not in ran]
    q["gate_commands_run_that_are_not_in_the_runbook"] = [k for k, v in jobs.items() if v[0].startswith("gate/joint/c22/") and v not in want]
    q["jobs"] = len(jobs); q["done_records"] = len(done)
    q["jobs_without_done_record"] = sorted(set(jobs) - set(done))
    q["non_zero_exit"] = {k: [d["returncode"], d["killed"]] for k, d in done.items() if d["returncode"] != 0}
    order = sorted(((d["started"], d["ended"], k) for k, d in done.items() if k.startswith("7")))
    q["order"] = [[k, s[5:19], e[5:19]] for s, e, k in order]
    q["no_overlap"] = all(order[i][1] <= order[i + 1][0] for i in range(len(order) - 1))
    q["guard_lines"] = {f[:-4]: [l for l in text(os.path.join(Q, f)).splitlines() if l.startswith("guard:")] for f in sorted(os.listdir(Q)) if f.endswith("guard.log")}
    q["evaluate_last_line"] = [l for l in text(os.path.join(Q, "77_c22_evaluate.log")).splitlines() if l.startswith("{")]
    q["cancelled_files"] = [f for f in os.listdir(Q) if "cancel" in f.lower()]
    res["queue"] = q

    # ---- smoke
    sm = json.load(open(os.path.join(R, "smoke", "smoke_report.json")))
    res["smoke"] = sm
    res["smoke_log_last_lines"] = [l for l in text(os.path.join(Q, "70_c22_smoke.log")).splitlines() if "smoke test" in l]

    # ---- verdict record
    res["verdict_record"] = {k: ver[k] for k in ("gate", "judged", "status", "missing", "non_finite", "verdict", "C1", "C2", "C1_value", "C2_value", "per_seed")}
    res["verdict_record"]["reported_readings"] = list(ver["reported_readings"])
    res["verdict_record"]["sha256"] = sha(os.path.join(R, "verdict.json"))
    out = json.dumps(res, indent=1, default=str)
    if a.out:
        open(a.out, "w").write(out)
    print(out)


if __name__ == "__main__":
    main()
